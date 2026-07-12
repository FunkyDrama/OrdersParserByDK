pragma Singleton
import QtQuick

// Central place for colors and fonts used across the app.
QtObject {
    readonly property color background: "#14161a"
    readonly property color surface: "#1c1f26"
    readonly property color surfaceLight: "#242832"
    readonly property color border: "#2e333d"
    readonly property color textPrimary: "#e8eaed"
    readonly property color textMuted: "#9aa0a6"

    readonly property color green: "#7ec97e"
    readonly property color red: "#e06c6c"
    readonly property color yellow: "#e6c352"
    readonly property color cyan: "#6cc4e0"
    readonly property color accent: "#4fc3f7"

    readonly property string monoFont: Qt.platform.os === "osx" ? "Menlo" : "Consolas"

    function levelColor(level) {
        switch (level) {
        case "success": return green
        case "error":   return red
        case "warning": return yellow
        case "header":  return cyan
        default:        return textPrimary
        }
    }

    function marketplaceColor(name) {
        switch (name) {
        case "Etsy":      return "#f1641e"
        case "Amazon":    return "#f0a53c"
        case "Wayfair":   return "#9061f9"
        case "Overstock": return "#e0475f"
        case "Ebay":      return "#4fc3f7"
        default:          return textMuted
        }
    }
}
