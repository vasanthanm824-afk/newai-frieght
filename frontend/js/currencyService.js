/**
 * Reusable Currency Conversion & Formatting Service for SmartVesselAI Engine
 * 
 * Pipeline:
 * Forecast Model / API → Numeric Freight Rate (USD) → Currency Conversion → Intl.NumberFormat → Dashboard UI
 */

const CurrencyService = {
  
  /**
   * Returns current exchange rate for target currency relative to USD.
   */
  getRate(targetCurrency = "USD") {
    const config = window.CURRENCY_CONFIG || { exchangeRatesFromUSD: { USD: 1.0, INR: 83.0, AUD: 1.52, RUB: 90.5, IDR: 15800.0 } };
    return config.exchangeRatesFromUSD[targetCurrency] || 1.0;
  },

  /**
   * Converts a numeric USD amount to target currency.
   */
  convertFromUSD(usdAmount, targetCurrency = "USD") {
    if (usdAmount === undefined || usdAmount === null || isNaN(usdAmount)) {
      return null;
    }
    const rate = this.getRate(targetCurrency);
    return Number(usdAmount) * rate;
  },

  /**
   * Formats a raw numeric value using Intl.NumberFormat according to selected currency settings.
   */
  formatValue(numericValue, targetCurrency = "USD", options = {}) {
    if (numericValue === undefined || numericValue === null || isNaN(numericValue)) {
      return "--";
    }

    const config = window.CURRENCY_CONFIG || {};
    const meta = (config.currencies && config.currencies[targetCurrency]) || {
      symbol: "$",
      locale: "en-US",
      decimals: 2
    };

    const dec = options.decimals !== undefined ? options.decimals : meta.decimals;

    try {
      // Use standard Intl.NumberFormat
      const formatter = new Intl.NumberFormat(meta.locale || "en-US", {
        style: "currency",
        currency: targetCurrency,
        minimumFractionDigits: dec,
        maximumFractionDigits: dec
      });
      return formatter.format(numericValue);
    } catch (e) {
      // Fallback formatting
      const numStr = Number(numericValue).toLocaleString(undefined, {
        minimumFractionDigits: dec,
        maximumFractionDigits: dec
      });
      return `${meta.symbol || targetCurrency} ${numStr}`;
    }
  },

  /**
   * Formats USD per-tonne freight rate to target currency string (e.g., "$ 25.50 / T" or "₹ 2,116.50 / T").
   */
  formatRate(usdAmount, targetCurrency = "USD") {
    const converted = this.convertFromUSD(usdAmount, targetCurrency);
    if (converted === null) return "-- / T";
    
    const formatted = this.formatValue(converted, targetCurrency);
    return `${formatted} / T`;
  },

  /**
   * Formats USD per-day charter hire rate to target currency string (e.g., "$ 22,040.00 / Day").
   */
  formatDailyHire(usdAmount, targetCurrency = "USD") {
    const converted = this.convertFromUSD(usdAmount, targetCurrency);
    if (converted === null) return "-- / Day";
    
    const formatted = this.formatValue(converted, targetCurrency);
    return `${formatted} / Day`;
  },

  /**
   * Formats total landed cost USD to target currency string.
   */
  formatCost(usdAmount, targetCurrency = "USD") {
    const converted = this.convertFromUSD(usdAmount, targetCurrency);
    if (converted === null) return "--";
    return this.formatValue(converted, targetCurrency);
  },

  /**
   * Formats array of numeric rates for Plotly charts.
   */
  convertRateSeries(usdRatesArray, targetCurrency = "USD") {
    if (!Array.isArray(usdRatesArray)) return [];
    const rate = this.getRate(targetCurrency);
    return usdRatesArray.map(val => {
      if (val === undefined || val === null || isNaN(val)) return 0;
      return Math.round((Number(val) * rate) * 100) / 100;
    });
  },

  /**
   * Returns formatted exchange rate metadata timestamp label.
   */
  getUpdateTimestampLabel() {
    const config = window.CURRENCY_CONFIG || {};
    return `Exchange rates updated: ${config.lastUpdated || "02 Sep 2026"} | Base Market: USD ($)`;
  }
};

if (typeof window !== "undefined") {
  window.CurrencyService = CurrencyService;
}
