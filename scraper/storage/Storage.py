class Storage:
    def __init__(self, serializer, dir_name:str, title: str, released_at_j: str, released_at: str, based_on_utc: str):
        self.serializer = serializer
        self.dir_name = dir_name
        self.title = title
        self.released_at_j = released_at_j
        self.released_at = released_at
        self.based_on_utc = based_on_utc
        self.files = []
        self.supplimental_files = []

    def save(self, entry: dict, content, type: dict, is_supplimental=False):
        """
        entry: {"id": ..., "name": ..., "title": ...} を含む辞書
               将来拡張で tags, description 等を追加可能
        """
        # serialize() 実行 → ファイル保存＋属性計算
        result = self.serializer.serialize(content, type, entry["name"])

        # entry に結果を追加
        entry.update(result)

        if is_supplimental:
            self.supplimental_files.append(entry)
        else:
            self.files.append(entry)

    def commit(self):
        """
        metadata.json と metadata_detail.json を生成する。
        - metadata.json: id, name, title のみ
        - metadata_detail.json: entry辞書そのもの
        """
        metadata_entry = {
            "id":"metadata",
            "name":"metadata.json",
            "title":"表示用メタデータ",
        }
        metadata_detail_entry = {
            "id":"metadata_detail",
            "name":"metadata_detail.json",
            "title":"メタデータ詳細",
        }

        # 軽量版 metadata.json
        metadata = {
            "id": self.dir_name,
            "title": self.title,
            "released_at_j": self.released_at_j,
            "released_at": self.released_at,
            "based_on_utc": self.based_on_utc,
            "files": [
                {"id": f["id"], "name": f["name"], "title": f["title"]}
                for f in self.files
            ],
            "supplimental_files": [
                {"id": f["id"], "name": f["name"], "title": f["title"]}
                for f in self.supplimental_files
            ]
        }
        result = self.serializer.serialize(metadata, {"input": "dict", "output": "application/json"}, metadata_entry["name"])
        metadata_entry.update(result)

        self.supplimental_files.append(metadata_entry)
        self.supplimental_files.append(metadata_detail_entry)

        # 詳細版 metadata_detail.json
        metadata_detail = {
            "id": self.dir_name,
            "title": self.title,
            "released_at_j": self.released_at_j,
            "released_at": self.released_at,
            "based_on_utc": self.based_on_utc,
            "files": self.files,  # entryそのもの（size, checksum_md5, output含む）
            "supplimental_files": self.supplimental_files
        }
        self.serializer.serialize(metadata_detail, {"input": "dict", "output": "application/json"}, metadata_detail_entry["name"])

