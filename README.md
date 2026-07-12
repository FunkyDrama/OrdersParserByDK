# OrdersParserByDK

A desktop tool that turns marketplace orders (**Etsy, Amazon, eBay,
Wayfair, Overstock**) into rows of a Google Sheets production table, finds the
matching design files on Google Drive and uploads shipping labels — so an
operator processes a batch of orders in seconds instead of copy-pasting them
by hand.

Built with **Python 3.12, PySide6 + QML (Material Dark), BeautifulSoup (lxml),
gspread and the Google Drive API**. Ships as a single PyInstaller binary for
macOS and Windows via GitHub Actions.

## Features

- **Five marketplaces, one pipeline.** Each parser only extracts fields; the
  shared `BaseParser` handles Drive lookups, shipping labels, tracking links
  and row building. Marketplace detection is order-sensitive and preserved
  1:1 from the battle-tested legacy version.
- **Parallel parsing, sequential writing.** Orders are parsed by a 4-thread
  pool (the work is mostly waiting on Google Drive), while spreadsheet writes
  stay strictly sequential and in the original order. The journal never
  interleaves: each order's output is buffered per thread and replayed in
  order.
- **Frugal with the Google API.** Writing an order costs 2–3 requests instead
  of the legacy 5 + 5·N: one `batch_update` (row insertion at the exact
  position + formatting), one `values_update`, and one merge request for
  multi-item orders only. Drive search results are cached per query; the
  first free row of every sheet is fetched once per run and tracked locally.
- **Graceful degradation.** A field that fails to parse becomes `!ERROR!` in
  its cell; a missing Drive file becomes `File Not Found` and routes the
  order to the ERROR sheet; an uncomputable total becomes `!ERROR!` in the
  Total cell — the order is still written. Only an unexpected exception skips
  an order, and the UI offers a one-click retry for exactly those.
- **Desktop UI (PySide6 + QML).** Dark Material theme, drag & drop of the
  orders file, a structured journal (per-order banners, key/value rows,
  error cards, clickable tracking/file links), an Orders tab with per-order
  cards, a Paste-HTML tab to process orders without a file, live progress
  and summary, and popups for important events (dismissed by a click
  anywhere).
- **Three languages end to end.** English (default), Russian and Ukrainian.
  The UI uses Qt Linguist (`.ts`/`.qm`) with live switching; runtime log
  messages follow the same language through a gettext-style catalog
  (`core/i18n.py`) — only hardcoded texts are translated, data values
  (SKUs, sheet names, addresses) pass through untouched. The choice is
  persisted in `QSettings`; the CLI takes a `--lang ru|uk` flag.
- **File logs with auto-cleanup.** Every message is mirrored to
  `logs/parser_YYYY-MM-DD.log`; files older than `LOG_RETENTION_DAYS`
  (7 by default) are removed at startup.
- **Tested.** 61 unit tests cover marketplace detection, sheet routing,
  positional insertion and batch formatting, the parallel pipeline's
  ordering guarantees, log parsing and log cleanup — all without touching
  the network.

## Architecture

```
main.py                  entry point: UI by default, --cli for console mode
├── core/
│   ├── dispatcher.py    marketplace detection (order-sensitive, 1:1 legacy)
│   ├── processor.py     pipeline: parallel parse → ordered sequential write
│   ├── console.py       cprint: console + file log + UI subscribers,
│   │                    per-thread capture/replay, log auto-cleanup
│   ├── constants.py     columns, sheets, palette, tracking templates
│   └── paths.py         script vs PyInstaller-frozen path handling
├── marketplaces/
│   ├── base_parser.py   shared parser infrastructure (ABC)
│   └── *_parser.py      Etsy / Amazon / eBay / Wayfair / Overstock
├── google_api/
│   ├── auth.py          one gspread client per app, one Drive service
│   │                    per thread (httplib2 is not thread-safe)
│   ├── gdrive_finder.py thread-safe file search with a shared query cache
│   └── gsheet_writer.py 2–3 requests per order, exact-position insertion
├── ui/
│   ├── app.py           QGuiApplication, translators, engine lifecycle
│   ├── backend.py       QObject bridge: Properties / Signals / Slots,
│   │                    QAbstractListModel ×2, QSortFilterProxyModel,
│   │                    QThread worker
│   ├── log_format.py    console lines → typed journal entries (pure, tested)
│   ├── i18n/            app_ru.ts / app_uk.ts sources + compiled .qm
│   └── qml/
│       ├── Main.qml     window, tabs, popup wiring
│       └── components/  Theme singleton + 14 small components
└── tests/               61 unit tests, network-free
```

