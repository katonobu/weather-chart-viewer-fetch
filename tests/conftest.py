import pytest
from scraper.storage.Storage import Storage
from scraper.storage.Serialize import LocalSerialize

@pytest.fixture
def serializer(tmp_path):
    """
    LocalSerialize を一時ディレクトリに設定するフィクスチャ。
    各テストで使い回せる。
    """
    return LocalSerialize(base_dir=str(tmp_path))


@pytest.fixture
def storage(serializer):
    """
    Storage インスタンスを返すフィクスチャ。
    各テストで共通の初期化処理をまとめる。
    """
    return Storage(
        serializer=serializer,
        title="テスト資料",
        released_at_j="2025年12月5日15時40分発表 気象庁。",
        released_at="2025-12-05T15:40:00+09:00",
        based_on_utc="2025-12-05T00:00:00Z"
    )