/**
 * SmartVessel AI — Flipkart/Amazon-Style Sequential Transaction Workflow Engine
 * Manages 8-step transaction flow, state invalidation, Step X of 8 headers,
 * active completion badges, and Back/Continue transaction footers.
 */

const SmartVesselWorkflow = {
  SESSION_KEY: 'svai_guided_session',

  // 8 Sequential Transaction Steps
  STEPS: [
    { id: 1, title: 'CARGO DETAILS', name: 'Cargo Details', desc: 'Enter bulk cargo shipment requirement to begin analysis.', page: 'index.html', icon: 'fa-pen-to-square' },
    { id: 2, title: 'FREIGHT FORECAST', name: 'Freight Forecast', desc: 'Analyze AI multi-horizon freight rate predictions.', page: 'forecast.html', icon: 'fa-chart-line' },
    { id: 3, title: 'VESSEL SELECTION', name: 'Vessel Selection', desc: 'Select carrier fleet matched to cargo tonnage and route.', page: 'vessels.html', icon: 'fa-ship' },
    { id: 4, title: 'PORT COMPATIBILITY', name: 'Port Compatibility', desc: 'Validate draft, LOA, and beam clearance at discharge port.', page: 'ports.html', icon: 'fa-anchor' },
    { id: 5, name: 'Voyage Cost', title: 'VOYAGE COST', desc: 'Calculate total landed voyage costs and pro-forma invoice.', page: 'billing.html', icon: 'fa-file-invoice-dollar' },
    { id: 6, name: 'Risk Analysis', title: 'RISK ANALYSIS', desc: 'Evaluate weather, congestion, route, and delay risks.', page: 'risk.html', icon: 'fa-shield-halved' },
    { id: 7, name: 'Charter Strategy', title: 'CHARTER OPTIMIZATION', desc: 'Compare Spot vs Time Charter vs COA financial savings.', page: 'optimization.html', icon: 'fa-sliders' },
    { id: 8, name: 'Final Decision', title: 'FINAL CHARTERING DECISION', desc: 'Consolidated executive decision statement & order confirmation.', page: 'decision.html', icon: 'fa-trophy' }
  ],

  // Get active session
  getSession() {
    try {
      const data = localStorage.getItem(this.SESSION_KEY);
      if (data) return JSON.parse(data);
    } catch (e) {
      console.warn("Could not read workflow session:", e);
    }
    return null;
  },

  // Save session state
  saveSession(sessionData) {
    try {
      localStorage.setItem(this.SESSION_KEY, JSON.stringify(sessionData));
    } catch (e) {
      console.error("Failed to save workflow session:", e);
    }
  },

  // Create new transaction session
  createNewSession(inputData) {
    const randomSuffix = Math.floor(1000 + Math.random() * 9000);
    const session = {
      id: `SVAI-2026-${randomSuffix}`,
      createdAt: new Date().toISOString(),
      currentStep: 2,
      completedSteps: [1],
      cargo: {
        origin_country: inputData.origin_country || 'Australia',
        origin_port: inputData.origin_port || 'Newcastle',
        destination_port: inputData.destination_port || 'Paradip',
        cargo_type: inputData.cargo_type || 'Coking Coal',
        cargo_quantity_mt: parseFloat(inputData.cargo_quantity_mt) || 75000,
        vessel_type: inputData.vessel_type || 'Panamax',
        arrival_date: inputData.arrival_date || new Date(Date.now() + 14 * 86400000).toISOString().split('T')[0]
      },
      results: {}
    };
    this.saveSession(session);
    return session;
  },

  // Reset session
  resetSession() {
    localStorage.removeItem(this.SESSION_KEY);
    window.location.href = 'index.html';
  },

  // Invalidate downstream steps when user changes a selection (e.g. vessel type)
  invalidateDownstream(fromStepId) {
    let session = this.getSession();
    if (!session) return;
    session.completedSteps = session.completedSteps.filter(s => s < fromStepId);
    if (fromStepId <= 3) delete session.results.port;
    if (fromStepId <= 4) delete session.results.cost;
    if (fromStepId <= 5) delete session.results.risk;
    if (fromStepId <= 6) delete session.results.optimization;
    this.saveSession(session);
  },

  // Navigate Back (Flipkart checkout style)
  goBack(currentStepId) {
    if (currentStepId <= 1) {
      window.location.href = 'index.html';
      return;
    }
    const prevStep = this.STEPS.find(s => s.id === currentStepId - 1);
    if (prevStep) {
      window.location.href = prevStep.page;
    }
  },

  // Navigate Next (Flipkart checkout style)
  goNext(currentStepId, targetUrl) {
    let session = this.getSession();
    if (session) {
      if (!session.completedSteps.includes(currentStepId)) {
        session.completedSteps.push(currentStepId);
      }
      session.currentStep = currentStepId + 1;
      this.saveSession(session);
    }
    window.location.href = targetUrl;
  },

  // Render Transaction Header (TOP of every workflow page)
  renderTransactionHeader(activeStepId) {
    const session = this.getSession();
    const stepDef = this.STEPS.find(s => s.id === activeStepId) || this.STEPS[0];

    const sessionText = session
      ? `${session.cargo.origin_country} (${session.cargo.origin_port}) ➔ ${session.cargo.destination_port} | ${Number(session.cargo.cargo_quantity_mt).toLocaleString()} MT (${session.cargo.vessel_type})`
      : `Australia (Newcastle) ➔ Paradip Port | 75,000 MT (Panamax)`;

    const html = `
      <div class="transaction-step-header glass-card p-4 mb-4 rounded-3 border border-warning border-opacity-40 text-white shadow-lg bg-dark-navy">
        <div class="d-flex flex-wrap justify-content-between align-items-center mb-3">
          <div>
            <span class="badge bg-warning text-dark font-monospace fw-bold fs-8 mb-2">
              <i class="fa-solid fa-layer-group me-1"></i> STEP ${stepDef.id} OF 8 — ${stepDef.title}
            </span>
            <h3 class="fw-bold text-white mb-1">
              <i class="fa-solid ${stepDef.icon} text-warning me-2"></i> ${stepDef.title}
            </h3>
            <p class="fs-7 text-info mb-0 opacity-90">${stepDef.desc}</p>
          </div>
          <div class="mt-3 mt-md-0 text-md-end">
            <span class="badge bg-dark border border-secondary text-warning fs-7 font-monospace px-3 py-2 shadow-sm">
              <i class="fa-solid fa-box-open me-1"></i> ${sessionText}
            </span>
          </div>
        </div>

        <!-- Checkout Steps Progress Bar -->
        <div class="checkout-steps-bar d-flex flex-wrap align-items-center justify-content-between gap-1 pt-3 border-top border-secondary border-opacity-25">
          ${this.STEPS.map(step => {
            const isCurrent = step.id === activeStepId;
            const isCompleted = session && session.completedSteps && session.completedSteps.includes(step.id);
            let styleClass = "bg-secondary bg-opacity-25 text-muted";
            let statusIcon = `<i class="fa-regular fa-circle me-1"></i>`;

            if (isCurrent) {
              styleClass = "bg-warning text-dark fw-bold shadow border border-warning";
              statusIcon = `<i class="fa-solid fa-arrow-right-long me-1"></i>`;
            } else if (isCompleted) {
              styleClass = "bg-success bg-opacity-25 text-success border border-success border-opacity-50";
              statusIcon = `<i class="fa-solid fa-circle-check me-1"></i>`;
            }

            return `
              <a href="${step.page}" class="text-decoration-none flex-grow-1" style="min-width: 100px;">
                <div class="px-2 py-1 rounded-2 text-center fs-8 transition-all ${styleClass}">
                  ${statusIcon} ${step.name}
                </div>
              </a>
            `;
          }).join('')}
        </div>
      </div>
    `;

    const container = document.getElementById('workflow-progress-container') || document.querySelector('main.main-content-custom');
    if (container) {
      if (document.getElementById('workflow-progress-container')) {
        document.getElementById('workflow-progress-container').innerHTML = html;
      } else {
        const wrapper = document.createElement('div');
        wrapper.id = 'workflow-progress-container';
        wrapper.innerHTML = html;
        container.insertBefore(wrapper, container.firstChild);
      }
    }
  },

  // Render Transaction Footer (BOTTOM of every workflow page)
  renderTransactionFooter(activeStepId, backUrl, continueUrl, continueBtnText = "CONTINUE TO NEXT STEP →") {
    const prevStep = this.STEPS.find(s => s.id === activeStepId - 1);
    const resolvedBackUrl = backUrl || (prevStep ? prevStep.page : 'index.html');

    const html = `
      <div class="transaction-nav-footer glass-card p-3 mt-4 rounded-3 border border-secondary border-opacity-25 d-flex flex-wrap justify-content-between align-items-center bg-dark-navy shadow-lg">
        <div>
          <button onclick="SmartVesselWorkflow.goBack(${activeStepId})" class="btn btn-outline-light text-white px-4 fs-7 fw-bold">
            ← BACK ${prevStep ? `(${prevStep.name})` : ''}
          </button>
        </div>
        <div class="d-flex align-items-center gap-3">
          <div class="badge bg-success bg-opacity-25 text-success fs-7 border border-success border-opacity-50 px-3 py-2">
            <i class="fa-solid fa-check-double me-1"></i> STEP ${activeStepId} COMPLETED
          </div>
          ${continueUrl ? `
            <button onclick="SmartVesselWorkflow.goNext(${activeStepId}, '${continueUrl}')" class="btn btn-warning text-dark fw-bold px-4 py-2 fs-6 shadow">
              ${continueBtnText}
            </button>
          ` : ''}
        </div>
      </div>
    `;

    const container = document.getElementById('workflow-nav-footer-container') || document.querySelector('main.main-content-custom');
    if (container) {
      if (document.getElementById('workflow-nav-footer-container')) {
        document.getElementById('workflow-nav-footer-container').innerHTML = html;
      } else {
        const wrapper = document.createElement('div');
        wrapper.id = 'workflow-nav-footer-container';
        wrapper.innerHTML = html;
        container.appendChild(wrapper);
      }
    }
  },

  // Open Step 1 Cargo Input Modal
  openInputModal() {
    let modalEl = document.getElementById('modal-cargo-input');
    if (!modalEl) {
      const modalHtml = `
        <div class="modal fade" id="modal-cargo-input" tabindex="-1" aria-hidden="true">
          <div class="modal-dialog modal-dialog-centered modal-lg">
            <div class="modal-content bg-dark-navy text-white border border-info border-opacity-50">
              <div class="modal-header border-bottom border-secondary border-opacity-25">
                <h5 class="modal-title fw-bold text-warning">
                  <i class="fa-solid fa-pen-to-square me-2"></i> STEP 1 OF 8 — CARGO DETAILS
                </h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
              </div>
              <div class="modal-body p-4">
                <form id="form-guided-input" onsubmit="SmartVesselWorkflow.handleInputSubmit(event)">
                  <div class="row g-3">
                    <div class="col-md-6">
                      <label class="form-label fs-7 fw-bold text-info">Origin Country</label>
                      <select class="form-select bg-dark text-white border-secondary fs-7" id="input_origin_country" required>
                        <option value="Australia" selected>Australia</option>
                        <option value="Indonesia">Indonesia</option>
                        <option value="South Africa">South Africa</option>
                        <option value="Russia">Russia</option>
                        <option value="USA">USA</option>
                      </select>
                      <div class="fs-8 text-muted mt-1">Country of loading port terminal.</div>
                    </div>
                    <div class="col-md-6">
                      <label class="form-label fs-7 fw-bold text-info">Origin Port</label>
                      <select class="form-select bg-dark text-white border-secondary fs-7" id="input_origin_port">
                        <option value="Newcastle" selected>Newcastle (Australia)</option>
                        <option value="Hay Point">Hay Point (Australia)</option>
                        <option value="Gladstone">Gladstone (Australia)</option>
                        <option value="Samarinda">Samarinda (Indonesia)</option>
                        <option value="Richards Bay">Richards Bay (South Africa)</option>
                      </select>
                      <div class="fs-8 text-muted mt-1">Specific loading port terminal.</div>
                    </div>
                    <div class="col-md-6">
                      <label class="form-label fs-7 fw-bold text-info">Destination Port (East Coast India)</label>
                      <select class="form-select bg-dark text-white border-secondary fs-7" id="input_destination_port" required>
                        <option value="Paradip" selected>Paradip (Odisha)</option>
                        <option value="Vizag">Vizag (Andhra Pradesh)</option>
                        <option value="Haldia">Haldia (West Bengal)</option>
                        <option value="Gangavaram">Gangavaram (Andhra Pradesh)</option>
                        <option value="Dhamra">Dhamra (Odisha)</option>
                        <option value="Gopalpur">Gopalpur (Odisha)</option>
                      </select>
                      <div class="fs-8 text-muted mt-1">Select East Coast Indian discharge port.</div>
                    </div>
                    <div class="col-md-6">
                      <label class="form-label fs-7 fw-bold text-info">Cargo Commodity Type</label>
                      <select class="form-select bg-dark text-white border-secondary fs-7" id="input_cargo_type">
                        <option value="Coking Coal" selected>Coking Coal (Steel Plant Grade)</option>
                        <option value="Thermal Coal">Thermal Coal (Power Generation)</option>
                        <option value="Iron Ore">Iron Ore Fines / Pellets</option>
                        <option value="Bauxite">Bauxite / Limestone</option>
                      </select>
                      <div class="fs-8 text-muted mt-1">Select bulk cargo commodity.</div>
                    </div>
                    <div class="col-md-6">
                      <label class="form-label fs-7 fw-bold text-info">Cargo Quantity (Metric Tonnes)</label>
                      <input type="number" class="form-control bg-dark text-white border-secondary fs-7" id="input_cargo_quantity_mt" value="75000" min="1000" max="250000" step="500" required>
                      <div class="fs-8 text-muted mt-1">Enter total cargo tonnage requirement.</div>
                    </div>
                    <div class="col-md-6">
                      <label class="form-label fs-7 fw-bold text-info">Preferred Vessel Category</label>
                      <select class="form-select bg-dark text-white border-secondary fs-7" id="input_vessel_type">
                        <option value="Panamax" selected>Panamax (70,000 – 80,000 DWT)</option>
                        <option value="Supramax">Supramax (50,000 – 60,000 DWT)</option>
                        <option value="Handymax">Handymax (40,000 – 50,000 DWT)</option>
                        <option value="Capesize">Capesize (150,000+ DWT)</option>
                      </select>
                      <div class="fs-8 text-muted mt-1">Select carrier fleet size.</div>
                    </div>
                    <div class="col-12">
                      <label class="form-label fs-7 fw-bold text-info">Required Arrival / Delivery Date</label>
                      <input type="date" class="form-control bg-dark text-white border-secondary fs-7" id="input_arrival_date">
                      <div class="fs-8 text-muted mt-1">Target arrival window at destination port.</div>
                    </div>
                  </div>
                  <div class="mt-4 text-end">
                    <button type="button" class="btn btn-outline-light me-2 fs-7" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-warning text-dark fw-bold px-4 fs-7 shadow">
                      START FREIGHT ANALYSIS →
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      `;
      document.body.insertAdjacentHTML('beforeend', modalHtml);
      modalEl = document.getElementById('modal-cargo-input');
    }

    const session = this.getSession();
    if (session && session.cargo) {
      if (document.getElementById('input_origin_country')) document.getElementById('input_origin_country').value = session.cargo.origin_country;
      if (document.getElementById('input_origin_port')) document.getElementById('input_origin_port').value = session.cargo.origin_port;
      if (document.getElementById('input_destination_port')) document.getElementById('input_destination_port').value = session.cargo.destination_port;
      if (document.getElementById('input_cargo_type')) document.getElementById('input_cargo_type').value = session.cargo.cargo_type || 'Coking Coal';
      if (document.getElementById('input_cargo_quantity_mt')) document.getElementById('input_cargo_quantity_mt').value = session.cargo.cargo_quantity_mt;
      if (document.getElementById('input_vessel_type')) document.getElementById('input_vessel_type').value = session.cargo.vessel_type;
    }

    const dateInput = document.getElementById('input_arrival_date');
    if (dateInput && !dateInput.value) {
      dateInput.value = new Date(Date.now() + 14 * 86400000).toISOString().split('T')[0];
    }

    const modal = new bootstrap.Modal(modalEl);
    modal.show();
  },

  // Handle Input Form Submission
  handleInputSubmit(e) {
    e.preventDefault();
    const inputData = {
      origin_country: document.getElementById('input_origin_country').value,
      origin_port: document.getElementById('input_origin_port').value,
      destination_port: document.getElementById('input_destination_port').value,
      cargo_type: document.getElementById('input_cargo_type').value,
      cargo_quantity_mt: document.getElementById('input_cargo_quantity_mt').value,
      vessel_type: document.getElementById('input_vessel_type').value,
      arrival_date: document.getElementById('input_arrival_date').value
    };

    if (parseFloat(inputData.cargo_quantity_mt) <= 0) {
      alert("Cargo Quantity must be greater than 0 MT.");
      return;
    }

    this.createNewSession(inputData);
    
    const modalEl = document.getElementById('modal-cargo-input');
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) modal.hide();

    // Flipkart-style checkout: Proceed directly to Step 2
    window.location.href = 'forecast.html';
  }
};

