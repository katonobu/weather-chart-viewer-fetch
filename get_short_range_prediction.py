import os
import json
import datetime
import markdown
from get_sat_image import get_sat_images
from get_rader_png import get_rader_png
from get_svg_from_pdf_url import get_svg_from_pdf_url, get_svg_from_url, extract_date
from extract_text import parse_tanki_yoho_kaisetsu
if __name__ == "__main__":

    jst_hour_diff = 9
    release_duration_hour = 6
    release_duration_minutes = 40

    file_infos = []
    md_text = '<a id="top"></a>\n'
    print(f'Start at {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

    # 短期予報解説資料を取得
    print("Getting 短期予報解説資料...")
    tanki_obj = get_svg_from_pdf_url("https://www.data.jma.go.jp/yoho/data/jishin/kaisetsu_tanki_latest.pdf")
    # textが抽出されていたら
    if tanki_obj["result"] and 0 < len(tanki_obj["pages"]) and "texts" in tanki_obj["pages"][0]:
        # textから発表日時を取得
        for idx in range(3):
            title_str = tanki_obj["pages"][0]["texts"].split("\n")[idx]
            if "短期予報解説資料" in title_str:
                break
        if "短期予報解説資料" not in title_str:
            print("Failed to extract title from 短期予報解説資料.")
            exit(1)
        md_text += f'# {title_str.split()[0].replace("1","")}\n'
        reported_at_str = title_str.split()[1]
        md_text += f'## {reported_at_str}\n'
        released_datetime = extract_date(reported_at_str)
        print(f'Published at {released_datetime}(JST)')

        # 参照元の観測時刻のUTC時刻を生成
        td = datetime.timedelta(hours = jst_hour_diff+release_duration_hour, minutes=release_duration_minutes)
        utc_snapshot_datetime = released_datetime - td
        get_utc_time_str = utc_snapshot_datetime.strftime("%Y%m%d%H%M")
        print(f'Based     on {utc_snapshot_datetime}(UTC)')

        output_base_dir = os.path.join(os.path.dirname(__file__), "output", released_datetime.strftime('%Y%m%d_%H%M'))

        # 発表時刻名のディレクトリを掘る
        os.makedirs(output_base_dir, exist_ok=True)

        if "svg" in tanki_obj["pages"][0]:
            # 短期予報のsvgを保存
            tanki_yoho_svg_path_name = os.path.join(output_base_dir, "kaisetsu_tanki.svg")
            with open(tanki_yoho_svg_path_name, "w", encoding="utf-8") as f:
                f.write(tanki_obj["pages"][0]["svg"])
            file_infos.append({
                "id":"tanki_yoho",
                "name":"kaisetsu_tanki.svg",
                "title":"短期予報解説資料",
            })

        # 実況天気図（アジア太平洋域）
        zikkyo_chijo_svg_url = f'https://www.data.jma.go.jp/yoho/data/wxchart/quick/{released_datetime.strftime("%Y%m")}/ASAS_MONO_{get_utc_time_str}.svgz'
        print("  Getting ASAS 実況天気図（アジア太平洋域）...")
        zikkyo_chijo_obj = get_svg_from_url(zikkyo_chijo_svg_url)
        if zikkyo_chijo_obj["result"] and "svg" in zikkyo_chijo_obj:
            zikkyo_chijo_svg_path_name = os.path.join(output_base_dir, "ASAS.svg")
            with open(zikkyo_chijo_svg_path_name, "w", encoding="utf-8") as f:
                f.write(zikkyo_chijo_obj["svg"].decode(encoding='utf-8'))
            file_infos.append({
                "id":"ASAS",
                "name":"ASAS.svg",
                "title":"実況天気図（アジア太平洋域）",
            })

        # レーダー画像取得
        yyyymmddhh_utc_str = get_utc_time_str[:10]
        rain_rader_png_path = get_rader_png(yyyymmddhh_utc_str, output_base_dir)
        file_infos.append({
            "id":"rain_rader_png",
            "name":os.path.basename(rain_rader_png_path),
            "title":f'レーダー画像({yyyymmddhh_utc_str})'
        })

        # 衛星画像取得
        file_infos += get_sat_images(output_base_dir, yyyymmddhh_utc_str+"0000")

        # 現況高層天気図
        get_utc_hour_str = get_utc_time_str[8:10]
        genkyo_objs = [
            {
                "url":f'https://www.jma.go.jp/bosai/numericmap/data/nwpmap/aupq35_{get_utc_hour_str}.pdf',
                "name":"AUPQ35.svg",
                "title":"アジア500hPa・300hPa高度・気温・風・等風速線天気図"
            },
            {
                "url":f'https://www.jma.go.jp/bosai/numericmap/data/nwpmap/aupq78_{get_utc_hour_str}.pdf',
                "name":"AUPQ78.svg",
                "title":"アジア850hPa・700hPa高度・気温・風・湿数天気図"
            },
            {
                "url":f'https://www.jma.go.jp/bosai/numericmap/data/nwpmap/axfe578_{get_utc_hour_str}.pdf',
                "name":"AXFE578.svg",
                "title":"極東850hPa気温・風、700hPa上昇流／500hPa高度・渦度天気図"
            },
            {
                "url":f'https://www.jma.go.jp/bosai/numericmap/data/nwpmap/axjp140_{get_utc_hour_str}.pdf',
                "name":"AXJP130_AXJP140.svg",
                "title":"高層断面図（風・気温・露点等）東経130度／140度解析"
            },
        ]
        # 予報天気図
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
                "url":f'https://www.jma.go.jp/bosai/numericmap/data/nwpmap/fxfe502_{get_utc_hour_str}.pdf',
                "name":"FXFE502.svg",
                "title":"極東地上気圧・風・降水量／500hPa高度・渦度予想図 12・24時間"
            },
            {
                "url":f'https://www.jma.go.jp/bosai/numericmap/data/nwpmap/fxfe504_{get_utc_hour_str}.pdf',
                "name":"FXFE504.svg",
                "title":"極東地上気圧・風・降水量／500hPa高度・渦度予想図 36・48時間"
            },
            {
                "url":f'https://www.jma.go.jp/bosai/numericmap/data/nwpmap/fxfe5782_{get_utc_hour_str}.pdf',
                "name":"FXFE5782.svg",
                "title":"極東850hPa気温・風、700hPa上昇流／700hPa湿数、500hPa気温予想図 12・24時間"
            },
            {
                "url":f'https://www.jma.go.jp/bosai/numericmap/data/nwpmap/fxfe5784_{get_utc_hour_str}.pdf',
                "name":"FXFE5784.svg",
                "title":"極東850hPa気温・風、700hPa上昇流／700hPa湿数、500hPa気温予想図 36・48時間"
            },
            {
                "url":f'https://www.jma.go.jp/bosai/numericmap/data/nwpmap/fxjp854_{get_utc_hour_str}.pdf',
                "name":"FXJP854.svg",
                "title":"日本850hPa相当温位・風予想図 12・24・36・48時間"
            },
        ]
        for url_file_obj in genkyo_objs:
            print(f'  Getting {url_file_obj["name"].replace(".svg","").replace(".png","")} {url_file_obj["title"]}...')
            obj = get_svg_from_pdf_url(url_file_obj["url"])
            if obj["result"] and 0 < len(obj["pages"]) and "svg" in obj["pages"][0]:
                file_name = url_file_obj["name"]
                svg_path_name = os.path.join(output_base_dir, file_name)
                with open(svg_path_name, "w", encoding="utf-8") as f:
                    f.write(obj["pages"][0]["svg"])
                file_infos.append({
                    "id":file_name.replace(".svg","").replace(".png",""),
                    "name":file_name,
                    "title":url_file_obj["title"]
                })

        for url_file_obj in yoho_objs:
            print(f'  Getting {url_file_obj["name"].replace(".svg","").replace(".png","")} {url_file_obj["title"]}...')
            obj = get_svg_from_pdf_url(url_file_obj["url"])
            if obj["result"] and 0 < len(obj["pages"]) and "svg" in obj["pages"][0]:
                file_name = url_file_obj["name"]
                svg_path_name = os.path.join(output_base_dir, file_name)
                with open(svg_path_name, "w", encoding="utf-8") as f:
                    f.write(obj["pages"][0]["svg"])
                file_infos.append({
                    "id":file_name.replace(".svg","").replace(".png",""),
                    "name":file_name,
                    "title":url_file_obj["title"]
                })
       
        md_text += '## ページ内画像リンク\n'
        for file_info in file_infos:
            md_text += f'- [{file_info["title"]}](#{file_info["id"]})\n'
        md_text += '\n\n'

        md_text += '## 画像\n'
        md_text += f'[ページトップ](#top)\n\n'
        for file_info in file_infos:
            md_text += f'<a href="{file_info["name"]}" target="_blank" id="{file_info["id"]}">{file_info["title"]}</a>\n'
            md_text += f'<img width="100%" height="auto" style="border: 2px solid black;" src="{file_info["name"]}"></img>\n'
            md_text += f'[ページトップ](#top)\n\n'

        md_path_name = os.path.join(output_base_dir, "index.md")
        with open(md_path_name, "w", encoding="utf-8") as f:
            f.write(md_text)

        html_text = """
<!doctype html>
<html lang="ja">

<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width" />
    <title>短期予報解説資料</title>
</head>

<body>
"""    
        html_text += markdown.markdown(md_text)
        html_text += """
</body>
</html>
"""

        html_path_name = os.path.join(output_base_dir, "index.html")
        with open(html_path_name, "w", encoding="utf-8") as f:
            f.write(html_text)

        print(f'Output saved to {output_base_dir}')

        # 短期予報解説資料のテキストを抽出
        tanki_yoho_text_path_name = os.path.join(output_base_dir, "kaisetsu_tanki.json")
        text_objs = parse_tanki_yoho_kaisetsu(tanki_yoho_svg_path_name)
        with open(tanki_yoho_text_path_name, "w", encoding="utf-8") as f:
            json.dump(text_objs, f, indent=2, ensure_ascii=False)
#        file_infos.append({
#            "id":"tanki_yoho_text",
#            "name":os.path.basename(tanki_yoho_text_path_name),
#            "title":'短期予報解説資料テキスト'
#        })

        # メタデータ生成
        meta_obj = {
            "title": text_objs[0]["name"],
            "released_at_j":text_objs[0]["sentences"][0],
            "released_at": released_datetime.strftime('%Y-%m-%d %H:%M:%S'),
            "based_on_utc": utc_snapshot_datetime.strftime('%Y-%m-%d %H:%M:%S'),
            "files": file_infos
        }
        metadata_path_name = os.path.join(output_base_dir, "metadata.json")
        with open(metadata_path_name, "w", encoding="utf-8") as f:
            json.dump(meta_obj, f, indent=2, ensure_ascii=False)

        print(f'Finished at {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        exit(0)
    else:
        print("Failed to get 短期予報解説資料 or no text found.")
        exit(1)
