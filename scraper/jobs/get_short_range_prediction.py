import datetime
from PIL import Image

from datetime import timedelta, timezone
from scraper.processors.get_svg import get_svg_from_pdf_url, get_svg_from_url
from scraper.processors.extract_text_parse import parse_tanki_yoho_kaisetsu_from_svg, extract_date
from scraper.processors.get_rader_image import get_rader_png
from scraper.processors.get_merge_tile_images import merge_images
from scraper.storage.Serialize import Serialize, LocalSerialize
from scraper.storage.Storage import Storage

def get_published_datetime():
    """
    短期予報解説のテキスト冒頭部分からdatetaime型の発表日時を取得する。
    合わせて、取得した短期予報解説のsvt,txt,url,発表日時の日本語文字列も返す。
    """
    url = "https://www.data.jma.go.jp/yoho/data/jishin/kaisetsu_tanki_latest.pdf"
    tanki_obj = get_svg_from_pdf_url(url)
    if "pages" in tanki_obj and 0 < len(tanki_obj["pages"]) and "texts" in tanki_obj["pages"][0]:
        svg = tanki_obj["pages"][0]["svg"]
        text_objs = parse_tanki_yoho_kaisetsu_from_svg(svg)
        if "name" in text_objs[0] and text_objs[0]["name"] == "短期予報解説資料":
            doc_title = text_objs[0]["sentences"][0].split()[0]
            published_at_jst = extract_date(doc_title)
            return (published_at_jst, svg, text_objs, url, doc_title)
    return (None, None, None, None, None)


def build_storage(published_at_jst:datetime, doc_title:str, Serialize:Serialize):
    """
    published_at_jst: timezone付のdatetime型の短期予報解資料説発表年月日時刻
    doc_title: 短期予報解資料記載の短期予報解説発表年月日時刻
    Serialize: 保存先メディアに応じたSerializeクラスのコンストラクタ
    """
    measure_publish_diff_hour = 6
    measure_publish_diff_min = 40
    measured_at_jst = published_at_jst - timedelta(hours = measure_publish_diff_hour, minutes=measure_publish_diff_min)
    measured_at_utc = measured_at_jst.astimezone(timezone.utc)
    dir_name = published_at_jst.strftime('%Y%m%d_%H%M')
    serializer = Serialize(dir_name)
    storage = Storage(serializer, dir_name, "短期予報解説資料", doc_title, published_at_jst.strftime("%Y-%m-%d %H:%M:%S"), measured_at_utc.strftime("%Y-%m-%d %H:%M:%S"))
    return (storage, measured_at_utc)


