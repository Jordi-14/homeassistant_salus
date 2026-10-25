# SALUS beta 0.9.11b7

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
   **v0.9.11b7** from the prerelease/version picker. Keep your configured
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
is finalized only after exact read-back. Pending journals survive restart;
they cannot be overwritten by another command until exact fresh state resolves
the original outcome. Journals from earlier beta versions are still readable.

The client sends at most once and verifies the complete expected settings.
A lost response triggers reading, not replay. An observed shared `B34L`
response no longer incorrectly blocks all future changes: it requires two
unchanged fresh settings reads before dispatch. Unknown or newer settings
responses remain blocked. The undocumented meaning of B34L is not assumed.
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
implementation. The full counter range is not hardware-proven. The beta uses
the upstream non-wrapping equations through 255 and stops there; counter reset,
rollover, arbitrary PIN encodings and other firmware are unsupported.

The test matrix covers HA 2024.11.0, 2026.5.4, 2026.9.4 and the user's 2026.10.3.
Browser tests use simulated HA states/services; the release is not automatically
installed on the user's running instance. No physical setting changes are made
during this review. Installations on untested releases still require checking.

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
