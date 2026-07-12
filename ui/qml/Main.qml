import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts
import "components"

ApplicationWindow {
    id: window

    visible: true
    visibility: Window.FullScreen
    width: 800
    height: 600
    title: qsTr("Orders Parser v%1 by Daniel K").arg(App.appVersion)

    Material.theme: Material.Dark
    Material.accent: Theme.accent
    Material.primary: "#1a1d23"
    color: Theme.background

    // Drag & drop of the orders file anywhere onto the window
    DropArea {
        anchors.fill: parent
        onDropped: (drop) => {
            if (drop.hasUrls && !App.running) {
                App.ordersPath = drop.urls[0]
                drop.accept()
            }
        }
    }

    // Important events arrive from Python as (kind, args) pairs and are
    // rendered here so every message stays translatable in QML.
    Connections {
        target: App

        function onNotify(kind, args) {
            switch (kind) {
            case "file_not_found":
                notification.show("error", qsTr("Orders file not found"), args.path)
                break
            case "read_error":
                notification.show("error", qsTr("Could not read the orders file"), args.error)
                break
            case "file_empty":
                notification.show("warning", qsTr("The orders file is empty"),
                                  qsTr("No orders were found in %1").arg(args.path))
                break
            case "paste_empty":
                notification.show("warning", qsTr("Nothing to process"),
                                  qsTr("No orders were found in the pasted text"))
                break
            case "finished":
                if (args.failed > 0)
                    notification.show("warning", qsTr("Finished with errors"),
                                      qsTr("Orders written: %1, failed: %2. Check the journal and the spreadsheet!").arg(args.ok).arg(args.failed))
                else
                    notification.show("success", qsTr("All orders processed"),
                                      qsTr("Orders written: %1. Please double-check the data in the spreadsheet!").arg(args.ok))
                break
            case "fatal":
                notification.show("error", qsTr("Processing stopped"), args.error)
                break
            }
        }

        // Jump to the Journal tab as soon as processing starts,
        // so the progress is visible no matter where it was started from.
        function onRunningChanged() {
            if (App.running)
                tabBar.currentIndex = 0
        }
    }

    NotificationPopup {
        id: notification
        parent: Overlay.overlay
        width: Math.min(460, window.width - 80)
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        HeaderBar {
            Layout.fillWidth: true
        }

        LaunchPanel {
            Layout.fillWidth: true
        }

        SummaryBar {
            Layout.fillWidth: true
        }

        TabBar {
            id: tabBar
            Layout.fillWidth: true
            TabButton { text: qsTr("Journal") }
            TabButton { text: qsTr("Orders (%1)").arg(App.okCount + App.failedCount) }
            TabButton { text: qsTr("Paste HTML") }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabBar.currentIndex

            LogPanel { }
            OrdersPanel { }
            PastePanel { }
        }
    }
}
