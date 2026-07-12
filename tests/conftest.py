"""Shared test setup: settings come from environment variables so the tests
require no config/.env and never touch the network."""

import os
import sys

os.environ.setdefault("TABLE_ID", "test-table-id")
os.environ.setdefault("SHIPPING_LABEL_FOLDER", "test-folder-id")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
