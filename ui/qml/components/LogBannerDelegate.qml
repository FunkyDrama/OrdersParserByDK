import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// "New order · Etsy" separator with marketplace-colored chip.
Item {
    required property var model
    property real viewWidth: 0

    width: viewWidth
    implicitHeight: 40

    RowLayout {
        anchors.fill: parent
        anchors.topMargin: 10
        spacing: 10

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: Qt.alpha(Theme.marketplaceColor(model.marketplace), 0.35)
        }
        Rectangle {
            radius: height / 2
            implicitHeight: 24
            implicitWidth: bannerLabel.implicitWidth + 22
            color: Qt.alpha(Theme.marketplaceColor(model.marketplace), 0.16)
            border.color: Qt.alpha(Theme.marketplaceColor(model.marketplace), 0.45)
            border.width: 1

            Label {
                id: bannerLabel
                anchors.centerIn: parent
                text: qsTr("New order · %1").arg(model.marketplace)
                color: Theme.marketplaceColor(model.marketplace)
                font.pixelSize: 12
                font.bold: true
            }
        }
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: Qt.alpha(Theme.marketplaceColor(model.marketplace), 0.35)
        }
        Label {
            text: model.time
            color: Theme.textMuted
            font.pixelSize: 10
        }
    }
}
