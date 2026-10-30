const { chromium } = require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const output=path.join(root,'.dashboard-test-output');fs.mkdirSync(output,{recursive:true});
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.SALUS_CARD_BROWSER_CHANNEL ? {channel:process.env.SALUS_CARD_BROWSER_CHANNEL} : {})});
 const touch=process.env.SALUS_CARD_TEST_TOUCH==='1';
 const page=await browser.newPage({viewport:{width:1024,height:1000},colorScheme:'dark',hasTouch:touch});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.setContent(`<style>body{margin:20px;background:#111416;color:#f1f2f2;font-family:Segoe UI,sans-serif;--primary-text-color:#f1f2f2;--secondary-text-color:#a8b0b5;--ha-card-background:#1c2023;--divider-color:#303639;--secondary-background-color:#252b2e}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(260px,100%),1fr));gap:16px}</style><main></main>`);
 await page.evaluate(()=>customElements.define('home-assistant',class extends HTMLElement {}));
 await page.addScriptTag({path:path.join(root,'custom_components/salus/frontend/salus-room-card.js'),type:'module'});
 await page.waitForFunction(()=>!!customElements.get('salus-room-card'));
 await page.evaluate(()=>{
  window.calls=[];
  window.sample=()=>({language:'da',config:{unit_system:{temperature:'°C'}},states:{
   'climate.test':{state:'heat',attributes:{friendly_name:'Stuen',current_temperature:21.8,current_humidity:44,temperature:22,min_temp:5,max_temp:35,target_temp_step:0.5}},
   'select.test':{state:'level_1',attributes:{options:['off','level_1','level_2','level_3']}}
  },callService:async(...args)=>{window.calls.push(args);}});
  window.card=document.createElement('salus-room-card');
  card.setConfig({climate:'climate.test',comfort:'select.test',name:'Stuen',icon:'mdi:sofa-outline'});
  document.querySelector('main').append(card);
  window.data=sample();card.hass=data;
 });
 const checks=[];
 async function check(name,fn){await fn();checks.push(name);}
 const card=page.locator('salus-room-card').first();
 await check('No commands on render',async()=>{if(await page.evaluate(()=>calls.length)!==0)throw Error('Implicit command');});
 await check('Measurements and initial level',async()=>{
  if(await card.locator('#actual').textContent()!=='21,8')throw Error('Temperature');
  if(await card.locator('#humidity').textContent()!=='44')throw Error('Humidity');
  if(await card.locator('#floor-state').textContent()!=='Niveau 1')throw Error('Floor');
 });
 await check('Temperature service, no optimistic value, no duplicate clicks',async()=>{
  await card.locator('#plus').click();
  const calls=await page.evaluate(()=>window.calls);
  if(JSON.stringify(calls)!==JSON.stringify([['climate','set_temperature',{entity_id:'climate.test',temperature:22.5}]]))throw Error(JSON.stringify(calls));
  if(await card.locator('#target').textContent()!=='22,0')throw Error('Optimistic target');
  await page.evaluate(()=>card._changeTemperature(1));
  if(await page.evaluate(()=>calls.length)!==1)throw Error('Duplicate');
  await page.evaluate(()=>{data.states['climate.test'].attributes.temperature=22.5;card.hass=data;});
  if(await card.locator('#target').textContent()!=='22,5')throw Error('Readback');
 });
 await check('Floor service and reported-state confirmation',async()=>{
  await card.locator('[data-level="3"]').click();
  const last=await page.evaluate(()=>calls.at(-1));
  if(JSON.stringify(last)!==JSON.stringify(['select','select_option',{entity_id:'select.test',option:'level_3'}]))throw Error('Wrong select service');
  if(await card.locator('[data-level="1"]').getAttribute('aria-pressed')!=='true')throw Error('Optimistic floor');
  await page.evaluate(()=>{data.states['select.test'].state='level_3';card.hass=data;});
  if(await card.locator('[data-level="3"]').getAttribute('aria-pressed')!=='true')throw Error('No confirmation');
 });
 await check('App state update and independent unavailable handling',async()=>{
  await page.evaluate(()=>{data.states['select.test'].state='off';card.hass=data;});
  if(await card.locator('#floor-state').textContent()!=='Fra')throw Error('Off update');
  await page.evaluate(()=>{data.states['select.test'].state='unavailable';card.hass=data;});
  if(!await card.locator('[data-level="1"]').isDisabled())throw Error('Unavailable enabled');
  if(await card.locator('#actual').textContent()!=='21,8')throw Error('Climate hidden');
 });
 await check('Unknown values never become zero',async()=>{
  await page.evaluate(()=>{data=sample();data.states['climate.test'].attributes.current_humidity=null;data.states['climate.test'].attributes.current_temperature=null;card.hass=data;});
  if(await card.locator('#actual').textContent()!=='—'||await card.locator('#humidity').textContent()!=='—')throw Error('Missing value');
 });
 await check('Offline does not show stale attributes',async()=>{
  await page.evaluate(()=>{data=sample();data.states['climate.test'].state='unavailable';card.hass=data;});
  if(await card.locator('#actual').textContent()!=='—'||!await card.locator('#plus').isDisabled())throw Error('Offline');
 });
 await check('Limits, step and clamping',async()=>{
  await page.evaluate(()=>{calls.length=0;data=sample();data.states['climate.test'].attributes.temperature=34.8;card.hass=data;});
  await card.locator('#plus').click();
  if(await page.evaluate(()=>calls[0][2].temperature)!==35)throw Error('Upper clamp');
  await page.evaluate(()=>{data.states['climate.test'].attributes.temperature=35;card.hass=data;});
  if(!await card.locator('#plus').isDisabled())throw Error('Upper limit');
  await page.evaluate(()=>{data.states['climate.test'].attributes.temperature=5;card.hass=data;});
  if(!await card.locator('#minus').isDisabled())throw Error('Lower limit');
 });
 await check('Missing limits disable temperature writes',async()=>{
  await page.evaluate(()=>{data=sample();delete data.states['climate.test'].attributes.min_temp;card.hass=data;});
  if(!await card.locator('#plus').isDisabled())throw Error('Missing bound');
 });
 await check('Service failure displayed, no retry',async()=>{
  await page.evaluate(()=>{calls.length=0;data=sample();data.callService=async(...args)=>{calls.push(args);throw Error('Disk full');};card.hass=data;});
  await card.locator('[data-level="3"]').click();
  if(!await card.locator('#error').textContent().then(t=>t.includes('Disk full')))throw Error('Error hidden');
  if(await page.evaluate(()=>calls.length)!==1)throw Error('Retry');
 });
 await check('Optional sensors and safe text',async()=>{
  await page.evaluate(()=>{data=sample();data.states['sensor.humidity']={state:'61',attributes:{}};data.states['sensor.temperature']={state:'23.2',attributes:{unit_of_measurement:'°C'}};card.setConfig({climate:'climate.test',comfort:'select.test',humidity_sensor:'sensor.humidity',temperature_sensor:'sensor.temperature',name:'<img src=x onerror=alert(1)>'});card.hass=data;});
  if(await card.locator('#actual').textContent()!=='23,2'||await card.locator('#humidity').textContent()!=='61')throw Error('Sensor override');
  if(await card.locator('img').count()!==0)throw Error('Unsafe HTML');
 });
 await check('No action if a select option is unsupported',async()=>{
  await page.evaluate(()=>{data=sample();data.states['select.test'].attributes.options=['off','level_1'];card.hass=data;});
  if(!await card.locator('[data-level="3"]').isDisabled())throw Error('Unsupported option');
 });
 await check('Bundled card picker, graphical editor and same-device pairing',async()=>{
  await page.evaluate(()=>{
   data=sample();
   data.entities={'climate.test':{device_id:'one'},'select.test':{device_id:'one'},'climate.other':{device_id:'two'},'select.other':{device_id:'two'}};
   data.states['climate.other']={...data.states['climate.test'],attributes:{...data.states['climate.test'].attributes,friendly_name:'Kontor'}};
   data.states['select.other']={...data.states['select.test'],attributes:{...data.states['select.test'].attributes,friendly_name:'Kontor gulvkomfort'}};
   const kind=customElements.get('salus-room-card');
   window.stub=kind.getStubConfig(data,['climate.test'],[]);
   window.editor=kind.getConfigElement();
   editor.setConfig({type:'custom:salus-room-card',...stub});editor.hass=data;
   window.editorConfig=null;editor.addEventListener('config-changed',event=>window.editorConfig=event.detail.config);
   document.body.append(editor);
  });
  if(await page.evaluate(()=>stub.comfort)!=='select.test')throw Error('Default pairing');
  const editor=page.locator('salus-room-card-editor');
  await editor.locator('#climate').selectOption('climate.other');
  const config=await page.evaluate(()=>editorConfig);
  if(config.comfort!=='select.other'||config.type!=='custom:salus-room-card')throw Error('Editor pairing');
  await editor.locator('#history_hours').selectOption('24');
  if(await page.evaluate(()=>editorConfig.history_hours)!==24)throw Error('History editor value is not numeric');
  await editor.locator('#name').fill('Mit kontor');await editor.locator('#name').dispatchEvent('change');
  if(await page.evaluate(()=>editorConfig.name)!=='Mit kontor')throw Error('Editor name');
  if(!await page.evaluate(()=>customCards.some(card=>card.type==='salus-room-card'&&card.name==='SALUS rumkort')))throw Error('Picker metadata');
  await editor.locator('#layout').selectOption('rows');
  if(await page.evaluate(()=>editorConfig.layout)!=='rows')throw Error('Editor layout');
  if(await page.evaluate(()=>editorConfig.grid_options.columns)!==12)throw Error('Row editor width');
  await editor.locator('#layout').selectOption('compact');
  if(await page.evaluate(()=>editorConfig.grid_options.columns)!==6)throw Error('Compact editor width');
  await page.evaluate(()=>{data.states['climate.plain']={...data.states['climate.test']};data.entities['climate.plain']={device_id:'no-floor'};editor.hass=data;});
  await editor.locator('#climate').selectOption('climate.plain');
  if(await page.evaluate(()=>editorConfig.comfort)!=='')throw Error('Old room floor entity retained');
  if(await editor.locator('#comfort').inputValue()!=='')throw Error('Optional floor editor value');
  if(!await editor.locator('#comfort option').first().textContent().then(t=>t.includes('Ingen')))throw Error('Optional floor placeholder');
  await page.evaluate(()=>editor.remove());
 });
 await check('History fetch is click-only, attribute-complete and read-only',async()=>{
  await page.evaluate(()=>{
   card.setConfig({climate:'climate.test',comfort:'select.test',name:'Stuen'});data=sample();window.historyCalls=[];
   const now=Date.now();
   const item=(hours,temp,action,state='heat')=>({entity_id:'climate.test',state,last_changed:new Date(now-5*3600000).toISOString(),last_updated:new Date(now-hours*3600000).toISOString(),attributes:{current_temperature:temp,temperature:22,hvac_action:action}});
   window.historyRows=[[item(5,20.5,'heating'),item(3,21.5,'idle'),item(2,21.5,'heating','unavailable'),item(1,22,'idle')]];
   data.callApi=async(...args)=>{historyCalls.push(args);return historyRows;};card.hass=data;
  });
  if(await page.evaluate(()=>historyCalls.length)!==0)throw Error('Eager history');
  await card.locator('#history-toggle').click();
  await card.locator('#history-chart').waitFor({state:'visible'});
  const request=await page.evaluate(()=>historyCalls[0]);
  const startTime=Date.parse(decodeURIComponent(request[1].split('history/period/')[1].split('?')[0]));
  const endTime=Date.parse(new URLSearchParams(request[1].split('?')[1]).get('end_time'));
  if(Math.abs(endTime-startTime-48*3600000)>1000)throw Error('Default history is not 48 hours');
  if(request[0]!=='GET'||!request[1].includes('filter_entity_id=climate.test')||!request[1].includes('significant_changes_only=0'))throw Error('History request');
  if(await card.locator('.actual-line').count()!==1||await card.locator('.heat-band').count()!==1)throw Error('History series');
  if(await card.locator('.unknown-band').count()<1)throw Error('Offline heat assumed active');
  await card.locator('#history-toggle').click();
  if(await card.locator('#history').isVisible())throw Error('History did not collapse');
  await page.evaluate(()=>{for(let i=0;i<5;i++)card.hass=data;});
  if(await page.evaluate(()=>historyCalls.length)!==1)throw Error('Background history request');
  await card.locator('#history-toggle').click();
  if(await page.evaluate(()=>historyCalls.length)!==1)throw Error('No history cache');
  await card.locator('#history-refresh').click();
  if(await page.evaluate(()=>historyCalls.length)!==2)throw Error('Explicit refresh missing');
 });
 await check('Stepped multi-day plot, quiet success and local legend controls',async()=>{
  if(!await card.locator('#history-message').isHidden())throw Error('Success explanation still occupies space');
  if(!await card.locator('#history-detail').isHidden())throw Error('Permanent history footer');
  const geometry=await card.locator('#history-chart').evaluate(svg=>({height:svg.getBoundingClientRect().height,path:svg.querySelector('.actual-line').getAttribute('d'),heatHeight:Number(svg.querySelector('.heat-band').getAttribute('height'))}));
  if(!geometry.path.includes('H')||!geometry.path.includes('V')||geometry.path.includes('L'))throw Error('Actual temperature is not stepped');
  if(geometry.heatHeight<geometry.height/3)throw Error('Heat still in detached strip');
  if(!await card.locator('#legend-target').textContent().then(t=>t.includes('22,0')))throw Error('Legend value missing');
  const beforeHover=await card.evaluate(el=>el.getBoundingClientRect().height);
  await card.locator('#history-chart').hover();
  if(!await card.locator('#history-detail').isVisible())throw Error('Floating hover detail missing');
  if(Math.abs(beforeHover-await card.evaluate(el=>el.getBoundingClientRect().height))>.75)throw Error('Hover changed card height');
  await card.locator('#name').hover();
  if(!await card.locator('#history-detail').isHidden())throw Error('Tooltip did not close');
  const before=await page.evaluate(()=>historyCalls.length);
  await card.locator('[data-series="temperature"]').click();
  if(await card.locator('.actual-line').isVisible())throw Error('Legend did not hide line');
  await card.locator('[data-series="temperature"]').click();
  if(!await card.locator('.actual-line').isVisible())throw Error('Legend did not restore line');
  if(await page.evaluate(()=>historyCalls.length)!==before)throw Error('Legend refetched history');
 });
 await check('History errors do not break controls or retry in the background',async()=>{
  await page.evaluate(()=>{data.callApi=async(...args)=>{historyCalls.push(args);throw Error('Recorder unavailable');};card.hass=data;});
  await card.locator('#history-refresh').click();
  if(!await card.locator('#history-message').textContent().then(t=>t.includes('kunne ikke hentes')))throw Error('History error hidden');
  const count=await page.evaluate(()=>historyCalls.length);
  await page.evaluate(()=>{card.hass=data;card.hass=data;});
  if(await page.evaluate(()=>historyCalls.length)!==count)throw Error('History auto retry');
  if(await card.locator('#plus').isDisabled())throw Error('History error disabled controls');
  await card.locator('#history-toggle').click();
 });
 await check('Row menu uses reported state and never expands history',async()=>{
  await page.evaluate(()=>{card.setConfig({climate:'climate.test',comfort:'select.test',layout:'rows'});data=sample();calls=[];card.hass=data;});
  if(!await card.locator('.levels').isHidden())throw Error('Row buttons visible');
  await card.locator('#floor-select').selectOption('3');
  if(await page.evaluate(()=>calls.length)!==1)throw Error('Menu command count');
  if(await card.locator('#floor-select').inputValue()!=='1')throw Error('Optimistic menu value');
  if(!await card.locator('#history').isHidden())throw Error('Menu opened history');
  if(!await card.locator('#floor-select').isDisabled())throw Error('Pending menu enabled');
  await page.evaluate(()=>{data.states['select.test'].state='level_3';card.hass=data;});
  if(await card.locator('#floor-select').inputValue()!=='3')throw Error('Menu confirmation');
  await page.evaluate(()=>{data.states['select.test'].state='unavailable';card.hass=data;});
  if(!await card.locator('#floor-select').isDisabled())throw Error('Offline menu enabled');
 });
 await check('Readings and controls stay fixed across updates, unknown values and pending writes',async()=>{
  for(const [layout,width] of [['compact',308],['rows',736],['rows',2000]]){
   await page.setViewportSize({width:Math.max(1024,width+40),height:1000});
   await page.evaluate(({layout,width})=>{card.style.width=width+'px';card.setConfig({climate:'climate.test',comfort:'select.test',layout,name:'Stort badeværelse'});data=sample();card.hass=data;},{layout,width});
   const boxes=()=>card.evaluate(el=>Object.fromEntries(['#name','.temperature-reading','.target-control','#floor'].map(selector=>{const r=el.shadowRoot.querySelector(selector).getBoundingClientRect(),host=el.getBoundingClientRect();return[selector,{x:r.x-host.x,y:r.y-host.y,width:r.width,height:r.height}];})));
   const initial=await boxes();
   async function stable(label){const current=await boxes();for(const key of Object.keys(initial))for(const axis of ['x','y','width','height'])if(Math.abs(initial[key][axis]-current[key][axis])>.75)throw Error(`${layout}/${width} ${label} moved ${key}.${axis}: ${initial[key][axis]} -> ${current[key][axis]}`);}
   await page.evaluate(()=>{data.states['climate.test'].attributes={...data.states['climate.test'].attributes,current_temperature:9,current_humidity:100,temperature:5};card.hass=data;});
   await stable('short numeric values');
   await page.evaluate(()=>{data.states['climate.test'].attributes={...data.states['climate.test'].attributes,current_temperature:null,current_humidity:null,temperature:null};card.hass=data;});
   await stable('unknown values');
   await page.evaluate(()=>{data.states['climate.test'].state='unavailable';data.states['select.test'].state='off';card.hass=data;});
   await stable('unavailable values');
   await page.evaluate(()=>{data=sample();data.callService=()=>new Promise(resolve=>window.resolveControl=resolve);card.hass=data;});
   const height=await card.evaluate(el=>el.getBoundingClientRect().height);
   await card.locator('#plus').click();
   await stable('pending confirmation');
   if(Math.abs(height-await card.evaluate(el=>el.getBoundingClientRect().height))>.75)throw Error('Pending status changed card height');
   await page.evaluate(()=>{data.states['climate.test'].attributes.temperature=22.5;card.hass=data;resolveControl();});
   await page.waitForFunction(()=>!card._inFlight);
   await stable('confirmed value');
  }
  await page.evaluate(()=>{card.style.width='';});
 });
 await check('Compact and rows fit their actual container, including narrow cards',async()=>{
  for(const layout of ['compact','rows']){
   for(const width of [2000,1024,736,600,580,540,340,280]){
    await page.setViewportSize({width:1024,height:1000});
    await page.evaluate(({layout,width})=>{card.style.width=width+'px';card.setConfig({climate:'climate.test',comfort:'select.test',layout,name:'Stort badeværelse'});data=sample();card.hass=data;},{layout,width});
    const bounds=await card.evaluate(el=>({width:el.clientWidth,scroll:el.shadowRoot.querySelector('ha-card').scrollWidth,height:el.shadowRoot.querySelector('ha-card').getBoundingClientRect().height,options:el.getGridOptions()}));
    if(bounds.scroll>bounds.width+1)throw Error(`${layout}/${width}: overflow ${JSON.stringify(bounds)}`);
    if(bounds.height>(touch?210:155))throw Error(`${layout}/${width}: oversized ${bounds.height}`);
    if(layout==='rows'&&width>=580&&bounds.height>100)throw Error('Row not horizontal');
    if(layout==='rows'&&width===2000){
     const fraction=await card.evaluate(el=>(el.shadowRoot.querySelector('.temperature-reading').getBoundingClientRect().left-el.getBoundingClientRect().left)/el.clientWidth);
     if(fraction>.65||fraction<.2)throw Error('Wide row still has empty left area');
    }
    if(bounds.options.columns!==(layout==='rows'?12:6))throw Error('Grid width');
   }
  }
  await page.evaluate(()=>{card.style.width='';});
 });
 await check('Rooms without floor comfort keep readings, temperature controls and history',async()=>{
  for(const layout of ['compact','rows'])for(const comfort of [undefined,'',null]){
   await page.evaluate(({layout,comfort})=>{card.setConfig({climate:'climate.test',comfort,layout});data=sample();delete data.states['select.test'];calls=[];window.optionalHistoryCalls=[];data.callApi=async(...args)=>{optionalHistoryCalls.push(args);return historyRows;};card.hass=data;},{layout,comfort});
   if(await card.locator('#actual').textContent()!=='21,8')throw Error('Optional floor hid temperature');
   if(await card.locator('#plus').isDisabled())throw Error('Optional floor disabled climate');
   if(!await card.locator('#status').isHidden())throw Error('No-floor warning');
   if(!await card.locator('#floor-select').isDisabled())throw Error('No-floor menu enabled');
   for(const b of await card.locator('[data-level]').all())if(!await b.isDisabled())throw Error('No-floor level enabled');
   await page.evaluate(()=>card._changeComfort(3));
   if(await page.evaluate(()=>calls.length)!==0)throw Error('Implicit floor write');
   await card.locator('#history-toggle').click();
   await card.locator('.actual-line').waitFor({state:'attached'});
   if(await page.evaluate(()=>optionalHistoryCalls.length)!==1)throw Error('No-floor history failed');
   await card.locator('#history-toggle').click();
   await card.locator('#plus').click();
   if(await page.evaluate(()=>calls[0]?.[0])!=='climate')throw Error('No-floor climate command failed');
   await page.evaluate(()=>{data.states['climate.test'].attributes.temperature=22.5;card.hass=data;});
  }
  await page.evaluate(()=>{card.setConfig({climate:'climate.test',comfort:'select.missing'});data=sample();card.hass=data;});
  if(await card.locator('#status').isHidden())throw Error('Explicit missing ID silently ignored');
 });
 await check('Per-room comfort timestamps, paused timers and entity activity',async()=>{
  await page.evaluate(()=>{
   card.style.width='';card.setConfig({climate:'climate.test',comfort:'select.test',layout:'rows'});data=sample();
   data.config.time_zone='Europe/Copenhagen';calls=[];window.moreInfo=[];
   card.addEventListener('hass-more-info',event=>moreInfo.push(event.detail.entityId));
   Object.assign(data.states['select.test'].attributes,{comfort_phase:'running',comfort_rule:'automation.test',comfort_automation_enabled:true,
    comfort_observed_on_at:'2026-10-29T14:35:15+01:00',comfort_on_time_basis:'observed_transition',
    comfort_period_started_at:'2026-10-29T14:35:15+01:00',
    comfort_next_check_at:'2026-10-29T20:35:15+01:00',comfort_last_reason:'Minimumperioden løber.',
    comfort_start_evidence:{temperature_c:7.5,start_below_c:8,minimum_at:'2026-10-29T21:00:00+01:00'}});
   data.callApi=async()=>historyRows;card.hass=data;
  });
  if(!/14[.:]35/.test(await card.locator('#comfort-start').textContent()))throw Error('Missing observed start');
  if(!/20[.:]35/.test(await card.locator('#comfort-next').textContent()))throw Error('Missing next check');
  if(!await card.locator('#comfort-timing').isHidden())throw Error('Timing leaked into collapsed card');
  if(!await card.locator('#comfort-details').isHidden())throw Error('Details leaked into collapsed card');
  if(!await card.locator('#comfort-activity').isHidden())throw Error('Activity should be collapsed');
  await card.locator('#history-toggle').click();
  if(!await card.locator('#comfort-timing').isVisible())throw Error('Expanded timing missing');
  if(!await card.locator('#comfort-details').isVisible())throw Error('Expanded details missing');
  if(!await card.locator('#comfort-period').isVisible())throw Error('Missing rule period');
  if(!(await card.locator('#comfort-reason').textContent()).includes('7,5'))throw Error('Missing trigger evidence');
  await card.locator('#comfort-activity').click();
  if(JSON.stringify(await page.evaluate(()=>moreInfo))!=='["select.test"]')throw Error('Wrong activity entity');
  for(const width of [320,390,900]){
   await page.evaluate(width=>{card.style.width=width+'px';},width);
   if(await card.evaluate(el=>el.shadowRoot.querySelector('ha-card').scrollWidth>el.clientWidth+1))throw Error('Expanded timing overflow '+width);
  }
  await card.screenshot({path:path.join(output,'comfort-expanded-preview.png')});
  await card.locator('#history-toggle').click();
  if(!await card.locator('#comfort-timing').isHidden())throw Error('Timing remained after collapse');
  for(const width of [320,390,1000]){
   await page.evaluate(width=>{card.style.width=width+'px';},width);
   if(await card.evaluate(el=>el.shadowRoot.querySelector('ha-card').scrollWidth>el.clientWidth+1))throw Error('Timing overflow '+width);
  }
  await page.evaluate(()=>{data.states['select.test'].attributes.comfort_automation_enabled=false;data.states['select.test'].attributes.comfort_next_check_at=null;card.hass=data;});
  if(await card.locator('#comfort-next').textContent()!=='Automatik pauset')throw Error('Paused deadline promise');
  await page.evaluate(()=>{data.states['select.test'].attributes.comfort_on_time_basis='already_active';card.hass=data;});
  if(!(await card.locator('#comfort-start').textContent()).startsWith('Opdaget tændt'))throw Error('Invented original start');
  await page.evaluate(()=>{data.states['select.test'].state='off';data.states['select.test'].attributes.comfort_last_off_at='2026-10-29T21:01:00+01:00';card.hass=data;});
  if(!(await card.locator('#comfort-start').textContent()).startsWith('Slukket registreret'))throw Error('Missing Off timestamp');
  if(await card.locator('#comfort-next').textContent())throw Error('Off still has next check');
  await page.evaluate(()=>{data.states['select.test'].state='unavailable';card.hass=data;});
  if(!await card.locator('#comfort-timing').isHidden())throw Error('Unavailable claims active timing');
  if(await page.evaluate(()=>calls.length)!==0)throw Error('Diagnostics dispatched command');
  await page.evaluate(()=>{card.style.width='';});
 });
 await check('Seven room cards and responsive layouts',async()=>{
  await page.evaluate(()=>{
   card.setConfig({climate:'climate.test',comfort:'select.test',name:'Stuen',icon:'mdi:sofa-outline'});data=sample();card.hass=data;
   for(const name of ['Hall','Bryggers','Køkken','Kontor','Stort badeværelse','Lille badeværelse']){
    const other=document.createElement('salus-room-card');other.setConfig({climate:'climate.test',comfort:'select.test',name});other.hass=sample();document.querySelector('main').append(other);
   }
  });
  for(const width of [1024,736,390,320]){
   await page.setViewportSize({width,height:1100});
   const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
   if(overflow)throw Error('Page overflow '+width);
   for(const room of await page.locator('salus-room-card').all()){
    if(await room.evaluate(el=>el.shadowRoot.querySelector('ha-card').scrollWidth>el.clientWidth+1))throw Error('Card overflow '+width);
   }
  }
 });
 await page.setViewportSize({width:1024,height:1100});
 await page.screenshot({path:path.join(output,'dashboard-preview.png'),fullPage:true});
 if(errors.length)throw Error(errors.join('\n'));
 const report={passed:checks.length,checks,limitations:['Browser test uses simulated Home Assistant entities and services.','No running Home Assistant or gateway settings changed.','Card picker and graphical editor tested with simulated registry device links.']};
 fs.writeFileSync(path.join(output,'testresultater.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify(report));
 await browser.close();
})();
