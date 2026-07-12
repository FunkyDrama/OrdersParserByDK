"""Tests for shared BaseParser utilities."""

from marketplaces.base_parser import BaseParser
from marketplaces.wayfair_parser import WayfairParser


class _FakeFinder:
    """Stub finder: never touches the network, counts the calls."""

    def __init__(self, results=None):
        self.results = results or {}
        self.calls = []

    def search_file_by_name(self, query):
        self.calls.append(query)
        return self.results.get(query)

    def upload_shipping_labels(self, order_id):
        return "File Not Found"


class _DummyParser(BaseParser):
    CHANNEL = "Dummy"

    def parse_order(self):
        return []


def _make_parser(order_id="ORDER-1", sku="SKU-1", results=None):
    parser = _DummyParser("<html></html>", finder=_FakeFinder(results))
    parser.order_id = order_id
    parser.sku = sku
    return parser


def test_parse_money():
    assert _DummyParser._parse_money("$4.99") == 4.99
    assert _DummyParser._parse_money("CA$1,234.50") == 1234.5
    assert _DummyParser._parse_money("Free") == 0


def test_files_or_placeholder():
    assert _DummyParser._files_or_placeholder(None) == [
        {"link": "File Not Found", "name": "File Not Found"}
    ]
    files = [{"link": "L", "name": "N"}]
    assert _DummyParser._files_or_placeholder(files) is files


def test_allocate_file_link_sequence():
    files = [
        {"link": "link-1", "name": "24x36 a.svg"},
        {"link": "link-2", "name": "12x18 b.svg"},
    ]
    link, idx = _DummyParser._allocate_file_link(files, 0)
    assert (link, idx) == ("link-1", 1)
    link, idx = _DummyParser._allocate_file_link(files, idx)
    assert (link, idx) == ("link-2", 2)
    # More items than files
    link, idx = _DummyParser._allocate_file_link(files, idx)
    assert (link, idx) == ("File Not Found", 2)


def test_get_extension_and_smaller_size_from_drive_filename():
    query = "name contains 'ORDER-1' and not name contains '.pdf'"
    parser = _make_parser(
        results={query: [{"link": "l", "name": "24,5x36 wall art.svg"}]}
    )
    assert parser.get_extension() == "svg"
    assert parser.get_smaller_size() == 24.5


def test_get_extension_unknown_when_nothing_found():
    parser = _make_parser(results={})
    assert parser.get_extension() == "Unknown"
    assert parser.get_smaller_size() == "!ERROR!"


def test_known_tracking_links():
    link = _DummyParser._known_tracking_link("USPS", "9400111")
    assert link == (
        "https://tools.usps.com/go/TrackConfirmAction_input?qtc_tLabels1=9400111"
    )
    assert "InquiryNumber1=1Z999" in _DummyParser._known_tracking_link("UPS", "1Z999")
    assert _DummyParser._known_tracking_link("UPS®", "1Z999") is not None
    assert _DummyParser._known_tracking_link("Nova Poshta", "123") is None
    assert _DummyParser._known_tracking_link(None, "123") is None


def test_make_row_includes_store_column():
    parser = _make_parser()
    row = parser._make_row(
        date="03.07.2026",
        store_title="Stickalz LLC",
        sku="SKU-1",
        listing_link="listing",
        listing_title="Title",
        address="Address",
        quantity=1,
        customization="",
        file_link="file",
        shipping_label_link="label",
        tracking_number="123456789",
        ship_by_date="04.07.2026",
        postal_service="FedEx",
        shipping_type="Home Delivery",
        tracking_link="track",
        items_total=10.0,
        shipping_total=0,
        shipping_price=0,
        total=10.0,
    )
    assert row["Store"] == "Stickalz LLC"


def _wayfair_tracking(postal_service, tracking_number):
    parser = WayfairParser("<html></html>", finder=_FakeFinder())
    return parser._WayfairParser__get_tracking_link(postal_service, tracking_number)


def _wayfair_tracking_number(html):
    parser = WayfairParser(html, finder=_FakeFinder())
    return parser._WayfairParser__get_tracking_number()


def test_wayfair_tracking_number_read_after_label_not_last_paragraph():
    html = """
    <p data-tag-default="order-details_orderDetails_Text">Tracking Number(s)</p>
    <p data-tag-default="order-details_orderDetails_Text">
      284905884098, 284905883816
    </p>
    <p data-tag-default="order-details_orderDetails_Text">Delivery Date</p>
    """
    assert _wayfair_tracking_number(html) == "284905884098\n284905883816"


def test_wayfair_tracking_number_missing_returns_error():
    html = """
    <p data-tag-default="order-details_orderDetails_Text">Tracking Number(s)</p>
    <p data-tag-default="order-details_orderDetails_Text">Delivery Date</p>
    <p data-tag-default="order-details_orderDetails_Text">02/01/2025</p>
    """
    assert _wayfair_tracking_number(html) == "!ERROR!"


def test_wayfair_tracking_link_missing_tracking_returns_error():
    assert _wayfair_tracking("FedEx", "!ERROR!") == "!ERROR!"


def test_wayfair_multiple_tracking_numbers_joined():
    result = _wayfair_tracking("USPS", "9400111\n9400222")
    assert result.count("https://tools.usps.com") == 2
    assert "\n\n" in result


def test_wayfair_duplicate_numbers_deduplicated_in_order():
    result = _wayfair_tracking("UPS", "1Z1\n1Z1\n1Z2")
    links = result.split("\n\n")
    assert len(links) == 2
    assert "1Z1" in links[0] and "1Z2" in links[1]


def test_wayfair_unknown_carrier_returns_error_not_crash():
    assert _wayfair_tracking("Nova Poshta", "12345") == "!ERROR!"


def test_safe_total_computes_normally():
    assert _DummyParser._safe_total(100.0, 5.0, 12.5) == 92.5
    assert _DummyParser._safe_total(10, 0, 0) == 10


def test_safe_total_returns_error_value_when_field_missing():
    assert _DummyParser._safe_total("!ERROR!", 5.0, 0) == "!ERROR!"
    assert _DummyParser._safe_total(100.0, "!ERROR!", 0) == "!ERROR!"
    assert _DummyParser._safe_total(100.0, 5.0, "!ERROR!") == "!ERROR!"
