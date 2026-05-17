.PHONY: build build-macos build-windows check

APP_NAME := OrdersParserByDK

build: build-macos

build-macos:
	pyinstaller --onefile --windowed \
	--add-data="config/token.json:config" \
	--add-data="config/.env:config" \
	--add-data="google_api:google_api" \
	--add-data="marketplaces:marketplaces" \
	--icon=assets/icon.png \
	--hidden-import="pydantic_settings" \
	--hidden-import="pydantic" \
	--name=OrdersParserByDK \
	main.py

build-windows:
	pyinstaller --onefile --add-data "config/token.json;config" --add-data "config/.env;config" --add-data "google_api;google_api" --add-data "marketplaces;marketplaces" --icon=assets/icon.png --hidden-import "pydantic_settings" --hidden-import "pydantic" --name $(APP_NAME) main.py

check:
	python -m py_compile \
		main.py \
		config/settings.py \
		google_api/gdrive_finder.py \
		google_api/gsheet_writer.py \
		marketplaces/amazon_parser.py \
		marketplaces/ebay_parser.py \
		marketplaces/etsy_parser.py \
		marketplaces/overstock_parser.py \
		marketplaces/wayfair_parser.py
