"""Python backend of the desktop UI (PySide6 + QML)."""

import os
from dataclasses import dataclass
from datetime import datetime

from PySide6.QtCore import (
    Property,
    QSettings,
    QAbstractListModel,
    QModelIndex,
    QObject,
    QSortFilterProxyModel,
    Qt,
    QThread,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QDesktopServices

from core import console
from core import i18n as core_i18n
from core.i18n import tr
from core.constants import APP_VERSION
from core.paths import get_executable_dir, get_orders_file_path
from core.processor import OrderResult, process_order_list, split_orders
from ui.log_format import parse_entry


@dataclass
class _LogEntry:
    text: str
    level: str
    time: str
    kind: str
    marketplace: str
    key: str
    value: str
    message: str


class LogModel(QAbstractListModel):
    """All journal entries of the current run (structured)."""

    TextRole = Qt.ItemDataRole.UserRole + 1
    LevelRole = Qt.ItemDataRole.UserRole + 2
    TimeRole = Qt.ItemDataRole.UserRole + 3
    KindRole = Qt.ItemDataRole.UserRole + 4
    MarketplaceRole = Qt.ItemDataRole.UserRole + 5
    KeyRole = Qt.ItemDataRole.UserRole + 6
    ValueRole = Qt.ItemDataRole.UserRole + 7
    MessageRole = Qt.ItemDataRole.UserRole + 8

    _ROLES = {
        TextRole: b"text",
        LevelRole: b"level",
        TimeRole: b"time",
        KindRole: b"kind",
        MarketplaceRole: b"marketplace",
        KeyRole: b"key",
        ValueRole: b"value",
        MessageRole: b"message",
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._entries: list[_LogEntry] = []

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._entries)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self._entries):
            return None
        entry = self._entries[index.row()]
        return {
            Qt.ItemDataRole.DisplayRole: entry.text,
            self.TextRole: entry.text,
            self.LevelRole: entry.level,
            self.TimeRole: entry.time,
            self.KindRole: entry.kind,
            self.MarketplaceRole: entry.marketplace,
            self.KeyRole: entry.key,
            self.ValueRole: entry.value,
            self.MessageRole: entry.message,
        }.get(role)

    def roleNames(self):  # noqa: N802
        return dict(self._ROLES)

    def append(self, text: str, level: str) -> None:
        parsed = parse_entry(text)
        position = len(self._entries)
        self.beginInsertRows(QModelIndex(), position, position)
        self._entries.append(
            _LogEntry(
                text=text,
                level=level,
                time=datetime.now().strftime("%H:%M:%S"),
                kind=parsed["kind"],
                marketplace=parsed["marketplace"],
                key=parsed["key"],
                value=parsed["value"],
                message=parsed["message"],
            )
        )
        self.endInsertRows()

    def clear(self) -> None:
        self.beginResetModel()
        self._entries.clear()
        self.endResetModel()

    def plain_text(self) -> str:
        return "\n".join(entry.text for entry in self._entries)


class LogFilterModel(QSortFilterProxyModel):
    """Journal filters: "problems only" and substring search."""

    filtersChanged = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._errors_only = False
        self._search = ""

    def _get_errors_only(self) -> bool:
        return self._errors_only

    def _set_errors_only(self, value: bool) -> None:
        if self._errors_only != value:
            self._errors_only = value
            self.invalidateRowsFilter()
            self.filtersChanged.emit()

    errorsOnly = Property(
        bool, _get_errors_only, _set_errors_only, notify=filtersChanged
    )

    def _get_search(self) -> str:
        return self._search

    def _set_search(self, value: str) -> None:
        if self._search != value:
            self._search = value
            self.invalidateRowsFilter()
            self.filtersChanged.emit()

    search = Property(str, _get_search, _set_search, notify=filtersChanged)

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:  # noqa: N802
        index = self.sourceModel().index(source_row, 0, source_parent)
        if self._errors_only:
            level = self.sourceModel().data(index, LogModel.LevelRole)
            if level not in ("error", "warning"):
                return False
        if self._search:
            text = self.sourceModel().data(index, LogModel.TextRole) or ""
            if self._search.lower() not in text.lower():
                return False
        return True


