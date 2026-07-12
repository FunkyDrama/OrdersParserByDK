"""Tests for parsing console messages into structured UI entries."""

from ui.log_format import linkify, parse_entry


def test_banner():
    entry = parse_entry("----- New order Etsy -----")
    assert entry["kind"] == "banner"
    assert entry["marketplace"] == "Etsy"


def test_field_simple():
    entry = parse_entry("- Order ID: 3672188392")
    assert entry["kind"] == "field"
    assert entry["key"] == "Order ID"
    assert entry["value"] == "3672188392"


def test_field_value_with_colon_and_url():
    entry = parse_entry("- Tracking link: https://tools.usps.com/go/x?id=1")
    assert entry["kind"] == "field"
    assert entry["key"] == "Tracking link"
    assert '<a href="https://tools.usps.com/go/x?id=1">' in entry["value"]


def test_field_multiline_address():
    entry = parse_entry("- Customer address:\nJohn Smith\n42 Oak street")
    assert entry["kind"] == "field"
    assert entry["key"] == "Customer address"
    assert entry["value"] == "John Smith<br>42 Oak street"


def test_problem():
    entry = parse_entry("||| Could not get the tracking number |||")
    assert entry["kind"] == "problem"
    assert entry["message"] == "Could not get the tracking number"


def test_problem_exclamation_style():
    entry = parse_entry("!!!An error occurred: quota exceeded!!!")
    assert entry["kind"] == "problem"
    assert entry["message"] == "An error occurred: quota exceeded"


def test_done():
    entry = parse_entry("\n<<<Order added to the spreadsheet>>>")
    assert entry["kind"] == "done"
    assert entry["message"] == "Order added to the spreadsheet"


def test_note_sheet():
    entry = parse_entry("---Routing to sheet: 22 roll---")
    assert entry["kind"] == "note"
    assert entry["message"] == "Routing to sheet: 22 roll"


def test_plain_fallback_traceback():
    entry = parse_entry('Traceback (most recent call last):\n  File "x.py"')
    assert entry["kind"] == "plain"


def test_banner_not_confused_with_note():
    entry = parse_entry("---Orders Parser v7.2.3 by Daniel K---")
    assert entry["kind"] == "note"
    assert "Orders Parser" in entry["message"]


def test_linkify_escapes_html():
    result = linkify("<b> and a link https://a.example/x?q=1&y=2")
    assert result.startswith("&lt;b&gt;")
    assert '<a href="https://a.example/x?q=1&amp;y=2">' in result
