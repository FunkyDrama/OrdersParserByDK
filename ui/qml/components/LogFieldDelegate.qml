import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// "Key: value" pair; value may be multiline and contain clickable links.
RowLayout {
    required property var model
    property real viewWidth: 0

    width: viewWidth
    spacing: 10

    Label {
        text: model.key
        color: Theme.textMuted
        font.pixelSize: 12
        Layout.preferredWidth: 240
        Layout.alignment: Qt.AlignTop
        elide: Text.ElideRight
        leftPadding: 12
    }
    Label {
        text: model.value
        textFormat: Text.RichText
        color: Theme.textPrimary
        linkColor: Theme.accent
        font.family: Theme.monoFont
        font.pixelSize: 12
        wrapMode: Text.Wrap
        Layout.fillWidth: true
        onLinkActivated: (link) => Qt.openUrlExternally(link)
    }
}
