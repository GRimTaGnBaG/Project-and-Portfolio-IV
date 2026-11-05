"""Qt regression checks: build real widgets but never make a model request."""
# Load os for use in this module.
import os
# Load json for use in this module.
import json
# Load pytest for use in this module.
import pytest
# Use setdefault on environ.
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
# Bring in QApplication from PySide6.QtWidgets.
from PySide6.QtWidgets import QApplication
# Bring in MainWindow, InferenceWorker from parentvault.gui.
from parentvault.gui import MainWindow,InferenceWorker
# Bring in baseline from parentvault.core.
from parentvault.core import baseline


# Verify worker construction and approval control state.
def test_worker_construction_and_approval_control_state(tmp_path):
    app=QApplication.instance() or QApplication([])
    # A worker is not a widget: creating it must not call widget-only APIs.
    worker=InferenceWorker(['fictional page'],'test-model')
    # Verify that pages equals 'fictional page' and there is no is running before treating this
    # check as successful.
    assert worker.pages==['fictional page'] and not worker.isRunning()
    # Set window from main window.
    window=MainWindow(tmp_path/'gui.sqlite3')
    # Set text to 'Beginning 2026-11-02, Parent A has seven consecutive ov'.
    text='Beginning 2026-11-02, Parent A has seven consecutive overnights, followed by seven consecutive overnights with Parent B. This 14-day cycle repeats.'
    # Use replace document on session.
    window.session.replace_document([text],'fictional.pdf','fixture')
    # Use present on window.
    window.present(baseline([text]),'Proposal')
    # Verify that there is no is enabled before treating this check as successful.
    assert not window.generate_button.isEnabled()
    # Update the review or navigation checkbox state.
    window.review_checkbox.setChecked(True)
    # Use approve on window.
    window.approve()
    # Verify that generate button is enabled before treating this check as successful.
    assert window.generate_button.isEnabled()
    # Use generate on window.
    window.generate()
    # Verify that row count equals 30 before treating this check as successful.
    assert window.table.rowCount()==30
    # Use insert plain text on rules.
    window.rules.insertPlainText(' ')
    # Verify that there is no is enabled and row count equals 0 before treating this check as
    # successful.
    assert not window.generate_button.isEnabled() and window.table.rowCount()==0
    # Release the underlying file, connection, or window.
    window.close(); app.processEvents()


# Verify comparison tab reads results without changing approval.
def test_comparison_tab_reads_results_without_changing_approval(tmp_path):
    app=QApplication.instance() or QApplication([])
    # Set window from main window.
    window=MainWindow(tmp_path/'comparison.sqlite3')
    # Build the file or folder path for path.
    path=tmp_path/'results.json'
    # Save the text or JSON output using the requested encoding.
    path.write_text(json.dumps([{'id':'fictional','kind':'reject','expected':None,
        'local_model':{'actual':{'warnings':[]},'seconds':2}}]))
    # Use open comparison on window.
    window.open_comparison(path)
    # Verify that count equals 5 and row count exceeds 0 before treating this check as successful.
    assert window.tabs.count()==5 and window.comparison_table.rowCount()>0
    # Verify that text equals 'MISSED WARNING' before treating this check as successful.
    assert window.comparison_table.item(0,5).text()=='MISSED WARNING'
    # Verify that schedule is no value and there is no approved before treating this check as
    # successful.
    assert window.session.schedule is None and not window.session.approved
    # Save the text or JSON output using the requested encoding.
    path.write_text('{}')
    # Use a managed context for raises so exit handling runs automatically.
    with pytest.raises(ValueError): window.open_comparison(path)
    # Verify that row count equals 0 before treating this check as successful.
    assert window.comparison_table.rowCount()==0
    # Release the underlying file, connection, or window.
    window.close(); app.processEvents()


