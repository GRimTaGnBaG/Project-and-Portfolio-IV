"""Desktop completion checks exercise actual PDFs, persistence, and state changes."""
import json
from PySide6.QtWidgets import QApplication
from parentvault.gui import MainWindow
from parentvault.core import baseline, extract_pdf
from parentvault.experiments import compare_document
from parentvault.paths import ASSET_ROOT, data_directory


def test_comparison_retains_transport_failure_without_mutating_rules(tmp_path):
    pages=extract_pdf(ASSET_ROOT/'fixtures'/'formal_recurring_plan.pdf')
    reference=baseline(pages)
    def unavailable(*args):
        raise ConnectionError('Synthetic offline server')
    result=compare_document(pages,'test',reference.model_dump(mode='json'),model_extractor=unavailable)
    assert result[0]['baseline']['actual']['cycle']==reference.cycle
    assert 'ConnectionError' in result[0]['local_model']['error']
    assert all(result[0][method]['seconds']>=0 for method in ('baseline','local_model'))
    assert reference.warnings==[]


def test_real_sample_to_saved_calendar_and_comparison(tmp_path):
    app=QApplication.instance() or QApplication([])
    window=MainWindow(tmp_path/'plans.sqlite3')
    window.sample_button.click()
    assert window.pdf_document.pageCount()==5
    window.run_baseline()
    window.review_checkbox.setChecked(True);window.approve();window.generate()
    assert window.session.approved and window.table.rowCount()==30
    assert window.session.rows[0]['parent']=='B'
    original=list(window.session.rows)
    def proposal(pages,model): return baseline(pages),{}
    results=compare_document(window.session.pages,'test',window.session.schedule.model_dump(mode='json'),model_extractor=proposal)
    window.comparison_ready(results)
    assert window.session.approved and window.session.rows==original
    assert window.comparison_table.rowCount()==8
    assert all(window.comparison_table.item(row,5).text()=='Match' for row in range(8))
    assert window.compare_export_button.isEnabled()
    assert 'not independent ground truth' in window.comparison_label.text()
    window.record_name.setText('Fictional sample');window.save()
    window.month.setCurrentPage(2027,2);window.load()
    assert not window.session.approved and window.pdf_document.pageCount()==0
    assert window.month.yearShown()==2026 and window.month.monthShown()==11
    assert window.table.rowCount()==0
    window.close();app.processEvents()


def test_data_directory_override_does_not_depend_on_working_directory(tmp_path,monkeypatch):
    monkeypatch.setenv('PARENTVAULT_DATA_DIR',str(tmp_path/'User data'))
    assert data_directory()==tmp_path/'User data'
    assert data_directory().is_dir()