def save_tanki_kaisetsu(storage:Storage, url:str, svg:str, text_objs:list):
    storage.save(
        {
            "id":"tanki_yoho",
            "name":"kaisetsu_tanki.svg",
            "title":"短期予報解説資料",
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
            "id":"tanki_yoho_text",
            "name":"kaisetsu_tanki.json",
            "title":"短期予報解説資料テキスト",
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

def get_zikkyo_asia(storage:Storage, measured_at_utc:datetime):
    url = f'https://www.data.jma.go.jp/yoho/data/wxchart/quick/{measured_at_utc.strftime("%Y%m")}/ASAS_MONO_{measured_at_utc.strftime("%Y%m%d%H%M")}.svgz'
    zikkyo_chijo_obj = get_svg_from_url(url)
    if zikkyo_chijo_obj["result"] and "svg" in zikkyo_chijo_obj:
        storage.save(
            {
                "id":"ASAS",
                "name":"ASAS.svg",
                "title":"実況天気図（アジア太平洋域）",
                "urls":[url],
                "download_at":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            zikkyo_chijo_obj["svg"].decode(encoding='utf-8'),
            {
                "input":"text", 
                "output":"image/svg+xml"
            },
            False
        )

def get_amagumo(storage:Storage, measured_at_utc:datetime):
    yyyymmddhh_utc_str = measured_at_utc.strftime("%Y%m%d%H")
    result = get_rader_png(yyyymmddhh_utc_str)
    if "image" in result and result["image"] is not None:
        storage.save(
            {
                "id":"rain_rader_png",
                "name":result["name"],
                "title":f'レーダー画像({yyyymmddhh_utc_str})',
                "urls":result["urls"],
                "download_at":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            result["image"],
            {
                "input":"pillow",
                "output":"image/png"
            },
            False
        )

def get_himawari(storage:Storage, measured_at_utc:datetime):
    # ベースURL
    url_infos = [
        {
            "url": "https://www.jma.go.jp/bosai/himawari/data/satimg/{utc_str}/fd/{utc_str}/B03/ALBD/{z}/{a}/{b}.jpg",
            "name":"可視画像",
            "en": "vis"
        },{
            "url": "https://www.jma.go.jp/bosai/himawari/data/satimg/{utc_str}/fd/{utc_str}/B13/TBB/{z}/{a}/{b}.jpg",
            "name":"赤外画像",
            "en": "ir"
        },{
            "url": "https://www.jma.go.jp/bosai/himawari/data/satimg/{utc_str}/fd/{utc_str}/B08/TBB/{z}/{a}/{b}.jpg",
            "name":"水蒸気画像",
            "en": "vap"
        },{
            "url": "https://www.jma.go.jp/bosai/himawari/data/satimg/{utc_str}/fd/{utc_str}/REP/ETC/{z}/{a}/{b}.jpg",
            "name":"カラー画像",
            "en": "color"
        },{
            "url": "https://www.jma.go.jp/bosai/himawari/data/satimg/{utc_str}/fd/{utc_str}/SND/ETC/{z}/{a}/{b}.jpg",
            "name":"雲頂強調画像",
            "en": "strengthen"
        }
    ]

    utc_str = measured_at_utc.strftime("%Y%m%d%H") + "0000"
    # タイルの座標範囲（a_valuesが横方向、b_valuesが縦方向）
    a_values = [25, 26, 27, 28, 29, 30]#, 31]  # 横方向（列）
    b_values = [11, 12, 13, 14]  # 縦方向（行）
    z = 5

    print("    Downloading overlay images...")
    overlay_image, ovl_urls = merge_images("https://www.jma.go.jp/tile/jma/sat/{z}/{a}/{b}.png",utc_str, z, a_values, b_values)
    for info in url_infos:
        # 各タイル画像をダウンロードして統合
        print(f'     Downloading {info["name"]} images...')
        merged_image, urls = merge_images(info["url"], utc_str, z, a_values, b_values)
        final_image = Image.alpha_composite(merged_image, overlay_image)

        storage.save(
            {
                "id":f'sat_{info["en"]}',
                "name":f'{utc_str}_{info["en"]}.png',
                "title":f'{info["name"]}({utc_str[:10]})',
                "urls":ovl_urls.copy() + urls,
                "download_at":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            final_image.convert("RGB"),
            {
                "input":"pillow",
                "output":"image/png"
            },
            False
        )

def get_genkyo_koso(storage:Storage, measured_at_utc:datetime):
    measured_utc_hour_str = measured_at_utc.strftime("%H")
    genkyo_koso_objs = [
        {
            "url":f'https://www.jma.go.jp/bosai/numericmap/data/nwpmap/aupq35_{measured_utc_hour_str}.pdf',
            "name":"AUPQ35.svg",
            "title":"アジア500hPa・300hPa高度・気温・風・等風速線天気図"
        },
        {
            "url":f'https://www.jma.go.jp/bosai/numericmap/data/nwpmap/aupq78_{measured_utc_hour_str}.pdf',
            "name":"AUPQ78.svg",
            "title":"アジア850hPa・700hPa高度・気温・風・湿数天気図"
        },
        {
            "url":f'https://www.jma.go.jp/bosai/numericmap/data/nwpmap/axfe578_{measured_utc_hour_str}.pdf',
            "name":"AXFE578.svg",
            "title":"極東850hPa気温・風、700hPa上昇流／500hPa高度・渦度天気図"
        },
        {
            "url":f'https://www.jma.go.jp/bosai/numericmap/data/nwpmap/axjp140_{measured_utc_hour_str}.pdf',
            "name":"AXJP130_AXJP140.svg",
            "title":"高層断面図（風・気温・露点等）東経130度／140度解析"
        },
    ]

    for url_file_obj in genkyo_koso_objs:
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

def get_prediction_charts(storage:Storage, measured_at_utc:datetime):
    measured_utc_hour_str = measured_at_utc.strftime("%H")
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
        },
        {
            "url":f'https://www.jma.go.jp/bosai/numericmap/data/nwpmap/fxfe502_{measured_utc_hour_str}.pdf',
            "name":"FXFE502.svg",
            "title":"極東地上気圧・風・降水量／500hPa高度・渦度予想図 12・24時間"
        },
        {
            "url":f'https://www.jma.go.jp/bosai/numericmap/data/nwpmap/fxfe504_{measured_utc_hour_str}.pdf',
            "name":"FXFE504.svg",
            "title":"極東地上気圧・風・降水量／500hPa高度・渦度予想図 36・48時間"
        },
        {
            "url":f'https://www.jma.go.jp/bosai/numericmap/data/nwpmap/fxfe5782_{measured_utc_hour_str}.pdf',
            "name":"FXFE5782.svg",
            "title":"極東850hPa気温・風、700hPa上昇流／700hPa湿数、500hPa気温予想図 12・24時間"
        },
        {
            "url":f'https://www.jma.go.jp/bosai/numericmap/data/nwpmap/fxfe5784_{measured_utc_hour_str}.pdf',
            "name":"FXFE5784.svg",
            "title":"極東850hPa気温・風、700hPa上昇流／700hPa湿数、500hPa気温予想図 36・48時間"
        },
        {
            "url":f'https://www.jma.go.jp/bosai/numericmap/data/nwpmap/fxjp854_{measured_utc_hour_str}.pdf',
            "name":"FXJP854.svg",
            "title":"日本850hPa相当温位・風予想図 12・24・36・48時間"
        },
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


def get_short_range_prediction():
    print("Getting 短期予報解説資料...")
    published_at_jst, svg, text_objs, url, doc_title = get_published_datetime()
    if published_at_jst is not None:
        storage, measured_at_utc = build_storage(published_at_jst, doc_title, LocalSerialize)
        save_tanki_kaisetsu(storage, url, svg, text_objs)

        print("  Getting ASAS 実況天気図（アジア太平洋域）...")
        get_zikkyo_asia(storage, measured_at_utc)

        print("  Getting 雨雲画像...")
        get_amagumo(storage, measured_at_utc)

        print("  Getting 衛星画像...")
        get_himawari(storage, measured_at_utc)

        print("  Getting 現況高層...")
        get_genkyo_koso(storage, measured_at_utc)

        print("  Getting 予想天気図...")
        get_prediction_charts(storage, measured_at_utc)

        storage.commit()

if __name__ == "__main__":
    get_short_range_prediction()