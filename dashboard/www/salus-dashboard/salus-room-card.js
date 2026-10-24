/* SALUS Room Card 1.0.0 — MIT License. No external frontend dependencies. */
class SalusRoomCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._pending = null;
    this._inFlight = false;
    this._error = "";
    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; height:100%; }
        * { box-sizing:border-box; }
        ha-card { display:block; height:100%; padding:20px; border-radius:22px;
          background:var(--ha-card-background,var(--card-background-color,#1c2023));
          color:var(--primary-text-color,#f1f2f2); border:1px solid var(--divider-color,#303639);
          box-shadow:none; font-family:var(--paper-font-body1_-_font-family,Roboto,sans-serif); }
        header { display:flex; align-items:center; gap:10px; margin-bottom:22px; }
        header ha-icon { --mdc-icon-size:20px; color:var(--secondary-text-color); }
        h2 { font-size:16px; font-weight:500; margin:0; line-height:1.3; }
        .metrics { display:grid; grid-template-columns:1.2fr 1fr; gap:12px; align-items:end; margin-bottom:22px; }
        .label { font-size:12px; color:var(--secondary-text-color,#a8b0b5); margin-bottom:5px; }
        .actual { font-size:42px; line-height:1.1; letter-spacing:-1.8px; font-variant-numeric:tabular-nums; }
        .unit { font-size:17px; color:var(--secondary-text-color); margin-left:3px; letter-spacing:0; }
        .humidity { border-left:1px solid var(--divider-color,#303639); padding-left:16px; }
        .moisture { display:flex; align-items:center; gap:4px; font-size:25px; line-height:1.4; font-variant-numeric:tabular-nums; }
        .moisture ha-icon { --mdc-icon-size:16px; color:var(--info-color,#72cbea); }
        .percent { font-size:15px; color:var(--secondary-text-color); }
        button { font:inherit; color:inherit; touch-action:manipulation; }
        button:focus-visible { outline:3px solid var(--primary-color,#72cbea); outline-offset:2px; }
        button:disabled { opacity:.4; }
        .stepper { display:flex; align-items:center; justify-content:space-between; padding:2px; min-height:48px;
          border-radius:12px; background:var(--secondary-background-color,#252b2e); }
        .step { background:transparent; border:0; min-width:44px; height:44px; font-size:23px; border-radius:10px; }
        .step:hover:enabled { background:var(--ha-card-background,var(--card-background-color)); }
        .target { font-size:19px; font-weight:500; font-variant-numeric:tabular-nums; }
        .target .unit { font-size:13px; font-weight:400; }
        .floor { margin-top:18px; border-top:1px solid var(--divider-color,#303639); padding-top:15px; }
        .floor-head { display:flex; align-items:center; justify-content:space-between; gap:8px; margin-bottom:10px; }
        .floor-label { display:flex; align-items:center; gap:7px; font-size:12px; color:var(--secondary-text-color); }
        .floor-label ha-icon { --mdc-icon-size:17px; }
        .floor-state { font-size:12px; font-weight:500; }
        .floor[data-active="true"] .floor-state { color:var(--salus-comfort-text,var(--warning-color,#d18a45)); }
        .levels { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:4px; padding:4px;
          border-radius:12px; background:var(--secondary-background-color,#252b2e); }
        .level { border:0; background:transparent; border-radius:9px; min-height:42px; min-width:0; font-size:13px; }
        .level[aria-pressed="true"] { background:var(--salus-comfort-color,#edaa70); color:var(--salus-comfort-contrast,#241a12); font-weight:500; }
        .level[data-level="0"][aria-pressed="true"] { background:var(--ha-card-background,var(--card-background-color)); color:var(--primary-text-color); }
        .status { font-size:12px; color:var(--secondary-text-color); margin-top:12px; overflow-wrap:anywhere; }
        .error { font-size:12px; color:var(--error-color,#db6060); margin-top:12px; overflow-wrap:anywhere; }
        [hidden] { display:none !important; }
      </style>
      <ha-card>
        <header><ha-icon id="icon"></ha-icon><h2 id="name"></h2></header>
        <div class="metrics">
          <div><div class="label">Temperatur</div><div class="actual"><span id="actual">—</span><span class="unit" id="actual-unit">°C</span></div></div>
          <div class="humidity"><div class="label">Luftfugtighed</div><div class="moisture"><ha-icon icon="mdi:water-percent"></ha-icon><span id="humidity">—</span><span class="percent">%</span></div></div>
        </div>
        <div class="label">Ønsket temperatur</div>
        <div class="stepper" role="group" aria-label="Ønsket temperatur">
          <button class="step" id="minus" type="button" aria-label="Sænk ønsket temperatur">−</button>
          <div class="target"><span id="target">—</span><span class="unit" id="target-unit">°C</span></div>
          <button class="step" id="plus" type="button" aria-label="Hæv ønsket temperatur">+</button>
        </div>
        <div class="floor" id="floor">
          <div class="floor-head"><span class="floor-label"><ha-icon icon="mdi:heating-coil"></ha-icon>Gulvkomfort</span><span id="floor-state" class="floor-state">—</span></div>
          <div class="levels" role="group" aria-label="Gulvkomfort">
            <button class="level" type="button" data-level="0" aria-label="Gulvkomfort fra" aria-pressed="false">Fra</button>
            <button class="level" type="button" data-level="1" aria-label="Gulvkomfort niveau 1" aria-pressed="false">1</button>
            <button class="level" type="button" data-level="2" aria-label="Gulvkomfort niveau 2" aria-pressed="false">2</button>
            <button class="level" type="button" data-level="3" aria-label="Gulvkomfort niveau 3" aria-pressed="false">3</button>
          </div>
        </div>
        <div id="status" class="status" role="status" aria-live="polite" hidden></div>
        <div id="error" class="error" role="alert" hidden></div>
      </ha-card>`;
    this._nodes = Object.fromEntries([...this.shadowRoot.querySelectorAll("[id]")].map(node => [node.id,node]));
    this._buttons = [...this.shadowRoot.querySelectorAll("[data-level]")];
    this._nodes.minus.addEventListener("click", () => this._changeTemperature(-1));
    this._nodes.plus.addEventListener("click", () => this._changeTemperature(1));
    this._buttons.forEach(button => button.addEventListener("click", () => this._changeComfort(Number(button.dataset.level))));
  }

  setConfig(config) {
    if (!config || !/^climate\.[a-z0-9_]+$/.test(config.climate || "")) throw new Error("Angiv climate: med termostatens entitets-id.");
    if (!/^select\.[a-z0-9_]+$/.test(config.comfort || "")) throw new Error("Angiv comfort: med Gulvkomfort-entitetens id.");
    for (const key of ["temperature_sensor","humidity_sensor"]) {
      if (config[key] && !/^sensor\.[a-z0-9_]+$/.test(config[key])) throw new Error(`${key} skal være et sensor-id.`);
    }
    if (this._inFlight) throw new Error("Vent til den igangværende ændring er afsluttet, før kortet ændres.");
    this._clearPending();
    this._error = "";
    this._config = {...config};
    this._nodes.icon.setAttribute("icon", config.icon || "mdi:home-thermometer-outline");
    this._render();
  }

  set hass(value) { this._hass = value; this._render(); }
  getCardSize() { return 7; }
  getGridOptions() { return {columns:12,rows:"auto",min_columns:6}; }

  connectedCallback() { this._render(); }
  disconnectedCallback() { this._clearPending(); }

  _number(value) {
    if (value === null || value === undefined || typeof value === "boolean" || (typeof value === "string" && !value.trim())) return null;
    const number = Number(value);
    return Number.isFinite(number) ? number : null;
  }
  _available(entity) { return !!entity && !["unavailable","unknown"].includes(entity.state); }
  _entities() {
    const states = this._hass?.states || {};
    return {climate:states[this._config?.climate],comfort:states[this._config?.comfort]};
  }
  _format(value, decimals=1) {
    if (value === null) return "—";
    const language = this._hass?.locale?.language || this._hass?.language || "da-DK";
    try { return value.toLocaleString(language,{minimumFractionDigits:decimals,maximumFractionDigits:decimals}); }
    catch { return value.toFixed(decimals).replace(".",","); }
  }
  _reportedMatches(pending) {
    const {climate,comfort} = this._entities();
    if (pending.kind === "comfort") return this._available(comfort) && comfort.state === pending.expected;
    const actual = this._number(climate?.attributes?.temperature);
    return this._available(climate) && actual !== null && Math.abs(actual-pending.expected) < 0.001;
  }
  _clearPending() {
    clearTimeout(this._timer);
    this._timer = undefined;
    this._pending = null;
  }

  _render() {
    if (!this._hass || !this._config) return;
    const {climate,comfort} = this._entities();
    const online = this._available(climate);
    const attributes = climate?.attributes || {};
    if (this._pending && this._reportedMatches(this._pending)) this._clearPending();
    const busy = this._inFlight || !!this._pending;
    let temperature = online ? this._number(attributes.current_temperature) : null;
    let humidity = online ? this._number(attributes.current_humidity) : null;
    if (this._config.temperature_sensor) {
      const sensor = this._hass.states[this._config.temperature_sensor];
      temperature = this._available(sensor) ? this._number(sensor.state) : null;
    }
    if (this._config.humidity_sensor) {
      const sensor = this._hass.states[this._config.humidity_sensor];
      humidity = this._available(sensor) ? this._number(sensor.state) : null;
    }
    if (humidity !== null && (humidity < 0 || humidity > 100)) humidity = null;
    const target = online ? this._number(attributes.temperature) : null;
    const min = this._number(attributes.min_temp), max = this._number(attributes.max_temp);
    const canSet = online && target !== null && min !== null && max !== null && min < max;
    const unit = this._hass.config?.unit_system?.temperature || "°C";
    const actualUnit = this._config.temperature_sensor ? this._hass.states[this._config.temperature_sensor]?.attributes?.unit_of_measurement || unit : unit;
    this._nodes.name.textContent = this._config.name || attributes.friendly_name || "Rum";
    this._nodes.actual.textContent = this._format(temperature);
    this._nodes["actual-unit"].textContent = actualUnit;
    this._nodes.humidity.textContent = this._format(humidity,0);
    this._nodes.target.textContent = this._format(target);
    this._nodes["target-unit"].textContent = unit;
    this._nodes.minus.disabled = busy || !canSet || target <= min;
    this._nodes.plus.disabled = busy || !canSet || target >= max;
    const options = Array.isArray(comfort?.attributes?.options) ? comfort.attributes.options : [];
    const states = ["off","level_1","level_2","level_3"];
    const level = this._available(comfort) ? states.indexOf(comfort.state) : -1;
    this._nodes.floor.dataset.active = String(level > 0);
    this._nodes["floor-state"].textContent = level < 0 ? "Utilgængelig" : level === 0 ? "Fra" : `Niveau ${level}`;
    this._buttons.forEach(button => {
      const index = Number(button.dataset.level);
      button.setAttribute("aria-pressed",String(index === level));
      button.disabled = busy || level < 0 || !options.includes(states[index]);
    });
    let message = busy ? "Afventer aflæsning…" : "";
    if (!message && !online) message = climate ? "Termostaten er utilgængelig." : "Termostatens entitets-id blev ikke fundet.";
    if (!message && !comfort) message = "Gulvkomfort-entiteten blev ikke fundet. Kontrollér id og aktivering.";
    else if (!message && level < 0) message = "Gulvkomfort er midlertidigt utilgængelig.";
    this._nodes.status.textContent = message;
    this._nodes.status.hidden = !message;
    this._nodes.error.textContent = this._error;
    this._nodes.error.hidden = !this._error;
  }

  async _request(kind,domain,service,data,expected) {
    if (this._inFlight || this._pending || !this._hass) return;
    this._error = "";
    this._inFlight = true;
    this._pending = {kind,expected};
    this._timer = setTimeout(() => {
      if (!this._pending) return;
      this._clearPending();
      this._error = "Ændringen er ikke bekræftet. Kontrollér den aktuelle værdi før et nyt forsøg.";
      this._render();
    },180000);
    this._render();
    try {
      await this._hass.callService(domain,service,data);
    } catch (error) {
      this._clearPending();
      this._error = `Ændringen kunne ikke gennemføres: ${error?.message || "Se Home Assistants log."}`;
    } finally {
      this._inFlight = false;
      this._render();
    }
  }

  _changeTemperature(direction) {
    const {climate} = this._entities();
    if (!this._available(climate)) return;
    const attrs = climate.attributes || {};
    const current = this._number(attrs.temperature), min = this._number(attrs.min_temp), max = this._number(attrs.max_temp);
    if (current === null || min === null || max === null || min >= max) return;
    const configuredStep = this._number(attrs.target_temp_step);
    const step = configuredStep !== null && configuredStep > 0 ? configuredStep : 0.5;
    const target = Number(Math.max(min,Math.min(max,current + direction*step)).toFixed(3));
    if (target === current) return;
    return this._request("temperature","climate","set_temperature",{entity_id:this._config.climate,temperature:target},target);
  }
  _changeComfort(level) {
    const {comfort} = this._entities();
    const option = ["off","level_1","level_2","level_3"][level];
    if (!this._available(comfort) || !option || !Array.isArray(comfort.attributes?.options) || !comfort.attributes.options.includes(option) || comfort.state === option) return;
    return this._request("comfort","select","select_option",{entity_id:this._config.comfort,option},option);
  }
}

if (!customElements.get("salus-room-card")) customElements.define("salus-room-card",SalusRoomCard);
window.customCards = window.customCards || [];
if (!window.customCards.some(card => card.type === "salus-room-card")) {
  window.customCards.push({type:"salus-room-card",name:"SALUS rumkort",description:"Temperatur, luftfugtighed, ønsket temperatur og gulvkomfort.",preview:false});
}
