"""Sheet routing tests — business-critical logic."""

from google_api.gsheet_writer import select_sheet_name


def test_wallpaper_by_customization_beats_everything():
    assert select_sheet_name("svg", 10.0, "Material: Peel and Stick") == "Wallpaper"
    assert select_sheet_name("png", 30.0, "non-woven wallpaper") == "Wallpaper"
    assert select_sheet_name("Unknown", "!ERROR!", "Peel & Stick") == "Wallpaper"


def test_colored_extensions():
    for ext in ("png", "jpg", "jpeg", "eps"):
        assert select_sheet_name(ext, 10.0) == "Colored"


def test_roll_sorting_by_smaller_size():
    assert select_sheet_name("svg", 22.0) == "22 roll"
    assert select_sheet_name("svg", 21.5) == "22 roll"
    assert select_sheet_name("svg", 22.1) == "46 roll"
    assert select_sheet_name("svg", 46.0) == "46 roll"


def test_error_sheet_fallbacks():
    assert select_sheet_name("Unknown", 10.0) == "ERROR"
    assert select_sheet_name("svg", "!ERROR!") == "ERROR"


def test_no_customization_is_not_wallpaper():
    assert select_sheet_name("svg", 10.0, None) == "22 roll"
    assert select_sheet_name("svg", 10.0, "") == "22 roll"
    assert select_sheet_name("svg", 10.0, "Size: 24x36 inches") == "22 roll"
