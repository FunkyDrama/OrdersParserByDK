import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// "Order added" success row.
RowLayout {
    required property var model
    property real viewWidth: 0

    width: viewWidth
    spacing: 8

    Label {
        text: "✓"
        color: Theme.green
        font.pixelSize: 13
        font.bold: true
        leftPadding: 12
    }
    Label {
        text: model.message
        textFormat: Text.RichText
        color: Theme.green
        font.pixelSize: 12
        font.bold: true
        Layout.fillWidth: true
    }
    Label {
        text: model.time
        color: Theme.textMuted
        font.pixelSize: 10
    }
}
