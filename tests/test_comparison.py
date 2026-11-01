"""Historical evidence must show wrong, missing, and rejected results honestly."""
import json
import pytest
from parentvault.comparison import load_comparison


def test_comparison_preserves_mismatch_null_and_method_error(tmp_path):
    path=tmp_path/'results.json'
    path.write_text(json.dumps([{'id':'fictional','expected':{'anchor_date':'2026-11-02','cycle':['A']*7+['B']*7,'exchange_time':None},
        'baseline':{'error':'No supported rule','seconds':.01},
        'local_model':{'actual':{'anchor_date':'2026-11-02','cycle':['A','B']*7,'exchange_time':None},'seconds':2}}]))
    rows=load_comparison(path)
    assert any(row[5]=='Error / abstention' and row[4]=='No supported rule' for row in rows)
    assert any(row[2]=='cycle' and row[5]=='MISMATCH' for row in rows)
    assert any(row[2]=='exchange_time' and row[5]=='Match' for row in rows)


def test_unsupported_without_warning_is_not_labeled_correct(tmp_path):
    path=tmp_path/'results.json'
    path.write_text(json.dumps([{'id':'exception','kind':'reject','expected':None,
        'local_model':{'actual':{'warnings':[]},'seconds':1}}]))
    rows=load_comparison(path)
    assert rows[0][5]=='MISSED WARNING'


def test_request_file_and_invalid_runtime_are_rejected(tmp_path):
    path=tmp_path/'results.json';path.write_text('{"request":{}}')
    with pytest.raises(ValueError,match='results.json'): load_comparison(path)
    path.write_text(json.dumps([{'id':'case','baseline':{'seconds':-1,'error':'failure'}}]))
    with pytest.raises(ValueError,match='Runtime'): load_comparison(path)
