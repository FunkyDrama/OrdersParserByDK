import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.qmlmodels

// Journal tab: search, "problems only" filter, copy button and the log list.
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

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            TextField {
                Layout.preferredWidth: 260
                placeholderText: qsTr("Search the journal…")
                text: App.logFilter.search
                onTextChanged: App.logFilter.search = text
            }
            Switch {
                text: qsTr("Problems only")
                checked: App.logFilter.errorsOnly
                onToggled: App.logFilter.errorsOnly = checked
            }
            Item { Layout.fillWidth: true }
            Button {
                text: qsTr("Copy")
                flat: true
                onClicked: {
                    hiddenCopy.text = App.logAsText()
                    hiddenCopy.selectAll()
                    hiddenCopy.copy()
                }
            }
        }

        // invisible buffer used as a clipboard bridge for the Copy button
        TextEdit { id: hiddenCopy; visible: false }

        ListView {
            id: logView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: App.logFilter
            spacing: 3
            boundsBehavior: Flickable.StopAtBounds

            // keep scrolled to the bottom while processing is running
            onCountChanged: if (App.running) positionViewAtEnd()

            ScrollBar.vertical: ScrollBar {}

            delegate: DelegateChooser {
                role: "kind"

                DelegateChoice {
                    roleValue: "banner"
                    delegate: LogBannerDelegate { viewWidth: logView.width }
                }
                DelegateChoice {
                    roleValue: "field"
                    delegate: LogFieldDelegate { viewWidth: logView.width }
                }
                DelegateChoice {
                    roleValue: "problem"
                    delegate: LogProblemDelegate { viewWidth: logView.width }
                }
                DelegateChoice {
                    roleValue: "done"
                    delegate: LogDoneDelegate { viewWidth: logView.width }
                }
                DelegateChoice {
                    roleValue: "note"
                    delegate: LogNoteDelegate { viewWidth: logView.width }
                }
                DelegateChoice {
                    delegate: LogPlainDelegate { viewWidth: logView.width }
                }
            }
        }
    }
}
