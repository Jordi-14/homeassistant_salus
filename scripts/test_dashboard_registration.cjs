// HA 2026.10.3 loads extra modules concurrently with app.ts, which installs
// @webcomponents/scoped-custom-element-registry@0.0.10 before home-assistant.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const modulePath=path.join(root,'custom_components/salus/frontend/salus-room-card.js');
const registryPath=process.env.SALUS_SCOPED_REGISTRY_PATH || require.resolve('@webcomponents/scoped-custom-element-registry/scoped-custom-element-registry.min.js');
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.SALUS_CARD_BROWSER_CHANNEL?{channel:process.env.SALUS_CARD_BROWSER_CHANNEL}:{})});
 const results=[];
 try {
  for(const order of ['extra-module-first','polyfill-first','ha-already-ready']) {
   const page=await browser.newPage();
   const errors=[];page.on('pageerror',error=>errors.push(error.message));
   const defineHA=()=>page.evaluate(()=>customElements.define('home-assistant',class extends HTMLElement {}));
   if(order==='extra-module-first')await page.addScriptTag({path:modulePath,type:'module'});
   await page.addScriptTag({path:registryPath});
   if(order==='ha-already-ready')await defineHA();
   if(order!=='extra-module-first')await page.addScriptTag({path:modulePath,type:'module'});
   if(order!=='ha-already-ready')await defineHA();
   await page.waitForFunction(()=>!!customElements.get('salus-room-card'));
   // Exercise the picker path: lookup class, await stub, merge type, configure
   // preview and editor. Never call a real service or fetch actual history.
   const result=await page.evaluate(async()=>{
    let calls=0;
    const hass={language:'da',config:{unit_system:{temperature:'°C'}},
     entities:{'climate.room':{device_id:'test'},'select.floor':{device_id:'test'}},
     states:{'climate.room':{state:'heat',attributes:{friendly_name:'Test',current_temperature:21,current_humidity:45,temperature:22}},
      'select.floor':{state:'off',attributes:{options:['off','level_1','level_2','level_3']}}},
     callService:async()=>{calls++;},callApi:async()=>{calls++;}};
    const cls=customElements.get('salus-room-card');
    const config={type:'custom:salus-room-card',...await cls.getStubConfig(hass,[],Object.keys(hass.states))};
    const card=document.createElement('salus-room-card');card.setConfig(config);card.hass=hass;document.body.append(card);
    const editor=await cls.getConfigElement();editor.setConfig(config);editor.hass=hass;document.body.append(editor);
    return {config,editor:editor.localName,temperature:card.shadowRoot.querySelector('#actual').textContent,
     title:window.customCards.find(card=>card.type==='salus-room-card')?.name,calls};
   });
   assert.equal(result.config.comfort,'select.floor');
   assert.equal(result.editor,'salus-room-card-editor');
   assert.equal(result.temperature,'21,0');
   assert.equal(result.title,'SALUS rumkort');
   assert.equal(result.calls,0);
   // Updating a module URL must not duplicate registry definitions or metadata.
   await page.addScriptTag({content:fs.readFileSync(modulePath,'utf8'),type:'module'});
   await page.evaluate(()=>Promise.resolve());
   assert.equal(await page.evaluate(()=>window.customCards.filter(c=>c.type==='salus-room-card').length),1);
   assert.deepEqual(errors,[]);
   results.push({order,status:'passed'});await page.close();
  }
  fs.mkdirSync(path.join(root,'.dashboard-test-output'),{recursive:true});
  fs.writeFileSync(path.join(root,'.dashboard-test-output/registration-results.json'),JSON.stringify(results,null,2));
  console.log(JSON.stringify(results));
 } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
