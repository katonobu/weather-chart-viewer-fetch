import boto3
import json
import os

if os.getenv("GITHUB_ACTIONS", "false").lower() == "true":
    BUCKET = os.environ.get("BUCKET")
    PREFIX = os.environ.get("PREFIX")
    s3 = boto3.client("s3")
else:
    BUCKET="frontend-cmn-weatherchart-content"
    PREFIX="shared/services/weatherchart/"

    session = boto3.Session(profile_name="cnt")
    s3 = session.client("s3")

response = s3.list_objects_v2(
    Bucket=BUCKET,
    Prefix=PREFIX,
    Delimiter="/"
)

dirs = []

for item in response.get("CommonPrefixes", []):
    prefix = item["Prefix"]

    # prefix削除
    name = prefix.replace(PREFIX, "", 1)

    # 末尾スラッシュ削除
    name = name.rstrip("/")

    if name:
        dirs.append(name)

# 新しい順に並び替え
dirs = sorted(dirs, reverse=True)

# JSON出力
with open("directory_list.json", "w") as f:
    json.dump(dirs, f, indent=2)

print("Generated directory_list.json")
print(json.dumps(dirs, indent=2))