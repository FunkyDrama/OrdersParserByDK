"""Desktop UI entry point (PySide6 + QML)."""

import os
import sys


def run_app() -> None:
    """Create the QGuiApplication and load the QML interface."""
    from PySide6.QtCore import QTranslator
    from PySide6.QtGui import QGuiApplication, QIcon
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuickControls2 import QQuickStyle

    from core.paths import resource_path
    from ui.backend import Backend

    QQuickStyle.setStyle("Material")

    app = QGuiApplication(sys.argv)
    app.setApplicationName("Orders Parser by DK")
    app.setOrganizationName("DanielK")

    icon_path = resource_path(os.path.join("assets", "icon.png"))
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    backend = Backend()
    engine = QQmlApplicationEngine()

    translator = QTranslator(app)

    def apply_language() -> None:
        app.removeTranslator(translator)
        code = backend.language
        if code != "en":
            qm_path = resource_path(os.path.join("ui", "i18n", f"app_{code}.qm"))
            if translator.load(qm_path):
                app.installTranslator(translator)
        engine.retranslate()  # noqa: F821

    backend.languageChanged.connect(apply_language)

    if backend.language != "en":
        qm_path = resource_path(
            os.path.join("ui", "i18n", f"app_{backend.language}.qm")
        )
        if translator.load(qm_path):
            app.installTranslator(translator)

    engine.rootContext().setContextProperty("App", backend)
    engine.load(resource_path(os.path.join("ui", "qml", "Main.qml")))

    if not engine.rootObjects():
        print("Failed to load the UI (ui/qml/Main.qml)", file=sys.stderr)
        sys.exit(1)

    exit_code = app.exec()
    del engine
    sys.exit(exit_code)
