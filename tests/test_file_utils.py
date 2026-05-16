import json

from assistant_core.execution.file_utils import load_supported_file


def test_load_text_markdown_json_and_log_files(tmp_path):
    txt = tmp_path / "note.txt"
    md = tmp_path / "note.md"
    log = tmp_path / "events.log"
    js = tmp_path / "data.json"
    txt.write_text("hello text", encoding="utf-8")
    md.write_text("# Hello", encoding="utf-8")
    log.write_text("INFO ok", encoding="utf-8")
    js.write_text(json.dumps({"a": 1}), encoding="utf-8")

    assert load_supported_file(txt)["content"] == "hello text"
    assert load_supported_file(md)["content"] == "# Hello"
    assert load_supported_file(log)["content"] == "INFO ok"
    assert load_supported_file(js)["parsed"] == {"a": 1}


def test_csv_profile_includes_shape_columns_preview_and_missing_values(tmp_path):
    csv_file = tmp_path / "people.csv"
    csv_file.write_text("name,age,city\nA,40,Riyadh\nB,,Dubai\n", encoding="utf-8")

    loaded = load_supported_file(csv_file)

    assert loaded["kind"] == "csv"
    assert loaded["profile"]["row_count"] == 2
    assert loaded["profile"]["columns"] == ["name", "age", "city"]
    assert loaded["profile"]["missing_values"]["age"] == 1
    assert len(loaded["profile"]["preview_rows"]) == 2
