import io
import requests
from PIL import Image

def merge_images(base_url:str, utc_str:str, z:int, a_values:list, b_values:list):
    # **各タイル画像をダウンロード**
    urls = []
    tiles = []
    tile_width, tile_height = None, None

    for b in b_values:  # 縦方向（行）を先に処理
        row_images = []
        for a in a_values:  # 横方向（列）を内側で処理
            url = base_url.format(z=z, a=a, b=b, utc_str=utc_str)
            urls.append(url)
            response = requests.get(url)
            image = Image.open(io.BytesIO(response.content))

            if tile_width is None or tile_height is None:
                tile_width, tile_height = image.size  # 最初の画像からタイルサイズ取得

            row_images.append(image)
        tiles.append(row_images)

    # **統合画像のサイズを計算**
    merged_width = len(a_values) * tile_width  # 横の合計サイズ
    merged_height = len(b_values) * tile_height  # 縦の合計サイズ

    # **統合画像を作成**
    merged_image = Image.new("RGBA", (merged_width, merged_height),(0, 0, 0, 0))

    # **タイルを統合**
    for row_index, row_images in enumerate(tiles):
        for col_index, img in enumerate(row_images):
            x_offset = col_index * tile_width  # a_values に対応
            y_offset = row_index * tile_height  # b_values に対応
            merged_image.paste(img, (x_offset, y_offset))
    return merged_image, urls
