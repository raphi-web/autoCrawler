pyinstaller -w -F --add-data "templates:templates" --add-data "static:static" --collect-all geopandas --onefile autoCrawler.py
cp geckodriver dist/geckodriver