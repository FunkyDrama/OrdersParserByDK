import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Totals row + human readable status line (built from App.statusKind).
RowLayout {
    id: root

    spacing: 10

    function statusText() {
        const args = App.statusArgs
        switch (App.statusKind) {
        case "ready":
            return qsTr("Ready to work")
        case "file_not_found":
            return qsTr("File not found: %1").arg(args.path)
        case "read_error":
            return qsTr("Could not read the file: %1").arg(args.error)
        case "file_empty":
            return qsTr("No orders found in the file")
        case "paste_empty":
            return qsTr("No orders found in the pasted text")
        case "processing":
            return qsTr("Processing %n order(s)…", "", args.total)
        case "progress":
            return qsTr("Processed %1 of %2").arg(args.current).arg(args.total)
        case "done":
            return args.failed > 0
                ? qsTr("Done: %1 written, %2 failed. Check the journal and the spreadsheet!").arg(args.ok).arg(args.failed)
                : qsTr("Done: %1 order(s) written. Please double-check the spreadsheet!").arg(args.ok)
        case "fatal":
            return qsTr("Processing stopped because of an error")
        default:
            return ""
        }
    }

    StatCard { label: qsTr("Total");   value: App.total;       accent: Theme.cyan }
    StatCard { label: qsTr("Written"); value: App.okCount;     accent: Theme.green }
    StatCard {
        label: qsTr("Failed")
        value: App.failedCount
        accent: App.failedCount > 0 ? Theme.red : Theme.textMuted
    }

    Item { Layout.fillWidth: true }

    Label {
        text: root.statusText()
        color: Theme.textMuted
        font.pixelSize: 13
        elide: Text.ElideLeft
        Layout.maximumWidth: 420
    }
}
