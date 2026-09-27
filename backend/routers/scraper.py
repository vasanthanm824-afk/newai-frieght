"""Web Scraper router — live indices, custom URL scraper, and data ingestion."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from ..core.web_scraper import (
    ingest_scraped_market_data,
    scrape_custom_url,
    scrape_live_shipping_indices,
)

router = APIRouter()


class ScrapeUrlRequest(BaseModel):
    url: str


class IngestRequest(BaseModel):
    scraped_data: dict[str, Any]


@router.get("/live-indices")
def get_live_indices():
    """Fetch live scraped shipping market indices and bunker fuel prices."""
    return scrape_live_shipping_indices()


@router.post("/scrape-url")
def scrape_url(req: ScrapeUrlRequest):
    """Scrape custom user-provided URL for shipping/freight market details."""
    return scrape_custom_url(req.url)


@router.post("/ingest")
def ingest_data(req: IngestRequest):
    """Ingest scraped market data into AI decision engine pipeline."""
    return ingest_scraped_market_data(req.scraped_data)
