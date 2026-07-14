# Python と pip があるか確認
echo "--- checking python/ update pip ---"
python3 --version
pip install --upgrade pip
pip --version

echo "--- 必要なライブラリ群をinstall ---"
sudo apt update
sudo apt install libjpeg-dev zlib1g-dev libpng-dev

# Pythonモジュールインストール
echo "--- install Python modules by requirements.txt ---"
cat requirements.txt
pip install -r requirements.txt
pip list

echo ""
echo "--- post create finished ---"
