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
    assert window.tabs.count()==4 and window.comparison_table.rowCount()>0
    assert window.comparison_table.item(0,5).text()=='MISSED WARNING'
    assert window.session.schedule is None and not window.session.approved
    path.write_text('{}')
    with pytest.raises(ValueError): window.open_comparison(path)
    assert window.comparison_table.rowCount()==0
    window.close(); app.processEvents()
