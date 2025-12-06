import fitz  # PyMuPDF
import requests

def get_svg_from_url(svg_url:str):
    result_obj = {
         "result":False,
         "url":svg_url,
         "response_ok":False,
    }

    response = requests.get(svg_url)
    result_obj.update({"response_ok":response.ok})
    response.raise_for_status()  # HTTPエラーがあれば例外を発生させる

    if response.ok:
        result_obj.update({"svg":response.content})
        result_obj.update({"result":True})
    return result_obj

def get_svg_from_pdf_url(pdf_url:str):
    result_obj = {
         "result":False,
         "url":pdf_url,
         "response_ok":False,
         "page_count":0,
         "pages":[]
    }

    # PDFをダウンロード（バイナリデータ取得）
    response = requests.get(pdf_url)
    result_obj.update({"response_ok":response.ok})
    response.raise_for_status()  # HTTPエラーがあれば例外を発生させる

    # メモリ上のバイナリデータからPDFを開く
    doc = fitz.open(stream=response.content, filetype="pdf")

    result_obj["page_count"] = doc.page_count
    # 各ページをSVG（ベクタ）としてエクスポート
    for page_index in range(doc.page_count):
        page = doc[page_index]
        page_obj = {
             "svg":page.get_svg_image(),
             "texts":page.get_text("text")
        }
        result_obj["pages"].append(page_obj)
    doc.close()
    result_obj.update({"result":True})
    return result_obj

