"""PySide6 research demonstrator: document → proposal → review → calendar.

This is the actual application, not the separate Assignment 3 design prototype.
Widgets delegate scheduling and persistence to tested backend modules. Network
inference runs in QThread so Qt's event loop can continue repainting the window.
Only the main thread updates widgets; the worker returns values through signals.
"""
import calendar
import hashlib
import json
from datetime import date
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import QDate, QThread, Signal, QPointF
from PySide6.QtGui import QColor, QTextCharFormat, QFont
from PySide6.QtWidgets import (
    QCalendarWidget, QComboBox, QFileDialog, QHBoxLayout, QInputDialog,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QPlainTextEdit, QPushButton,
    QSplitter, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)
from .core import baseline, extract_pdf
from .local_model import extract_local
from .session import ReviewSession
from .storage import Store, export_csv
from .comparison import HEADERS, load_comparison

ROOT = Path(__file__).resolve().parents[1]


class InferenceWorker(QThread):
    """Own one bounded request; emit data rather than touching Qt widgets."""
    succeeded = Signal(object, object)
    failed = Signal(str)

    def __init__(self, pages, model):
        super().__init__()
        self.pages, self.model = list(pages), model

    def run(self):
        try:
            # Unique names retain individual prompts/results for the report.
            evidence = ROOT/'evidence'/f'local-run-{uuid4().hex}.json'
            evidence.parent.mkdir(exist_ok=True)
            schedule, record = extract_local(self.pages,self.model,evidence_path=evidence)
            self.succeeded.emit(schedule, record)
        except Exception as error:
            self.failed.emit(f'{type(error).__name__}: {error}')