class OrdersModel(QAbstractListModel):
    """Processed orders: the summary list behind the Orders tab."""

    NumberRole = Qt.ItemDataRole.UserRole + 1
    MarketplaceRole = Qt.ItemDataRole.UserRole + 2
    OrderIdRole = Qt.ItemDataRole.UserRole + 3
    SheetRole = Qt.ItemDataRole.UserRole + 4
    ItemsRole = Qt.ItemDataRole.UserRole + 5
    OkRole = Qt.ItemDataRole.UserRole + 6
    ErrorRole = Qt.ItemDataRole.UserRole + 7

    _ROLES = {
        NumberRole: b"number",
        MarketplaceRole: b"marketplace",
        OrderIdRole: b"orderId",
        SheetRole: b"sheet",
        ItemsRole: b"items",
        OkRole: b"ok",
        ErrorRole: b"error",
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._results: list[OrderResult] = []

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._results)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self._results):
            return None
        result = self._results[index.row()]
        return {
            self.NumberRole: result.number,
            self.MarketplaceRole: result.marketplace or "—",
            self.OrderIdRole: result.order_id or "—",
            self.SheetRole: result.sheet or "—",
            self.ItemsRole: result.items,
            self.OkRole: result.ok,
            self.ErrorRole: result.error or "",
        }.get(role)

    def roleNames(self):  # noqa: N802
        return dict(self._ROLES)

    def append(self, result: OrderResult) -> None:
        position = len(self._results)
        self.beginInsertRows(QModelIndex(), position, position)
        self._results.append(result)
        self.endInsertRows()

    def clear(self) -> None:
        self.beginResetModel()
        self._results.clear()
        self.endResetModel()

    def failed_order_texts(self) -> list[str]:
        return [r.order_text for r in self._results if not r.ok and r.order_text]


class Worker(QThread):
    """Processes a batch of orders in the background.

    Subscribes to the console for the duration of the run: all parser
    messages flow to the GUI via the logLine signal (and still into the
    file log).
    """

    logLine = Signal(str, str)
    progressChanged = Signal(int, int)
    orderFinished = Signal(object)
    finishedWithSummary = Signal(int, int)
    fatalError = Signal(str)

    def __init__(self, orders: list[str], parent=None) -> None:
        super().__init__(parent)
        self._orders = orders

    def run(self) -> None:  # noqa: D102
        def on_console(text: str, level: str) -> None:
            self.logLine.emit(text, level)

        console.subscribe(on_console)
        try:
            ok, failed = process_order_list(
                self._orders,
                progress_callback=lambda cur, tot: self.progressChanged.emit(cur, tot),
                result_callback=lambda res: self.orderFinished.emit(res),
            )
            self.finishedWithSummary.emit(ok, failed)
        except Exception as error:  # noqa: BLE001
            self.fatalError.emit(str(error))
        finally:
            console.unsubscribe(on_console)


