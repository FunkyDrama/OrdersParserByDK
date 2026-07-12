"""Marketplace detection tests."""

from core.dispatcher import MARKETPLACES, detect_marketplace


def test_detection_order_preserved():
    assert [spec.name for spec in MARKETPLACES] == [
        "Etsy",
        "Amazon",
        "Wayfair",
        "Overstock",
        "Ebay",
    ]


def test_each_marketplace_detected():
    cases = {
        "an order with an etsy.com link inside": "Etsy",
        "an amazon.com order about an order": "Amazon",
        "text with an Order ID but no explicit amazon": "Amazon",
        "https://partners.wayfair.com/v/landing/index": "Wayfair",
        "https://edge.supplieroasis.com/dashboard/ order": "Overstock",
        "visit https://www.ebay.com for details": "Ebay",
    }
    for text, expected in cases.items():
        spec = detect_marketplace(text)
        assert spec is not None, text
        assert spec.name == expected


def test_etsy_wins_over_amazon_keyword():
    spec = detect_marketplace("Order ID: 1 see etsy.com")
    assert spec.name == "Etsy"


def test_unknown_returns_none():
    assert detect_marketplace("plain text with no markers") is None
