/**
 * Centralized Currency Configuration for SmartVesselAI Platform
 * Treats Freight Market Currency (USD) and Dashboard Display Currency as separate concepts.
 */

const CURRENCY_CONFIG = {
  baseCurrency: "USD",
  lastUpdated: "02 Sep 2026",
  source: "Baltic Exchange & Global FX Benchmark",
  
  currencies: {
    INR: { symbol: "₹", name: "Indian Rupee", locale: "en-IN", decimals: 2 },
    USD: { symbol: "$", name: "US Dollar", locale: "en-US", decimals: 2 },
    AUD: { symbol: "A$", name: "Australian Dollar", locale: "en-AU", decimals: 2 },
    RUB: { symbol: "₽", name: "Russian Ruble", locale: "ru-RU", decimals: 2 },
    IDR: { symbol: "Rp", name: "Indonesian Rupiah", locale: "id-ID", decimals: 0 }
  },

  // Base Exchange Rates relative to 1 USD
  exchangeRatesFromUSD: {
    USD: 1.0,
    INR: 83.0,
    AUD: 1.52,
    RUB: 90.5,
    IDR: 15800.0
  }
};

if (typeof window !== "undefined") {
  window.CURRENCY_CONFIG = CURRENCY_CONFIG;
}
