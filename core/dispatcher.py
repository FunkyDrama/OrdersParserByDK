"""Marketplace detection based on the HTML content."""

from collections.abc import Callable
from typing import NamedTuple

from colorama import Fore

from marketplaces.amazon_parser import AmazonParser
from marketplaces.base_parser import BaseParser
from marketplaces.ebay_parser import EbayParser
from marketplaces.etsy_parser import EtsyParser
from marketplaces.overstock_parser import OverstockParser
from marketplaces.wayfair_parser import WayfairParser


class MarketplaceSpec(NamedTuple):
    """Marketplace descriptor: name, detector, parser class and colorama banner color."""

    name: str
    detect: Callable[[str], bool]
    parser_cls: type[BaseParser]
    banner_style: str  # colorama Fore.* ANSI string


# Entry order = check order in the legacy main.py
MARKETPLACES: tuple[MarketplaceSpec, ...] = (
    MarketplaceSpec(
        name="Etsy",
        detect=lambda order: "etsy.com" in order,
        parser_cls=EtsyParser,
        banner_style=Fore.GREEN,
    ),
    MarketplaceSpec(
        name="Amazon",
        detect=lambda order: "amazon.com" in order or "Order ID" in order,
        parser_cls=AmazonParser,
        banner_style=Fore.LIGHTBLUE_EX,
    ),
    MarketplaceSpec(
        name="Wayfair",
        detect=lambda order: "https://partners.wayfair.com/v/landing/index" in order,
        parser_cls=WayfairParser,
        banner_style=Fore.LIGHTMAGENTA_EX,
    ),
    MarketplaceSpec(
        name="Overstock",
        detect=lambda order: "https://edge.supplieroasis.com/dashboard/" in order,
        parser_cls=OverstockParser,
        banner_style=Fore.LIGHTYELLOW_EX,
    ),
    MarketplaceSpec(
        name="Ebay",
        detect=lambda order: "https://www.ebay.com" in order,
        parser_cls=EbayParser,
        banner_style=Fore.BLUE,
    ),
)


def detect_marketplace(order: str) -> MarketplaceSpec | None:
    """Returns the first matching marketplace or None"""
    for spec in MARKETPLACES:
        if spec.detect(order):
            return spec
    return None
