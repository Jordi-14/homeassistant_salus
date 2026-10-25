# SALUS beta 0.9.11b11

## New in b11: comfort-only writes and separate start/stop temperatures

Floor writes now copy counter metadata unchanged from fresh state. Only comfort
is changed (plus the required write-frame marker). Two actual hardware tests
confirmed Off → 1 → Off with outgoing counters 40/41 unchanged and read-back
counters 41/42 maintained by the device. Confirmation and durable-journal
recovery compare actual comfort and every protected setting, without predicting
metadata. Older journals remain resolvable. The artificial 255 cutoff is removed;
the software never increments, calculates or resets counter bytes. Actual device
rollover remains unobserved; simulated boundary tests are not hardware proof.

With forecast enabled, **start uses the minimum in the next X hours** and
**temperature stop uses the current outdoor value** from the weather entity.
An outdoor sensor uses its current reading for both. A cold forecast does not
prevent a warm-current stop; a failed forecast does not block a valid warm stop.
If current temperature already reaches the enabled stop threshold, starting is
blocked to avoid immediate on/off cycling. With temperature stop disabled this
gate does not apply. Missing current data never falls back to a future forecast
for stopping; maximum runtime remains independent of all weather data.

Update HACS to **v0.9.11b11**, restart HA, re-import the simple comfort blueprint
and reload automations under **Settings → Tools → YAML**. Input names, configured
values and stored cycle deadlines are retained. No extra automation is needed.
In the Resultat trace step, `taendgrundlag_c` is the start temperature and
`slukgrundlag_c` is the current outdoor stop temperature. `slukdata` reports
current data validity separately from `vejrdata` (forecast). The previous
`temperaturgrundlag_c` field remains an alias of the start temperature.

## New in b10: see the actual comfort-rule decision

The evaluation action now optionally returns the actual temperature used, source
data status, forecast window/minimum timestamp/cache age, and each room's
decision, command, reported level, original runtime deadline and restart pause.
Explanations distinguish warm-enough, running, cooldown, manual control, other
rules, unavailable rooms and missing/incomplete forecasts. Unknown temperatures
remain null. No extra thermostat commands or weather fetches are used for reporting.

Update to **v0.9.11b10**, restart HA, then **re-import the simple comfort
blueprint** and reload automations. Updating HACS alone does not replace your
imported blueprint. Existing input settings and stored cycles remain compatible;
old b9 actions without a response variable continue to work.

Open the automation's next trace, select **Resultat – forklaring, temperatur og
timer**, then **Ændrede variabler**. The `forklaring` field explains the decision;
`temperaturgrundlag_c`, `vejrdata` and `rum_og_timer` provide the details. The
timestamp fields include a time-zone offset. Missing maximum runtime has a null
deadline, not a new four-hour limit. Failed commands still surface as errors.
Only new traces contain these details; old traces cannot be reconstructed.

## New in b9: one simple comfort rule

Install **v0.9.11b9 in HACS and restart Home Assistant**, then follow
[the Danish setup guide and new blueprint import link](blueprints/README.md).
The blueprint is named **SALUS – enkel gulvkomfort med slukgrænse og pause**.
It replaces the separate schedule/day-rule setup for new automations.
Existing imported blueprints are left intact; disable an old rule before
enabling the new rule for the same rooms.

Choose an outdoor sensor/current weather temperature or a rolling forecast
minimum, rooms, level, start threshold, optional warmer stop threshold, optional
maximum runtime, and minimum restart pause. Every field explains its purpose.
At least one stopping condition is required. When both are selected, the first
one wins. No manually created helpers are needed. The original runtime deadline
and per-room pause are saved before commands; restarts do not extend them.

Only floor comfort changes; normal climate control continues. Manually changed
levels are respected and already-active manual comfort is not adopted. A missing
temperature cannot start a room. Maximum runtime still applies if the automation
is disabled or weather fails. Offline thermostats cannot be guaranteed to switch
off at a deadline; overdue rooms are checked when available. An uncertain command
is not automatically replayed and creates a repair issue. Set the room to Off
and use **Nulstil blokeret Gulvkomfort-regel** after checking the actual setting.

