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

from PySide6.QtCore import QDate, QThread, Signal
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
        self.setWindowTitle('ParentVault AI — R&D Demonstrator')
        self.resize(1180,820)
        self.session = ReviewSession()
        self.worker = None
        # Tests inject a temporary database; normal launches use local app data.
        self.store = Store(store_path or ROOT/'data'/'parentvault.sqlite3')
        self.setStyleSheet('QPushButton { padding: 7px; } QTabWidget { margin-top: 8px; }')
        body = QWidget(); self.setCentralWidget(body)
        layout = QVBoxLayout(body)
        title=QLabel('ParentVault AI | Document to Calendar')
        title.setStyleSheet('font-size: 22px; font-weight: bold;')
        layout.addWidget(title)
        layout.addWidget(QLabel('Fictional research data • Recurring overnight assignments • Review before generation'))

        # Controls are retained as attributes because approval/busy state must
        # enable and disable them together rather than relying on user memory.
        toolbar=QHBoxLayout(); layout.addLayout(toolbar)
        self.open_button=QPushButton('Select PDF'); toolbar.addWidget(self.open_button)
        self.baseline_button=QPushButton('Extract baseline'); toolbar.addWidget(self.baseline_button)
        self.ai_button=QPushButton('Extract with local AI'); toolbar.addWidget(self.ai_button)
        toolbar.addWidget(QLabel('Loaded model:'))
        self.model=QLineEdit('parentvault-research'); toolbar.addWidget(self.model)
        self.open_button.clicked.connect(self.open_pdf)
        self.baseline_button.clicked.connect(self.run_baseline)
        self.ai_button.clicked.connect(self.run_ai)
        self.file_label=QLabel('No document selected'); layout.addWidget(self.file_label)
        self.status=QLabel('Select the fictional PDF in fixtures to begin.')
        self.status.setWordWrap(True); layout.addWidget(self.status)

        self.tabs=QTabWidget(); layout.addWidget(self.tabs)
        review=QWidget(); review_layout=QVBoxLayout(review)
        split=QSplitter(); review_layout.addWidget(split)
        source_box=QWidget(); source_layout=QVBoxLayout(source_box)
        source_layout.addWidget(QLabel('Source document with page references'))
        self.source=QPlainTextEdit(); self.source.setReadOnly(True)
        source_layout.addWidget(self.source); split.addWidget(source_box)
        rules_box=QWidget(); rules_layout=QVBoxLayout(rules_box)
        rules_layout.addWidget(QLabel('Editable structured rules — A/B cycle begins on anchor_date'))
        self.rules=QPlainTextEdit(); self.rules.setAccessibleName('Proposed scheduling rules JSON')
        rules_layout.addWidget(self.rules); split.addWidget(rules_box)
        self.rules.textChanged.connect(self.rules_edited)
        review_layout.addWidget(QLabel('Review the anchor, 14 owners, quotes, warnings, and exchange metadata. Clear warnings only after resolving them.'))
        self.approve_button=QPushButton('Validate and approve reviewed rules')
        self.approve_button.clicked.connect(self.approve); review_layout.addWidget(self.approve_button)
        self.tabs.addTab(review,'1  Document and review')

        result=QWidget(); result_layout=QVBoxLayout(result)
        self.generate_button=QPushButton('Generate displayed month from approved rules')
        self.generate_button.clicked.connect(self.generate); result_layout.addWidget(self.generate_button)
        self.month=QCalendarWidget(); self.month.setGridVisible(True)
        self.month.currentPageChanged.connect(self.month_changed)
        result_layout.addWidget(self.month)
        result_layout.addWidget(QLabel('Blue: Parent A • Gold: Parent B • Text table below is the authoritative overnight listing.'))
        self.table=QTableWidget(0,2); self.table.setHorizontalHeaderLabels(['Date','Overnight parent'])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        result_layout.addWidget(self.table)
        self.export_button=QPushButton('Export displayed dates to CSV')
        self.export_button.clicked.connect(self.export); result_layout.addWidget(self.export_button)
        self.tabs.addTab(result,'2  Calendar')

        records=QWidget(); records_layout=QVBoxLayout(records)
        self.record_name=QLineEdit(); self.record_name.setPlaceholderText('Name this fictional configuration')
        records_layout.addWidget(self.record_name)
        self.save_button=QPushButton('Save approved configuration')
        self.save_button.clicked.connect(self.save); records_layout.addWidget(self.save_button)
        self.record_list=QComboBox(); records_layout.addWidget(self.record_list)
        self.load_button=QPushButton('Load selected record for review')
        self.load_button.clicked.connect(self.load); records_layout.addWidget(self.load_button)
        self.delete_button=QPushButton('Delete selected record…')
        self.delete_button.clicked.connect(self.delete); records_layout.addWidget(self.delete_button)
        records_layout.addStretch(); self.tabs.addTab(records,'3  Saved records')

        # This view is the Iteration 1 increment. It reads retained experiment
        # evidence independently of the currently approved document, so opening
        # a comparison cannot silently replace rules or invalidate a calendar.
        comparison=QWidget(); comparison_layout=QVBoxLayout(comparison)
        comparison_layout.addWidget(QLabel('Saved experiment evidence — opening results does not run a new extraction.'))
        self.comparison_label=QLabel('No experiment results loaded.')
        self.comparison_label.setWordWrap(True); comparison_layout.addWidget(self.comparison_label)
        self.comparison_button=QPushButton('Open saved experiment results JSON')
        self.comparison_button.clicked.connect(self.choose_comparison)
        comparison_layout.addWidget(self.comparison_button)
        self.comparison_table=QTableWidget(0,len(HEADERS))
        self.comparison_table.setHorizontalHeaderLabels(HEADERS)
        self.comparison_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.comparison_table.setWordWrap(True)
        self.comparison_table.horizontalHeader().setStretchLastSection(True)
        comparison_layout.addWidget(self.comparison_table)
        comparison_layout.addWidget(QLabel('Match refers only to the recorded answer key. Rejections and warnings are not proof of semantic understanding.'))
        self.tabs.addTab(comparison,'4  Research comparison')
        self.refresh_records(); self.update_controls()

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
        for button in (self.open_button,self.load_button,self.delete_button): button.setEnabled(not busy)
        self.model.setEnabled(not busy)
        self.baseline_button.setEnabled(has_document and not busy)
        self.ai_button.setEnabled(has_document and not busy)
        self.rules.setReadOnly(busy)
        self.approve_button.setEnabled(bool(self.rules.toPlainText().strip()) and not busy)
        self.generate_button.setEnabled(self.session.approved and not busy)
        self.save_button.setEnabled(self.session.approved and not busy)
        self.export_button.setEnabled(bool(self.session.rows) and not busy)

    def clear_results(self):
        # Clearing both the table and date formats prevents a previous plan's
        # colors from remaining visible after rules become unapproved.
        self.table.setRowCount(0)
        self.month.setDateTextFormat(QDate(),QTextCharFormat())

    def rules_edited(self):
        self.session.invalidate(); self.clear_results()
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
        self.session=ReviewSession(); self.rules.clear(); self.source.clear(); self.clear_results()
        self.file_label.setText(Path(path).name)
        try:
            pages=extract_pdf(Path(path))
            digest=hashlib.sha256(Path(path).read_bytes()).hexdigest()
            self.session.replace_document(pages,Path(path).name,digest)
            self.source.setPlainText('\n\n'.join(f'PAGE {i+1}\n{p}' for i,p in enumerate(pages)))
            self.status.setText('Text extracted. Choose baseline or local AI extraction.')
        except Exception as error: self.error(error)
        self.update_controls()

    def present(self, schedule, message):
        self.session.propose(schedule)
        self.file_label.setText(self.session.source_name)
        self.rules.setPlainText(schedule.model_dump_json(indent=2))
        self.month.setCurrentPage(schedule.anchor_date.year,schedule.anchor_date.month)
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
        for record_id,name,created in self.store.list_records():
            self.record_list.addItem(f'{name} | {created}',record_id)

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
            self.source.setPlainText('\n\n'.join(f'PAGE {i+1}\n{p}' for i,p in enumerate(session.pages)))
            self.file_label.setText(session.source_name)
            self.rules.setPlainText(session.schedule.model_dump_json(indent=2))
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
