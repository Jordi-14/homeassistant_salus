/* SALUS Room Card 1.1.1 — MIT License. Bundled with the SALUS integration. */
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
    return {climate,comfort:salusComfortForClimate(hass,climate)};
  }
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._pending = null;
    this._inFlight = false;
    this._error = "";
    this._historyOpen = false;
    this._historyGeneration = 0;
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
        header h2 {flex:1}
        .history-toggle {border:0;background:transparent;min-width:40px;min-height:40px;border-radius:10px;color:var(--secondary-text-color)}
        .history-toggle ha-icon {--mdc-icon-size:22px;transition:transform .15s}
        .history-toggle[aria-expanded="true"] ha-icon {transform:rotate(180deg)}
        .history {margin-top:18px;padding-top:15px;border-top:1px solid var(--divider-color)}
        .history-head {display:flex;align-items:center;justify-content:space-between;gap:6px;font-size:13px}
        .history-refresh {border:0;background:transparent;min-height:40px;padding:6px;color:var(--primary-color)}
        .history-message,.history-detail {font-size:11px;line-height:1.5;color:var(--secondary-text-color);margin:5px 0;overflow-wrap:anywhere}
        .history-chart {display:block;width:100%;height:174px;overflow:visible}
        .history-chart text {fill:var(--secondary-text-color);font:11px sans-serif}
        .history-chart .grid {stroke:var(--divider-color);stroke-width:1;fill:none}
        .history-chart .actual-line {stroke:var(--info-color,#72cbea);stroke-width:2;fill:none}
        .history-chart .target-line {stroke:var(--salus-comfort-color,#edaa70);stroke-width:1.6;stroke-dasharray:5 3;fill:none}
        .history-chart .heat-band {fill:var(--salus-comfort-color,#edaa70);opacity:.75}
        .history-chart .unknown-band {fill:var(--secondary-text-color);opacity:.25}
        .history-legend {display:flex;flex-wrap:wrap;gap:8px 12px;font-size:11px;color:var(--secondary-text-color)}
        .history-legend span {display:flex;align-items:center;gap:5px}
        .swatch {width:16px;height:0;border-top:2px solid var(--info-color,#72cbea)}
        .swatch.target-swatch {border-color:var(--salus-comfort-color,#edaa70);border-top-style:dashed}
        .swatch.heat-swatch {height:7px;border:0;background:var(--salus-comfort-color,#edaa70);opacity:.75}
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
        <header><ha-icon id="icon"></ha-icon><h2 id="name"></h2><button id="history-toggle" class="history-toggle" type="button" aria-label="Vis historik" aria-expanded="false" aria-controls="history"><ha-icon icon="mdi:chevron-down"></ha-icon></button></header>
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
        <section id="history" class="history" aria-label="Temperatur og varmebehov" hidden>
          <div class="history-head"><span id="history-title">Seneste 6 timer</span><button id="history-refresh" class="history-refresh" type="button">Opdater</button></div>
          <div id="history-message" class="history-message" role="status"></div>
          <svg id="history-chart" class="history-chart" role="img" aria-label="Temperatur, ønsket temperatur og termostatens varmebehov" hidden></svg>
          <div id="history-legend" class="history-legend" hidden><span><i class="swatch"></i>Temperatur</span><span><i class="swatch target-swatch"></i>Ønsket</span><span><i class="swatch heat-swatch"></i>Varmebehov</span></div>
          <div id="history-detail" class="history-detail"></div>
        </section>
      </ha-card>`;
    this._nodes = Object.fromEntries([...this.shadowRoot.querySelectorAll("[id]")].map(node => [node.id,node]));
    this._buttons = [...this.shadowRoot.querySelectorAll("[data-level]")];
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
    this._resizeObserver = new ResizeObserver(()=>{if(this._historyOpen && this._historyCache)this._drawHistory();});
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
    if (config.history_hours !== undefined && (!Number.isFinite(config.history_hours) || config.history_hours < 1 || config.history_hours > 48)) throw new Error("Historik skal være mellem 1 og 48 timer.");
    this._historyGeneration++;
    this._historyOpen=false;
    this._historyLoading=false;
    this._historyCache=null;
    this._nodes.history.hidden=true;
    this._nodes["history-toggle"].setAttribute("aria-expanded","false");
    this._nodes.icon.setAttribute("icon", config.icon || "mdi:home-thermometer-outline");
    this._render();
  }

  set hass(value) { this._hass = value; this._render(); }
  getCardSize() { return 7; }
  getGridOptions() { return {columns:12,rows:"auto",min_columns:12}; }

  connectedCallback() { this._resizeObserver.observe(this);this._render(); }
  disconnectedCallback() { this._resizeObserver.disconnect();this._clearPending(); }

  _toggleHistory() {
    this._historyOpen=!this._historyOpen;
    this._nodes.history.hidden=!this._historyOpen;
    this._nodes["history-toggle"].setAttribute("aria-expanded",String(this._historyOpen));
    this._nodes["history-toggle"].setAttribute("aria-label",this._historyOpen ? "Skjul historik" : "Vis historik");
    if(this._historyOpen)this._loadHistory();
  }
  async _loadHistory(force=false) {
    if(!this._historyOpen || this._historyLoading || !this._config || !this._hass)return;
    if(!force && this._historyCache && Date.now()-this._historyCache.loaded < 300000){this._drawHistory();return;}
    const generation=this._historyGeneration;
    const end=Date.now(),start=end-(this._config.history_hours || 6)*3600000;
    this._historyLoading=true;
    this._nodes["history-refresh"].disabled=true;
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
  _drawHistory() {
    const cache=this._historyCache;
    if(!cache || !this._historyOpen)return;
    const {points,start,end}=cache;
    const svg=this._nodes["history-chart"];
    this._nodes["history-title"].textContent=`Seneste ${this._config.history_hours || 6} timer`;
    const values=points.flatMap(point=>[point.temperature,point.target]).filter(value=>value!==null);
    if(!points.length || !values.length){svg.setAttribute("hidden","");this._nodes["history-legend"].hidden=true;this._nodes["history-message"].textContent="Ingen temperaturhistorik i perioden.";return;}
    svg.removeAttribute("hidden");this._nodes["history-legend"].hidden=false;
    this._nodes["history-message"].textContent=`Hentet ${this._historyTime(cache.loaded)} · grå varmeperioder har ukendt status`;
    const width=Math.max(180,this._nodes.history.clientWidth),left=34,right=8,top=12,bottom=112;
    const min=Math.floor((Math.min(...values)-.5)*2)/2,max=Math.ceil((Math.max(...values)+.5)*2)/2;
    const x=time=>left+Math.max(0,Math.min(1,(time-start)/(end-start)))*(width-left-right);
    const y=value=>bottom-(value-min)/(max-min)*(bottom-top);
    const node=(tag,attrs,text)=>{const element=document.createElementNS("http://www.w3.org/2000/svg",tag);Object.entries(attrs).forEach(([key,value])=>element.setAttribute(key,String(value)));if(text!==undefined)element.textContent=text;svg.append(element);return element;};
    svg.replaceChildren();svg.setAttribute("viewBox",`0 0 ${width} 174`);
    node("title",{},"Temperatur og ønsket temperatur med varmebehov under kurverne");
    for(let i=0;i<3;i++){
      const value=min+(max-min)*i/2;
      node("path",{d:`M${left} ${y(value)}H${width-right}`,class:"grid"});
      node("text",{x:left-6,y:y(value)+4,"text-anchor":"end"},this._format(value));
      const time=start+(end-start)*i/2;
      node("text",{x:x(time),y:170,"text-anchor":i===0?"start":i===2?"end":"middle"},this._historyTime(time));
    }
    node("text",{x:left,y:10},this._hass.config?.unit_system?.temperature || "°C");
    const pathFor=(key,step)=>{
      let path="",previous=null;
      for(const point of points){if(point[key]===null){previous=null;continue;}const px=x(point.time),py=y(point[key]);path+=previous===null?`M${px} ${py}`:step?`H${px}V${py}`:`L${px} ${py}`;previous=point;}
      if(previous)path+=`H${x(end)}`;
      return path;
    };
    node("path",{d:pathFor("temperature",false),class:"actual-line"});
    node("path",{d:pathFor("target",true),class:"target-line"});
    node("text",{x:left,y:129},"Varmebehov");
    let cursor=start,heat=null;
    const intervals=[];
    for(const point of points){const time=Math.max(start,point.time);if(time>cursor)intervals.push({from:cursor,to:time,heat});cursor=time;heat=point.heat;}
    if(cursor<end)intervals.push({from:cursor,to:end,heat});
    const merged=[];
    for(const interval of intervals){const last=merged.at(-1);if(last && last.heat===interval.heat && last.to===interval.from)last.to=interval.to;else merged.push({...interval});}
    for(const interval of merged){if(interval.heat===0)continue;const rect=node("rect",{x:x(interval.from),y:135,width:Math.max(0,x(interval.to)-x(interval.from)),height:10,class:interval.heat===1?"heat-band":"unknown-band"});const title=document.createElementNS("http://www.w3.org/2000/svg","title");title.textContent=`${this._historyTime(interval.from)}–${this._historyTime(interval.to)}: ${interval.heat===1?"Kalder på varme":"Ukendt"}`;rect.append(title);}
    this._nodes["history-detail"].textContent="Varmebehov følger termostatens meldte varmestatus.";
  }
  _historyPointer(event) {
    const cache=this._historyCache;if(!cache?.points.length)return;
    const rect=this._nodes["history-chart"].getBoundingClientRect();
    const time=cache.start+Math.max(0,Math.min(1,(event.clientX-rect.left-34)/(rect.width-42)))*(cache.end-cache.start);
    let low=0,high=cache.points.length-1;
    while(low<high){const mid=Math.ceil((low+high)/2);if(cache.points[mid].time<=time)low=mid;else high=mid-1;}
    const point=cache.points[low];
    this._nodes["history-detail"].textContent=`${this._historyTime(point.time)} · ${this._format(point.temperature)}° · ønsket ${this._format(point.target)}° · ${point.heat===null?"Ukendt varmebehov":point.heat===1?"Kalder på varme":"Intet varmebehov"}`;
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
    const config={...this._config,[name]:value};
    if (name === "climate" && value !== this._config.climate) config.comfort=salusComfortForClimate(this._hass,value);
    if ((name === "name" || name === "icon") && !value.trim()) delete config[name];
    this._config=config;
    this._render();
    this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:{...config}},bubbles:true,composed:true}));
  }
  _render() {
    if (!this._config || !this._hass) return;
    const states=this._hass.states || {};
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
