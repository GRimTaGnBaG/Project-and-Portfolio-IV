"""Historical evidence must show wrong, missing, and rejected results honestly."""
# Load json for use in this module.
import json
# Load pytest for use in this module.
import pytest
# Bring in load_comparison from parentvault.comparison.
from parentvault.comparison import load_comparison


# Verify comparison preserves mismatch null and method error.
def test_comparison_preserves_mismatch_null_and_method_error(tmp_path):
    # Build the file or folder path for path.
    path=tmp_path/'results.json'
    # Save the text or JSON output using the requested encoding.
    path.write_text(json.dumps([{'id':'fictional','expected':{'anchor_date':'2026-11-02','cycle':['A']*7+['B']*7,'exchange_time':None},
        'baseline':{'error':'No supported rule','seconds':.01},
        'local_model':{'actual':{'anchor_date':'2026-11-02','cycle':['A','B']*7,'exchange_time':None},'seconds':2}}]))
    # Set rows from load comparison.
    rows=load_comparison(path)
    # Verify that any is present or true before treating this check as successful.
    assert any(row[5]=='Error / abstention' and row[4]=='No supported rule' for row in rows)
    # Verify that any is present or true before treating this check as successful.
    assert any(row[2]=='cycle' and row[5]=='MISMATCH' for row in rows)
    # Verify that any is present or true before treating this check as successful.
    assert any(row[2]=='exchange_time' and row[5]=='Match' for row in rows)


# Verify unsupported without warning is not labeled correct.
def test_unsupported_without_warning_is_not_labeled_correct(tmp_path):
    # Build the file or folder path for path.
    path=tmp_path/'results.json'
    # Save the text or JSON output using the requested encoding.
    path.write_text(json.dumps([{'id':'exception','kind':'reject','expected':None,
        'local_model':{'actual':{'warnings':[]},'seconds':1}}]))
    # Set rows from load comparison.
    rows=load_comparison(path)
    # Verify that 5 field equals 'MISSED WARNING' before treating this check as successful.
    assert rows[0][5]=='MISSED WARNING'


# Verify request file and invalid runtime are rejected.
def test_request_file_and_invalid_runtime_are_rejected(tmp_path):
    # Build the file or folder path for path.
    path=tmp_path/'results.json';path.write_text('{"request":{}}')
    # Use a managed context for raises so exit handling runs automatically.
    with pytest.raises(ValueError,match='results.json'): load_comparison(path)
    # Save the text or JSON output using the requested encoding.
    path.write_text(json.dumps([{'id':'case','baseline':{'seconds':-1,'error':'failure'}}]))
    # Use a managed context for raises so exit handling runs automatically.
    with pytest.raises(ValueError,match='Runtime'): load_comparison(path)