The new controller uses the existing select backup/read-back path. This release
was tested with simulated services and clocks; no real thermostat test writes
were performed. At the b9 release the counter-255 restriction remained; it is removed in b11. Card version 1.3.1
and the existing dashboard layout are unchanged.

## New in b8: rooms without floor comfort

The floor-comfort entity is optional. In the graphical editor choose **Ingen
gulvkomfort** for thermostats that do not have this function. Temperature,
humidity when supported, target-temperature controls and click-only history
continue to work normally. The floor controls retain their place but are
disabled, with no configuration error or missing-floor warning.

Selecting another thermostat without a matching floor select clears the old
room's floor selection. A configured but missing/unavailable floor entity is
still reported, so a real entity failure is not silently treated as no feature.
The backend and the previous graph/layout behavior are unchanged.

## New in b7: stable positions and a multi-day plot

Room, temperature, desired temperature and floor controls keep fixed slots as
readings change or temporarily become unknown. Pending confirmation now appears
inside the existing desired-temperature caption, without inserting a footer
that changes the card height. History hover values use a floating tooltip.

The expanded plot defaults to 48 hours. Choose 6, 12, 24 or 48 hours in the
graphical editor. Both temperature curves are stepped, with blue actual and
gold desired temperatures. Actual heat-demand intervals are marked inside
the plot; unknown action data stays distinct. No demand is inferred from the
target/current temperature difference. The legend includes the last history
values and can locally hide/show series without another history request.

The graph adapts its height and tick density to its actual width, including
300 px cards and very wide rows. Multi-day dates are shown on the time axis.
Successful loads have no permanent fetched-time/unknown-status explanation
or narrative footer. Loading and actual errors remain visible. Wide row
headers distribute the controls rather than leaving one huge name column.

## New in b6: compact cards and rows

The graphical card editor now offers **Kompakt** and **Rækker** under **Layout**.
Kompakt is the default and puts measurements, a small temperature stepper and
four floor-level buttons in one small card. Rækker aligns the information
horizontally in a wide card and uses a floor-comfort menu. Narrow row cards
reflow so every control remains visible.

Choosing a layout in the editor sets the suggested width to half a section
for Kompakt or a full section for Rækker, with automatic height. Existing
saved widths are retained until you choose a layout or resize the card in HA.
An older card without an explicit layout shows a layout prompt; choose Kompakt
or Rækker once to apply the new suggested width. HA's normal layout controls
can still resize either style.

Click the card or arrow to expand the small history graph. Adjusting a
temperature or floor control does not expand it. No history is fetched on
load or while collapsed. Floor menus display reported values, with controls
disabled while a change awaits confirmation. Backend and gateway logic are
unchanged from b5. This release performs no hardware test writes.

## Fixed in b5: endless card-picker spinner

The extra frontend module now waits for Home Assistant before defining either
the card or its editor. HA 2026.10.3 installs a scoped custom element registry
during startup; registering before that could leave picker metadata visible
while losing the actual element definitions. The card picker then timed out
with `Custom element not found: salus-room-card` and kept showing a spinner.
This was an integration startup race, not a missing thermostat entity.

Browser regression tests use HA's exact scoped registry polyfill (0.0.10)
and cover either load order and an already-started frontend. Backend thermostat
logic and the client dependency are unchanged from b4.

## Update and add your own room cards

1. Keep a full Home Assistant backup and the previous working release.
2. In HACS, open MichaelBusackBertelsen/homeassistant_salus and download
   **v0.9.11b8** from the prerelease/version picker. Keep your configured
   Salus integration and existing devices. Restart Home Assistant.
3. Reload the browser or Home Assistant app so the bundled frontend module loads.
4. Open your own dashboard, choose Edit -> Add card, and search for
   **SALUS rumkort**. Choose a thermostat in the graphical editor. The matching
   floor-comfort select is chosen by registry device ID when available; it can
   also be chosen explicitly. Room title and icon are optional.
