import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Top bar: app title, language selector and quick actions.
RowLayout {
    id: root

    spacing: 12

    ColumnLayout {
        spacing: 2
        Label {
            text: "Orders Parser by Daniel K"
            font.pixelSize: 22
            font.bold: true
            color: Theme.textPrimary
        }
        Label {
            text: "v" + App.appVersion + " · Etsy · Amazon · eBay · Wayfair · Overstock"
            font.pixelSize: 12
            color: Theme.textMuted
        }
    }

    Item { Layout.fillWidth: true }

    ComboBox {
        id: languageBox
        Layout.preferredWidth: 150
        model: [
            { code: "en", label: "English" },
            { code: "ru", label: "Русский" },
            { code: "uk", label: "Українська" }
        ]
        textRole: "label"
        valueRole: "code"
        Component.onCompleted: currentIndex = indexOfValue(App.language)
        onActivated: App.language = currentValue

        // Keep the selector in sync when the language changes
        // programmatically (not through this ComboBox)
        Connections {
            target: App
            function onLanguageChanged() {
                languageBox.currentIndex = languageBox.indexOfValue(App.language)
            }
        }
    }

    Button {
        text: qsTr("Open spreadsheet")
        flat: true
        enabled: App.spreadsheetUrl !== ""
        onClicked: App.openSpreadsheet()
    }
    Button {
        text: qsTr("Logs folder")
        flat: true
        onClicked: App.openLogsFolder()
    }
}
