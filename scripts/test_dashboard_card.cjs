const { chromium } = require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const output=path.join(root,'.dashboard-test-output');fs.mkdirSync(output,{recursive:true});
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.SALUS_CARD_BROWSER_CHANNEL ? {channel:process.env.SALUS_CARD_BROWSER_CHANNEL} : {})});
 const page=await browser.newPage({viewport:{width:1024,height:1000},colorScheme:'dark'});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.setContent(`<style>body{margin:20px;background:#111416;color:#f1f2f2;font-family:Segoe UI,sans-serif;--primary-text-color:#f1f2f2;--secondary-text-color:#a8b0b5;--ha-card-background:#1c2023;--divider-color:#303639;--secondary-background-color:#252b2e}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(260px,100%),1fr));gap:16px}</style><main></main>`);
 await page.addScriptTag({path:path.join(root,'dashboard/www/salus-dashboard/salus-room-card.js')});
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
 const report={passed:checks.length,checks,limitations:['Browser test uses simulated Home Assistant entities and services.','No running Home Assistant or gateway settings changed.','Entity IDs still need to be mapped to the user installation.']};
 fs.writeFileSync(path.join(output,'testresultater.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify(report));
 await browser.close();
})();
