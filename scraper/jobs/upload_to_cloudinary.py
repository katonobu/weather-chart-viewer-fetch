import json
import glob
import os
from pathlib import Path
import cloudinary
import cloudinary.uploader

# ---------------------------------------------------------
# 1. Cloudinary の設定（環境変数で設定するのが推奨）
# ---------------------------------------------------------
cloudinary.config(
#    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
#    api_key=os.getenv("CLOUDINARY_API_KEY"),
#    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    cloud_name="dywvp4rgx",
    api_key="585786924164654",
    api_secret="CwDkUvLj30VW3kMYN4wCvexg6T0",
    secure=True
)
# ---------------------------------------------------------
# 2. metadata_detail.json を読み込み、アップロード対象を抽出
# ---------------------------------------------------------
def upload_weather_images(base_dir: str):
    """
    base_dir: scraper/data/yyyymmdd_hhmm の絶対 or 相対パス
    """
    base_path = Path(base_dir)
    metadata_path = base_path / "metadata_detail.json"
    files_dir = base_path

    # metadata.json を読む
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # yyyymmdd_hhmm の部分をパス名に使う
    timestamp = metadata.get("id", base_path.name)  # 例: "20240214_1530"
    is_lognrange = timestamp.endswith("1000")
    is_am = int(timestamp.split("_")[-1], 10) < 1200
    tag_str = "long-range" if is_lognrange else ("short-range, am" if is_am else "short-range, pm")

    for target in ["files", "supplimental_files"]:
        for item in metadata.get(target, []):
            filename = item["name"]
            id = item["id"] # item["name"]の拡張子なし
            title = item["title"]
            local_file_path = files_dir / filename

            if not local_file_path.exists():
                print(f"⚠ ファイルが存在しません: {local_file_path}")
                continue

            # Cloudinary 側の保存パス
            cloudinary_public_id_wo_ext = f"weather-chart/{timestamp}/{id}"
            cloudinary_public_id_w_ext = f"weather-chart/{timestamp}/{filename}"

            print("Uploading:", local_file_path)
            print("Exists:", local_file_path.exists())
            print("Size:", local_file_path.stat().st_size if local_file_path.exists() else "N/A")

            # ---------------------------------------------------------
            # 3. Cloudinary にアップロード
            # ---------------------------------------------------------
            if target == "files":
                try:
                    print(f"⬆ Uploading {local_file_path} → {cloudinary_public_id_wo_ext}")
                    result = cloudinary.uploader.upload(
                        str(local_file_path),
                        public_id=cloudinary_public_id_wo_ext,
                        overwrite=True,
                        resource_type="image",
                        asset_folder=f"weather-chart/{timestamp}",
                        tags=tag_str,
                        context=f"caption={title}"                 
                    )
                    print(f"✔ Uploaded: {result.get('secure_url')}")
                except Exception as e:
                    try:
                        print(f"⬆ Uploading {local_file_path} → {cloudinary_public_id_w_ext}")
                        result = cloudinary.uploader.upload(
                            str(local_file_path),
                            public_id=cloudinary_public_id_w_ext,
                            overwrite=True,
                            resource_type="raw",
                            asset_folder=f"weather-chart/{timestamp}",
                            tags=tag_str,
                            context=f"caption={title}"                 
                        )
                        print(f"✔ Uploaded: {result.get('secure_url')}")

                    except Exception as e:
                        print(f"❌ Upload failed for {local_file_path}: {e}")
                print("-" * 50)
            else:
                try:
                    print(f"⬆ Uploading {local_file_path} → {cloudinary_public_id_w_ext}")
                    result = cloudinary.uploader.upload(
                        str(local_file_path),
                        public_id=cloudinary_public_id_w_ext,
                        overwrite=True,
                        resource_type="raw",
                        asset_folder=f"weather-chart/{timestamp}",
                        tags=tag_str,
                        context=f"caption={title}"                 
                    )
                    print(f"✔ Uploaded: {result.get('secure_url')}")
                except Exception as e:
                    print(f"❌ Upload failed for {local_file_path}: {e}")
                print("-" * 50)



def upload_to_cloudinary():
    dirs = sorted(glob.glob("scraper/data/**"), key = lambda x: x.split("/")[-1], reverse=True)
    if 0 < len(dirs):
        path = dirs[0]
        upload_weather_images(path)

# ---------------------------------------------------------
# 実行例
# ---------------------------------------------------------
if __name__ == "__main__":
    upload_to_cloudinary()

