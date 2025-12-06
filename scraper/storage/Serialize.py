import os
import json
import hashlib
from PIL import Image

class Serialize:
    def serialize(self, content, type: dict, file_name: str) -> dict:
        raise NotImplementedError


class LocalSerialize(Serialize):
    VALID_COMBINATIONS = {
        ("text", "image/svg+xml"),
        ("binary", "image/png"),
        ("binary", "image/jpeg"),
        ("pillow", "image/png"),
        ("pillow", "image/jpeg"),
        ("dict", "application/json"),
    }

    def __init__(self, base_name: str):
        self.base_dir = os.path.join(os.path.dirname(__file__), "..", "data", base_name)
        os.makedirs(self.base_dir, exist_ok=True)

    def serialize(self, content, type: dict, file_name: str) -> dict:
        input_type = type.get("input")
        output_type = type.get("output")

        # 組み合わせチェック
        if (input_type, output_type) not in self.VALID_COMBINATIONS:
            raise ValueError(f"Unsupported input/output combination: {input_type} -> {output_type}")

        file_path = os.path.join(self.base_dir, file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # 保存処理
        if (input_type, output_type) == ("text", "image/svg+xml"):
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

        elif (input_type, output_type) == ("binary", "image/png"):
            with open(file_path, "wb") as f:
                f.write(content)

        elif (input_type, output_type) == ("binary", "image/jpeg"):
            with open(file_path, "wb") as f:
                f.write(content)

        elif (input_type, output_type) == ("pillow", "image/png"):
            content.save(file_path, format="PNG")

        elif (input_type, output_type) == ("pillow", "image/jpeg"):
            content.save(file_path, format="JPEG")

        elif (input_type, output_type) == ("dict", "application/json"):
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(content, f, ensure_ascii=False, indent=2)

        # ファイル属性計算
        size = os.path.getsize(file_path)
        checksum_md5 = self._calc_md5(file_path)

        return {"size": size, "checksum_md5": checksum_md5, "output": output_type}

    def _calc_md5(self, file_path: str) -> str:
        md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5.update(chunk)
        return md5.hexdigest()
