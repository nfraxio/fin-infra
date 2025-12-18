"""Data models for normalization module."""

from datetime import date as DateType

from pydantic import BaseModel, Field


class SymbolMetadata(BaseModel):
    """Company/asset metadata for a symbol."""

    ticker: str = Field(..., description="Standard ticker symbol")
    name: str = Field(..., description="Company or asset name")
    exchange: str | None = Field(None, description="Primary exchange (e.g., NASDAQ, NYSE)")
    cusip: str | None = Field(None, description="CUSIP identifier")
    isin: str | None = Field(None, description="ISIN identifier")
    sector: str | None = Field(None, description="Business sector")
    industry: str | None = Field(None, description="Industry classification")
    market_cap: float | None = Field(None, description="Market capitalization in USD")
    asset_type: str = Field(default="stock", description="Asset type: stock, etf, crypto, forex")


class ExchangeRate(BaseModel):
    """Exchange rate between two currencies."""

    from_currency: str = Field(..., description="Source currency code (e.g., USD)")
    to_currency: str = Field(..., description="Target currency code (e.g., EUR)")
    rate: float = Field(..., description="Exchange rate (1 from_currency = rate to_currency)")
    date: DateType | None = Field(None, description="Rate date (None = current)")
    timestamp: int | None = Field(None, description="Unix timestamp of rate")


class CurrencyConversionResult(BaseModel):
    """Result of a currency conversion."""

    amount: float = Field(..., description="Original amount")
    from_currency: str = Field(..., description="Source currency")
    to_currency: str = Field(..., description="Target currency")
    converted: float = Field(..., description="Converted amount")
    rate: float = Field(..., description="Exchange rate used")
    date: DateType | None = Field(None, description="Rate date")
