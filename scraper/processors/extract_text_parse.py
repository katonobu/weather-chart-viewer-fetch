import re
import html
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo

def extract_date(released_at_str:str):
    normalized_str = unicodedata.normalize("NFKC", released_at_str)
    if re.match(r"^\d{4}年\d{1,2}月\d{1,2}日\d{1,2}時\d{2}分発表.*$", normalized_str):
        dt = datetime.strptime(normalized_str, "%Y年%m月%d日%H時%M分発表")
        released_at = dt.replace(tzinfo=ZoneInfo("Asia/Tokyo"))
        return released_at
    return None

def extract_text_from_svg(svg_text:str):
    # SVGファイルを読み込み
    root = ET.fromstring(svg_text)

    # SVGの名前空間を定義
    namespace = {'svg': 'http://www.w3.org/2000/svg'}

    extracted_texts = ""
    # use要素を検索し、data-text属性を抽出
    for use in root.findall('.//svg:use', namespace):
        data_text = use.get('data-text')
        if data_text:
            # HTMLエスケープされた文字列をデコード
            extracted_texts += html.unescape(data_text)
    return extracted_texts

section_separetors = [
    "短期予報解説資料1",
    "１．実況上の着目点",
    "２．主要じょう乱の予想根拠と防災事項を含む解説上の留意点",
    "３．数値予報資料解釈上の留意点",
    "４．防災関連事項 [量的予報等] ",
    "５．全般気象情報発表の有無"
]
subsectoin_separetors = [
    "① ",
    "② ",
    "③ ",
    "④ ",
    "⑤ ",
    "⑥ ",
    "⑦ ",
    "⑧ ",
    "⑨ ",
    "⑩ ",
    "⑪ ",
    "⑫ ",
]

def parse_tanki_yoho_kaisetsu_from_svg(svg_text:str):
    text = extract_text_from_svg(svg_text)
    # section_separetorsの各要素の直後に改行を付ける
    for sep in section_separetors:
        # なぜか、sectionタイトルが2回出てくる。(ずらして2回出して太字にしてる?)
        text = text.replace(f'{sep}{sep}', f"\n{sep}")
        text = text.replace(f'{sep} {sep}', f"\n{sep}")
        text = text.replace(f'{sep}  {sep}', f"\n{sep}")
        # 2回出てきていないsectionタイトルもあるので、改行を付与
        text = text.replace(sep, f"{sep}\n")

    sections = []
    section_obj = {"name":"","sentences":[],"subsections":[]}
    idx = 0
    # 改行コードで分割された各文字列に対して。
    for line in text.split("\n"):
        stripped = line.strip()
        # section_separetorsの要素と一致する場合
        if stripped in section_separetors:
            idx += 1
            section_name = stripped.split("．")[-1].replace("1","")
            if 0 < len(section_obj["name"]):
                sections.append(section_obj)
            section_obj = {"name":section_name,"sentences":[],"subsections":[]}
        else:
            sentences = [sentence.strip() for sentence in line.strip().split("。") if 0 < len(sentence.strip())]

            sub_idx = 0
            subsection_name = None
            subsection_obj = {"name":"","sentences":[]}
            for ele in sentences:
                sentence = ele.strip()+"。"
                # 〇数字で始まるもの。
                if sentence.strip().startswith(subsectoin_separetors[sub_idx]):
                    subsection_name = subsectoin_separetors[sub_idx].strip()
                    if 0 < sub_idx:
                        section_obj["subsections"].append(subsection_obj)
                    subsection_obj = {"name":subsection_name,"sentences":[]}
                    subsection_obj["sentences"].append(sentence.replace(subsectoin_separetors[sub_idx], ""))
                    sub_idx += 1
                elif sub_idx == 0:
                    if sentence.startswith("1量的な予報については"):
                        sentence = sentence.replace("1量的な予報については", "量的な予報については")
                    section_obj["sentences"].append(sentence)
                else:
                    subsection_obj["sentences"].append(sentence)
            if 0 < len(subsection_obj["sentences"]):
                section_obj["subsections"].append(subsection_obj)
    sections.append(section_obj)
    return sections

def parse_syukan_yoho_kaisetsu(text:str):
    results = []
    lines = text.split("\n")
    sentences = []

    stt = "idle"
    for line in lines:
        if stt == "idle":
            if line == "週間天気予報解説資料":
                stt = "header"
                name = line.strip()
            elif line.endswith("利⽤ください。)"):
                stt = "forecast"
                name = line.split("(")[0].replace("◆","").strip()
            elif line.startswith("＜主要じょう乱の概要"):
                stt = "disturbance"
                name = line.strip()
        elif stt == "header":
            if line.endswith("発表"):
                sentences.append(line.strip())
            elif line == "気象庁":
                sentences.append(line.strip())
            elif line.startswith("予報期間") and line.endswith("まで") and stt == "header":
                stt = "idle"
                sentences.append(line.strip())
                results.append({
                    "name":name,
                    "sentences":sentences
                })
                sentences = []
        elif stt == "forecast":
            if line.startswith("天気") or line.startswith("晴") or line.startswith("曇り") or line.startswith("⾬") or line.startswith("雪"):
                pass
            elif line.endswith("今期間のポイント"):
                stt = "idle"
                results.append({
                    "name":name,
                    "sentences":sentences
                })
                sentences = []
            else:
                sentences.append(line.strip())
        elif stt == "disturbance":
            if line.startswith("＜防災事項"):
                stt = "disaster"
                results.append({
                    "name":name,
                    "sentences":sentences
                })
                name = "＜防災事項＞"
                sentences = []
            else:
                sentences.append(line.strip())
        elif stt == "disaster":
            if line.startswith("※最新の"):
                stt = "idle"
                results.append({
                    "name":name,
                    "sentences":sentences
                })
                name = ""
                sentences = []
            else:
                sentences.append(line.strip())
    return results

