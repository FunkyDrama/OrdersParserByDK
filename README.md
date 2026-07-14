# OrdersParserByDK

Production-focused desktop automation for marketplace order operations.

OrdersParserByDK turns raw marketplace order HTML from Etsy, Amazon, eBay,
Wayfair and Overstock into correctly routed Google Sheets rows, finds matching
production files in Google Drive, uploads shipping labels, and leaves a
structured processing journal for operators to review.

The project started as a large single-file internal script and was rebuilt into
a tested desktop application with a reusable parsing pipeline, a PySide6/QML UI,
parallel order processing, and release builds for macOS, Windows and Windows
Server.

## What It Solves

Marketplace order processing is repetitive, error-prone and full of small
format differences:

- each marketplace exposes order IDs, totals, shipping data and customizations
  differently;
- production routing depends on SKU, file type and product size;
- Google Sheets writes must preserve exact row order and formatting;
- Drive searches and label uploads need to be fast but rate-limit friendly;
- operators need a clear journal when an order partially fails.

This application automates that workflow end to end while keeping failures
visible and recoverable.

## Highlights

- **Five marketplaces, one pipeline.** Marketplace-specific parsers extract raw
  fields; shared infrastructure handles Drive lookup, sheet routing, shipping
  labels, tracking links and row construction.
- **Parallel parsing with ordered writes.** Orders are parsed in a worker pool,
  while Google Sheets writes remain sequential and deterministic. The UI journal
  never interleaves messages from different orders.
- **Efficient Google API usage.** Each order is written with a small batch of
  requests instead of repeated row-by-row calls. Drive searches are cached per
  run.
- **Graceful degradation.** Missing or malformed fields become explicit
  `!ERROR!` values, missing Drive files route to the ERROR sheet, and only truly
  unexpected exceptions skip an order.
- **Operator-friendly desktop UI.** PySide6 + QML interface with drag and drop,
  live progress, structured logs, retry for failed orders, order summaries,
  paste-from-HTML mode and live language switching.
- **Server-compatible build.** A separate Windows Server artifact runs the same
  processing core without importing the Qt UI stack.
- **Internationalization.** Runtime logs and QML UI support English, Russian and
  Ukrainian.
- **Tested without network access.** Unit tests cover parser behavior, routing,
  sheet row construction, log parsing, i18n coverage and cleanup logic.

## Tech Stack

- Python 3.12
- PySide6 + QML / Qt Quick Controls
- BeautifulSoup + lxml
- Google Sheets API, Google Drive API, gspread
- Pydantic settings
- PyInstaller release builds
- pytest, ruff, mypy

## Architecture

```text
main.py                  GUI entry point; --cli keeps source CLI access
main_cli.py              Windows Server entry point without UI imports
core/
  cli.py                 shared CLI runner
  dispatcher.py          marketplace detection
  processor.py           parallel parse -> ordered sequential write
  console.py             console/file log bridge and UI subscribers
  paths.py               source vs PyInstaller path handling
  constants.py           columns, sheets, palette and tracking templates
marketplaces/
  base_parser.py         shared parser infrastructure
  amazon_parser.py
  ebay_parser.py
  etsy_parser.py
  overstock_parser.py
  wayfair_parser.py
google_api/
  auth.py                service-account auth and per-thread Drive services
  gdrive_finder.py       Drive lookup, upload and cache logic
  gsheet_writer.py       exact-position row insertion and formatting
ui/
  app.py                 QGuiApplication and QML engine setup
  backend.py             QObject bridge, models, worker thread
  log_format.py          console text -> typed journal entries
  qml/                   QML application and components
tests/                   network-free unit tests
```

## Design Choices

**Exact Google Sheets insertion.** The app does not use `values.append`, because
append heuristics are unreliable with frozen headers and grouped rows. Instead,
it inserts rows at the exact target position and applies formatting in a batch.

**Buffered per-order logs.** Each worker captures its own parser output and the
processor replays logs in original order. Operators see a coherent journal even
when parsing is parallel.

**Runtime marker format.** Parser logs use stable markers such as `|||...|||`,
`---...---` and `- Key: value`. The QML journal parses those markers into
banners, field rows, warnings and success messages in every supported language.

**Server build without Qt.** Windows Server 2016 is unreliable with modern Qt.
The server artifact uses `main_cli.py`, so PyInstaller does not need to import
or bundle the desktop UI stack.

## Running From Source

Requires Python 3.12.

```bash
git clone https://github.com/FunkyDrama/OrdersParserByDK.git
cd OrdersParserByDK
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install uv
uv sync --dev
```

Create `config/.env`:

```ini
TABLE_ID=<google-sheets-spreadsheet-id>
SHIPPING_LABEL_FOLDER=<google-drive-folder-id>
```

Add a Google service-account JSON at:

```text
config/token.json
```

The service account needs Sheets and Drive access, and the spreadsheet/folders
must be shared with the service-account email.

Run the app:

```bash
uv run python main.py
```

Run the source CLI:

```bash
uv run python main.py --cli
uv run python main.py --cli --lang ru
```

Run the server entry point locally:

```bash
uv run python main_cli.py
```

## Builds

GitHub Actions builds release artifacts on tag pushes and manual dispatch.

| Artifact | Entry point | UI stack | Target |
| --- | --- | --- | --- |
| `OrdersParserByDK.exe` | `main.py` | PySide6/QML | Windows desktop |
| `OrdersParserByDK.app` | `main.py` | PySide6/QML | macOS desktop |
| `OrdersParserByDKServer.exe` | `main_cli.py` | none | Windows Server |

Local build targets:

```bash
make build-macos
make build-windows
make build-windows-server
```

The Windows Server build intentionally uses `--windowed`, matching the legacy
operator flow. It processes `orders.txt` next to the executable, keeps the
process open until Enter is pressed, and writes file logs to the platform log
directory.

## Tests And Quality

```bash
uv run pytest tests -q
uv run ruff check .
uv run mypy --check-untyped-defs .
```

The test suite is network-free: Google API behavior is exercised through the
row builders, routing logic and pure processing components rather than live
services.

## Internationalization

QML strings are managed with Qt Linguist:

```bash
pyside6-lupdate ui/qml/Main.qml ui/qml/components/*.qml \
    -ts ui/i18n/app_ru.ts -ts ui/i18n/app_uk.ts
pyside6-lrelease ui/i18n/app_ru.ts ui/i18n/app_uk.ts
```

Runtime parser messages use `core/i18n.py`; tests verify that every literal
`tr()` key used in source code has Russian and Ukrainian translations.

## Release Notes

- **7.2.x** - UI language sync, runtime i18n, Windows icon/resource fixes and
  Windows Server build support.
- **7.1.x** - PySide6/QML desktop UI, parallel parsing, ordered writes,
  structured journal and log cleanup.
- **7.0.x** - major parser refactor: shared `BaseParser`, dispatcher/processor
  split, fewer Google API calls, Drive query cache and network-free tests.
- **6.x** - original single-file legacy script.
