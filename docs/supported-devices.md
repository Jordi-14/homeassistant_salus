# Supported Devices

Device support depends on the model, gateway firmware, and the fields reported
by the UGE600 or UG800 local API. The integration exposes Home Assistant
entities from normalized `salus-it600-client` models whenever possible.

## Climate Devices

| Device | Gateway family | Home Assistant entities | Control support | Notes |
|---|---|---|---|---|
| HTRP-RF(50) | Standard iT600 thermostat | `climate`, sensors, diagnostic binary sensors, optional `lock` | Target temperature, HVAC mode, schedule/manual/off, child lock when reported | Heat-only behavior. Schedule is exposed as HVAC `Auto`. |
| TS600 | Standard iT600 thermostat | `climate`, sensors, diagnostic binary sensors, optional `lock` | Target temperature, HVAC mode, schedule/manual/off, child lock when reported | Heat-only behavior. |
| VS10WRF / VS10BRF | Standard iT600 thermostat | `climate`, sensors, diagnostic binary sensors, optional `lock` | Target temperature, HVAC mode, schedule/manual/off, child lock when reported | Heat-only behavior. |
| VS20WRF / VS20BRF | Standard iT600 thermostat | `climate`, sensors, diagnostic binary sensors, optional `lock` | Target temperature, HVAC mode, schedule/manual/off, child lock when reported | Heat-only behavior. |
| SQ610 / SQ610RF | Quantum thermostat | `climate`, humidity sensor, floor temperature sensor when reported, diagnostic binary sensors, optional `lock` | Target temperature, HVAC mode, preset mode, schedule/manual/away/off, cool mode when reported, child lock when reported | Schedule is exposed as preset `Follow Schedule`, not HVAC `Auto`. `Schedule Override` is shown only while the thermostat reports an active schedule override. |
| FC600 | Fan-coil controller | `climate`, humidity sensor, diagnostic binary sensors, optional `lock` | Target temperature, HVAC mode, preset mode, fan mode, schedule/manual/eco/off, child lock when reported | Supports fan modes and heat/cool operation when reported by the gateway. `Schedule Override` is shown only while active. |
| TRV3RF | Thermostatic radiator valve | `climate`, sensors, diagnostic binary sensors | Target temperature and heat/off behavior when reported | Exposed through the climate platform. |
| it600MINITRV | Thermostatic radiator valve | `climate`, battery sensor, diagnostic binary sensors | Target temperature and heat/off behavior when reported | Low battery is exposed from `TRVError22` when available. |
| EL600T / Elypso thermostat | Newer Zigbee 3.0-era thermostat | May appear as a generic thermostat | Under investigation | Read support may work when the gateway maps it to known thermostat fields. Write support may need model-specific client handling. |

## Sensors

| Device | Home Assistant entities | Notes |
|---|---|---|
| PS600 | Temperature sensor, battery sensor when reported | Standalone temperature sensor. |
| Thermostat humidity fields | Humidity sensor | Exposed when the thermostat reports humidity through normalized client fields. |
| Thermostat floor probe fields | Floor temperature sensor | Exposed when the thermostat reports an external floor probe value. |
| Smart plug metering fields | Power and energy sensors | Exposed for supported plug and relay devices that report metering data. |

## Binary Sensors

| Device | Home Assistant entities | Notes |
|---|---|---|
| SW600 | Window/door binary sensor, battery sensor when reported | Open/closed state. |
| OS600 | Window/door binary sensor, battery sensor when reported | Open/closed state. |
| WLS600 | Moisture binary sensor, battery sensor when reported | Water leak detection. |
| SD600 | Smoke binary sensor, battery sensor when reported | Smoke alarm state when exposed by the gateway. |
| SmokeSensor-EM | Smoke binary sensor, battery sensor when reported | Smoke alarm state when exposed by the gateway. |
| TRV10RFM | Diagnostic binary sensor | Receiver or TRV-related diagnostic state when reported by the gateway. |
| RX10RF | Diagnostic binary sensor | Receiver diagnostic state when reported by the gateway. |
| Thermostat error fields | Problem and battery problem binary sensors | Aggregated thermostat error flags are exposed with readable attributes. |

## Switches, Covers, And Locks

| Device | Home Assistant entities | Control support | Notes |
|---|---|---|---|
| SP600 | `switch`, power sensor, energy sensor | On/off | Metering is exposed when the gateway reports it. |
| SPE600 | `switch`, power sensor, energy sensor | On/off | Metering is exposed when the gateway reports it. |
| SR600 | `switch` | On/off | Treated as a dry relay switch, not as a cover. |
| RS600 relay endpoints | `switch` | On/off | Relay endpoints may appear separately from cover behavior. |
| RS600 shutter/blind | `cover` | Open, close, set position | A shutter installation may expose a cover entity. Disable unused switch or cover entities if the gateway exposes both representations for one device. |
| Thermostat child lock fields | `lock` | Lock/unlock keypad | Exposed for thermostat models that report child-lock support. |

## Known Unsupported Or Limited Devices

| Device | Status | Notes |
|---|---|---|
| SB600 | Not supported | Button actions only work through the Salus Smart Home app. |
| CSB600 | Not supported | Button actions only work through the Salus Smart Home app. |
| New or unlisted Zigbee 3.0 devices | Needs diagnostics | Open a Feature Request with diagnostics so the reported gateway fields can be mapped safely. |

## Requesting Support For Another Device

Open a Feature Request and include diagnostics from **Settings** -> **Devices &
Services** -> **Salus iT600** -> **Download diagnostics**. If the device can be
controlled from the Salus Smart Home app, mention that too; it helps separate
gateway support from integration support.
