import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Small numeric card used in the summary row.
Rectangle {
    property string label
    property int value
    property color accent: Theme.cyan

    radius: 10
    color: Theme.surface
    border.color: Theme.border
    border.width: 1
    implicitWidth: 110
    implicitHeight: 54

    ColumnLayout {
        anchors.centerIn: parent
        spacing: 0
        Label {
            text: value
            color: accent
            font.pixelSize: 20
            font.bold: true
            Layout.alignment: Qt.AlignHCenter
        }
        Label {
            text: label
            color: Theme.textMuted
            font.pixelSize: 11
            Layout.alignment: Qt.AlignHCenter
        }
    }
}
