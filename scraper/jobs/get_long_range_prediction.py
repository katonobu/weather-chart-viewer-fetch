import datetime
from PIL import Image

from datetime import timedelta, timezone
from scraper.processors.get_svg import get_svg_from_pdf_url, get_svg_from_url
from scraper.processors.extract_text_parse import parse_syukan_yoho_kaisetsu, extract_date
from scraper.processors.get_rader_image import get_png_from_url
from scraper.processors.get_merge_tile_images import merge_images
from scraper.storage.Serialize import Serialize, LocalSerialize
from scraper.storage.Storage import Storage

def get_published_datetime():
    """
    週間天気予報解説のテキスト冒頭部分からdatetaime型の発表日時を取得する。
    合わせて、取得した週間天気予報解説のsvt,txt,url,発表日時の日本語文字列も返す。
    """
    url = "https://www.data.jma.go.jp/yoho/data/jishin/kaisetsu_shukan_latest.pdf"
    weekly_obj = get_svg_from_pdf_url(url)
    if "pages" in weekly_obj and 0 < len(weekly_obj["pages"]) and "texts" in weekly_obj["pages"][0]:
        svgs = [item["svg"] for item in weekly_obj["pages"]]
        text_objs = parse_syukan_yoho_kaisetsu(weekly_obj["pages"][0]["texts"])
        if "name" in text_objs[0] and text_objs[0]["name"] == "週間天気予報解説資料":
            doc_title = text_objs[0]["sentences"][0]
            published_at_jst = extract_date(doc_title)
            return (published_at_jst, svgs, text_objs, url, doc_title)
    return (None, None, None, None, None)


def build_storage(published_at_jst:datetime, doc_title:str, Serialize:Serialize):
    """
    published_at_jst: timezone付のdatetime型の週間天気予報解資料説発表年月日時刻
    doc_title: 週間天気予報解資料記載の短期予報解説発表年月日時刻
    Serialize: 保存先メディアに応じたSerializeクラスのコンストラクタ
    """
    dir_name = published_at_jst.strftime('%Y%m%d_%H%M')
    serializer = Serialize(dir_name)
    storage = Storage(serializer, dir_name, "週間天気予報解説資料", doc_title, published_at_jst.strftime("%Y-%m-%d %H:%M:%S"), None)
    return (storage, None)


def save_syukan_kaisetsu(storage:Storage, url:str, svgs:list, text_objs:list):
    for idx, svg in enumerate(svgs):
        file_name = f'syukan_yoho_{idx + 1}.svg'
        storage.save(
            {
                "id":file_name.replace(".svg",""),
                "name":file_name,
                "title":f'週間天気予報解説資料ページ{idx + 1}',
                "urls":[url],
                "download_at":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            svg,
            {
                "input":"text", 
                "output":"image/svg+xml"
            },
            False
        )
    storage.save(
        {
            "id":"syukan_yoho_text",
            "name":"syukan_yuoho.json",
            "title":"週間天気予報解説資料テキスト",
            "urls":[url],
            "download_at":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        text_objs,
        {
            "input":"dict",
            "output":"application/json"
        },
        True
    )


def get_yoho_shien(storage:Storage, measured_at_utc:datetime):
    # 週間予報支援図
    yoho_shien_objs = [
        {
            "url":'https://www.jma.go.jp/bosai/numericmap/data/nwpmap/fzcx50.png',
            "name":"FZCX50.png",
            "title":"週間予報支援図（アンサンブル）"
        },
        {
            "url":'https://www.jma.go.jp/bosai/numericmap/data/nwpmap/fxxn519.png',
            "name":"FXXN519.png",
            "title":"週間予報支援図"
        }
    ]

    for url_file_obj in yoho_shien_objs:
        print(f'  Getting {url_file_obj["name"].replace(".png","")} {url_file_obj["title"]}...')
        obj = get_png_from_url(url_file_obj["url"])
        if obj["result"] and "content" in obj:
            file_name = url_file_obj["name"]
            storage.save(
                {
                    "id":file_name.replace(".png",""),
                    "name":url_file_obj["name"],
                    "title":url_file_obj["title"],
                    "urls":[url_file_obj["url"]],
                    "download_at":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                obj["content"],
                {
                    "input":"binary", 
                    "output":"image/png"
                },
                False
            )

def get_prediction_charts(storage:Storage, measured_at_utc:datetime):
    yoho_objs = [
        {
            "url":'https://www.data.jma.go.jp/yoho/data/wxchart/quick/FSAS24_MONO_ASIA.pdf',
            "name":"FSAS24.svg",
            "title":"アジア太平洋域 24時間"
        },
        {
            "url":'https://www.data.jma.go.jp/yoho/data/wxchart/quick/FSAS48_MONO_ASIA.pdf',
            "name":"FSAS48.svg",
            "title":"アジア太平洋域 48時間"
        }
    ]
    for url_file_obj in yoho_objs:
        print(f'  Getting {url_file_obj["name"].replace(".svg","")} {url_file_obj["title"]}...')
        obj = get_svg_from_pdf_url(url_file_obj["url"])
        if obj["result"] and 0 < len(obj["pages"]) and "svg" in obj["pages"][0]:
            file_name = url_file_obj["name"]
            storage.save(
                {
                    "id":file_name.replace(".svg",""),
                    "name":url_file_obj["name"],
                    "title":url_file_obj["title"],
                    "urls":[url_file_obj["url"]],
                    "download_at":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                obj["pages"][0]["svg"],
                {
                    "input":"text", 
                    "output":"image/svg+xml"
                },
                False
            )


def get_long_range_prediction():
    print("Getting 週間天気予報解説資料...")
    published_at_jst, svgs, text_objs, url, doc_title = get_published_datetime()
    if published_at_jst is not None:
        storage, measured_at_utc = build_storage(published_at_jst, doc_title, LocalSerialize)
        save_syukan_kaisetsu(storage, url, svgs, text_objs)

        print("  Getting 予報支援図...")
        get_yoho_shien(storage, measured_at_utc)

        print("  Getting 予想天気図...")
        get_prediction_charts(storage, measured_at_utc)

        storage.commit()

if __name__ == "__main__":
    get_long_range_prediction()
    pass