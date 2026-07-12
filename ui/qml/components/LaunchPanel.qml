import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Controls.Material
import QtQuick.Dialogs

// Orders file selection, start / retry buttons and the progress bar.
Rectangle {
    id: root

    radius: 10
    color: Theme.surface
    border.color: Theme.border
    border.width: 1
    implicitHeight: content.implicitHeight + 24

    FileDialog {
        id: fileDialog
        title: qsTr("Choose the orders file")
        nameFilters: [qsTr("Text files (*.txt)"), qsTr("All files (*)")]
        onAccepted: App.ordersPath = selectedFile
    }

    ColumnLayout {
        id: content
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            TextField {
                Layout.fillWidth: true
                text: App.ordersPath
                placeholderText: qsTr("Path to orders.txt (or drop the file onto the window)")
                enabled: !App.running
                onEditingFinished: App.ordersPath = text
            }
            Button {
                text: qsTr("Browse…")
                enabled: !App.running
                onClicked: fileDialog.open()
            }
            Button {
                text: App.running ? qsTr("Processing…") : qsTr("Process orders")
                highlighted: true
                enabled: !App.running
                onClicked: App.startProcessing()
            }
            Button {
                text: qsTr("Retry failed (%1)").arg(App.failedCount)
                visible: App.hasFailed && !App.running
                Material.foreground: Theme.yellow
                onClicked: App.retryFailed()
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 12
            visible: App.total > 0 || App.running

            ProgressBar {
                Layout.fillWidth: true
                from: 0
                to: Math.max(App.total, 1)
                value: App.progress
                indeterminate: App.running && App.progress === 0
            }
            Label {
                text: App.progress + " / " + App.total
                color: Theme.textMuted
                font.pixelSize: 12
            }
        }
    }
}
