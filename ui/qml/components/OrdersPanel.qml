import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Orders tab: one card per processed order.
Rectangle {
    id: root

    radius: 10
    color: Theme.surface
    border.color: Theme.border
    border.width: 1

    ListView {
        anchors.fill: parent
        anchors.margins: 10
        clip: true
        model: App.ordersModel
        spacing: 6
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar {}

        delegate: Rectangle {
            width: ListView.view.width
            implicitHeight: row.implicitHeight + 16
            radius: 8
            color: Theme.surfaceLight
            border.color: model.ok ? Theme.border : Qt.alpha(Theme.red, 0.5)
            border.width: 1

            RowLayout {
                id: row
                anchors.fill: parent
                anchors.margins: 8
                spacing: 12

                Label {
                    text: "#" + model.number
                    color: Theme.textMuted
                    font.pixelSize: 12
                    Layout.preferredWidth: 34
                }

                Rectangle {
                    radius: height / 2
                    color: Qt.alpha(Theme.marketplaceColor(model.marketplace), 0.18)
                    implicitWidth: chip.implicitWidth + 18
                    implicitHeight: 22
                    Label {
                        id: chip
                        anchors.centerIn: parent
                        text: model.marketplace
                        color: Theme.marketplaceColor(model.marketplace)
                        font.pixelSize: 11
                        font.bold: true
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    Label {
                        text: model.orderId
                        color: Theme.textPrimary
                        font.pixelSize: 13
                        font.bold: true
                        elide: Text.ElideMiddle
                        Layout.fillWidth: true
                    }
                    Label {
                        visible: !model.ok
                        text: model.error
                        color: Theme.red
                        font.pixelSize: 11
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }
                }

                Label {
                    visible: model.ok
                    text: qsTr("sheet: %1").arg(model.sheet)
                    color: Theme.textMuted
                    font.pixelSize: 12
                }
                Label {
                    visible: model.ok
                    text: qsTr("%n item(s)", "", model.items)
                    color: Theme.textMuted
                    font.pixelSize: 12
                }
                Label {
                    text: model.ok ? "✓" : "✕"
                    color: model.ok ? Theme.green : Theme.red
                    font.pixelSize: 16
                    font.bold: true
                }
            }
        }
    }
}