# Verify visual form edits clear approval and update serialized rules.
def test_visual_form_edits_clear_approval_and_update_serialized_rules(tmp_path):
    app=QApplication.instance() or QApplication([])
    # Set window from main window.
    window=MainWindow(tmp_path/'forms.sqlite3')
    # Set text to 'Beginning 2026-11-02, Parent A has seven consecutive ov'.
    text='Beginning 2026-11-02, Parent A has seven consecutive overnights, followed by seven consecutive overnights with Parent B. This 14-day cycle repeats.'
    # Use replace document on session.
    window.session.replace_document([text],'fictional.pdf','fixture')
    # Use present on window.
    window.present(baseline([text]),'Proposal')
    # Verify that current index equals 1 before treating this check as successful.
    assert window.tabs.currentIndex()==1
    # Verify that there is no is enabled before treating this check as successful.
    assert not window.approve_button.isEnabled()
    # Use approve on window.
    window.approve()
    # Verify that there is no approved before treating this check as successful.
    assert not window.session.approved
    # Update the review or navigation checkbox state.
    window.review_checkbox.setChecked(True);window.approve();window.generate()
    # Verify that approved is present or true and row count equals 30 before treating this check
    # as successful.
    assert window.session.approved and window.table.rowCount()==30
    # Select the specified page or option.
    window.cycle_edits[0].setCurrentIndex(1)
    # Verify that 0 field equals 'B' before treating this check as successful.
    assert json.loads(window.rules.toPlainText())['cycle'][0]=='B'
    # Verify that there is no approved and there is no is checked before treating this check as
    # successful.
    assert not window.session.approved and not window.review_checkbox.isChecked()
    # Verify that row count equals 0 and there is no is enabled before treating this check as
    # successful.
    assert window.table.rowCount()==0 and not window.generate_button.isEnabled()
    # Use show page on window.
    window.show_page(4)
    # Verify that checked id equals 4 before treating this check as successful.
    assert window.navigation.checkedId()==4
    # Release the underlying file, connection, or window.
    window.close();app.processEvents()


# Verify saved record search filters real records.
def test_saved_record_search_filters_real_records(tmp_path):
    app=QApplication.instance() or QApplication([])
    # Set window from main window.
    window=MainWindow(tmp_path/'search.sqlite3')
    # Set text to 'Beginning 2026-11-02, Parent A has seven consecutive ov'.
    text='Beginning 2026-11-02, Parent A has seven consecutive overnights, followed by seven consecutive overnights with Parent B. This 14-day cycle repeats.'
    # Use replace document on session.
    window.session.replace_document([text],'fictional.pdf','fixture')
    # Use present on window.
    window.present(baseline([text]),'Proposal')
    # Update the review or navigation checkbox state.
    window.review_checkbox.setChecked(True);window.approve()
    november_id=window.store.save('November fictional plan',window.session)
    # Preserve the current state or write the record through its storage interface.
    window.store.save('December fictional plan',window.session)
    # Use refresh records on window.
    window.refresh_records();window.record_search.setText('november')
    # Build visible by transforming the entries from range.
    visible=[r for r in range(window.record_table.rowCount()) if not window.record_table.isRowHidden(r)]
    # Verify that the number of visible equals 1 and 'November' is in text before treating this
    # check as successful.
    assert len(visible)==1 and 'November' in window.record_table.item(visible[0],0).text()
    # Verify that current data equals november id before treating this check as successful.
    assert window.record_list.currentData()==november_id
    # Verify that load button is enabled and delete button is enabled before treating this check
    # as successful.
    assert window.load_button.isEnabled() and window.delete_button.isEnabled()
    # Display the new text in the label or editor.
    window.record_search.setText('no matching fictional plan')
    # Verify that current data is no value before treating this check as successful.
    assert window.record_list.currentData() is None
    # Verify that there is no is enabled and there is no is enabled before treating this check as
    # successful.
    assert not window.load_button.isEnabled() and not window.delete_button.isEnabled()
    # An invisible selection must not be loaded even through a direct call.
    current_session=window.session
    # Use load on window.
    window.load()
    # Verify that session is current session before treating this check as successful.
    assert window.session is current_session
    # Remove the previous contents before displaying the next result.
    window.record_search.clear()
    # Verify that current data is not no value and load button is enabled before treating this
    # check as successful.
    assert window.record_list.currentData() is not None and window.load_button.isEnabled()
    # Release the underlying file, connection, or window.
    window.close();app.processEvents()
