"""Desktop completion checks exercise actual PDFs, persistence, and state changes."""
# Load json for use in this module.
import json
# Bring in QApplication from PySide6.QtWidgets.
from PySide6.QtWidgets import QApplication
# Bring in MainWindow from parentvault.gui.
from parentvault.gui import MainWindow
# Bring in baseline, extract_pdf from parentvault.core.
from parentvault.core import baseline, extract_pdf
# Bring in compare_document from parentvault.experiments.
from parentvault.experiments import compare_document
# Bring in ASSET_ROOT, data_directory from parentvault.paths.
from parentvault.paths import ASSET_ROOT, data_directory


# Verify comparison retains transport failure without mutating rules.
def test_comparison_retains_transport_failure_without_mutating_rules(tmp_path):
    # Set pages from extract pdf.
    pages=extract_pdf(ASSET_ROOT/'fixtures'/'formal_recurring_plan.pdf')
    # Set reference from baseline.
    reference=baseline(pages)
    def unavailable(*args):
        # Stop with a clear error explaining synthetic offline server.
        raise ConnectionError('Synthetic offline server')
    # Set result from compare document.
    result=compare_document(pages,'test',reference.model_dump(mode='json'),model_extractor=unavailable)
    # Verify that cycle field equals cycle before treating this check as successful.
    assert result[0]['baseline']['actual']['cycle']==reference.cycle
    # Verify that 'ConnectionError' is in error field before treating this check as successful.
    assert 'ConnectionError' in result[0]['local_model']['error']
    # Verify that all is present or true before treating this check as successful.
    assert all(result[0][method]['seconds']>=0 for method in ('baseline','local_model'))
    # Verify that warnings equals  before treating this check as successful.
    assert reference.warnings==[]


# Verify real sample to saved calendar and comparison.
def test_real_sample_to_saved_calendar_and_comparison(tmp_path):
    app=QApplication.instance() or QApplication([])
    # Set window from main window.
    window=MainWindow(tmp_path/'plans.sqlite3')
    # Use click on sample button.
    window.sample_button.click()
    # Verify that page count equals 5 before treating this check as successful.
    assert window.pdf_document.pageCount()==5
    # Use run baseline on window.
    window.run_baseline()
    # Update the review or navigation checkbox state.
    window.review_checkbox.setChecked(True);window.approve();window.generate()
    # Verify that approved is present or true and row count equals 30 before treating this check
    # as successful.
    assert window.session.approved and window.table.rowCount()==30
    # Verify that parent field equals 'B' before treating this check as successful.
    assert window.session.rows[0]['parent']=='B'
    # Set original from list.
    original=list(window.session.rows)
    def proposal(pages,model): return baseline(pages),{}
    # Set results from compare document.
    results=compare_document(window.session.pages,'test',window.session.schedule.model_dump(mode='json'),model_extractor=proposal)
    # Use comparison ready on window.
    window.comparison_ready(results)
    # Verify that approved is present or true and rows equals original before treating this check
    # as successful.
    assert window.session.approved and window.session.rows==original
    # Verify that row count equals 8 before treating this check as successful.
    assert window.comparison_table.rowCount()==8
    # Verify that all is present or true before treating this check as successful.
    assert all(window.comparison_table.item(row,5).text()=='Match' for row in range(8))
    # Verify that compare export button is enabled before treating this check as successful.
    assert window.compare_export_button.isEnabled()
    # Verify that 'not independent ground truth' is in text before treating this check as
    # successful.
    assert 'not independent ground truth' in window.comparison_label.text()
    # Display the new text in the label or editor.
    window.record_name.setText('Fictional sample');window.save()
    # Jump the calendar to the selected year and month.
    window.month.setCurrentPage(2027,2);window.load()
    # Verify that there is no approved and page count equals 0 before treating this check as
    # successful.
    assert not window.session.approved and window.pdf_document.pageCount()==0
    # Verify that year shown equals 2026 and month shown equals 11 before treating this check as
    # successful.
    assert window.month.yearShown()==2026 and window.month.monthShown()==11
    # Verify that row count equals 0 before treating this check as successful.
    assert window.table.rowCount()==0
    # Release the underlying file, connection, or window.
    window.close();app.processEvents()


# Verify data directory override does not depend on working directory.
def test_data_directory_override_does_not_depend_on_working_directory(tmp_path,monkeypatch):
    # Use setenv on monkeypatch.
    monkeypatch.setenv('PARENTVAULT_DATA_DIR',str(tmp_path/'User data'))
    assert data_directory()==tmp_path/'User data'
    # Verify that is dir is present or true before treating this check as successful.
    assert data_directory().is_dir()
