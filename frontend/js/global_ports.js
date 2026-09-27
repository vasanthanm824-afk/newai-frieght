/* Dynamic Country-Based Currency & Global Port Dropdown Helpers */

const COUNTRY_CURRENCY_MAP = {
  "India": { symbol: "₹", code: "INR", name: "Indian Rupee", rateMultiplier: 83.0 },
  "Australia": { symbol: "A$", code: "AUD", name: "Australian Dollar", rateMultiplier: 1.52 },
  "USA": { symbol: "$", code: "USD", name: "US Dollar", rateMultiplier: 1.0 },
  "United States": { symbol: "$", code: "USD", name: "US Dollar", rateMultiplier: 1.0 },
  "China": { symbol: "¥", code: "CNY", name: "Chinese Yuan", rateMultiplier: 7.23 },
  "Singapore": { symbol: "S$", code: "SGD", name: "Singapore Dollar", rateMultiplier: 1.34 },
  "South Africa": { symbol: "R", code: "ZAR", name: "South African Rand", rateMultiplier: 18.2 },
  "Indonesia": { symbol: "Rp", code: "IDR", name: "Indonesian Rupiah", rateMultiplier: 15800.0 },
  "Japan": { symbol: "¥", code: "JPY", name: "Japanese Yen", rateMultiplier: 155.0 },
  "Brazil": { symbol: "R$", code: "BRL", name: "Brazilian Real", rateMultiplier: 5.65 },
  "Germany": { symbol: "€", code: "EUR", name: "Euro", rateMultiplier: 0.92 },
  "France": { symbol: "€", code: "EUR", name: "Euro", rateMultiplier: 0.92 },
  "Netherlands": { symbol: "€", code: "EUR", name: "Euro", rateMultiplier: 0.92 },
  "Europe": { symbol: "€", code: "EUR", name: "Euro", rateMultiplier: 0.92 },
  "UK": { symbol: "£", code: "GBP", name: "British Pound", rateMultiplier: 0.78 },
  "United Kingdom": { symbol: "£", code: "GBP", name: "British Pound", rateMultiplier: 0.78 },
  "UAE": { symbol: "AED", code: "AED", name: "UAE Dirham", rateMultiplier: 3.67 },
  "Qatar": { symbol: "QAR", code: "QAR", name: "Qatari Riyal", rateMultiplier: 3.64 }
};

function getCurrencyInfo(countryOrPort) {
  if (!countryOrPort) return COUNTRY_CURRENCY_MAP["India"];
  
  const key = String(countryOrPort).trim();
  if (COUNTRY_CURRENCY_MAP[key]) return COUNTRY_CURRENCY_MAP[key];
  
  for (const c in COUNTRY_CURRENCY_MAP) {
    if (key.toLowerCase().includes(c.toLowerCase()) || c.toLowerCase().includes(key.toLowerCase())) {
      return COUNTRY_CURRENCY_MAP[c];
    }
  }
  
  return { symbol: "$", code: "USD", name: "US Dollar", rateMultiplier: 1.0 };
}

/**
 * Formats rate or cost string with dynamic currency symbol & unit via CurrencyService.
 */
