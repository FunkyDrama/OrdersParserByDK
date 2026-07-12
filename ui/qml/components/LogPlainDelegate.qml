import QtQuick

// Fallback: raw monospace text (tracebacks and unrecognized lines).
TextEdit {
    required property var model
    property real viewWidth: 0

    width: viewWidth
    text: model.text
    color: Theme.levelColor(model.level)
    font.family: Theme.monoFont
    font.pixelSize: 11
    readOnly: true
    selectByMouse: true
    wrapMode: TextEdit.Wrap
    padding: 2
    leftPadding: 12
}
