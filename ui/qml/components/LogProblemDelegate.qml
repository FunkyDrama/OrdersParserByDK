import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Error / warning card with a tinted background.
Rectangle {
    required property var model
    property real viewWidth: 0

    readonly property color tone: model.level === "warning" ? Theme.yellow : Theme.red

    width: viewWidth
    implicitHeight: row.implicitHeight + 12
    radius: 6
    color: Qt.alpha(tone, 0.10)
    border.color: Qt.alpha(tone, 0.35)
    border.width: 1

    RowLayout {
        id: row
        anchors.fill: parent
        anchors.margins: 6
        spacing: 8

        Label {
            text: model.level === "warning" ? "⚠" : "✕"
            color: tone
            font.pixelSize: 13
            font.bold: true
            Layout.alignment: Qt.AlignTop
        }
        Label {
            text: model.message
            textFormat: Text.RichText
            color: tone
            linkColor: Theme.accent
            font.pixelSize: 12
            wrapMode: Text.Wrap
            Layout.fillWidth: true
            onLinkActivated: (link) => Qt.openUrlExternally(link)
        }
        Label {
            text: model.time
            color: Theme.textMuted
            font.pixelSize: 10
            Layout.alignment: Qt.AlignTop
        }
    }
}
