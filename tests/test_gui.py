"""Qt regression checks: build real widgets but never make a model request."""
import os
import json
import pytest
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from parentvault.gui import MainWindow,InferenceWorker
from parentvault.core import baseline


def test_worker_construction_and_approval_control_state(tmp_path):
    app=QApplication.instance() or QApplication([])
    # A worker is not a widget: creating it must not call widget-only APIs.
    worker=InferenceWorker(['fictional page'],'test-model')
    assert worker.pages==['fictional page'] and not worker.isRunning()
    window=MainWindow(tmp_path/'gui.sqlite3')
    text='Beginning 2026-11-02, Parent A has seven consecutive overnights, followed by seven consecutive overnights with Parent B. This 14-day cycle repeats.'
    window.session.replace_document([text],'fictional.pdf','fixture')
    window.present(baseline([text]),'Proposal')
    assert not window.generate_button.isEnabled()
    window.review_checkbox.setChecked(True)
    window.approve()
    assert window.generate_button.isEnabled()
    window.generate()
    assert window.table.rowCount()==30
    window.rules.insertPlainText(' ')
    assert not window.generate_button.isEnabled() and window.table.rowCount()==0
    window.close(); app.processEvents()


def test_comparison_tab_reads_results_without_changing_approval(tmp_path):
    app=QApplication.instance() or QApplication([])
    window=MainWindow(tmp_path/'comparison.sqlite3')
    path=tmp_path/'results.json'
    path.write_text(json.dumps([{'id':'fictional','kind':'reject','expected':None,
        'local_model':{'actual':{'warnings':[]},'seconds':2}}]))
    window.open_comparison(path)
    assert window.tabs.count()==5 and window.comparison_table.rowCount()>0
    assert window.comparison_table.item(0,5).text()=='MISSED WARNING'
    assert window.session.schedule is None and not window.session.approved
    path.write_text('{}')
    with pytest.raises(ValueError): window.open_comparison(path)
    assert window.comparison_table.rowCount()==0
    window.close(); app.processEvents()


def test_visual_form_edits_clear_approval_and_update_serialized_rules(tmp_path):
    app=QApplication.instance() or QApplication([])
    window=MainWindow(tmp_path/'forms.sqlite3')
    text='Beginning 2026-11-02, Parent A has seven consecutive overnights, followed by seven consecutive overnights with Parent B. This 14-day cycle repeats.'
    window.session.replace_document([text],'fictional.pdf','fixture')
    window.present(baseline([text]),'Proposal')
    assert window.tabs.currentIndex()==1
    assert not window.approve_button.isEnabled()
    window.approve()
    assert not window.session.approved
    window.review_checkbox.setChecked(True);window.approve();window.generate()
    assert window.session.approved and window.table.rowCount()==30
    window.cycle_edits[0].setCurrentIndex(1)
    assert json.loads(window.rules.toPlainText())['cycle'][0]=='B'
    assert not window.session.approved and not window.review_checkbox.isChecked()
    assert window.table.rowCount()==0 and not window.generate_button.isEnabled()
    window.show_page(4)
    assert window.navigation.checkedId()==4
    window.close();app.processEvents()


def test_saved_record_search_filters_real_records(tmp_path):
    app=QApplication.instance() or QApplication([])
    window=MainWindow(tmp_path/'search.sqlite3')
    text='Beginning 2026-11-02, Parent A has seven consecutive overnights, followed by seven consecutive overnights with Parent B. This 14-day cycle repeats.'
    window.session.replace_document([text],'fictional.pdf','fixture')
    window.present(baseline([text]),'Proposal')
    window.review_checkbox.setChecked(True);window.approve()
    window.store.save('November fictional plan',window.session)
    window.store.save('December fictional plan',window.session)
    window.refresh_records();window.record_search.setText('november')
    visible=[r for r in range(window.record_table.rowCount()) if not window.record_table.isRowHidden(r)]
    assert len(visible)==1 and 'November' in window.record_table.item(visible[0],0).text()
    window.close();app.processEvents()
