import os
import json
from PIL import Image

def test_storage_and_serialize_integration(tmp_path):
    # LocalSerialize を直接初期化
    from scraper.storage.Serialize import LocalSerialize
    from scraper.storage.Storage import Storage

    serializer = LocalSerialize(base_dir=str(tmp_path))
    storage = Storage(
        serializer=serializer,
        title="統合テスト資料",
        released_at_j="2025年12月5日15時40分発表 気象庁。",
        released_at="2025-12-05T15:40:00+09:00",
        based_on_utc="2025-12-05T00:00:00Z"
    )

    # PNGファイルを保存
    img = Image.new("RGB", (5, 5), color="yellow")
    entry = {"id": "integration_png", "name": "integration.png", "title": "統合PNG"}
    storage.save(entry, img, {"input": "pillow", "output": "image/png"})

    # JSONファイルを保存
    entry_json = {"id": "integration_json", "name": "integration.json", "title": "統合JSON"}
    storage.save(entry_json, {"key": "value"}, {"input": "dict", "output": "application/json"})

    # commit 実行
    storage.commit()

    # ファイル存在確認
    assert (tmp_path / "integration.png").exists()
    assert (tmp_path / "integration.json").exists()
    assert (tmp_path / "metadata.json").exists()
    assert (tmp_path / "metadata_detail.json").exists()

    # metadata.json 確認（軽量版）
    with open(tmp_path / "metadata.json", encoding="utf-8") as f:
        metadata = json.load(f)
    ids = [f["id"] for f in metadata["files"]]
    assert "integration_png" in ids
    assert "integration_json" in ids

    # metadata_detail.json 確認（詳細版）
    with open(tmp_path / "metadata_detail.json", encoding="utf-8") as f:
        detail = json.load(f)
    outputs = [f["output"] for f in detail["files"]]
    assert "image/png" in outputs
    assert "application/json" in outputs
    # size と checksum が含まれているか
    for f in detail["files"]:
        assert "size" in f
        assert "checksum_md5" in f