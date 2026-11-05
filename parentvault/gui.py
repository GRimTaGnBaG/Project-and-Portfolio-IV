"""PySide6 research demonstrator: document → proposal → review → calendar.

This is the actual application, not the separate Assignment 3 design prototype.
Widgets delegate scheduling and persistence to tested backend modules. Network
inference runs in QThread so Qt's event loop can continue repainting the window.
Only the main thread updates widgets; the worker returns values through signals.
"""
# Load calendar for use in this module.
import calendar
# Load hashlib for use in this module.
import hashlib
# Load json for use in this module.
import json
# Bring in date from datetime.
from datetime import date
# Bring in Path from pathlib.
from pathlib import Path
# Bring in data_directory from paths.
from .paths import data_directory
# Bring in compare_document from experiments.
from .experiments import compare_document

# Bring in QDate, QThread, Signal, QPointF from PySide6.QtCore.
from PySide6.QtCore import QDate, QThread, Signal, QPointF
# Bring in QColor, QTextCharFormat, QFont from PySide6.QtGui.
from PySide6.QtGui import QColor, QTextCharFormat, QFont
# Bring in QCalendarWidget, QComboBox, QFileDialog, QHBoxLayout, QInputDialog, QLabel, QLineEdit,
# QMainWindow, QMessageBox, QPlainTextEdit, QPushButton, QSplitter, QTableWidget,
# QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget from PySide6.QtWidgets.
from PySide6.QtWidgets import (
    QCalendarWidget, QComboBox, QFileDialog, QHBoxLayout, QInputDialog,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QPlainTextEdit, QPushButton,
    QSplitter, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)
# Bring in baseline, extract_pdf from core.
from .core import baseline, extract_pdf
# Bring in extract_local from local_model.
from .local_model import extract_local
# Bring in ReviewSession from session.
from .session import ReviewSession
# Bring in Store, export_csv from storage.
from .storage import Store, export_csv
# Bring in HEADERS, load_comparison from comparison.
from .comparison import HEADERS, load_comparison

# Keep 1 field as root.
ROOT = Path(__file__).resolve().parents[1]


class InferenceWorker(QThread):
    """Own one bounded request; emit data rather than touching Qt widgets."""
    # Set succeeded from signal.
    succeeded = Signal(object, object)
    # Set failed from signal.
    failed = Signal(str)

    def __init__(self, pages, model):
        # Use init on super.
        super().__init__()
        # Keep list, model as pages, model.
        self.pages, self.model = list(pages), model

    def run(self):
        # Attempt this operation so its failure can be handled below.
        try:
            # Interactive use keeps source text and raw model responses in memory.
            # Explicit research runners remain responsible for evidence archives.
            schedule, record = extract_local(self.pages,self.model)
            self.succeeded.emit(schedule, record)
        # Handle exception raised by the attempted operation.
        except Exception as error:
            self.failed.emit(f'{type(error).__name__}: {error}')


class ComparisonWorker(QThread):
    """Compare a snapshot of the document without changing its review session."""
    # Set succeeded from signal.
    succeeded = Signal(object)
    # Set failed from signal.
    failed = Signal(str)

    def __init__(self, pages, model, expected, name):
        # Use init on super.
        super().__init__()
        # Keep list, model, expected, name as pages, model, expected, name.
        self.pages, self.model, self.expected, self.name = list(pages), model, expected, name

    def run(self):
        # Attempt this operation so its failure can be handled below.
        try:
            self.succeeded.emit(compare_document(self.pages, self.model, self.expected, self.name))
        # Handle exception raised by the attempted operation.
        except Exception as error:
            self.failed.emit(str(error))


class ModelStatusWorker(QThread):
    """Probe only the local server with a short timeout, without blocking Qt."""
    # Set succeeded from signal.
    succeeded = Signal(object)
    # Set failed from signal.
    failed = Signal(str)

    def run(self):
        # Load httpx for use in this module.
        import httpx
        # Attempt this operation so its failure can be handled below.
        try:
            # Use a managed context for client so exit handling runs automatically.
            with httpx.Client(timeout=5, trust_env=False) as client:
                # Set response from get.
                response=client.get('http://127.0.0.1:1235/v1/models')
                # Use raise for status on response.
                response.raise_for_status()
                # Build identifiers by transforming the entries from data field.
                identifiers=[item['id'] for item in response.json()['data']]
            self.succeeded.emit(identifiers)
        # Handle exception raised by the attempted operation.
        except Exception:
            self.failed.emit('Local model unavailable. Start LM Studio, load a model, and start its local server on port 1235. Baseline extraction works without it.')


