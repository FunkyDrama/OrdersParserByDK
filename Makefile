.PHONY: build build-macos build-windows check test

APP_NAME := OrdersParserByDK
PYTHON := uv run python
PYINSTALLER := uv run pyinstaller

build: build-macos

build-macos:
	$(PYINSTALLER) --windowed \
	--add-data="config/token.json:config" \
	--add-data="config/.env:config" \
	--add-data="google_api:google_api" \
	--add-data="marketplaces:marketplaces" \
	--add-data="core:core" \
	--add-data="ui:ui" \
	--add-data="assets:assets" \
	--osx-bundle-identifier=dev.danielkravchenko.ordersparser \
	--icon=assets/icon.png \
	--hidden-import="pydantic_settings" \
	--hidden-import="pydantic" \
	--name=OrdersParserByDK \
	main.py

build-windows:
	$(PYINSTALLER) --onefile --windowed --add-data "config/token.json;config" --add-data "config/.env;config" --add-data "google_api;google_api" --add-data "marketplaces;marketplaces" --add-data "core;core" --add-data "ui;ui" --add-data "assets;assets" --icon=assets/icon.ico --hidden-import "pydantic_settings" --hidden-import "pydantic" --name $(APP_NAME) main.py

check:
	$(PYTHON) -m py_compile \
		main.py \
		config/settings.py \
		core/console.py \
		core/constants.py \
		core/dispatcher.py \
		core/paths.py \
		core/processor.py \
		google_api/auth.py \
		google_api/gdrive_finder.py \
		google_api/gsheet_writer.py \
		marketplaces/base_parser.py \
		marketplaces/amazon_parser.py \
		marketplaces/ebay_parser.py \
		marketplaces/etsy_parser.py \
		marketplaces/overstock_parser.py \
		marketplaces/wayfair_parser.py \
		ui/app.py \
		ui/backend.py \
		ui/log_format.py
	uv run ruff format
	uv run ruff check --fix
	uv run mypy --check-untyped-defs .

test:
	uv run pytest tests -q

i18n:
	uv run pyside6-lupdate ui/qml/Main.qml ui/qml/components/*.qml \
		-ts ui/i18n/app_ru.ts -ts ui/i18n/app_uk.ts
	uv run pyside6-lrelease ui/i18n/app_ru.ts ui/i18n/app_uk.ts