window.SmartVesselWorkflow = SmartVesselWorkflow;

// Global Interactive Toast Notification System
window.showToast = function(message, type = 'success', duration = 3200) {
  let container = document.getElementById('smartvessel-toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'smartvessel-toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `sv-toast sv-toast-${type}`;
  
  let iconHtml = '<i class="fa-solid fa-circle-check"></i>';
  if (type === 'info') iconHtml = '<i class="fa-solid fa-circle-info"></i>';
  if (type === 'warning') iconHtml = '<i class="fa-solid fa-triangle-exclamation"></i>';
  if (type === 'danger') iconHtml = '<i class="fa-solid fa-circle-xmark"></i>';

  const now = new Date();
  const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  toast.innerHTML = `
    ${iconHtml}
    <div style="flex-grow:1;">
      <div style="line-height:1.25;">${message}</div>
      <small style="color:#64748b; font-size:0.72rem; font-weight:500;">Synchronized at ${timeStr}</small>
    </div>
  `;

  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('show'));

  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, duration);
};

// Global Interactive Button Refresh Handler with Spinner & Feedback
window.triggerButtonRefresh = async function(btn, actionFn, successMessage = "Data refreshed successfully") {
  if (!btn) {
    if (typeof actionFn === 'function') return await actionFn();
    return;
  }

  const icon = btn.querySelector('i');
  let originalIconClass = '';
  if (icon) {
    originalIconClass = icon.className;
    icon.className = 'fa-solid fa-spinner fa-spin me-1';
  }
  btn.classList.add('btn-refresh-loading');
  btn.disabled = true;

  try {
    if (typeof actionFn === 'function') {
      await actionFn();
    }
    if (icon) {
      icon.className = 'fa-solid fa-check text-success me-1';
    }
    window.showToast(successMessage, 'success');
  } catch (err) {
    console.error("Refresh execution error:", err);
    if (icon) {
      icon.className = 'fa-solid fa-triangle-exclamation text-warning me-1';
    }
    window.showToast("Refresh encountered an issue. Re-syncing...", 'warning');
  } finally {
    setTimeout(() => {
      if (icon) icon.className = originalIconClass;
      btn.classList.remove('btn-refresh-loading');
      btn.disabled = false;
    }, 1000);
  }
};