5. Repeat for the rooms you want. The card follows the dashboard theme and
   responsive sections layout. No separate frontend package, www file copying,
   manual resource registration or entity-ID list is needed for normal setup.

The card shows current temperature, humidity, desired temperature and floor
comfort Off/1/2/3. It uses Home Assistant's normal climate and select actions.
Existing dashboards are not replaced and no thermostat command is sent by
installing the integration, activating an entity, or rendering a card.

## Click-only history

Click the card background or its arrow to expand 48 hours of temperature by default,
desired temperature and thermostat-reported heat demand. History is fetched
only after opening it, for that one climate entity, with attribute changes
included. Requests use the authenticated Home Assistant connection.

The heat band uses `hvac_action == heating`; it is not inferred from a
setpoint/current-temperature difference and is not a separate boiler measurement.
Offline or absent action data is marked unknown. Hover/touch the graph for
values. Closing it starts no background polling. Reopening uses a short cache;
Opdater explicitly fetches fresh history. HA History/Recorder must retain the
climate entity. Temperature override sensors in advanced YAML do not replace
the climate source used by this history graph.

## Automatically enabled floor-comfort entities

Supported floor selects are enabled by default. Existing floor selects disabled
by the integration's original default are enabled before platform setup.
Explicit user disables, unrelated diagnostic entities, unsupported profiles
and other gateway entries are preserved. This enables the HA entity and does
not change the thermostat's comfort level.

## Write safeguards and reviewed fixes

A fresh backup is atomically written, fsynced and checked from disk before an
actual floor-comfort write. The latest pre-write journal for each thermostat
is kept privately in `.storage/salus_floor_backup_<hash>.json`. A backup error
prevents dispatch. The journal marks a new write pending before dispatch and
is finalized only after protected-settings and level read-back. Pending journals survive restart;
they cannot be overwritten by another command until verified fresh state resolves
the original outcome. Journals from earlier beta versions are still readable.

The client sends at most once and verifies the level and all protected settings.
Device-maintained counter metadata may change independently.
A lost response triggers reading, not replay. An observed shared `B34L`
response no longer incorrectly blocks all future changes: it requires two
unchanged fresh settings reads before dispatch. Unknown settings-response layouts and pending same-counter changes remain blocked. The undocumented meaning of B34L is not assumed.
Unrelated edits or unexpected results preserve the backup for review.
There is no blind automatic rollback or replay-backup action.

The code review also tightened finite numeric inputs/readings, validated
rounded setpoints against actual limits, made hex-alias comparison independent
of letter case and added a read-only fallback for an incomplete preferred
advanced-settings alias. Writer alias checks remain strict.

## Verified scope and unfinished protocol work

Floor-comfort writes remain restricted to SQ610RFNH firmware 00000054, heating
mode, a paired underfloor wiring centre, no TRVs and the validated no-PIN format.
75-write trial vectors and subsequent manual changes/read captures support the
historical incrementing strategy. Two further hardware captures verify the new
comfort-only strategy, without client-side counter arithmetic. The artificial
255 cutoff is removed. Actual hardware rollover, arbitrary PIN-required settings
and other firmware remain unverified.

The test matrix covers HA 2024.11.0, 2026.5.4, 2026.9.4 and the user's 2026.10.3.
Browser tests use simulated HA states/services; the release is not automatically
installed on the user's running instance. The two explicitly authorized comfort-only hardware changes are captured in
the client fixtures. Installation itself sends no thermostat changes. Installations on untested releases still require checking.

## Return to the previous beta

Reinstall the recorded working release in HACS and restart Home Assistant.
Keep the config entry and entity registry. Reload the browser. If any manually
configured room cards are not supported by that older version, remove them
from your dashboard. Code rollback does not change thermostat settings.
Restore your full HA backup if configuration/registry recovery is needed.

## References

- https://contributors.home-assistant.io/frontend/custom-ui/card/
- https://contributors.home-assistant.io/frontend/custom-ui/card-editor/
- https://contributors.home-assistant.io/blog/2024/06/18/async_register_static_paths/
- https://www.home-assistant.io/integrations/climate/
- https://www.home-assistant.io/integrations/select/
