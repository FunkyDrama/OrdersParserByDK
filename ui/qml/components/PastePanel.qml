import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Paste-HTML tab: process orders without an orders.txt file.
Rectangle {
    id: root

    radius: 10
    color: Theme.surface
    border.color: Theme.border
    border.width: 1

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        Label {
            text: qsTr("Paste order HTML (multiple orders are separated by </html>) and press \"Process pasted\"")
            color: Theme.textMuted
            font.pixelSize: 12
            wrapMode: Text.Wrap
            Layout.fillWidth: true
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true

            TextArea {
                id: pasteArea
                placeholderText: "<html> … </html>"
                font.family: Theme.monoFont
                font.pixelSize: 12
                wrapMode: TextArea.Wrap
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            Button {
                text: qsTr("Clear")
                flat: true
                onClicked: pasteArea.clear()
            }
            Button {
                text: qsTr("Process pasted")
                highlighted: true
                enabled: !App.running && pasteArea.text.trim().length > 0
                onClicked: App.processText(pasteArea.text)
            }
        }
    }
}
