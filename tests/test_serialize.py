import os
import json
import pytest
from PIL import Image
from scraper.storage.Serialize import LocalSerialize

def test_serialize_png(serializer, tmp_path):
    # PillowオブジェクトをPNGとして保存
    img = Image.new("RGB", (5, 5), color="blue")
    result = serializer.serialize(img, {"input": "pillow", "output": "image/png"}, "test.png")

    # ファイル存在確認
    file_path = tmp_path / "test.png"
    assert file_path.exists()

    # 戻り値の属性確認
    assert result["output"] == "image/png"
    assert result["size"] == os.path.getsize(file_path)
    assert "checksum_md5" in result


def test_serialize_json(serializer, tmp_path):
    data = {"key": "value"}
    result = serializer.serialize(data, {"input": "dict", "output": "application/json"}, "test.json")

    file_path = tmp_path / "test.json"
    assert file_path.exists()

    # JSON内容確認
    with open(file_path, encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["key"] == "value"

    # 戻り値の属性確認
    assert result["output"] == "application/json"
    assert result["size"] == os.path.getsize(file_path)
    assert "checksum_md5" in result


def test_serialize_svg(serializer, tmp_path):
    svg_text = "<svg><rect width='10' height='10' fill='red'/></svg>"
    result = serializer.serialize(svg_text, {"input": "text", "output": "image/svg+xml"}, "test.svg")

    file_path = tmp_path / "test.svg"
    assert file_path.exists()

    # 内容確認
    with open(file_path, encoding="utf-8") as f:
        content = f.read()
    assert "<rect" in content

    # 戻り値の属性確認
    assert result["output"] == "image/svg+xml"
    assert result["size"] == os.path.getsize(file_path)
    assert "checksum_md5" in result


# 有効な組み合わせ一覧
valid_cases = [
    ("text", "image/svg+xml", "<svg><rect width='10' height='10'/></svg>", "test.svg"),
    ("binary", "image/png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 10, "bin.png"),
    ("binary", "image/jpeg", b"\xff\xd8\xff" + b"\x00" * 10, "bin.jpg"),
    ("pillow", "image/png", Image.new("RGB", (5, 5), color="blue"), "pillow.png"),
    ("pillow", "image/jpeg", Image.new("RGB", (5, 5), color="green"), "pillow.jpg"),
    ("dict", "application/json", {"key": "value"}, "test.json"),
]

@pytest.mark.parametrize("input_type,output_type,content,file_name", valid_cases)
def test_valid_combinations(tmp_path, input_type, output_type, content, file_name):
    serializer = LocalSerialize(base_dir=str(tmp_path))
    result = serializer.serialize(content, {"input": input_type, "output": output_type}, file_name)

    # ファイルが生成されているか
    file_path = tmp_path / file_name
    assert file_path.exists()

    # 戻り値の属性確認
    assert result["output"] == output_type
    assert result["size"] == os.path.getsize(file_path)
    assert "checksum_md5" in result

    # JSONの場合は内容確認
    if output_type == "application/json":
        with open(file_path, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded["key"] == "value"


def test_invalid_combination(tmp_path):
    serializer = LocalSerialize(base_dir=str(tmp_path))
    # NG: pillow → application/json は許可されていない
    with pytest.raises(ValueError):
        serializer.serialize(Image.new("RGB", (5, 5)), {"input": "pillow", "output": "application/json"}, "bad.json")    