class Backend(QObject):
    """The QML <-> Python bridge."""

    runningChanged = Signal()
    progressChanged = Signal()
    statusChanged = Signal()
    ordersPathChanged = Signal()
    summaryChanged = Signal()
    languageChanged = Signal()
    notify = Signal(str, "QVariantMap")

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._log_model = LogModel(self)
        self._log_filter = LogFilterModel(self)
        self._log_filter.setSourceModel(self._log_model)
        self._orders_model = OrdersModel(self)

        self._worker: Worker | None = None
        self._running = False
        self._progress = 0
        self._total = 0
        self._status_kind = "ready"
        self._status_args: dict = {}
        self._orders_path = get_orders_file_path()
        self._ok = 0
        self._failed = 0

        self._settings = QSettings("DanielK", "OrdersParserByDK")
        self._language = str(self._settings.value("ui/language", "en"))
        core_i18n.set_language(self._language)

    @Property(str, constant=True)
    def appVersion(self) -> str:  # noqa: N802
        return APP_VERSION

    @Property(QObject, constant=True)
    def logModel(self) -> LogModel:  # noqa: N802
        return self._log_model

    @Property(QObject, constant=True)
    def logFilter(self) -> LogFilterModel:  # noqa: N802
        return self._log_filter

    @Property(QObject, constant=True)
    def ordersModel(self) -> OrdersModel:  # noqa: N802
        return self._orders_model

    @Property(bool, notify=runningChanged)
    def running(self) -> bool:
        return self._running

    @Property(int, notify=progressChanged)
    def progress(self) -> int:
        return self._progress

    @Property(int, notify=progressChanged)
    def total(self) -> int:
        return self._total

    @Property(str, notify=statusChanged)
    def statusKind(self) -> str:  # noqa: N802
        return self._status_kind

    @Property("QVariantMap", notify=statusChanged)
    def statusArgs(self) -> dict:  # noqa: N802
        return self._status_args

    def _set_status(self, kind: str, **args) -> None:
        self._status_kind = kind
        self._status_args = args
        self.statusChanged.emit()

    @Property(str, notify=languageChanged)
    def language(self) -> str:
        return self._language

    @language.setter
    def language(self, code: str) -> None:
        if code in ("en", "ru", "uk") and code != self._language:
            self._language = code
            self._settings.setValue("ui/language", code)
            core_i18n.set_language(code)
            self.languageChanged.emit()

    @Property(str, notify=ordersPathChanged)
    def ordersPath(self) -> str:  # noqa: N802
        return self._orders_path

    @ordersPath.setter
    def ordersPath(self, value: str) -> None:  # noqa: N802
        path = QUrl(value).toLocalFile() if value.startswith("file:") else value
        if path and path != self._orders_path:
            self._orders_path = path
            self.ordersPathChanged.emit()

    @Property(int, notify=summaryChanged)
    def okCount(self) -> int:  # noqa: N802
        return self._ok

    @Property(int, notify=summaryChanged)
    def failedCount(self) -> int:  # noqa: N802
        return self._failed

    @Property(bool, notify=summaryChanged)
    def hasFailed(self) -> bool:  # noqa: N802
        return self._failed > 0

    @Property(str, constant=True)
    def spreadsheetUrl(self) -> str:  # noqa: N802
        try:
            from config.settings import get_settings

            return "https://docs.google.com/spreadsheets/d/" + get_settings().TABLE_ID
        except Exception:  # noqa: BLE001
            return ""

    @Slot()
    def startProcessing(self) -> None:  # noqa: N802
        """Process the orders file at the current path."""
        try:
            with open(self._orders_path, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            self._set_status("file_not_found", path=self._orders_path)
            self.notify.emit("file_not_found", {"path": self._orders_path})
            return
        except OSError as error:
            self._set_status("read_error", error=str(error))
            self.notify.emit("read_error", {"error": str(error)})
            return

        orders = split_orders(content)
        if not orders:
            self._set_status("file_empty")
            self.notify.emit("file_empty", {"path": self._orders_path})
            return
        self._start(orders)

    @Slot(str)
    def processText(self, text: str) -> None:  # noqa: N802
        """Process HTML pasted directly into the app."""
        orders = split_orders(text)
        if not orders:
            self._set_status("paste_empty")
            self.notify.emit("paste_empty", {})
            return
        self._start(orders)

    @Slot()
    def retryFailed(self) -> None:  # noqa: N802
        """Retry only the orders that failed."""
        failed_orders = self._orders_model.failed_order_texts()
        if failed_orders:
            self._start(failed_orders)

    @Slot()
    def openSpreadsheet(self) -> None:  # noqa: N802
        url = self.spreadsheetUrl
        if url:
            QDesktopServices.openUrl(QUrl(url))

    @Slot()
    def openLogsFolder(self) -> None:  # noqa: N802
        logs_dir = os.path.join(get_executable_dir(), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(logs_dir))

    @Slot(result=str)
    def logAsText(self) -> str:  # noqa: N802
        return self._log_model.plain_text()

    def _start(self, orders: list[str]) -> None:
        if self._running:
            return

        self._log_model.clear()
        self._orders_model.clear()
        self._ok = 0
        self._failed = 0
        self._progress = 0
        self._total = len(orders)
        self._running = True
        self.summaryChanged.emit()
        self.progressChanged.emit()
        self.runningChanged.emit()
        self._set_status("processing", total=self._total)

        self._worker = Worker(orders, self)
        self._worker.logLine.connect(self._log_model.append)
        self._worker.progressChanged.connect(self._on_progress)
        self._worker.orderFinished.connect(self._on_order_finished)
        self._worker.finishedWithSummary.connect(self._on_finished)
        self._worker.fatalError.connect(self._on_fatal)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    def _on_progress(self, current: int, total: int) -> None:
        self._progress = current
        self._total = total
        self.progressChanged.emit()
        self._set_status("progress", current=current, total=total)

    def _on_order_finished(self, result: OrderResult) -> None:
        self._orders_model.append(result)
        if result.ok:
            self._ok += 1
        else:
            self._failed += 1
        self.summaryChanged.emit()

    def _on_finished(self, ok: int, failed: int) -> None:
        self._running = False
        self.runningChanged.emit()
        self._set_status("done", ok=ok, failed=failed)
        self.notify.emit("finished", {"ok": ok, "failed": failed})

    def _on_fatal(self, message: str) -> None:
        self._running = False
        self.runningChanged.emit()
        self._log_model.append(tr("Fatal error: {message}", message=message), "error")
        self._set_status("fatal", error=message)
        self.notify.emit("fatal", {"error": message})