Design decisions worth calling out:

- **Python ↔ QML.** The backend is exposed as the `App` context property.
  UI state is structured (`statusKind` + `statusArgs`, `notify(kind, args)`
  signal) and all user-visible texts are composed in QML with `qsTr()` — so
  every message follows the selected language, including live retranslation
  via `QQmlEngine::retranslate()`.
- **Why not `values.append`.** Sheets' append locates the "end of the table"
  heuristically and misbehaves with frozen headers and grouped rows;
  `insertDimension` inserts at the exact row, matching the legacy
  `insert_row` semantics that operators rely on.
- **Structured, stable log format.** Console messages use `|||…|||` /
  `---…---` / `- Key: value` markers in every language, so the UI's
  `log_format.py` parses them into typed journal entries (banners,
  key/value rows, error cards) regardless of the selected language — the
  banner pattern is built from the catalog itself.

## Running from source

Requires Python 3.12+.

```bash
git clone https://github.com/FunkyDrama/OrdersParserByDK.git
cd OrdersParserByDK
python -m venv .venv && source .venv/bin/activate   # .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Configuration — `config/.env`:

```ini
TABLE_ID=<Google Sheets spreadsheet id>
SHIPPING_LABEL_FOLDER=<Google Drive folder id for shipping labels>
```

plus a Google **service account** JSON at `config/credentials.json` with the
Sheets and Drive scopes (share the spreadsheet and the folders with the
service-account email).

```bash
python main.py          # desktop UI
python main.py --cli    # legacy console mode
```

## Tests

```bash
pip install pytest
python -m pytest tests -q
```

## Building a binary

```bash
make build        # PyInstaller one-file build for the current OS
```

GitHub Actions builds macOS and Windows binaries on every tag; secrets
provide `config/.env` and `credentials.json` at build time.

## Updating translations

```bash
pyside6-lupdate ui/qml/Main.qml ui/qml/components/*.qml \
    -ts ui/i18n/app_ru.ts -ts ui/i18n/app_uk.ts   # extract qsTr() strings
# edit the .ts files (Qt Linguist or any editor)
pyside6-lrelease ui/i18n/app_ru.ts ui/i18n/app_uk.ts   # compile .qm
```

The compiled `.qm` files are bundled into the binary together with the `ui/`
directory.

## Version history

- **7.2.3** — the language selector stays in sync when the language is
  changed programmatically.
- **7.2.2** — runtime log messages follow the application language
  (EN/RU/UK) via a gettext-style catalog with an AST-based coverage test;
  CLI gets a `--lang` flag.
- **7.2.1** — all console/log messages translated to English; the
  structural markers and the journal parser are unchanged.
- **7.2.0** — UI internationalization (EN/RU/UK) with live switching; QML
  decomposed into components with a `Theme` singleton; important events as
  click-anywhere-to-dismiss popups; auto-switch to the Journal tab when
  processing starts; all docstrings, comments and this README in English.
- **7.1.2** — file logs with automatic cleanup (older than 7 days).
- **7.1.1** — an uncomputable Total writes `!ERROR!` into the cell instead of
  skipping the order.
- **7.1.0** — parallel parsing (4 threads) with ordered writes and a
  non-interleaving journal; the PySide6 + QML interface (structured journal,
  Orders tab, Paste HTML, retry-failed).
- **7.0.x** — the big refactor: `BaseParser` (−85% duplicated code),
  dispatcher/processor split, 2–3 Sheets requests per order instead of
  5 + 5·N, Drive query cache, unit-test suite; several legacy crashes fixed
  (Wayfair unknown-carrier `TypeError`, silent `None` totals).
- **6.x** — the legacy single-file version this project was refactored from.