# Group the state and behavior for the main window.
class MainWindow(QMainWindow):
    def __init__(self, store_path: Path | None = None):
        # Use init on super.
        super().__init__()
        # Select the font used to draw the next text.
        self.setFont(QFont('Segoe UI',10))
        # Use set window title on self.
        self.setWindowTitle('ParentVault AI — Document to Calendar')
        # Keep one review session shared by the document, review, and calendar pages.
        self.session = ReviewSession()
        # Set worker to no value.
        self.worker = None
        # Set syncing to False.
        self._syncing = False
        # Choose data dir based on whether store path is present or true.
        self.data_dir = Path(store_path).parent if store_path else data_directory()
        # Set comparison results to no value.
        self.comparison_results = None
        # Open the saved-record store separately from the current review session.
        self.store = Store(store_path or self.data_dir/'parentvault.sqlite3')
        # Bring in build from views.
        from .views import build
        # Run build with the supplied input.
        build(self)
        # Use refresh records on self.
        self.refresh_records()
        # Use update controls on self.
        self.update_controls()

    @staticmethod
    def month_default_date():
        # Return current date to the caller.
        return QDate.currentDate()

    def show_page(self, index):
        """Navigate without changing the current document or approval state."""
        # Select the specified page or option.
        self.tabs.setCurrentIndex(index)
        # Update the review or navigation checkbox state.
        self.navigation.button(index).setChecked(True)

    def page_changed(self, index):
        # Update the review or navigation checkbox state.
        self.navigation.button(index).setChecked(True)

    def set_source_text(self):
        """Both document and review pages display the same extracted evidence."""
        # Set text from join.
        text='\n\n'.join(f'PAGE {i+1}\n{page}' for i,page in enumerate(self.session.pages))
        # Replace the editor contents with the current text.
        self.source.setPlainText(text)
        # Replace the editor contents with the current text.
        self.document_source.setPlainText(text)

    def sync_form(self):
        """Populate controls without treating programmatic updates as user edits.

        The structured editor remains the serialization boundary. Form changes
        update that editor, then use exactly the same revalidation/approval path.
        An invalid advanced edit leaves existing form values visible but cannot
        preserve approval or enable generation.
        """
        # Bring in Schedule from core.
        from .core import Schedule
        # Attempt this operation so its failure can be handled below.
        try:
            schedule=Schedule.model_validate_json(self.rules.toPlainText())
        # Handle value error raised by the attempted operation.
        except ValueError:
            # Display the new text in the label or editor.
            self.warning_label.setText('No valid proposed rules yet. Extract a plan or correct the advanced fields.')
            # End this operation here.
            return
        # Set syncing to True.
        self._syncing=True
        # Attempt this operation so its failure can be handled below.
        try:
            # Use set date on anchor edit.
            self.anchor_edit.setDate(QDate(schedule.anchor_date.year,schedule.anchor_date.month,schedule.anchor_date.day))
            # Process each control, owner from zip.
            for control,owner in zip(self.cycle_edits,schedule.cycle):
                # Select the specified page or option.
                control.setCurrentIndex(control.findData(owner))
                # Apply the widget styling for this state.
                control.setStyleSheet('background:'+('#e4efff' if owner=='A' else '#fff0c9')+';')
            # Display the new text in the label or editor.
            self.exchange_day.setText(schedule.exchange_weekday or '')
            # Display the new text in the label or editor.
            self.exchange_time.setText(schedule.exchange_time or '')
            # Display the new text in the label or editor.
            self.evidence_label.setText('\n'.join(f'Page {item.page}: {item.quote}' for item in schedule.evidence))
            # Display the new text in the label or editor.
            self.warning_label.setText('Unresolved: '+'; '.join(schedule.warnings) if schedule.warnings else
                'Review required: verify the start date and rotation against the source. No unresolved warnings were returned.')
        finally:
            # Set syncing to False.
            self._syncing=False

    def form_edited(self, *_):
        # Handle the case where syncing is present or true.
        if self._syncing: return
        # Clear approval and calendar rows because the source or rules are changing.
        self.session.invalidate()
        # Use clear results on self.
        self.clear_results()
        # Attempt this operation so its failure can be handled below.
        try:
            # Set data from loads.
            data=json.loads(self.rules.toPlainText())
            # Set anchor date field from to string.
            data['anchor_date']=self.anchor_edit.date().toString('yyyy-MM-dd')
            # Build cycle field by transforming the entries from cycle edits.
            data['cycle']=[control.currentData() for control in self.cycle_edits]
            data['exchange_weekday']=self.exchange_day.text().strip() or None
            data['exchange_time']=self.exchange_time.text().strip() or None
            # Replace the editor contents with the current text.
            self.rules.setPlainText(json.dumps(data,indent=2))
        # Handle value error, type error raised by the attempted operation.
        except (ValueError,TypeError):
            # Update the review or navigation checkbox state.
            self.review_checkbox.setChecked(False)
            # Display the new text in the label or editor.
            self.status.setText('Correct the invalid advanced rules before editing structured fields.')
        # Use update controls on self.
        self.update_controls()

    def filter_records(self):
        # Set query from casefold.
        query=self.record_search.text().strip().casefold()
        # Initialize visible as an empty list.
        visible=[]
        # Process each row from range.
        for row in range(self.record_table.rowCount()):
            # Set value from item.
            value=self.record_table.item(row,0)
            matches=value is not None and query in value.text().casefold()
            # Use set row hidden on record table.
            self.record_table.setRowHidden(row,not matches)
            # Handle the case where matches is present or true.
            if matches:visible.append(row)
        # Filtering must also update the action target. Otherwise Load/Delete
        # could operate on an old selection that is now hidden by the search.
        current=self.record_table.currentRow()
        # Handle the case where current is absent from visible.
        if current not in visible:
            # Use clear selection on record table.
            self.record_table.clearSelection()
            # Handle the case where visible is present or true.
            if visible:self.record_table.selectRow(visible[0])
            else:self.record_table.setCurrentCell(-1,-1)
        # Use record selected on self.
        self.record_selected()

    def record_selected(self):
        # Set row from current row.
        row=self.record_table.currentRow()
        # Choose item based on whether row is at least 0.
        item=self.record_table.item(row,0) if row>=0 else None
        # Handle the case where item is not no value and there is no is row hidden.
        if item is not None and not self.record_table.isRowHidden(row):
            # Set record id from data.
            record_id=item.data(256)
            # Set index from find data.
            index=self.record_list.findData(record_id)
            # Select the specified page or option.
            self.record_list.setCurrentIndex(index)
        else:
            # Select the specified page or option.
            self.record_list.setCurrentIndex(-1)
        # Use update controls on self.
        self.update_controls()

    def choose_comparison(self):
        # Set path,  from get open file name.
        path,_=QFileDialog.getOpenFileName(self,'Open recorded evaluator results',str(ROOT/'data'),'JSON files (*.json)')
        # Handle the case where there is no path.
        if not path: return
        # Attempt this operation so its failure can be handled below.
        try: self.open_comparison(Path(path))
        # Handle exception raised by the attempted operation.
        except Exception as error: self.error(error)

    def open_comparison(self, path: Path):
        """Render reviewed result files, keeping failures visibly distinct."""
        # Clear first: a malformed replacement must not leave prior results
        # looking as though they came from the newly selected evidence file.
        self.comparison_results = None
        # Use update controls on self.
        self.update_controls()
        # Resize the table to the number of result rows.
        self.comparison_table.setRowCount(0)
        # Display the new text in the label or editor.
        self.comparison_label.setText('Loading historical results…')
        # Build the file or folder path for manifest.
        manifest=ROOT/'fixtures'/'formal_fixture_answers.json'
        # Attempt this operation so its failure can be handled below.
        try:
            # Choose answers based on whether manifest exists.
            answers=json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else {}
            # Set rows from load comparison.
            rows=load_comparison(path,answers)
        # Handle exception raised by the attempted operation.
        except Exception:
            # Display the new text in the label or editor.
            self.comparison_label.setText('Selected results were not loaded. Previous comparison cleared.')
            # Pass the failure back to the caller.
            raise
        # Resize the table to the number of result rows.
        self.comparison_table.setRowCount(len(rows))
        # Process each index, row from enumerate.
        for index,row in enumerate(rows):
            # Process each column, value from enumerate.
            for column,value in enumerate(row):
                # Create the Qt table widget item used for item.
                item=QTableWidgetItem(value)
                # Use set tool tip on item.
                item.setToolTip(value)  # Long cycles/errors remain inspectable.
                # Handle the case where column equals 5.
                if column==5:
                    # Use set background on item.
                    item.setBackground(QColor('#ffd5d5' if value in ('MISMATCH','MISSED WARNING') else
                                              '#e7f3e8' if value=='Match' else '#fff0cc'))
                # Put the cell value at the specified row and column.
                self.comparison_table.setItem(index,column,item)
        # Use resize columns to contents on comparison table.
        self.comparison_table.resizeColumnsToContents()
        # Process each column from range.
        for column in range(len(HEADERS)):
            # Use set column width on comparison table.
            self.comparison_table.setColumnWidth(column,min(260,self.comparison_table.columnWidth(column)))
        # Use resize rows to contents on comparison table.
        self.comparison_table.resizeRowsToContents()
        # Display the new text in the label or editor.
        self.comparison_label.setText(f'Historical evidence: {path.parent.name}/{path.name} | {len(rows)} comparison rows. No new inference was run.')

    def update_controls(self):
        """Make workflow prerequisites visible in control availability."""
        # While a worker is active, disable controls that could replace its input or start another request.
        busy=self.worker is not None and self.worker.isRunning()
        # Set has document from whether pages is present.
        has_document=bool(self.session.pages)
        # Set whether the user can interact with this control.
        self.open_button.setEnabled(not busy)
        # Process each button from load button, delete button.
        for button in (self.load_button,self.delete_button):
            # Set whether the user can interact with this control.
            button.setEnabled(not busy and self.record_list.currentData() is not None)
        # Set whether the user can interact with this control.
        self.model.setEnabled(not busy)
        # Set whether the user can interact with this control.
        self.model_check_button.setEnabled(not busy)
        # Set whether the user can interact with this control.
        self.sample_button.setEnabled(not busy)
        # Set whether the user can interact with this control.
        self.compare_run_button.setEnabled(has_document and not busy)
        # Set whether the user can interact with this control.
        self.compare_export_button.setEnabled(bool(self.comparison_results) and not busy)
        # Set whether the user can interact with this control.
        self.baseline_button.setEnabled(has_document and not busy)
        # Set whether the user can interact with this control.
        self.ai_button.setEnabled(has_document and not busy)
        # Control whether the user can edit this field.
        self.rules.setReadOnly(busy)
        for control in [self.anchor_edit,*self.cycle_edits,self.exchange_day,self.exchange_time,self.review_checkbox]:
            # Set whether the user can interact with this control.
            control.setEnabled(bool(self.rules.toPlainText().strip()) and not busy)
        # Display the new text in the label or editor.
        self.approval_badge.setText('Rules approved' if self.session.approved else 'Not yet approved')
        # Set whether the user can interact with this control.
        self.approve_button.setEnabled(bool(self.rules.toPlainText().strip()) and self.review_checkbox.isChecked() and not busy)
        # Enable calendar generation only while the current proposal has approval.
        self.generate_button.setEnabled(self.session.approved and not busy)
        # Set whether the user can interact with this control.
        self.save_button.setEnabled(self.session.approved and not busy)
        # Set whether the user can interact with this control.
        self.export_button.setEnabled(bool(self.session.rows) and not busy)

    def clear_results(self):
        # Clearing both the table and date formats prevents a previous plan's
        # colors from remaining visible after rules become unapproved.
        self.table.setRowCount(0)
        # Use set date text format on month.
        self.month.setDateTextFormat(QDate(),QTextCharFormat())
        # Use set ownership on month.
        self.month.set_ownership([])

    def rules_edited(self):
        # Clear approval and calendar rows because the source or rules are changing.
        self.session.invalidate(); self.clear_results()
        # Update the review or navigation checkbox state.
        self.review_checkbox.setChecked(False)
        # Use sync form on self.
        self.sync_form()
        # Display the new text in the label or editor.
        self.status.setText('Unapproved — validate and approve the current edited rules before generating dates.')
        # Use update controls on self.
        self.update_controls()

    def error(self, error):
        # Display the new text in the label or editor.
        self.status.setText(f'Action failed: {error}')
        # Use warning on qmessage box.
        QMessageBox.warning(self,'Action failed',str(error))
        # Use update controls on self.
        self.update_controls()

    def open_pdf(self):
        # Set path,  from get open file name.
        path,_=QFileDialog.getOpenFileName(self,'Select fictional text PDF',str(ROOT/'fixtures'),'PDF files (*.pdf)')
        # Handle the case where there is no path.
        if not path: return  # Cancel is not replacement; preserve the current session.
        # Use load pdf on self.
        self.load_pdf(Path(path))

    # Replace the source and clear the previous document’s rules and calendar.
    def load_pdf(self, path):
        # Set path from str.
        path = str(path)
        # Invalidate first, so even a failed replacement cannot leave an old
        # calendar looking like it belongs to the newly selected filename.
        self.session=ReviewSession(); self.rules.clear(); self.source.clear(); self.document_source.clear(); self.clear_results()
        # Release the underlying file, connection, or window.
        self.pdf_document.close()
        # Display the new text in the label or editor.
        self.file_label.setText(Path(path).name)
        # Attempt this operation so its failure can be handled below.
        try:
            # Extract text for validation while the PDF widget handles the visual preview.
            pages=extract_pdf(Path(path))
            # Hash the PDF bytes to identify the source independently of its filename.
            digest=hashlib.sha256(Path(path).read_bytes()).hexdigest()
            # Use replace document on session.
            self.session.replace_document(pages,Path(path).name,digest)
            # Use load on pdf document.
            self.pdf_document.load(path)
            # Select the specified page or option.
            self.document_preview_tabs.setCurrentIndex(0)
            # Select the specified page or option.
            self.review_preview_tabs.setCurrentIndex(0)
            # Use set source text on self.
            self.set_source_text()
            # Display the new text in the label or editor.
            self.status.setText('Text extracted. Choose baseline or local AI extraction.')
        # Handle exception raised by the attempted operation.
        except Exception as error: self.error(error)
        # Use update controls on self.
        self.update_controls()

    # Show the extracted proposal and move the preview to its source evidence.
    def present(self, schedule, message):
        # Install a validated proposal. Approval is a separate action taken on the review page.
        self.session.propose(schedule)
        # Use set source text on self.
        self.set_source_text()
        # Display the new text in the label or editor.
        self.file_label.setText(self.session.source_name)
        # Put the proposal into the editable rules panel as JSON.
        self.rules.setPlainText(schedule.model_dump_json(indent=2))
        # Jump the calendar to the selected year and month.
        self.month.setCurrentPage(schedule.anchor_date.year,schedule.anchor_date.month)
        # Handle the case where page count is present or true.
        if self.pdf_document.pageCount():
            # Use jump on page navigator.
            self.review_pdf_view.pageNavigator().jump(schedule.evidence[0].page-1,QPointF(),0)
        else:
            # Select the specified page or option.
            self.review_preview_tabs.setCurrentIndex(1)
        # Use show page on self.
        self.show_page(1)
        # Display the new text in the label or editor.
        self.status.setText(message+' Review the source and approve the rules.')
        # Use update controls on self.
        self.update_controls()

    # Extract a proposal locally using the supported alternating-week pattern.
    def run_baseline(self):
        # Clear approval and calendar rows because the source or rules are changing.
        self.session.invalidate(); self.rules.clear(); self.clear_results()
        # Attempt this operation so its failure can be handled below.
        try: self.present(baseline(self.session.pages),'Baseline proposal ready.')
        # Handle exception raised by the attempted operation.
        except Exception as error: self.error(error)

    # Start the model request on a background worker.
    def run_ai(self):
        # Handle the case where there is no strip.
        if not self.model.text().strip():
            # Use error on self.
            self.error('Enter the exact loaded LM Studio model identifier'); return
        # Clear approval and calendar rows because the source or rules are changing.
        self.session.invalidate(); self.rules.clear(); self.clear_results()
        # Set worker from inference worker.
        self.worker=InferenceWorker(self.session.pages,self.model.text().strip())
        # Connect each signal to its handler before starting the background request.
        self.worker.succeeded.connect(self.ai_ready)
        # Register the callback that receives this Qt signal.
        self.worker.failed.connect(self.error)
        # Register the callback that receives this Qt signal.
        self.worker.finished.connect(self.worker_finished)
        # Start the worker after connecting its result and cleanup signals.
        self.worker.start()
        # Display the new text in the label or editor.
        self.status.setText('Local AI is extracting proposed rules. Request has a bounded timeout.')
        # Use update controls on self.
        self.update_controls()

    def ai_ready(self, schedule, record):
        # Attempt this operation so its failure can be handled below.
        try: self.present(schedule,f"Local AI validated in {record['elapsed_seconds']:.2f} seconds.")
        # Handle exception raised by the attempted operation.
        except Exception as error: self.error(error)

    # Release the worker and refresh which controls are available.
    def worker_finished(self):
        # Use delete later on worker.
        self.worker.deleteLater(); self.worker=None; self.update_controls()

    # Validate the rules in the editor before recording approval.
    def approve(self):
        # Handle the case where there is no is checked.
        if not self.review_checkbox.isChecked():
            # Display the new text in the label or editor.
            self.status.setText('Check that you reviewed the rules and source before approval.')
            # End this operation here.
            return
        # Attempt this operation so its failure can be handled below.
        try:
            # Pass the exact text on screen into the session's schema, source, and warning checks.
            self.session.approve(self.rules.toPlainText())
            # Display the new text in the label or editor.
            self.status.setText('Approved. Generate the displayed month or save the configuration.')
        # Handle exception raised by the attempted operation.
        except Exception as error: self.error(error)
        # Use update controls on self.
        self.update_controls()

    def month_changed(self, year, month):
        # Month navigation changes the requested output range, not the approved
        # source rules. Clear old rows to avoid exporting a different month.
        self.session.rows=[]; self.clear_results(); self.update_controls()

    # Produce the selected month from the approved recurring schedule.
    def generate(self):
        # Attempt this operation so its failure can be handled below.
        try:
            # Keep year shown, month shown as year, month.
            year,month=self.month.yearShown(),self.month.monthShown()
            # Generate an inclusive range from the first through the last date of the selected month.
            rows=self.session.generate(date(year,month,1),date(year,month,calendar.monthrange(year,month)[1]))
            # Resize the table to the number of result rows.
            self.table.setRowCount(len(rows))
            # Process each index, row from enumerate.
            for index,row in enumerate(rows):
                # Put the cell value at the specified row and column.
                self.table.setItem(index,0,QTableWidgetItem(row['date']))
                # Put the cell value at the specified row and column.
                self.table.setItem(index,1,QTableWidgetItem('Parent '+row['parent']))
                # Create the Qt text char format used for calendar text format.
                fmt=QTextCharFormat()
                # Use set background on calendar text format.
                fmt.setBackground(QColor('#cfe8ff' if row['parent']=='A' else '#ffe6aa'))
                # Use set date text format on month.
                self.month.setDateTextFormat(QDate.fromString(row['date'],'yyyy-MM-dd'),fmt)
            # Give the calendar the same ownership rows that populate the table.
            self.month.set_ownership(rows)
            # Display the new text in the label or editor.
            self.status.setText(f'Generated {len(rows)} overnight assignments from approved rules.')
        # Handle exception raised by the attempted operation.
        except Exception as error: self.error(error)
        # Use update controls on self.
        self.update_controls()

    # Ask for a CSV destination and confirm before replacing an existing file.
    def export(self):
        # Set path,  from get save file name.
        path,_=QFileDialog.getSaveFileName(self,'Export calendar CSV',str(self.data_dir/'calendar.csv'),'CSV files (*.csv)')
        # Handle the case where there is no path.
        if not path: return
        # QFileDialog normally confirms replacement; an explicit second check
        # here also protects platforms that disable the native dialog prompt.
        overwrite=Path(path).exists()
        # Handle the case where overwrite is present or true and question differs from yes.
        if overwrite and QMessageBox.question(self,'Replace file?',f'Replace {Path(path).name}?') != QMessageBox.StandardButton.Yes: return
        # Attempt this operation so its failure can be handled below.
        try:
            # Run export csv with the supplied input.
            export_csv(Path(path),self.session.rows,overwrite)
            # Display the new text in the label or editor.
            self.status.setText('Calendar CSV exported successfully.')
        # Handle exception raised by the attempted operation.
        except Exception as error: self.error(error)

    def refresh_records(self):
        # Remove the previous contents before displaying the next result.
        self.record_list.clear()
        # Set records from list records.
        records=self.store.list_records()
        # Use block signals on record table.
        self.record_table.blockSignals(True)
        # Resize the table to the number of result rows.
        self.record_table.setRowCount(len(records))
        # Process each row, record id, name, created from enumerate.
        for row,(record_id,name,created) in enumerate(records):
            # Use add item on record list.
            self.record_list.addItem(f'{name} | {created}',record_id)
            # Create the Qt table widget item used for item.
            item=QTableWidgetItem(name)
            # Use set data on item.
            item.setData(256,record_id)
            # Put the cell value at the specified row and column.
            self.record_table.setItem(row,0,item)
            # Put the cell value at the specified row and column.
            self.record_table.setItem(row,1,QTableWidgetItem('Review again when loaded'))
            # Put the cell value at the specified row and column.
            self.record_table.setItem(row,2,QTableWidgetItem(created[:16].replace('T',' ')))
        # Use resize columns to contents on record table.
        self.record_table.resizeColumnsToContents()
        # Use block signals on record table.
        self.record_table.blockSignals(False)
        # Use filter records on self.
        self.filter_records()

    def save(self):
        # Attempt this operation so its failure can be handled below.
        try:
            # Preserve the current state or write the record through its storage interface.
            self.store.save(self.record_name.text(),self.session)
            # Use refresh records on self.
            self.refresh_records(); self.status.setText('Approved configuration saved locally.')
        # Handle exception raised by the attempted operation.
        except Exception as error: self.error(error)

    def load(self):
        # Set record id from current data.
        record_id=self.record_list.currentData()
        # Handle the case where record id is no value.
        if record_id is None: return
        # Attempt this operation so its failure can be handled below.
        try:
            # Rebuild the review state from saved rules and extracted pages.
            session=self.store.load(record_id)
            # Keep session as session.
            self.session=session; self.clear_results()
            # Saved provenance includes extracted source pages, not a retained
            # PDF file. Never keep showing the previous document's PDF preview.
            self.pdf_document.close()
            # Select the specified page or option.
            self.document_preview_tabs.setCurrentIndex(1)
            # Select the specified page or option.
            self.review_preview_tabs.setCurrentIndex(1)
            # Use set source text on self.
            self.set_source_text()
            # Display the new text in the label or editor.
            self.file_label.setText(session.source_name)
            # Replace the editor contents with the current text.
            self.rules.setPlainText(session.schedule.model_dump_json(indent=2))
            # Jump the calendar to the selected year and month.
            self.month.setCurrentPage(session.schedule.anchor_date.year,session.schedule.anchor_date.month)
            # Use show page on self.
            self.show_page(1)
            # Display the new text in the label or editor.
            self.status.setText('Saved rules loaded. Review and approve again before generating.')
            # Use update controls on self.
            self.update_controls()
        # Handle exception raised by the attempted operation.
        except Exception as error: self.error(error)

    def delete(self):
        # Set record id from current data.
        record_id=self.record_list.currentData()
        # Handle the case where record id is no value.
        if record_id is None: return
        # Handle the case where question differs from yes.
        if QMessageBox.question(self,'Delete record?','Delete the selected local saved configuration?') != QMessageBox.StandardButton.Yes: return
        # Attempt this operation so its failure can be handled below.
        try:
            # Use delete on store.
            self.store.delete(record_id); self.refresh_records()
            # Display the new text in the label or editor.
            self.status.setText('Selected saved configuration deleted.')
        # Handle exception raised by the attempted operation.
        except Exception as error: self.error(error)

    def check_model(self):
        # Set worker from model status worker.
        self.worker=ModelStatusWorker()
        # Register the callback that receives this Qt signal.
        self.worker.succeeded.connect(self.model_status_ready)
        # Register the callback that receives this Qt signal.
        self.worker.failed.connect(self.model_status.setText)
        # Register the callback that receives this Qt signal.
        self.worker.finished.connect(self.worker_finished)
        # Display the new text in the label or editor.
        self.model_status.setText('Checking the local model server…')
        # Start the worker after connecting its result and cleanup signals.
        self.worker.start()
        # Use update controls on self.
        self.update_controls()

    def model_status_ready(self, identifiers):
        # Handle the case where there is no identifiers.
        if not identifiers:
            # Display the new text in the label or editor.
            self.model_status.setText('Server connected, but no models are available. Load a model in LM Studio.'); return
        # Display the new text in the label or editor.
        self.model_status.setText('Server connected. Available model IDs: ' + ', '.join(identifiers))
        # Handle the case where strip is absent from identifiers.
        if self.model.text().strip() not in identifiers:
            # Display the new text in the label or editor.
            self.model.setText('parentvault-research' if 'parentvault-research' in identifiers else identifiers[0])

    def run_comparison(self):
        """Use approved rules as an explicitly labeled reference, never a hidden key."""
        # Handle the case where there is no pages or there is no strip.
        if not self.session.pages or not self.model.text().strip():
            # Use error on self.
            self.error('Select a document and enter the loaded model identifier first.'); return
        # Use approved rules as the comparison reference when available. Otherwise the result reports outputs without a match score.
        expected = self.session.schedule.model_dump(mode='json') if self.session.approved else None
        # Set comparison results to no value.
        self.comparison_results = None
        # Resize the table to the number of result rows.
        self.comparison_table.setRowCount(0)
        # Display the new text in the label or editor.
        self.comparison_label.setText('Running both methods. Reference: ' +
            ('current reviewed rules (not independent ground truth).' if expected else 'none; outputs cannot be scored for accuracy.'))
        # Set worker from comparison worker.
        self.worker = ComparisonWorker(self.session.pages, self.model.text().strip(), expected, self.session.source_name)
        # Register the callback that receives this Qt signal.
        self.worker.succeeded.connect(self.comparison_ready)
        # Register the callback that receives this Qt signal.
        self.worker.failed.connect(self.error)
        # Register the callback that receives this Qt signal.
        self.worker.finished.connect(self.worker_finished)
        # Start the worker after connecting its result and cleanup signals.
        self.worker.start()
        # Use update controls on self.
        self.update_controls()

    def comparison_ready(self, results):
        """Reuse the historical renderer after writing only summarized results."""
        # Build the file or folder path for path.
        path = self.data_dir/'comparison-latest.json'
        # Create the output directory before writing files into it.
        path.parent.mkdir(parents=True, exist_ok=True)
        # Save the text or JSON output using the requested encoding.
        path.write_text(json.dumps(results, indent=2), encoding='utf-8')
        # Use open comparison on self.
        self.open_comparison(path)
        # Keep the summarized result available for a later JSON export.
        self.comparison_results = results
        # Choose reference based on whether get is present or true.
        reference = 'reviewed rules; not independent ground truth' if results[0].get('expected') else 'none; accuracy unscored'
        # Display the new text in the label or editor.
        self.comparison_label.setText('Fresh measured comparison. Reference: ' + reference + '. Approval is unchanged.')
        # Display the new text in the label or editor.
        self.status.setText('Comparison complete. Method failures remain visible alongside successful outputs.')
        # Use update controls on self.
        self.update_controls()

    def export_comparison(self):
        # Handle the case where there is no comparison results.
        if not self.comparison_results: return
        # Set path,  from get save file name.
        path,_ = QFileDialog.getSaveFileName(self,'Save comparison results',str(self.data_dir/'comparison.json'),'JSON files (*.json)')
        # Handle the case where there is no path.
        if not path: return
        # Attempt this operation so its failure can be handled below.
        try:
            # Save the text or JSON output using the requested encoding.
            Path(path).write_text(json.dumps(self.comparison_results,indent=2),encoding='utf-8')
            # Display the new text in the label or editor.
            self.status.setText('Comparison summary exported.')
        # Handle exception raised by the attempted operation.
        except Exception as error: self.error(error)

    def closeEvent(self, event):
        # Destroying a running QThread can crash Qt. Keep the window alive until
        # its bounded network request finishes rather than force-killing it.
        if self.worker is not None and self.worker.isRunning():
            # Display the new text in the label or editor.
            self.status.setText('Wait for the current bounded AI request to finish before closing.')
            # Use ignore on event.
            event.ignore()
        else: event.accept()
