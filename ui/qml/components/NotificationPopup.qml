import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Centered notification for important events (empty file, run finished, …).
// Dismissed by a click anywhere, Escape, or automatically after a timeout.
Popup {
    id: root

    // "info" | "success" | "warning" | "error"
    property string severity: "info"
    property string title: ""
    property string body: ""

    function show(newSeverity, newTitle, newBody) {
        severity = newSeverity
        title = newTitle
        body = newBody
        open()
        autoClose.restart()
    }

    readonly property color tone: {
        switch (severity) {
        case "success": return Theme.green
        case "warning": return Theme.yellow
        case "error":   return Theme.red
        default:        return Theme.cyan
        }
    }

    anchors.centerIn: parent
    modal: true
    dim: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    padding: 0

    Timer {
        id: autoClose
        interval: 6000
        onTriggered: root.close()
    }

    background: Rectangle {
        radius: 12
        color: Theme.surfaceLight
        border.color: Qt.alpha(root.tone, 0.6)
        border.width: 1

        // a click on the popup itself also dismisses it
        MouseArea {
            anchors.fill: parent
            onClicked: root.close()
        }
    }

    contentItem: ColumnLayout {
        spacing: 6

        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 16
            Layout.leftMargin: 20
            Layout.rightMargin: 20
            spacing: 10

            Label {
                text: {
                    switch (root.severity) {
                    case "success": return "✓"
                    case "warning": return "⚠"
                    case "error":   return "✕"
                    default:        return "ℹ"
                    }
                }
                color: root.tone
                font.pixelSize: 20
                font.bold: true
            }
            Label {
                text: root.title
                color: Theme.textPrimary
                font.pixelSize: 15
                font.bold: true
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }
        }

        Label {
            text: root.body
            visible: root.body.length > 0
            color: Theme.textMuted
            font.pixelSize: 13
            wrapMode: Text.Wrap
            Layout.fillWidth: true
            Layout.leftMargin: 20
            Layout.rightMargin: 20
        }

        Label {
            text: qsTr("Click anywhere to dismiss")
            color: Qt.alpha(Theme.textMuted, 0.6)
            font.pixelSize: 10
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: 4
            Layout.bottomMargin: 12
        }
    }

    Overlay.modal: Rectangle {
        color: Qt.alpha("#000000", 0.45)
        MouseArea {
            anchors.fill: parent
            onClicked: root.close()
        }
    }
}