class MainWindow(QMainWindow):
    def __init__(self, store_path: Path | None = None):
        super().__init__()
        self.setFont(QFont('Segoe UI',10))
        self.setWindowTitle('ParentVault AI — Document to Calendar')
        self.session = ReviewSession()
        self.worker = None
        self._syncing = False
        self.store = Store(store_path or ROOT/'data'/'parentvault.sqlite3')
        from .views import build
        build(self)
        self.refresh_records()
        self.update_controls()

    @staticmethod
    def month_default_date():
        return QDate.currentDate()

    def show_page(self, index):
        """Navigate without changing the current document or approval state."""
        self.tabs.setCurrentIndex(index)
        self.navigation.button(index).setChecked(True)

    def page_changed(self, index):
        self.navigation.button(index).setChecked(True)

    def set_source_text(self):
        """Both document and review pages display the same extracted evidence."""
        text='\n\n'.join(f'PAGE {i+1}\n{page}' for i,page in enumerate(self.session.pages))
        self.source.setPlainText(text)
        self.document_source.setPlainText(text)

    def sync_form(self):
        """Populate controls without treating programmatic updates as user edits.

        The structured editor remains the serialization boundary. Form changes
        update that editor, then use exactly the same revalidation/approval path.
        An invalid advanced edit leaves existing form values visible but cannot
        preserve approval or enable generation.
        """
        from .core import Schedule
        try:
            schedule=Schedule.model_validate_json(self.rules.toPlainText())
        except ValueError:
            self.warning_label.setText('No valid proposed rules yet. Extract a plan or correct the advanced fields.')
            return
        self._syncing=True
        try:
            self.anchor_edit.setDate(QDate(schedule.anchor_date.year,schedule.anchor_date.month,schedule.anchor_date.day))
            for control,owner in zip(self.cycle_edits,schedule.cycle):
                control.setCurrentIndex(control.findData(owner))
                control.setStyleSheet('background:'+('#e4efff' if owner=='A' else '#fff0c9')+';')
            self.exchange_day.setText(schedule.exchange_weekday or '')
            self.exchange_time.setText(schedule.exchange_time or '')
            self.evidence_label.setText('\n'.join(f'Page {item.page}: {item.quote}' for item in schedule.evidence))
            self.warning_label.setText('Unresolved: '+'; '.join(schedule.warnings) if schedule.warnings else
                'Review required: verify the start date and rotation against the source. No unresolved warnings were returned.')
        finally:
            self._syncing=False

    def form_edited(self, *_):
        if self._syncing: return
        self.session.invalidate()
        self.clear_results()
        try:
            data=json.loads(self.rules.toPlainText())
            data['anchor_date']=self.anchor_edit.date().toString('yyyy-MM-dd')
            data['cycle']=[control.currentData() for control in self.cycle_edits]
            data['exchange_weekday']=self.exchange_day.text().strip() or None
            data['exchange_time']=self.exchange_time.text().strip() or None
            self.rules.setPlainText(json.dumps(data,indent=2))
        except (ValueError,TypeError):
            self.review_checkbox.setChecked(False)
            self.status.setText('Correct the invalid advanced rules before editing structured fields.')
        self.update_controls()

    def filter_records(self):
        query=self.record_search.text().strip().casefold()
        visible=[]
        for row in range(self.record_table.rowCount()):
            value=self.record_table.item(row,0)
            matches=value is not None and query in value.text().casefold()
            self.record_table.setRowHidden(row,not matches)
            if matches:visible.append(row)
        # Filtering must also update the action target. Otherwise Load/Delete
        # could operate on an old selection that is now hidden by the search.
        current=self.record_table.currentRow()
        if current not in visible:
            self.record_table.clearSelection()
            if visible:self.record_table.selectRow(visible[0])
            else:self.record_table.setCurrentCell(-1,-1)
        self.record_selected()

    def record_selected(self):
        row=self.record_table.currentRow()
        item=self.record_table.item(row,0) if row>=0 else None
        if item is not None and not self.record_table.isRowHidden(row):
            record_id=item.data(256)
            index=self.record_list.findData(record_id)
            self.record_list.setCurrentIndex(index)
        else:
            self.record_list.setCurrentIndex(-1)
        self.update_controls()

    def choose_comparison(self):
        path,_=QFileDialog.getOpenFileName(self,'Open recorded evaluator results',str(ROOT/'data'),'JSON files (*.json)')
        if not path: return
        try: self.open_comparison(Path(path))
        except Exception as error: self.error(error)

    def open_comparison(self, path: Path):
        """Render reviewed result files, keeping failures visibly distinct."""
        # Clear first: a malformed replacement must not leave prior results
        # looking as though they came from the newly selected evidence file.
        self.comparison_table.setRowCount(0)
        self.comparison_label.setText('Loading historical results…')
        manifest=ROOT/'fixtures'/'formal_fixture_answers.json'
        try:
            answers=json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else {}
            rows=load_comparison(path,answers)
        except Exception:
            self.comparison_label.setText('Selected results were not loaded. Previous comparison cleared.')
            raise
        self.comparison_table.setRowCount(len(rows))
        for index,row in enumerate(rows):
            for column,value in enumerate(row):
                item=QTableWidgetItem(value)
                item.setToolTip(value)  # Long cycles/errors remain inspectable.
                if column==5:
                    item.setBackground(QColor('#ffd5d5' if value in ('MISMATCH','MISSED WARNING') else
                                              '#e7f3e8' if value=='Match' else '#fff0cc'))
                self.comparison_table.setItem(index,column,item)
        self.comparison_table.resizeColumnsToContents()
        for column in range(len(HEADERS)):
            self.comparison_table.setColumnWidth(column,min(260,self.comparison_table.columnWidth(column)))
        self.comparison_table.resizeRowsToContents()
        self.comparison_label.setText(f'Historical evidence: {path.parent.name}/{path.name} | {len(rows)} comparison rows. No new inference was run.')

    def update_controls(self):
        """Make workflow prerequisites visible in control availability."""
        busy=self.worker is not None and self.worker.isRunning()
        has_document=bool(self.session.pages)
        self.open_button.setEnabled(not busy)
        for button in (self.load_button,self.delete_button):
            button.setEnabled(not busy and self.record_list.currentData() is not None)
        self.model.setEnabled(not busy)
        self.baseline_button.setEnabled(has_document and not busy)
        self.ai_button.setEnabled(has_document and not busy)
        self.rules.setReadOnly(busy)
        for control in [self.anchor_edit,*self.cycle_edits,self.exchange_day,self.exchange_time,self.review_checkbox]:
            control.setEnabled(bool(self.rules.toPlainText().strip()) and not busy)
        self.approval_badge.setText('Rules approved' if self.session.approved else 'Not yet approved')
        self.approve_button.setEnabled(bool(self.rules.toPlainText().strip()) and self.review_checkbox.isChecked() and not busy)
        self.generate_button.setEnabled(self.session.approved and not busy)
        self.save_button.setEnabled(self.session.approved and not busy)
        self.export_button.setEnabled(bool(self.session.rows) and not busy)

    def clear_results(self):
        # Clearing both the table and date formats prevents a previous plan's
        # colors from remaining visible after rules become unapproved.
        self.table.setRowCount(0)
        self.month.setDateTextFormat(QDate(),QTextCharFormat())
        self.month.set_ownership([])

    def rules_edited(self):
        self.session.invalidate(); self.clear_results()
        self.review_checkbox.setChecked(False)
        self.sync_form()
        self.status.setText('Unapproved — validate and approve the current edited rules before generating dates.')
        self.update_controls()

    def error(self, error):
        self.status.setText(f'Action failed: {error}')
        QMessageBox.warning(self,'Action failed',str(error))
        self.update_controls()

    def open_pdf(self):
        path,_=QFileDialog.getOpenFileName(self,'Select fictional text PDF',str(ROOT/'fixtures'),'PDF files (*.pdf)')
        if not path: return  # Cancel is not replacement; preserve the current session.
        # Invalidate first, so even a failed replacement cannot leave an old
        # calendar looking like it belongs to the newly selected filename.
        self.session=ReviewSession(); self.rules.clear(); self.source.clear(); self.document_source.clear(); self.clear_results()
        self.pdf_document.close()
        self.file_label.setText(Path(path).name)
        try:
            pages=extract_pdf(Path(path))
            digest=hashlib.sha256(Path(path).read_bytes()).hexdigest()
            self.session.replace_document(pages,Path(path).name,digest)
            self.pdf_document.load(path)
            self.document_preview_tabs.setCurrentIndex(0)
            self.review_preview_tabs.setCurrentIndex(0)
            self.set_source_text()
            self.status.setText('Text extracted. Choose baseline or local AI extraction.')
        except Exception as error: self.error(error)
        self.update_controls()

    def present(self, schedule, message):
        self.session.propose(schedule)
        self.set_source_text()
        self.file_label.setText(self.session.source_name)
        self.rules.setPlainText(schedule.model_dump_json(indent=2))
        self.month.setCurrentPage(schedule.anchor_date.year,schedule.anchor_date.month)
        if self.pdf_document.pageCount():
            self.review_pdf_view.pageNavigator().jump(schedule.evidence[0].page-1,QPointF(),0)
        else:
            self.review_preview_tabs.setCurrentIndex(1)
        self.show_page(1)
        self.status.setText(message+' Review the source and approve the rules.')
        self.update_controls()

    def run_baseline(self):
        self.session.invalidate(); self.rules.clear(); self.clear_results()
        try: self.present(baseline(self.session.pages),'Baseline proposal ready.')
        except Exception as error: self.error(error)

    def run_ai(self):
        if not self.model.text().strip():
            self.error('Enter the exact loaded LM Studio model identifier'); return
        self.session.invalidate(); self.rules.clear(); self.clear_results()
        self.worker=InferenceWorker(self.session.pages,self.model.text().strip())
        self.worker.succeeded.connect(self.ai_ready)
        self.worker.failed.connect(self.error)
        self.worker.finished.connect(self.worker_finished)
        self.worker.start()
        self.status.setText('Local AI is extracting proposed rules. Request has a bounded timeout.')
        self.update_controls()

    def ai_ready(self, schedule, record):
        try: self.present(schedule,f"Local AI validated in {record['elapsed_seconds']:.2f} seconds.")
        except Exception as error: self.error(error)

    def worker_finished(self):
        self.worker.deleteLater(); self.worker=None; self.update_controls()

    def approve(self):
        if not self.review_checkbox.isChecked():
            self.status.setText('Check that you reviewed the rules and source before approval.')
            return
        try:
            self.session.approve(self.rules.toPlainText())
            self.status.setText('Approved. Generate the displayed month or save the configuration.')
        except Exception as error: self.error(error)
        self.update_controls()

    def month_changed(self, year, month):
        # Month navigation changes the requested output range, not the approved
        # source rules. Clear old rows to avoid exporting a different month.
        self.session.rows=[]; self.clear_results(); self.update_controls()

    def generate(self):
        try:
            year,month=self.month.yearShown(),self.month.monthShown()
            rows=self.session.generate(date(year,month,1),date(year,month,calendar.monthrange(year,month)[1]))
            self.table.setRowCount(len(rows))
            for index,row in enumerate(rows):
                self.table.setItem(index,0,QTableWidgetItem(row['date']))
                self.table.setItem(index,1,QTableWidgetItem('Parent '+row['parent']))
                fmt=QTextCharFormat()
                fmt.setBackground(QColor('#cfe8ff' if row['parent']=='A' else '#ffe6aa'))
                self.month.setDateTextFormat(QDate.fromString(row['date'],'yyyy-MM-dd'),fmt)
            self.month.set_ownership(rows)
            self.status.setText(f'Generated {len(rows)} overnight assignments from approved rules.')
        except Exception as error: self.error(error)
        self.update_controls()

    def export(self):
        path,_=QFileDialog.getSaveFileName(self,'Export calendar CSV',str(ROOT/'calendar.csv'),'CSV files (*.csv)')
        if not path: return
        # QFileDialog normally confirms replacement; an explicit second check
        # here also protects platforms that disable the native dialog prompt.
        overwrite=Path(path).exists()
        if overwrite and QMessageBox.question(self,'Replace file?',f'Replace {Path(path).name}?') != QMessageBox.StandardButton.Yes: return
        try:
            export_csv(Path(path),self.session.rows,overwrite)
            self.status.setText('Calendar CSV exported successfully.')
        except Exception as error: self.error(error)

    def refresh_records(self):
        self.record_list.clear()
        records=self.store.list_records()
        self.record_table.blockSignals(True)
        self.record_table.setRowCount(len(records))
        for row,(record_id,name,created) in enumerate(records):
            self.record_list.addItem(f'{name} | {created}',record_id)
            item=QTableWidgetItem(name)
            item.setData(256,record_id)
            self.record_table.setItem(row,0,item)
            self.record_table.setItem(row,1,QTableWidgetItem('Review again when loaded'))
            self.record_table.setItem(row,2,QTableWidgetItem(created[:16].replace('T',' ')))
        self.record_table.resizeColumnsToContents()
        self.record_table.blockSignals(False)
        self.filter_records()

    def save(self):
        try:
            self.store.save(self.record_name.text(),self.session)
            self.refresh_records(); self.status.setText('Approved configuration saved locally.')
        except Exception as error: self.error(error)

    def load(self):
        record_id=self.record_list.currentData()
        if record_id is None: return
        try:
            session=self.store.load(record_id)
            self.session=session; self.clear_results()
            # Saved provenance includes extracted source pages, not a retained
            # PDF file. Never keep showing the previous document's PDF preview.
            self.pdf_document.close()
            self.document_preview_tabs.setCurrentIndex(1)
            self.review_preview_tabs.setCurrentIndex(1)
            self.set_source_text()
            self.file_label.setText(session.source_name)
            self.rules.setPlainText(session.schedule.model_dump_json(indent=2))
            self.show_page(1)
            self.status.setText('Saved rules loaded. Review and approve again before generating.')
            self.update_controls()
        except Exception as error: self.error(error)

    def delete(self):
        record_id=self.record_list.currentData()
        if record_id is None: return
        if QMessageBox.question(self,'Delete record?','Delete the selected local saved configuration?') != QMessageBox.StandardButton.Yes: return
        try:
            self.store.delete(record_id); self.refresh_records()
            self.status.setText('Selected saved configuration deleted.')
        except Exception as error: self.error(error)

    def closeEvent(self, event):
        # Destroying a running QThread can crash Qt. Keep the window alive until
        # its bounded network request finishes rather than force-killing it.
        if self.worker is not None and self.worker.isRunning():
            self.status.setText('Wait for the current bounded AI request to finish before closing.')
            event.ignore()
        else: event.accept()
