/* SALUS Room Card 1.3.0 — MIT License. Bundled with the SALUS integration. */
async function registerSalusRoomCard() {
// Extra modules can run before HA installs its scoped custom element registry.
// Wait before defining classes as well: the polyfill replaces HTMLElement too.
await customElements.whenDefined("home-assistant");
function salusComfortForClimate(hass, climateId) {
  const device = hass?.entities?.[climateId]?.device_id;
  if (!device) return "";
  return Object.keys(hass.states || {}).find(id => id.startsWith("select.")
    && hass.entities[id]?.device_id === device
    && ["off","level_1","level_2","level_3"].every(option => hass.states[id].attributes?.options?.includes(option))) || "";
}

class SalusRoomCard extends HTMLElement {
  static getConfigElement() { return document.createElement("salus-room-card-editor"); }
  static getStubConfig(hass, entities = [], entitiesFallback = []) {
    const candidates = [...new Set([...entities,...entitiesFallback,...Object.keys(hass?.states || {})])]
      .filter(id => id.startsWith("climate."));
    const climate = candidates.find(id => salusComfortForClimate(hass,id)) || candidates[0] || "";
    return {climate,comfort:salusComfortForClimate(hass,climate),layout:"compact"};
  }
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._pending = null;
    this._inFlight = false;
    this._error = "";
    this._historyOpen = false;
    this._historyGeneration = 0;
    this._hiddenSeries = new Set();
    this.shadowRoot.innerHTML = `
      <style>
        :host {display:block;min-width:0;container-type:inline-size;}
        * {box-sizing:border-box;}
        ha-card {display:grid;grid-template-columns:minmax(0,1fr) 128px;gap:0 10px;
          grid-template-areas:"head head" "actual target" "floor floor" "status status" "error error" "history history";
          padding:10px 12px;border-radius:14px;background:var(--ha-card-background,var(--card-background-color,#1c2023));
          color:var(--primary-text-color,#f1f2f2);border:1px solid var(--divider-color,#303639);box-shadow:none;
          font-family:var(--paper-font-body1_-_font-family,Roboto,sans-serif);}
        header {grid-area:head;display:flex;align-items:center;gap:6px;min-width:0;min-height:28px;}
        #icon {grid-area:icon;align-self:center;flex:0 0 16px;}
        h2 {grid-area:name;align-self:center;flex:1;}
        header>ha-icon {--mdc-icon-size:16px;color:var(--secondary-text-color);flex-shrink:0;}
        h2 {font-size:14px;font-weight:500;margin:0;min-width:0;overflow-wrap:anywhere;}
        .history-toggle {border:0;background:transparent;min-width:28px;min-height:28px;padding:0;
          display:grid;place-items:center;border-radius:8px;color:var(--secondary-text-color);grid-area:toggle;align-self:center;flex:0 0 28px;}
        .history-toggle ha-icon {--mdc-icon-size:16px;transition:transform .15s;}
        .history-toggle[aria-expanded="true"] ha-icon {transform:rotate(180deg);}
        .temperature-reading {grid-area:actual;align-self:center;margin:4px 0;}
        .label {font-size:11px;color:var(--secondary-text-color,#a8b0b5);margin-bottom:3px;}
        .temperature-reading>.label,.humidity>.label {display:none;}
        .actual {font-size:26px;font-weight:500;line-height:1.2;letter-spacing:-.7px;font-variant-numeric:tabular-nums;}
        #actual {display:inline-block;width:4.6ch;text-align:right;}
        #humidity {display:inline-block;width:3ch;text-align:right;}
        .unit {font-size:12px;font-weight:400;color:var(--secondary-text-color);margin-left:3px;letter-spacing:0;}
        .humidity {grid-area:humid;align-self:center;justify-self:end;flex:0 0 56px;width:56px;}
        .moisture {justify-content:flex-end;display:flex;align-items:center;gap:3px;font-size:12px;color:var(--secondary-text-color);font-variant-numeric:tabular-nums;}
        .moisture ha-icon {--mdc-icon-size:13px;color:var(--info-color,#72cbea);}
        .percent {font-size:11px;}
        button,select {font:inherit;color:inherit;touch-action:manipulation;}
        button:focus-visible,select:focus-visible {outline:2px solid var(--primary-color,#72cbea);outline-offset:2px;}
        button:disabled,select:disabled {opacity:.4;}
        .target-control {grid-area:target;align-self:center;min-width:0;margin:4px 0;}
        .target-control>.label {text-align:center;}
        .stepper {display:flex;align-items:center;justify-content:space-between;border-radius:8px;
          background:var(--secondary-background-color,#252b2e);min-height:30px;}
        .step {background:transparent;border:0;min-width:30px;min-height:30px;padding:0 5px;font-size:19px;border-radius:8px;}
        .step:hover:enabled {background:var(--ha-card-background,var(--card-background-color));}
        .target {flex:0 0 50px;text-align:center;font-size:13px;font-weight:500;font-variant-numeric:tabular-nums;white-space:nowrap;}
        .target .unit {font-size:11px;margin-left:1px;}
        .floor {grid-area:floor;display:flex;align-items:center;gap:8px;border-top:1px solid var(--divider-color,#303639);padding-top:7px;margin-top:4px;min-width:0;}
        .floor-head {display:flex;align-items:center;}
        .floor-label {display:flex;align-items:center;gap:4px;font-size:11px;color:var(--secondary-text-color);white-space:nowrap;}
        .floor-label ha-icon {--mdc-icon-size:14px;}
        .row-caption {display:none;}
        .floor-state {position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap;}
        .levels {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:3px;flex:1;min-width:0;}
        .level {border:0;background:var(--secondary-background-color,#252b2e);color:var(--secondary-text-color);
          border-radius:7px;min-height:28px;min-width:0;padding:2px 4px;font-size:12px;}
        .level[aria-pressed="true"] {background:var(--salus-comfort-color,#edaa70);color:var(--salus-comfort-contrast,#241a12);font-weight:500;}
        .level[data-level="0"][aria-pressed="true"] {background:var(--secondary-background-color,#252b2e);color:var(--primary-text-color);box-shadow:inset 0 0 0 1px var(--secondary-text-color);}
        .floor-select {display:none;min-width:0;min-height:32px;border:0;border-radius:8px;padding:4px 6px;
          background:var(--secondary-background-color,#252b2e);font-size:12px;}
        .floor-select option {background:var(--card-background-color,#1c2023);color:var(--primary-text-color,#f1f2f2);}
        .floor[data-active="true"] .floor-select {color:var(--salus-comfort-text,var(--warning-color,#d18a45));}
        :host([layout="rows"]) .levels {display:none;}
        :host([layout="rows"]) .floor-select {display:block;flex:1;}
        :host([layout="rows"]) .compact-caption {display:none;}
        :host([layout="rows"]) .row-caption {display:inline;}
        .status {grid-area:status;font-size:12px;color:var(--secondary-text-color);overflow-wrap:anywhere;margin-top:6px;}
        .error {grid-area:error;font-size:12px;color:var(--error-color,#db6060);overflow-wrap:anywhere;margin-top:6px;}
        .history {position:relative;grid-area:history;min-width:0;margin-top:3px;padding-top:8px;border-top:1px solid var(--divider-color);}
        .history-head {display:flex;align-items:center;justify-content:space-between;gap:6px;font-size:11px;color:var(--secondary-text-color);}
        .history-refresh {border:0;background:transparent;min-height:30px;padding:4px;color:var(--primary-color);}
        .history-message,.history-detail {font-size:11px;line-height:1.4;color:var(--secondary-text-color);margin:3px 0;overflow-wrap:anywhere;}
        .history-chart {display:block;width:100%;height:220px;overflow:visible;}
        .history-chart text {fill:var(--secondary-text-color);font:11px sans-serif;}
        .history-chart .grid {stroke:var(--divider-color);stroke-width:1;fill:none;}
        .history-chart .actual-line {stroke:var(--salus-history-temperature,#4d78f4);stroke-width:2;fill:none;}
        .history-chart .target-line {stroke:var(--salus-history-target,#efb83b);stroke-width:1.6;fill:none;}
        .history-chart .heat-band {fill:var(--salus-comfort-color,#edaa70);opacity:.10;}
        .history-chart .heat-start {stroke:var(--salus-comfort-color,#edaa70);stroke-width:1;opacity:.5;}
        .history-chart .unknown-band {fill:var(--secondary-text-color);opacity:.08;}
        .history-legend {display:flex;flex-wrap:wrap;gap:6px 10px;font-size:11px;color:var(--secondary-text-color);}
        .history-legend button {display:flex;align-items:center;gap:5px;background:transparent;border:0;padding:4px 0;color:var(--secondary-text-color);font-size:11px;}
        .history-legend button[aria-pressed="false"] {opacity:.4;}
        .history-detail {position:absolute;top:36px;max-width:min(300px,100%);padding:7px 9px;border:1px solid var(--divider-color);border-radius:7px;color:var(--primary-text-color);background:var(--ha-card-background,var(--card-background-color,#1c2023));pointer-events:none;z-index:2;}
        .swatch {width:14px;height:0;border-top:2px solid var(--salus-history-temperature,#4d78f4);}
        .swatch.target-swatch {border-color:var(--salus-history-target,#efb83b);}
        .swatch.heat-swatch {height:6px;border:0;background:var(--salus-comfort-color,#edaa70);opacity:.75;}
        @container (min-width:580px) {
          :host([layout="rows"]) ha-card {grid-template-columns:16px minmax(100px,1.2fr) minmax(72px,1fr) minmax(110px,1fr) minmax(100px,1fr) 28px;gap:0 6px;padding:10px;
            grid-template-areas:"icon name actual target floor toggle" "icon humid actual target floor toggle" "status status status status status status" "error error error error error error" "history history history history history history";}
          :host([layout="rows"]) header {display:contents;}
          :host([layout="rows"]) #icon {grid-area:icon;align-self:center;flex:0 0 16px;}
          :host([layout="rows"]) h2 {grid-area:name;align-self:end;font-size:13px;}
          :host([layout="rows"]) .humidity {justify-self:start;align-self:start;}
          :host([layout="rows"]) .history-toggle {grid-area:toggle;margin:0;align-self:center;}
          :host([layout="rows"]) .actual {font-size:22px;}
          :host([layout="rows"]) #actual {width:3.8ch;}
          :host([layout="rows"]) .temperature-reading>.label {display:block;}
          :host([layout="rows"]) .floor {border:0;padding:0;margin:0;display:flex;flex-direction:column;align-items:stretch;gap:3px;}
          :host([layout="rows"]) .floor-label ha-icon {display:none;}
          :host([layout="rows"]) .target-control,:host([layout="rows"]) .floor {width:100%;max-width:180px;justify-self:center;}
          :host([layout="rows"]) .temperature-reading {justify-self:center;}
        }
        @media(pointer:coarse) {
          .target {flex-basis:40px;}
          .history-toggle {flex-basis:44px;}
          .step {min-width:44px;min-height:44px;}
          .history-toggle,.history-refresh {min-width:44px;min-height:44px;}
          .level,.floor-select {min-height:44px;}
          .floor-select {font-size:16px;}
          @container (min-width:580px) {
            :host([layout="rows"]) ha-card {grid-template-columns:16px minmax(80px,1.2fr) minmax(60px,1fr) minmax(128px,1fr) minmax(100px,1fr) 44px;}
          }
        }
        [hidden] {display:none !important;}
      </style>
      <ha-card>
        <header><ha-icon id="icon"></ha-icon><h2 id="name"></h2><div class="humidity" aria-label="Luftfugtighed"><div class="label">Luftfugtighed</div><div class="moisture"><ha-icon icon="mdi:water-percent"></ha-icon><span id="humidity">—</span><span class="percent">%</span></div></div><button id="history-toggle" class="history-toggle" type="button" aria-label="Vis historik" aria-expanded="false" aria-controls="history"><ha-icon icon="mdi:chevron-down"></ha-icon></button></header>
        <div class="temperature-reading" aria-label="Aktuel temperatur"><div class="label">Temperatur</div><div class="actual"><span id="actual">—</span><span class="unit" id="actual-unit">°C</span></div></div>
        <div class="target-control"><div class="label" id="target-label" role="status" aria-live="polite">Ønsket</div>
          <div class="stepper" role="group" aria-label="Ønsket temperatur">
            <button class="step" id="minus" type="button" aria-label="Sænk ønsket temperatur">−</button>
            <div class="target"><span id="target">—</span><span class="unit" id="target-unit">°C</span></div>
            <button class="step" id="plus" type="button" aria-label="Hæv ønsket temperatur">+</button>
          </div>
        </div>
        <div class="floor" id="floor">
          <div class="floor-head"><span class="floor-label"><ha-icon icon="mdi:heating-coil"></ha-icon><span class="compact-caption">Gulv</span><span class="row-caption">Gulvkomfort</span></span><span id="floor-state" class="floor-state">—</span></div>
          <div class="levels" role="group" aria-label="Gulvkomfort">
            <button class="level" type="button" data-level="0" aria-label="Gulvkomfort fra" aria-pressed="false">Fra</button>
            <button class="level" type="button" data-level="1" aria-label="Gulvkomfort niveau 1" aria-pressed="false">1</button>
            <button class="level" type="button" data-level="2" aria-label="Gulvkomfort niveau 2" aria-pressed="false">2</button>
            <button class="level" type="button" data-level="3" aria-label="Gulvkomfort niveau 3" aria-pressed="false">3</button>
          </div>
          <select id="floor-select" class="floor-select" aria-label="Gulvkomfort"><option value="" disabled>Utilgængelig</option><option value="0">Fra</option><option value="1">Niveau 1</option><option value="2">Niveau 2</option><option value="3">Niveau 3</option></select>
        </div>
        <div id="status" class="status" role="status" aria-live="polite" hidden></div>
        <div id="error" class="error" role="alert" hidden></div>
        <section id="history" class="history" aria-label="Temperatur og varmebehov" hidden>
          <div class="history-head"><span id="history-title">Seneste 48 timer</span><button id="history-refresh" class="history-refresh" type="button">Opdater</button></div>
          <div id="history-message" class="history-message" role="status" hidden></div>
          <svg id="history-chart" class="history-chart" role="img" aria-label="Temperatur, ønsket temperatur og termostatens varmebehov" hidden></svg>
          <div id="history-legend" class="history-legend" hidden><button type="button" data-series="temperature" aria-pressed="true"><i class="swatch"></i><span id="legend-temperature">Temperatur</span></button><button type="button" data-series="target" aria-pressed="true"><i class="swatch target-swatch"></i><span id="legend-target">Ønsket</span></button><button type="button" data-series="heat" aria-pressed="true"><i class="swatch heat-swatch"></i>Varmebehov</button></div>
          <div id="history-detail" class="history-detail" role="tooltip" hidden></div>
        </section>
      </ha-card>`;
    this._nodes = Object.fromEntries([...this.shadowRoot.querySelectorAll("[id]")].map(node => [node.id,node]));
    this._buttons = [...this.shadowRoot.querySelectorAll("[data-level]")];
    this._nodes["floor-select"].addEventListener("change",()=>{
      const value=this._nodes["floor-select"].value;
      if(value!=="")this._changeComfort(Number(value));
      this._render();
    });
    this._nodes.minus.addEventListener("click", () => this._changeTemperature(-1));
    this._nodes.plus.addEventListener("click", () => this._changeTemperature(1));
    this._buttons.forEach(button => button.addEventListener("click", () => this._changeComfort(Number(button.dataset.level))));
    this._nodes["history-toggle"].addEventListener("click",()=>this._toggleHistory());
    this._nodes["history-refresh"].addEventListener("click",()=>this._loadHistory(true));
    this.shadowRoot.querySelector("ha-card").addEventListener("click",event=>{
      if (event.target.closest?.("button,input,select,a,#history")) return;
      this._toggleHistory();
    });
    this._nodes["history-chart"].addEventListener("pointermove",event=>this._historyPointer(event));
    this._nodes["history-chart"].addEventListener("pointerdown",event=>this._historyPointer(event));
    this._nodes["history-chart"].addEventListener("pointerleave",()=>{this._nodes["history-detail"].hidden=true;});
    this.shadowRoot.querySelectorAll('[data-series]').forEach(button=>button.addEventListener("click",()=>{
      const series=button.dataset.series;
      if(this._hiddenSeries.has(series))this._hiddenSeries.delete(series);else this._hiddenSeries.add(series);
      this._drawHistory();
    }));
    this._resizeObserver = new ResizeObserver(()=>{if(this._historyOpen && this._historyCache)this._drawHistory();});
  }

  setConfig(config) {
    if (!config || !/^climate\.[a-z0-9_]+$/.test(config.climate || "")) throw new Error("Angiv climate: med termostatens entitets-id.");
    if (!/^select\.[a-z0-9_]+$/.test(config.comfort || "")) throw new Error("Angiv comfort: med Gulvkomfort-entitetens id.");
    for (const key of ["temperature_sensor","humidity_sensor"]) {
      if (config[key] && !/^sensor\.[a-z0-9_]+$/.test(config[key])) throw new Error(`${key} skal være et sensor-id.`);
    }
    if (config.layout !== undefined && !["compact","rows"].includes(config.layout)) throw new Error("Vælg layout compact eller rows.");
    if (this._inFlight) throw new Error("Vent til den igangværende ændring er afsluttet, før kortet ændres.");
    this._clearPending();
    this._error = "";
    this._config = {...config};
    this.setAttribute("layout",config.layout || "compact");
    if (config.history_hours !== undefined && (!Number.isFinite(config.history_hours) || config.history_hours < 1 || config.history_hours > 48)) throw new Error("Historik skal være mellem 1 og 48 timer.");
    this._historyGeneration++;
    this._hiddenSeries.clear();
    this._nodes["history-detail"].hidden=true;
    this._historyOpen=false;
    this._historyLoading=false;
    this._historyCache=null;
    this._nodes.history.hidden=true;
    this._nodes["history-toggle"].setAttribute("aria-expanded","false");
    this._nodes.icon.setAttribute("icon", config.icon || "mdi:home-thermometer-outline");
    this._render();
  }

  set hass(value) { this._hass = value; this._render(); }
  getCardSize() { return (this._config?.layout === "rows" && this.clientWidth >= 580 ? 2 : 3) + (this._historyOpen ? 5 : 0); }
  getGridOptions() { return {columns:this._config?.layout === "rows" ? 12 : 6,rows:"auto",min_columns:6}; }

  connectedCallback() { this._resizeObserver.observe(this);this._render(); }
  disconnectedCallback() { this._resizeObserver.disconnect();this._clearPending(); }

  _toggleHistory() {
    this._historyOpen=!this._historyOpen;
    this._nodes["history-detail"].hidden=true;
    this._nodes.history.hidden=!this._historyOpen;
    this._nodes["history-toggle"].setAttribute("aria-expanded",String(this._historyOpen));
    this._nodes["history-toggle"].setAttribute("aria-label",this._historyOpen ? "Skjul historik" : "Vis historik");
    if(this._historyOpen)this._loadHistory();
  }
  async _loadHistory(force=false) {
    if(!this._historyOpen || this._historyLoading || !this._config || !this._hass)return;
    if(!force && this._historyCache && Date.now()-this._historyCache.loaded < 300000){this._drawHistory();return;}
    const generation=this._historyGeneration;
    const end=Date.now(),start=end-(this._config.history_hours || 48)*3600000;
    this._historyLoading=true;
    this._nodes["history-refresh"].disabled=true;
    this._nodes["history-message"].hidden=false;
    this._nodes["history-message"].textContent="Henter historik…";
    try {
      if(typeof this._hass.callApi!=="function")throw new Error("Historik er ikke tilgængelig.");
      const query=new URLSearchParams({filter_entity_id:this._config.climate,end_time:new Date(end).toISOString(),significant_changes_only:"0"});
      const result=await this._hass.callApi("GET",`history/period/${encodeURIComponent(new Date(start).toISOString())}?${query}`);
      if(generation!==this._historyGeneration)return;
      const rows=Array.isArray(result) && Array.isArray(result[0]) ? result[0] : [];
      const points=rows.map(row=>{
        const time=Date.parse(row.last_updated || row.last_changed);
        const online=!["unknown","unavailable"].includes(row.state);
        const action=row.attributes?.hvac_action;
        return {time,temperature:online ? this._number(row.attributes?.current_temperature) : null,target:online ? this._number(row.attributes?.temperature) : null,
          heat:!online ? null : action==="heating" ? 1 : ["idle","off","cooling","drying","fan"].includes(action) ? 0 : null};
      }).filter(point=>Number.isFinite(point.time) && point.time<=end).sort((a,b)=>a.time-b.time);
      this._historyCache={points,start,end,loaded:Date.now()};
      this._drawHistory();
    } catch(error) {
      if(generation!==this._historyGeneration)return;
      this._nodes["history-message"].hidden=false;
      this._nodes["history-message"].textContent="Historikken kunne ikke hentes. Kontrollér Historik/Recorder og prøv Opdater.";
    } finally {
      if(generation===this._historyGeneration){this._historyLoading=false;this._nodes["history-refresh"].disabled=false;}
    }
  }
  _historyTime(time) {
    const options={hour:"2-digit",minute:"2-digit"};
    if(this._hass?.config?.time_zone)options.timeZone=this._hass.config.time_zone;
    try{return new Date(time).toLocaleTimeString("da-DK",options);}catch{return new Date(time).toLocaleTimeString("da-DK",{hour:"2-digit",minute:"2-digit"});}
  }
  _historyDate(time) {
    const options={day:"numeric",month:"short"};
    if(this._hass?.config?.time_zone)options.timeZone=this._hass.config.time_zone;
    try{return new Date(time).toLocaleDateString("da-DK",options);}catch{return new Date(time).toLocaleDateString("da-DK");}
  }
  _drawHistory() {
    const cache=this._historyCache;
    if(!cache || !this._historyOpen)return;
    const {points,start,end}=cache;
    const svg=this._nodes["history-chart"];
    this._nodes["history-title"].textContent=`Seneste ${this._config.history_hours || 48} timer`;
    const inWindow=points.filter(point=>point.time>=start);
    const seed=points.filter(point=>point.time<start).at(-1);
    const visible=seed ? [{...seed,time:start},...inWindow] : inWindow;
    const values=visible.flatMap(point=>[point.temperature,point.target]).filter(value=>value!==null);
    if(!visible.length || !values.length){svg.setAttribute("hidden","");this._nodes["history-legend"].hidden=true;this._nodes["history-message"].hidden=false;this._nodes["history-message"].textContent="Ingen temperaturhistorik i perioden.";return;}
    svg.removeAttribute("hidden");this._nodes["history-legend"].hidden=false;
    this._nodes["history-message"].hidden=true;
    const width=Math.max(180,this._nodes.history.clientWidth),left=35,right=9,top=15;
    const height=Math.round(Math.max(160,Math.min(280,width*.39))),bottom=height-40;
    svg.style.height=`${height}px`;
    const rawMin=Math.min(...values),rawMax=Math.max(...values);
    const step=[.5,1,2,5,10,20].find(value=>value>=(rawMax-rawMin)/5) || 50;
    const min=Math.floor((rawMin-.15)/step)*step,max=Math.ceil((rawMax+.15)/step)*step;
    const x=time=>left+Math.max(0,Math.min(1,(time-start)/(end-start)))*(width-left-right);
    const y=value=>bottom-(value-min)/(max-min)*(bottom-top);
    this._historyGeometry={left,right,start,end};
    const node=(tag,attrs,text)=>{const element=document.createElementNS("http://www.w3.org/2000/svg",tag);Object.entries(attrs).forEach(([key,value])=>element.setAttribute(key,String(value)));if(text!==undefined)element.textContent=text;svg.append(element);return element;};
    svg.replaceChildren();svg.setAttribute("viewBox",`0 0 ${width} ${height}`);
    node("title",{},"Temperatur og ønsket temperatur som trappekurver; varmebehov markeret i grafen");
    let cursor=start,heat=null;
    const intervals=[];
    for(const point of visible){if(point.time>cursor)intervals.push({from:cursor,to:point.time,heat});cursor=point.time;heat=point.heat;}
    if(cursor<end)intervals.push({from:cursor,to:end,heat});
    const merged=[];
    for(const interval of intervals){const last=merged.at(-1);if(last && last.heat===interval.heat && last.to===interval.from)last.to=interval.to;else merged.push({...interval});}
    if(!this._hiddenSeries.has("heat"))for(const interval of merged){
      if(interval.heat===0)continue;
      const rect=node("rect",{x:x(interval.from),y:top,width:Math.max(0,x(interval.to)-x(interval.from)),height:bottom-top,class:interval.heat===1?"heat-band":"unknown-band"});
      const title=document.createElementNS("http://www.w3.org/2000/svg","title");title.textContent=`${this._historyTime(interval.from)}–${this._historyTime(interval.to)}: ${interval.heat===1?"Kalder på varme":"Ukendt varmebehov"}`;rect.append(title);
      if(interval.heat===1)node("path",{d:`M${x(interval.from)} ${top}V${bottom}`,class:"heat-start"});
    }
    for(let value=min;value<=max+.001;value+=step){
      node("path",{d:`M${left} ${y(value)}H${width-right}`,class:"grid"});
      node("text",{x:left-6,y:y(value)+4,"text-anchor":"end"},this._format(value,Number.isInteger(step)&&Number.isInteger(value)?0:1));
    }
    const tickCount=Math.max(3,Math.min(9,Math.floor((width-left-right)/75)+1));
    let previousDate="";
    for(let i=0;i<tickCount;i++){
      const time=start+(end-start)*i/(tickCount-1),date=this._historyDate(time);
      const anchor=i===0?"start":i===tickCount-1?"end":"middle";
      node("path",{d:`M${x(time)} ${top}V${bottom}`,class:"grid"});
      node("text",{x:x(time),y:height-20,"text-anchor":anchor},this._historyTime(time));
      if(date!==previousDate || tickCount<=3)node("text",{x:x(time),y:height-5,"text-anchor":anchor},date);
      previousDate=date;
    }
    node("text",{x:left,y:10},this._hass.config?.unit_system?.temperature || "°C");
    const pathFor=key=>{
      let path="",previous=null;
      for(const point of visible){
        const px=x(point.time);
        if(point[key]===null){if(previous)path+=`H${px}`;previous=null;continue;}
        const py=y(point[key]);path+=previous===null?`M${px} ${py}`:`H${px}V${py}`;previous=point;
      }
      if(previous)path+=`H${x(end)}`;
      return path;
    };
    node("path",{d:pathFor("temperature"),class:"actual-line",hidden:this._hiddenSeries.has("temperature")?"":"false"});
    node("path",{d:pathFor("target"),class:"target-line",hidden:this._hiddenSeries.has("target")?"":"false"});
    // SVG boolean attributes must be absent when false.
    svg.querySelectorAll('[hidden="false"]').forEach(element=>element.removeAttribute("hidden"));
    const last=visible.at(-1),unit=this._hass.config?.unit_system?.temperature || "°C";
    this._nodes["legend-temperature"].textContent=`Temperatur ${this._format(last.temperature)} ${unit}`;
    this._nodes["legend-target"].textContent=`Ønsket ${this._format(last.target)} ${unit}`;
    this.shadowRoot.querySelectorAll('[data-series]').forEach(button=>button.setAttribute("aria-pressed",String(!this._hiddenSeries.has(button.dataset.series))));
  }
  _historyPointer(event) {
    const cache=this._historyCache,geometry=this._historyGeometry;
    if(!cache?.points.length || !geometry)return;
    const rect=this._nodes["history-chart"].getBoundingClientRect();
    const time=cache.start+Math.max(0,Math.min(1,(event.clientX-rect.left-geometry.left)/(rect.width-geometry.left-geometry.right)))*(cache.end-cache.start);
    let low=0,high=cache.points.length-1;
    while(low<high){const mid=Math.ceil((low+high)/2);if(cache.points[mid].time<=time)low=mid;else high=mid-1;}
    const point=cache.points[low].time<=time ? cache.points[low] : {time,temperature:null,target:null,heat:null};
    const detail=this._nodes["history-detail"];
    detail.textContent=`${this._historyDate(point.time)} ${this._historyTime(point.time)} · ${this._format(point.temperature)}° · ønsket ${this._format(point.target)}° · ${point.heat===null?"Ukendt varmebehov":point.heat===1?"Kalder på varme":"Intet varmebehov"}`;
    detail.hidden=false;
    detail.style.left=`${Math.max(0,Math.min(this._nodes.history.clientWidth-detail.offsetWidth,event.clientX-rect.left-80))}px`;
  }

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
    this._nodes["target-label"].textContent=busy ? "Afventer…" : "Ønsket";
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
    this._nodes["floor-select"].value=level < 0 ? "" : String(level);
    this._nodes["floor-select"].disabled=busy || level < 0;
    [...this._nodes["floor-select"].options].forEach(option=>{option.disabled=option.value==="" || !options.includes(states[Number(option.value)]);});
    this._buttons.forEach(button => {
      const index = Number(button.dataset.level);
      button.setAttribute("aria-pressed",String(index === level));
      button.disabled = busy || level < 0 || !options.includes(states[index]);
    });
    let message = "";
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

class SalusRoomCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({mode:"open"});
    this.shadowRoot.innerHTML = `
      <style>
        :host {display:block;color:var(--primary-text-color);font-family:var(--paper-font-body1_-_font-family,Roboto,sans-serif)}
        label {display:block;font-size:13px;margin-bottom:18px;color:var(--secondary-text-color)}
        input,select {display:block;width:100%;box-sizing:border-box;min-height:48px;margin-top:6px;padding:10px 12px;
          font:inherit;font-size:16px;color:var(--primary-text-color);background:var(--card-background-color);
          border:1px solid var(--divider-color);border-radius:8px;}
        input:focus-visible,select:focus-visible {outline:2px solid var(--primary-color);outline-offset:2px}
        .help {font-size:13px;color:var(--secondary-text-color);line-height:1.5;margin:4px 0 18px}
      </style>
      <div class="help">Vælg en termostat. Gulvkomfort fra samme enhed vælges automatisk, når den findes.</div>
      <label>Layout<select id="layout" aria-label="Layout"><option value="" disabled>Vælg layout (standard: Kompakt)</option><option value="compact">Kompakt – små kort med niveauknapper</option><option value="rows">Rækker – vandret kort med gulvmenu</option></select></label>
      <div class="help">Kompakt foreslår halv bredde. Rækker bruger fuld bredde og tilpasser sig mindre skærme. Et eksisterende kort kan tilpasses under Layout. Klik på kortet eller pilen for historik.</div>
      <label>Historikperiode<select id="history_hours" aria-label="Historikperiode"><option value="6">6 timer</option><option value="12">12 timer</option><option value="24">24 timer</option><option value="48">48 timer</option></select></label>
      <label>Rumtitel (valgfri)<input id="name" type="text" placeholder="Brug termostatens navn"></label>
      <label>Termostat<select id="climate" aria-label="Termostat"></select></label>
      <label>Gulvkomfort<select id="comfort" aria-label="Gulvkomfort"></select></label>
      <label>Ikon (valgfrit)<input id="icon" type="text" placeholder="mdi:home-thermometer-outline"></label>`;
    this._inputs = Object.fromEntries([...this.shadowRoot.querySelectorAll("[id]")].map(node=>[node.id,node]));
    Object.entries(this._inputs).forEach(([name,input])=>input.addEventListener("change",()=>this._changed(name,input.value)));
  }
  setConfig(config) { this._config={...config};this._render(); }
  set hass(hass) {this._hass=hass;this._render();}
  _changed(name,value) {
    if (!this._config) return;
    const config={...this._config,[name]:name === "history_hours" ? Number(value) : value};
    if (name === "layout") config.grid_options={...config.grid_options,columns:value === "rows" ? 12 : 6,rows:"auto"};
    if (name === "climate" && value !== this._config.climate) config.comfort=salusComfortForClimate(this._hass,value);
    if ((name === "name" || name === "icon") && !value.trim()) delete config[name];
    this._config=config;
    this._render();
    this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:{...config}},bubbles:true,composed:true}));
  }
  _render() {
    if (!this._config || !this._hass) return;
    const states=this._hass.states || {};
    this._inputs.layout.value=this._config.layout || "";
    this._inputs.history_hours.value=String(this._config.history_hours || 48);
    for (const name of ["name","icon"]) {
      if (this.shadowRoot.activeElement !== this._inputs[name]) this._inputs[name].value=this._config[name] || "";
    }
    for (const domain of ["climate","select"]) {
      const name=domain === "climate" ? "climate" : "comfort";
      let ids=Object.keys(states).filter(id=>id.startsWith(domain+"."));
      if (domain === "select") ids=ids.filter(id=>["off","level_1","level_2","level_3"].every(option=>states[id].attributes?.options?.includes(option)));
      const selected=this._config[name] || "";
      if (selected && !ids.includes(selected)) ids.push(selected);
      ids.sort((a,b)=>(states[a]?.attributes?.friendly_name || a).localeCompare(states[b]?.attributes?.friendly_name || b,"da"));
      const signature=JSON.stringify(ids.map(id=>[id,states[id]?.attributes?.friendly_name]));
      const picker=this._inputs[name];
      if (picker.dataset.options !== signature) {
        const placeholder=document.createElement("option");placeholder.value="";placeholder.textContent="Vælg…";
        picker.replaceChildren(placeholder,...ids.map(id=>{
          const option=document.createElement("option");option.value=id;
          option.textContent=`${states[id]?.attributes?.friendly_name || id} · ${id}`;
          return option;
        }));
        picker.dataset.options=signature;
      }
      picker.value=selected;
    }
  }
}

if (!customElements.get("salus-room-card-editor")) customElements.define("salus-room-card-editor",SalusRoomCardEditor);
if (!customElements.get("salus-room-card")) customElements.define("salus-room-card",SalusRoomCard);
window.customCards = window.customCards || [];
if (!window.customCards.some(card => card.type === "salus-room-card")) {
  window.customCards.push({type:"salus-room-card",name:"SALUS rumkort",description:"Temperatur, luftfugtighed, ønsket temperatur og gulvkomfort.",preview:false,
    documentationURL:"https://github.com/MichaelBusackBertelsen/homeassistant_salus/blob/feature/floor-dashboard/dashboard/Start-her.txt"});
}
}
registerSalusRoomCard();
