"""Prevent invalid experiment definitions from corrupting stored evidence."""
# Load json for use in this module.
import json
# Bring in Path from pathlib.
from pathlib import Path
# Load pytest for use in this module.
import pytest
# Bring in load_cases from evaluate_dataset.
from evaluate_dataset import load_cases


# Verify authored manifest contains expected groups.
def test_authored_manifest_contains_expected_groups():
    # Set cases from load cases.
    cases=load_cases(Path(__file__).resolve().parents[1]/'fixtures'/'evaluation_cases.json')
    # Verify that the number of cases equals 12 before treating this check as successful.
    assert len(cases)==12
    assert {kind:sum(c['kind']==kind for c in cases) for kind in ('week','pattern','reject')}=={
        'week':4,'pattern':4,'reject':4}
    # Verify that sum equals 6 before treating this check as successful.
    assert sum(c['split']=='held_out' for c in cases)==6


# Verify manifest ids cannot escape the evidence folder.
@pytest.mark.parametrize('identifier',['../outside','folder/case','folder\\case',''])
def test_manifest_ids_cannot_escape_the_evidence_folder(tmp_path,identifier):
    # Build the file or folder path for path.
    path=tmp_path/'cases.json'
    # Save the text or JSON output using the requested encoding.
    path.write_text(json.dumps([{'id':identifier,'split':'held_out','kind':'reject','text':'Fictional incomplete input'}]))
    # Use a managed context for raises so exit handling runs automatically.
    with pytest.raises(ValueError,match='filename-safe'): load_cases(path)


# Verify duplicate ids cannot overwrite experiment results.
def test_duplicate_ids_cannot_overwrite_experiment_results(tmp_path):
    # Group id, split, kind, anchor, first, second in case.
    case={'id':'duplicate','split':'held_out','kind':'week','anchor':'2026-11-02','first':'A','second':'B'}
    # Build the file or folder path for path.
    path=tmp_path/'cases.json';path.write_text(json.dumps([case,case]))
    # Use a managed context for raises so exit handling runs automatically.
    with pytest.raises(ValueError,match='Duplicate'): load_cases(path)


# Verify pattern answer key cannot silently have thirteen days.
def test_pattern_answer_key_cannot_silently_have_thirteen_days(tmp_path):
    # Build the file or folder path for path.
    path=tmp_path/'cases.json'
    # Save the text or JSON output using the requested encoding.
    path.write_text(json.dumps([{'id':'bad_pattern','split':'development','kind':'pattern','anchor':'2026-11-02','cycle':['A']*6+['B']*7}]))
    # Use a managed context for raises so exit handling runs automatically.
    with pytest.raises(ValueError,match='fourteen'): load_cases(path)
