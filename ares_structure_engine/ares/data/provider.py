"""
ARES STRUCTURE ENGINE v1.0 — Data Provider Dispatcher

Routes data requests to mock or live provider based on DATA_MODE config.
"""

from ares.utils.constants import DATA_MODE
from ares.utils.logger import get_logger

log = get_logger("ares.data")


def fetch_data(content_type: str, date_str: str) -> dict:
    """
    Fetch normalized data for the given content type and date.
    Routes to mock or live provider based on DATA_MODE environment variable.
    """
    if DATA_MODE == "live":
        from ares.data.live_provider import fetch_data as live_fetch
        log.info(f"Fetching LIVE data: {content_type} for {date_str}")
        return live_fetch(content_type, date_str)
    else:
        from ares.data.mock_provider import fetch_data as mock_fetch
        log.info(f"Fetching MOCK data: {content_type} for {date_str}")
        return mock_fetch(content_type, date_str)