function formatCurrencyValue(usdAmount, countryOrPort, isPerTonne = false) {
  if (typeof CurrencyService !== "undefined") {
    const code = CurrencyService.getActiveCurrency ? CurrencyService.getActiveCurrency() : "INR";
    if (isPerTonne) {
      return CurrencyService.formatRate(usdAmount, code);
    } else {
      return CurrencyService.formatCost(usdAmount, code);
    }
  }
  const curr = getCurrencyInfo(countryOrPort);
  const val = usdAmount * curr.rateMultiplier;
  return `${curr.symbol}${val.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
}

const DEFAULT_TRADING_COUNTRIES = [
  "Australia", "India", "USA", "South Africa", "Brazil", "Indonesia",
  "China", "Germany", "Netherlands", "Singapore", "UAE", "UK", "Canada", "Qatar", "Saudi Arabia"
];

const DEFAULT_GLOBAL_PORTS = [
  { port_name: "Newcastle", country: "Australia", max_draft: 15.2 },
  { port_name: "Hay Point", country: "Australia", max_draft: 17.5 },
  { port_name: "Gladstone", country: "Australia", max_draft: 16.0 },
  { port_name: "Port Hedland", country: "Australia", max_draft: 19.5 },
  { port_name: "Fremantle", country: "Australia", max_draft: 13.5 },
  { port_name: "Paradip", country: "India", max_draft: 14.5 },
  { port_name: "Vizag", country: "India", max_draft: 16.5 },
  { port_name: "Gangavaram", country: "India", max_draft: 16.0 },
  { port_name: "Gopalpur", country: "India", max_draft: 13.0 },
  { port_name: "Dhamra", country: "India", max_draft: 18.0 },
  { port_name: "Sagar-Sandheads", country: "India", max_draft: 15.5 },
  { port_name: "Haldia", country: "India", max_draft: 8.5 },
  { port_name: "Qingdao", country: "China", max_draft: 20.0 },
  { port_name: "Shanghai", country: "China", max_draft: 16.0 },
  { port_name: "Ningbo-Zhoushan", country: "China", max_draft: 22.0 },
  { port_name: "Richards Bay", country: "South Africa", max_draft: 17.5 },
  { port_name: "Durban", country: "South Africa", max_draft: 12.8 },
  { port_name: "Tubarao", country: "Brazil", max_draft: 23.0 },
  { port_name: "Santos", country: "Brazil", max_draft: 14.5 },
  { port_name: "Houston", country: "USA", max_draft: 14.0 },
  { port_name: "Baltimore", country: "USA", max_draft: 15.0 },
  { port_name: "Rotterdam", country: "Netherlands", max_draft: 24.0 },
  { port_name: "Hamburg", country: "Germany", max_draft: 15.0 },
  { port_name: "Singapore", country: "Singapore", max_draft: 18.0 },
  { port_name: "Jebel Ali", country: "UAE", max_draft: 16.0 }
];

async function initGlobalPortDropdowns(originId, destId, defaultOrigin = "Australia", defaultDest = "Paradip") {
  let ports = [];
  let countries = [];

  try {
    const [pResp, cResp] = await Promise.all([
      fetch('/api/ports').catch(() => null),
      fetch('/api/countries').catch(() => null)
    ]);

    if (pResp && pResp.ok) {
      const pData = await pResp.json();
      ports = Array.isArray(pData) ? pData : (pData.ports || pData.data || []);
    }
    if (cResp && cResp.ok) {
      const cData = await cResp.json();
      countries = Array.isArray(cData) ? cData : (cData.countries || cData.data || []);
    }
  } catch (err) {
    console.warn("Notice loading ports/countries API, using fallback defaults:", err);
  }

  // Normalize countries format
  if (!Array.isArray(countries) || countries.length === 0) {
    countries = DEFAULT_TRADING_COUNTRIES;
  } else {
    countries = countries.map(c => typeof c === 'string' ? c : (c.country || c.name || c.country_name || String(c))).filter(Boolean);
    if (countries.length === 0) countries = DEFAULT_TRADING_COUNTRIES;
  }

  // Normalize ports format
  if (!Array.isArray(ports) || ports.length === 0) {
    ports = DEFAULT_GLOBAL_PORTS;
  } else {
    ports = ports.map(p => {
      if (typeof p === 'string') return { port_name: p, country: "Global", max_draft: 15.0 };
      return {
        port_name: p.port_name || p.name || p.id || "Port",
        country: p.country || "Global",
        max_draft: p.max_draft || p.draft || 15.0
      };
    });
    if (ports.length === 0) ports = DEFAULT_GLOBAL_PORTS;
  }

  const origEl = document.getElementById(originId);
  const destEl = document.getElementById(destId);

  if (origEl) {
    let origHtml = '<optgroup label="🌍 Trading Countries">';
    const addedCountries = new Set();
    countries.forEach(c => {
      const cName = String(c).trim();
      if (!cName || addedCountries.has(cName)) return;
      addedCountries.add(cName);
      const curr = getCurrencyInfo(cName);
      const sel = cName.toLowerCase() === defaultOrigin.toLowerCase() ? 'selected' : '';
      origHtml += `<option value="${cName}" ${sel}>${cName} (${curr.symbol} ${curr.code})</option>`;
    });
    origHtml += '</optgroup><optgroup label="⚓ Specific Export Ports">';
    ports.forEach(p => {
      const curr = getCurrencyInfo(p.country);
      const sel = p.port_name.toLowerCase() === defaultOrigin.toLowerCase() ? 'selected' : '';
      origHtml += `<option value="${p.port_name}" ${sel}>${p.port_name} (${p.country} - ${curr.symbol})</option>`;
    });
    origHtml += '</optgroup>';
    origEl.innerHTML = origHtml;
  }

  if (destEl) {
    let destHtml = '';
    const grouped = {};
    ports.forEach(p => {
      const cName = p.country || "Global";
      if (!grouped[cName]) grouped[cName] = [];
      grouped[cName].push(p);
    });

    for (const country in grouped) {
      const curr = getCurrencyInfo(country);
      destHtml += `<optgroup label="📍 ${country} (${curr.symbol} ${curr.code})">`;
      grouped[country].forEach(p => {
        const sel = p.port_name.toLowerCase() === defaultDest.toLowerCase() ? 'selected' : '';
        destHtml += `<option value="${p.port_name}" ${sel}>${p.port_name} (Max Draft ${p.max_draft}m)</option>`;
      });
      destHtml += `</optgroup>`;
    }
    destEl.innerHTML = destHtml;
  }
}
