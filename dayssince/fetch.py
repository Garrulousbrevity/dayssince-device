"""Fetch the current daysSince value from the public GraphQL endpoint."""

import logging
import time

import requests

from . import config

logger = logging.getLogger(__name__)

QUERY = 'query { events(name: "%s") { name daysSince lastEvent } }' % config.EVENT_NAME


class FetchError(Exception):
    pass


def fetch_days_since(retries: int = 4, backoff: float = 5.0) -> dict:
    """Return {"daysSince": int, "lastEvent": str}. Raises FetchError after retries.

    Retries cover the WiFi-still-associating window right after boot.
    """
    last_err = None
    for attempt in range(retries):
        try:
            resp = requests.post(
                config.GRAPHQL_ENDPOINT,
                json={"query": QUERY},
                timeout=15,
            )
            resp.raise_for_status()
            body = resp.json()
            events = body["data"]["events"]
            if not events:
                raise FetchError(f"event {config.EVENT_NAME!r} not found")
            event = events[0]
            return {"daysSince": int(event["daysSince"]), "lastEvent": event.get("lastEvent")}
        except FetchError:
            raise
        except Exception as err:  # network errors, bad JSON, etc.
            last_err = err
            logger.warning("fetch attempt %d/%d failed: %s", attempt + 1, retries, err)
            if attempt < retries - 1:
                time.sleep(backoff * (attempt + 1))
    raise FetchError(f"all {retries} fetch attempts failed: {last_err}")
