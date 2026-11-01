"""Prevent invalid experiment definitions from corrupting stored evidence."""
import json
from pathlib import Path
import pytest
from evaluate_dataset import load_cases


def test_authored_manifest_contains_expected_groups():
    cases=load_cases(Path(__file__).resolve().parents[1]/'fixtures'/'evaluation_cases.json')
    assert len(cases)==12
    assert {kind:sum(c['kind']==kind for c in cases) for kind in ('week','pattern','reject')}=={
        'week':4,'pattern':4,'reject':4}
    assert sum(c['split']=='held_out' for c in cases)==6


@pytest.mark.parametrize('identifier',['../outside','folder/case','folder\\case',''])
def test_manifest_ids_cannot_escape_the_evidence_folder(tmp_path,identifier):
    path=tmp_path/'cases.json'
    path.write_text(json.dumps([{'id':identifier,'split':'held_out','kind':'reject','text':'Fictional incomplete input'}]))
    with pytest.raises(ValueError,match='filename-safe'): load_cases(path)


def test_duplicate_ids_cannot_overwrite_experiment_results(tmp_path):
    case={'id':'duplicate','split':'held_out','kind':'week','anchor':'2026-11-02','first':'A','second':'B'}
    path=tmp_path/'cases.json';path.write_text(json.dumps([case,case]))
    with pytest.raises(ValueError,match='Duplicate'): load_cases(path)


def test_pattern_answer_key_cannot_silently_have_thirteen_days(tmp_path):
    path=tmp_path/'cases.json'
    path.write_text(json.dumps([{'id':'bad_pattern','split':'development','kind':'pattern','anchor':'2026-11-02','cycle':['A']*6+['B']*7}]))
    with pytest.raises(ValueError,match='fourteen'): load_cases(path)
