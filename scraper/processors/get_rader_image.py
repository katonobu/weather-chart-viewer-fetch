import os
import re
import requests
import tempfile
from PIL import Image

def get_png_from_url(url:str):
    result_obj = {
         "result":False,
         "url":url,
         "response_ok":False,
    }

    response = requests.get(url)
    result_obj.update({"response_ok":response.ok})
    response.raise_for_status()  # HTTPエラーがあれば例外を発生させる

    if response.ok:
        result_obj.update({"content":response.content})
        result_obj.update({"result":True})
    return result_obj


def get_border_png():
    url = "https://www.jma.go.jp/bosai/rain/const/map/border_a00.png"
    return get_png_from_url(url)

def get_rain_png(time_str:str):
    if re.match(r'^\d{10}0000$', time_str) is None:
        raise ValueError("Invalid time_str format. Expected format: YYYYMMDDHH0000")
    url = f"https://www.jma.go.jp/bosai/rain/data/rain/{time_str}/rain_{time_str}_f00_a00.png"
    return get_png_from_url(url)

def combie_border_rain_image(border_path:str, rain_path:str):
    # 得られた2つのpngを重ね合わせたファイルを生成する
    frame = Image.open(border_path).convert("RGBA")  # 枠線画像
    data = Image.open(rain_path).convert("RGBA")  # 時間変化する値
    white_background = Image.new("RGBA", frame.size, (255, 255, 255, 255))  # 白 (R=255, G=255, B=255, Alpha=255)

    white_background.paste(data, (0, 0), data)  # まずデータ画像を重ねる
    white_background.paste(frame, (0, 0), frame)  # 次に枠線画像を重ねる
    return white_background

def get_rader_png(yyyymmddhh_utc_str:str):
    ret_obj = {
        "urls":[],
        "image":None,
        "name":""
    }
    if re.match(r'^\d{10}$', yyyymmddhh_utc_str) is not None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = get_border_png()
            if result["result"]:
                ret_obj["urls"].append(result["url"])
                border_path = os.path.join(temp_dir, "border_a00.png")
                with open(border_path, "wb") as f:
                    f.write(result["content"])
                time_str = f"{yyyymmddhh_utc_str}0000"
                try:
                    result = get_rain_png(time_str)
                    if result["result"]:
                        ret_obj["urls"].append(result["url"])
                        target_path = os.path.join(temp_dir, f"rain_{time_str}_f00_a00.png")
                        with open(target_path, "wb") as f:
                            f.write(result["content"])
                        ret_obj["image"] = combie_border_rain_image(border_path, target_path)
                        ret_obj["name"] = f"rain_{time_str}_f00_a00_combined.png"

                    else:
                        print(f"Failed to retrieve image for {time_str}: {result['url']}")
                except ValueError as e:
                    print(f"Error for {time_str}: {e}")
            else:
                print("Failed to retrieve border image:", result["url"])
    else:
        print(f"Invalid date format: {yyyymmddhh_utc_str}. Expected format: YYYYMMDDHH")

    return ret_obj

if __name__ == "__main__":
    pass