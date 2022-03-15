rmdir /s dist 
rmdir /s build
pyinstaller -w -F --add-data "templates;templates" --add-data "static;static" --collect-all seleniumwire --onefile autoCrawler.py
COPY geckodriver dist/geckodriver
pause