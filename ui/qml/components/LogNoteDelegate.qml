import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Informational note (sheet selection etc.).
RowLayout {
    required property var model
    property real viewWidth: 0

    width: viewWidth
    spacing: 8

    Label {
        text: "→"
        color: Theme.cyan
        font.pixelSize: 12
        leftPadding: 12
    }
    Label {
        text: model.message
        textFormat: Text.RichText
        color: Theme.levelColor(model.level) === Theme.textPrimary ? Theme.cyan : Theme.levelColor(model.level)
        font.pixelSize: 12
        font.italic: true
        wrapMode: Text.Wrap
        Layout.fillWidth: true
    }
}
