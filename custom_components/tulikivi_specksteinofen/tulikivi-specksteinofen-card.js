/**
 * Tulikivi Specksteinofen Lovelace Card
 * Custom Card für Home Assistant zur eleganten Darstellung aller Ofen-Parameter.
 */

class TulikiviSpecksteinofenCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._historyData = null;
    this._lastHistoryFetch = 0;
  }

  static getStubConfig(hass, entities, entitiesFallback) {
    return {
      type: "custom:tulikivi-specksteinofen-card",
      title: "Tulikivi Specksteinofen",
      entity: "sensor.tulikivi_specksteinofen_betriebsstatus",
      flue_sensor: "sensor.tulikivi_specksteinofen_rauchrohr_temperatur",
      stone_sensor: "sensor.tulikivi_specksteinofen_speckstein_temperatur",
      storage_pct_sensor: "sensor.tulikivi_specksteinofen_speicherladung",
      stored_heat_sensor: "sensor.tulikivi_specksteinofen_gespeicherte_warme",
      max_heat_sensor: "sensor.tulikivi_specksteinofen_max_speicherkapazitat",
      remaining_hours_sensor: "sensor.tulikivi_specksteinofen_restwarmedauer",
      auto_learn_switch: "switch.tulikivi_specksteinofen_automatisches_lernen_auto_learn",
      max_temp_number: "number.tulikivi_specksteinofen_maximale_speichertemperatur"
    };
  }

  static getConfigForm() {
    return {
      schema: [
        { name: "title", label: "Titel (optional)", selector: { text: {} } },
        { name: "entity", label: "Betriebsstatus Sensor", selector: { entity: { domain: "sensor" } } },
        { name: "flue_sensor", label: "Rauchgas Temperatur Sensor", selector: { entity: { domain: "sensor" } } },
        { name: "stone_sensor", label: "Speckstein Temperatur Sensor", selector: { entity: { domain: "sensor" } } },
        { name: "storage_pct_sensor", label: "Speicherladung (%) Sensor", selector: { entity: { domain: "sensor" } } },
        { name: "stored_heat_sensor", label: "Gespeicherte Wärme (kWh) Sensor", selector: { entity: { domain: "sensor" } } },
        { name: "max_heat_sensor", label: "Max. Speicherkapazität Sensor", selector: { entity: { domain: "sensor" } } },
        { name: "remaining_hours_sensor", label: "Restwärmedauer Sensor", selector: { entity: { domain: "sensor" } } },
        { name: "auto_learn_switch", label: "Auto-Learn Schalter", selector: { entity: { domain: "switch" } } },
        { name: "max_temp_number", label: "Maximale Speichertemperatur Einstellung", selector: { entity: { domain: "number" } } }
      ]
    };
  }

  setConfig(config) {
    this._config = {
      title: "Tulikivi Specksteinofen",
      entity: "sensor.tulikivi_specksteinofen_betriebsstatus",
      flue_sensor: "sensor.tulikivi_specksteinofen_rauchrohr_temperatur",
      stone_sensor: "sensor.tulikivi_specksteinofen_speckstein_temperatur",
      storage_pct_sensor: "sensor.tulikivi_specksteinofen_speicherladung",
      stored_heat_sensor: "sensor.tulikivi_specksteinofen_gespeicherte_warme",
      max_heat_sensor: "sensor.tulikivi_specksteinofen_max_speicherkapazitat",
      remaining_hours_sensor: "sensor.tulikivi_specksteinofen_restwarmedauer",
      auto_learn_switch: "switch.tulikivi_specksteinofen_automatisches_lernen_auto_learn",
      max_temp_number: "number.tulikivi_specksteinofen_maximale_speichertemperatur",
      ...config
    };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._updateState();
  }

  _getState(entityId, defaultVal = "--") {
    if (!this._hass || !this._hass.states[entityId]) return defaultVal;
    return this._hass.states[entityId].state;
  }

  _getFloat(entityId, defaultVal = 0) {
    const val = parseFloat(this._getState(entityId, defaultVal));
    return isNaN(val) ? defaultVal : val;
  }

  async _fetchHistory() {
    if (!this._hass || !this._config) return;
    const now = Date.now();
    if (now - this._lastHistoryFetch < 60000 && this._historyData) return;
    this._lastHistoryFetch = now;

    const startTime = new Date(now - 24 * 3600 * 1000).toISOString();
    const entities = [this._config.flue_sensor, this._config.stone_sensor].filter(Boolean);

    try {
      const history = await this._hass.callWS({
        type: "history/history_during_period",
        start_time: startTime,
        entity_ids: entities,
        significant_changes_only: false,
        minimal_response: true
      });
      this._historyData = history;
      this._renderChart();
    } catch (e) {
      // Fallback if history query fails
    }
  }

  _render() {
    if (!this.shadowRoot) return;
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
        }
        ha-card {
          padding: 16px;
          background: var(--card-background-color, #1c1c1e);
          color: var(--primary-text-color, #ffffff);
          border-radius: var(--ha-card-border-radius, 12px);
          box-shadow: var(--ha-card-box-shadow, none);
          font-family: var(--paper-font-body1_-_font-family, sans-serif);
          overflow: hidden;
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 14px;
        }
        .title-group {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .icon-fireplace {
          --mdc-icon-size: 28px;
          color: #ff9800;
        }
        .title {
          font-size: 1.15rem;
          font-weight: 600;
          letter-spacing: 0.2px;
        }
        .status-pill {
          padding: 4px 12px;
          border-radius: 16px;
          font-size: 0.85rem;
          font-weight: 600;
          display: inline-flex;
          align-items: center;
          gap: 6px;
          transition: all 0.3s ease;
        }
        .status-kalt { background: rgba(144, 164, 174, 0.2); color: #90a4ae; }
        .status-anheizen { background: rgba(255, 193, 7, 0.2); color: #ffc107; }
        .status-abbrand { background: rgba(255, 112, 67, 0.25); color: #ff7043; }
        .status-glut {
          background: rgba(239, 83, 80, 0.25);
          color: #ef5350;
          animation: pulse 1.5s infinite;
        }
        .status-abgabe { background: rgba(102, 187, 106, 0.2); color: #66bb6a; }

        @keyframes pulse {
          0% { box-shadow: 0 0 0 0 rgba(239, 83, 80, 0.5); }
          70% { box-shadow: 0 0 0 8px rgba(239, 83, 80, 0); }
          100% { box-shadow: 0 0 0 0 rgba(239, 83, 80, 0); }
        }

        .alert-banner {
          background: rgba(239, 83, 80, 0.18);
          border: 1px solid rgba(239, 83, 80, 0.4);
          border-radius: 8px;
          padding: 10px 14px;
          margin-bottom: 14px;
          display: flex;
          align-items: center;
          gap: 10px;
          font-size: 0.88rem;
          color: #ff8a80;
          font-weight: 500;
        }

        /* Tachos / Gauges */
        .gauges-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
          margin-bottom: 14px;
        }
        .gauge-card {
          background: rgba(255, 255, 255, 0.04);
          border-radius: 10px;
          padding: 12px 10px;
          text-align: center;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          position: relative;
        }
        .circle-svg {
          width: 110px;
          height: 110px;
          transform: rotate(-90deg);
        }
        .circle-bg {
          fill: none;
          stroke: rgba(255, 255, 255, 0.1);
          stroke-width: 8;
        }
        .circle-progress {
          fill: none;
          stroke-width: 8;
          stroke-linecap: round;
          transition: stroke-dashoffset 0.8s ease, stroke 0.4s ease;
        }
        .gauge-inner {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          display: flex;
          flex-direction: column;
          align-items: center;
        }
        .gauge-val {
          font-size: 1.35rem;
          font-weight: 700;
          line-height: 1.1;
        }
        .gauge-unit {
          font-size: 0.75rem;
          opacity: 0.7;
        }
        .gauge-title {
          margin-top: 6px;
          font-size: 0.8rem;
          font-weight: 500;
          color: var(--secondary-text-color, #aaa);
        }

        /* Metrics Grid */
        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 8px;
          margin-bottom: 14px;
        }
        @media (max-width: 480px) {
          .metrics-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }
        .metric-box {
          background: rgba(255, 255, 255, 0.03);
          border-radius: 8px;
          padding: 8px 10px;
          display: flex;
          flex-direction: column;
          gap: 2px;
          cursor: pointer;
          transition: background 0.2s;
        }
        .metric-box:hover {
          background: rgba(255, 255, 255, 0.07);
        }
        .metric-header {
          display: flex;
          align-items: center;
          gap: 5px;
          font-size: 0.75rem;
          color: var(--secondary-text-color, #aaa);
        }
        .metric-header ha-icon {
          --mdc-icon-size: 15px;
        }
        .metric-value {
          font-size: 1.1rem;
          font-weight: 600;
        }

        /* 24h Graph Section */
        .chart-section {
          background: rgba(255, 255, 255, 0.02);
          border-radius: 8px;
          padding: 10px;
          margin-bottom: 14px;
        }
        .chart-header {
          display: flex;
          justify-content: space-between;
          font-size: 0.8rem;
          color: var(--secondary-text-color, #aaa);
          margin-bottom: 6px;
        }
        .chart-legend {
          display: flex;
          gap: 12px;
        }
        .legend-item {
          display: flex;
          align-items: center;
          gap: 5px;
        }
        .legend-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }
        .chart-svg {
          width: 100%;
          height: 90px;
          overflow: visible;
        }

        /* Controls Footer */
        .controls-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: rgba(255, 255, 255, 0.03);
          border-radius: 8px;
          padding: 8px 14px;
          font-size: 0.85rem;
        }
        .control-item {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .btn-toggle {
          background: rgba(255, 255, 255, 0.1);
          border: none;
          color: inherit;
          padding: 4px 10px;
          border-radius: 6px;
          cursor: pointer;
          font-size: 0.8rem;
          font-weight: 600;
          transition: background 0.2s;
        }
        .btn-toggle.active {
          background: #ff9800;
          color: #000;
        }
      </style>
      <ha-card>
        <div class="header">
          <div class="title-group">
            <ha-icon icon="mdi:fireplace" class="icon-fireplace"></ha-icon>
            <span class="title">${this._config.title || "Tulikivi Specksteinofen"}</span>
          </div>
          <div id="status-pill" class="status-pill status-kalt">
            <span id="status-text">Laden...</span>
          </div>
        </div>

        <div id="alert-banner" class="alert-banner" style="display: none;">
          <ha-icon icon="mdi:alert-decagram" style="--mdc-icon-size: 20px;"></ha-icon>
          <span><strong>Glutphase:</strong> Luftklappe schließen, um Wärme im Stein zu halten!</span>
        </div>

        <div class="gauges-row">
          <!-- Speicherladung Gauge -->
          <div class="gauge-card">
            <svg class="circle-svg" viewBox="0 0 100 100">
              <circle class="circle-bg" cx="50" cy="50" r="42" />
              <circle id="progress-storage" class="circle-progress" cx="50" cy="50" r="42"
                      stroke="#42a5f5" stroke-dasharray="263.89" stroke-dashoffset="263.89" />
            </svg>
            <div class="gauge-inner">
              <span id="storage-val" class="gauge-val">0</span>
              <span class="gauge-unit">% Ladung</span>
            </div>
            <span class="gauge-title">Wärmespeicher</span>
          </div>

          <!-- Wärmemenge Gauge -->
          <div class="gauge-card">
            <svg class="circle-svg" viewBox="0 0 100 100">
              <circle class="circle-bg" cx="50" cy="50" r="42" />
              <circle id="progress-kwh" class="circle-progress" cx="50" cy="50" r="42"
                      stroke="#66bb6a" stroke-dasharray="263.89" stroke-dashoffset="263.89" />
            </svg>
            <div class="gauge-inner">
              <span id="kwh-val" class="gauge-val">0.0</span>
              <span class="gauge-unit">kWh Wärme</span>
            </div>
            <span class="gauge-title">Gespeichert</span>
          </div>
        </div>

        <!-- 4 Kennzahlen -->
        <div class="metrics-grid">
          <div class="metric-box" id="box-flue">
            <div class="metric-header">
              <ha-icon icon="mdi:fire" style="color: #ff7043;"></ha-icon>
              <span>Rauchrohr</span>
            </div>
            <div class="metric-value" id="val-flue">-- °C</div>
          </div>
          <div class="metric-box" id="box-stone">
            <div class="metric-header">
              <ha-icon icon="mdi:radiator" style="color: #ffa726;"></ha-icon>
              <span>Speckstein</span>
            </div>
            <div class="metric-value" id="val-stone">-- °C</div>
          </div>
          <div class="metric-box" id="box-remaining">
            <div class="metric-header">
              <ha-icon icon="mdi:timer-sand" style="color: #26a69a;"></ha-icon>
              <span>Restwärme</span>
            </div>
            <div class="metric-value" id="val-remaining">-- Std.</div>
          </div>
          <div class="metric-box" id="box-maxtemp">
            <div class="metric-header">
              <ha-icon icon="mdi:thermometer-chevron-up" style="color: #ab47bc;"></ha-icon>
              <span>100% Stein</span>
            </div>
            <div class="metric-value" id="val-maxtemp">-- °C</div>
          </div>
        </div>

        <!-- 24h Graph -->
        <div class="chart-section">
          <div class="chart-header">
            <span>24h Verlauf (Phasenverschiebung)</span>
            <div class="chart-legend">
              <div class="legend-item">
                <span class="legend-dot" style="background: #ff5722;"></span>
                <span>Rauchgas</span>
              </div>
              <div class="legend-item">
                <span class="legend-dot" style="background: #ffa726;"></span>
                <span>Speckstein</span>
              </div>
            </div>
          </div>
          <svg id="chart-svg" class="chart-svg" preserveAspectRatio="none" viewBox="0 0 300 80">
            <path id="chart-flue" fill="none" stroke="#ff5722" stroke-width="2" opacity="0.85" />
            <path id="chart-stone" fill="none" stroke="#ffa726" stroke-width="2.5" />
          </svg>
        </div>

        <!-- Footer: Auto-Learn Schalter & 100% Kalibrierung -->
        <div class="controls-footer">
          <div class="control-item">
            <ha-icon icon="mdi:school" style="--mdc-icon-size: 18px; color: #ffb74d;"></ha-icon>
            <span>Auto-Learn:</span>
            <button id="btn-autolearn" class="btn-toggle">Aus</button>
          </div>
          <div class="control-item" id="item-maxtemp">
            <ha-icon icon="mdi:tune-vertical" style="--mdc-icon-size: 18px; color: #aaa;"></ha-icon>
            <span id="footer-maxtemp">Max: -- °C</span>
          </div>
        </div>
      </ha-card>
    `;

    // Click handlers for more-info dialogs
    const bindMoreInfo = (elemId, entityId) => {
      const el = this.shadowRoot.getElementById(elemId);
      if (el) {
        el.addEventListener("click", () => {
          const event = new Event("hass-more-info", { bubbles: true, composed: true });
          event.detail = { entityId };
          this.dispatchEvent(event);
        });
      }
    };

    bindMoreInfo("box-flue", this._config.flue_sensor);
    bindMoreInfo("box-stone", this._config.stone_sensor);
    bindMoreInfo("box-remaining", this._config.remaining_hours_sensor);
    bindMoreInfo("box-maxtemp", this._config.max_temp_number);
    bindMoreInfo("item-maxtemp", this._config.max_temp_number);

    // Auto-Learn Toggle button
    const btnAuto = this.shadowRoot.getElementById("btn-autolearn");
    if (btnAuto) {
      btnAuto.addEventListener("click", () => {
        if (!this._hass || !this._config.auto_learn_switch) return;
        this._hass.callService("switch", "toggle", {
          entity_id: this._config.auto_learn_switch
        });
      });
    }

    this._updateState();
  }

  _updateState() {
    if (!this.shadowRoot || !this._hass || !this._config) return;

    const status = this._getState(this._config.entity, "Kalt / Aus");
    const flueTemp = this._getFloat(this._config.flue_sensor, 0);
    const stoneTemp = this._getFloat(this._config.stone_sensor, 0);
    const storagePct = this._getFloat(this._config.storage_pct_sensor, 0);
    const storedKwh = this._getFloat(this._config.stored_heat_sensor, 0);
    const maxKwh = this._getFloat(this._config.max_heat_sensor, 10);
    const remainingH = this._getFloat(this._config.remaining_hours_sensor, 0);
    const maxTemp = this._getFloat(this._config.max_temp_number, 65);
    const autoLearnState = this._getState(this._config.auto_learn_switch, "off");

    // Status Pill
    const pill = this.shadowRoot.getElementById("status-pill");
    const statusText = this.shadowRoot.getElementById("status-text");
    const banner = this.shadowRoot.getElementById("alert-banner");

    if (pill && statusText) {
      statusText.textContent = status;
      pill.className = "status-pill";
      if (status.includes("Glutphase")) {
        pill.classList.add("status-glut");
        if (banner) banner.style.display = "flex";
      } else {
        if (banner) banner.style.display = "none";
        if (status === "Voller Abbrand") pill.classList.add("status-abbrand");
        else if (status === "Anheizen") pill.classList.add("status-anheizen");
        else if (status.includes("Wärmeabgabe")) pill.classList.add("status-abgabe");
        else pill.classList.add("status-kalt");
      }
    }

    // Storage Gauge
    const valStorage = this.shadowRoot.getElementById("storage-val");
    const progStorage = this.shadowRoot.getElementById("progress-storage");
    if (valStorage && progStorage) {
      valStorage.textContent = Math.round(storagePct);
      const circumference = 2 * Math.PI * 42; // ~263.89
      const capped = Math.min(Math.max(storagePct, 0), 120);
      const offset = circumference - (capped / 100) * circumference;
      progStorage.style.strokeDashoffset = Math.max(0, offset);

      if (storagePct > 100) progStorage.style.stroke = "#ef5350";
      else if (storagePct >= 80) progStorage.style.stroke = "#ffa726";
      else if (storagePct >= 45) progStorage.style.stroke = "#66bb6a";
      else if (storagePct >= 20) progStorage.style.stroke = "#42a5f5";
      else progStorage.style.stroke = "#90a4ae";
    }

    // kWh Gauge
    const valKwh = this.shadowRoot.getElementById("kwh-val");
    const progKwh = this.shadowRoot.getElementById("progress-kwh");
    if (valKwh && progKwh) {
      valKwh.textContent = storedKwh.toFixed(1);
      const circumference = 2 * Math.PI * 42;
      const refMax = maxKwh > 0 ? maxKwh : 10;
      const ratio = Math.min(Math.max(storedKwh / refMax, 0), 1.2);
      progKwh.style.strokeDashoffset = Math.max(0, circumference - ratio * circumference);
    }

    // Metric Values
    const vFlue = this.shadowRoot.getElementById("val-flue");
    const vStone = this.shadowRoot.getElementById("val-stone");
    const vRemaining = this.shadowRoot.getElementById("val-remaining");
    const vMaxTemp = this.shadowRoot.getElementById("val-maxtemp");

    if (vFlue) vFlue.textContent = `${flueTemp.toFixed(1)} °C`;
    if (vStone) vStone.textContent = `${stoneTemp.toFixed(1)} °C`;
    if (vRemaining) vRemaining.textContent = `${remainingH.toFixed(1)} h`;
    if (vMaxTemp) vMaxTemp.textContent = `${maxTemp.toFixed(0)} °C`;

    // Controls
    const btnAuto = this.shadowRoot.getElementById("btn-autolearn");
    if (btnAuto) {
      const isOn = autoLearnState === "on";
      btnAuto.textContent = isOn ? "Aktiv (Ein)" : "Festgesetzt (Aus)";
      btnAuto.className = `btn-toggle ${isOn ? "active" : ""}`;
    }
    const footerMax = this.shadowRoot.getElementById("footer-maxtemp");
    if (footerMax) {
      footerMax.textContent = `100% Grenze: ${maxTemp.toFixed(1)} °C`;
    }

    this._fetchHistory();
  }

  _renderChart() {
    if (!this._historyData || !this.shadowRoot) return;

    const flueHistory = this._historyData[this._config.flue_sensor] || [];
    const stoneHistory = this._historyData[this._config.stone_sensor] || [];

    const pFlue = this.shadowRoot.getElementById("chart-flue");
    const pStone = this.shadowRoot.getElementById("chart-stone");
    if (!pFlue || !pStone) return;

    const parsePoints = (history) => {
      return history
        .map((item) => {
          const val = parseFloat(item.s);
          const time = new Date(item.lu * 1000).getTime();
          return isNaN(val) ? null : { time, val };
        })
        .filter(Boolean);
    };

    const ptsFlue = parsePoints(flueHistory);
    const ptsStone = parsePoints(stoneHistory);

    if (ptsFlue.length < 2 && ptsStone.length < 2) return;

    const now = Date.now();
    const tMin = now - 24 * 3600 * 1000;
    const tMax = now;

    // Normalizing paths to SVG coordinates (width: 300, height: 80)
    const buildPath = (pts, maxVal, minVal = 0) => {
      if (pts.length < 2) return "";
      const rangeVal = Math.max(maxVal - minVal, 1);
      return pts
        .map((p, idx) => {
          const x = ((p.time - tMin) / (tMax - tMin)) * 300;
          const y = 80 - ((p.val - minVal) / rangeVal) * 75 - 2;
          return `${idx === 0 ? "M" : "L"} ${x.toFixed(1)},${y.toFixed(1)}`;
        })
        .join(" ");
    };

    // Rauchrohr scale (0 to 300°C typical max)
    const flueMax = Math.max(150, ...ptsFlue.map((p) => p.val));
    pFlue.setAttribute("d", buildPath(ptsFlue, flueMax, 0));

    // Speckstein scale (15 to ~80°C typical range)
    const stoneMax = Math.max(50, ...ptsStone.map((p) => p.val));
    const stoneMin = Math.min(20, ...ptsStone.map((p) => p.val));
    pStone.setAttribute("d", buildPath(ptsStone, stoneMax, stoneMin));
  }
}

customElements.define("tulikivi-specksteinofen-card", TulikiviSpecksteinofenCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "tulikivi-specksteinofen-card",
  name: "Tulikivi Specksteinofen",
  description: "Elegante Übersichtskarte für den Tulikivi Specksteinofen mit Status, Tachos, Live-Werten und 24h-Kurve.",
  preview: true,
  documentationURL: "https://github.com/romanmartens86/Tulikivi_Specksteinofen"
});

console.info(
  "%c TULIKIVI-SPECKSTEINOFEN-CARD %c v1.3.0 geladen ",
  "color: white; background: #ff9800; font-weight: 700; border-radius: 3px 0 0 3px;",
  "color: #ff9800; background: #263238; font-weight: 700; border-radius: 0 3px 3px 0;"
);
