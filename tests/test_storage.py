import os
import json
from PIL import Image
import pytest


def test_save_and_commit_png(storage, tmp_path):
    # PNGファイルを保存
    img = Image.new("RGB", (5, 5), color="red")
    entry = {"id": "png_test", "name": "test.png", "title": "PNGテスト"}
    storage.save(entry, img, {"input": "pillow", "output": "image/png"})
    storage.commit()

    # ファイル存在確認
    assert (tmp_path / "test.png").exists()

    # metadata.json 確認（軽量版）
    with open(tmp_path / "metadata.json", encoding="utf-8") as f:
        metadata = json.load(f)
    assert metadata["files"][0]["id"] == "png_test"
    assert "title" in metadata["files"][0]

    # metadata_detail.json 確認（詳細版）
    with open(tmp_path / "metadata_detail.json", encoding="utf-8") as f:
        detail = json.load(f)
    assert detail["files"][0]["output"] == "image/png"
    assert "size" in detail["files"][0]
    assert "checksum_md5" in detail["files"][0]


def test_save_supplimental_file(storage, tmp_path):
    # 補助ファイルとして保存
    entry = {"id": "sup_test", "name": "sup.json", "title": "補助JSON"}
    storage.save(entry, {"key": "value"}, {"input": "dict", "output": "application/json"}, is_supplimental=True)
    storage.commit()

    # metadata.json 確認
    with open(tmp_path / "metadata.json", encoding="utf-8") as f:
        metadata = json.load(f)
    assert metadata["supplimental_files"][0]["id"] == "sup_test"

    # metadata_detail.json 確認
    with open(tmp_path / "metadata_detail.json", encoding="utf-8") as f:
        detail = json.load(f)
    assert detail["supplimental_files"][0]["output"] == "application/json"


def test_invalid_entry(storage):
    # entry に name がない場合 → KeyError
    entry = {"id": "bad_entry", "title": "不正"}
    with pytest.raises(KeyError):
        storage.save(entry, b"dummy", {"input": "binary", "output": "image/png"})