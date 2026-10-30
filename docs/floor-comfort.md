# Floor comfort, room card and weather automation

## Release dependency

This contribution depends on [salus-it600-client PR #32](https://github.com/Jordi-14/salus-it600-client/pull/32).
The integration's production requirement remains at the currently published
`0.7.0`; ordinary thermostats continue working, but that release does not
advertise the new floor-comfort capability. Release the client first, then
update the production requirement to that real published version before
shipping this feature. CI tests the immutable companion client contribution.
Version numbering and release decisions remain with the maintainers.

## Supported devices and commands

Only client-verified SQ610RFNH firmware `00000054` profiles expose a select.
Other devices retain normal climate controls. Floor comfort is Off or level
1/2/3; it does not alter the climate setpoint or HVAC mode. Entities are enabled
by default; explicit user disable choices are retained during migration.

Every write starts from fresh device settings. A private journal in Home
Assistant's `.storage` is atomically written, flushed and read back before the
command is sent. Confirmation checks the requested level and protected settings.
Unknown profiles, pending commands and unresolved journals block new writes.
Timeouts do not cause blind retry or automatic restoration of stale settings.
Keep unresolved journals for diagnosis; do not replay raw snapshots.

Counter metadata is copied unchanged and maintained by the device. Two actual
comfort-only changes were verified separately from the earlier 75-write trial
with the old encoder. Actual stored-counter rollover has not been observed.
The client protocol guide contains the evidence and limitations.

## Room card

The bundled `custom:salus-room-card` registers automatically with a graphical
editor. It supports compact and row layouts, temperature, humidity, target
temperature, optional floor-comfort controls, and expandable history. A room
without a floor entity shows disabled floor controls rather than a setup error.
History is fetched on expansion, defaults to 48 hours and shows measured
temperature, target and the thermostat's reported heating state. Demand is not
inferred from the difference between temperature and target. Unknown intervals
remain distinguishable. See [the card guide](../dashboard/Start-her.txt).

## Automation

Import the [comfort blueprint](../blueprints/automation/salus_comfort_rule.yaml)
after installing a release with the matching client. The form groups weather
sources, rooms, start periods, stop threshold, optional indoor limits and manual
control. Each field has help text; [the detailed guide](../blueprints/README.md)
includes decisions, examples and trace fields.

The hourly forecast starts a cycle when any valid forecast temperature in the
configured horizon is below the start threshold. Each room then gets its own
minimum runtime. At its boundary, measured outdoor temperature is preferred;
otherwise the weather entity's current temperature is used. A cold or
unmeasurable stop source extends that room by the configured period. A warm
source stops it unless its own optional indoor minimum requires a hold.
Forecast revisions do not cancel an active protected period.

An optional upper indoor threshold can interrupt an owned cycle on a new valid
room reading, including during protected periods. Indoor hold never starts a
cycle alone. Manual adoption is optional and preserves the existing level;
its minimum period starts at the qualifying evaluation. Manual changes end
ownership and start cooldown. Room matching uses the HA device registry,
not guessed entity names. Disabling the new minimum-runtime automation pauses
its commands; elapsed deadlines are evaluated when enabled again.

State and uncertain-write handling persist across restarts. Older maximum-time
templates retain their API semantics until explicitly re-imported. Take an HA
backup before migration; rollback requires the matching state and blueprint.
Do not run competing rules for the same room. Controller scenarios are primarily
simulated tests; user acceptance testing of the fork is not evidence for every
weather provider or thermostat firmware.

## Per-room timing and decision activity

All comfort diagnostics are inside the expanded card, above the temperature
chart; collapsed cards retain their compact controls. The panel shows observed
activation, protected-period start, next evaluation, current decision and saved
start evidence. Activity opens the exact floor entity's native HA logbook.

New decisions log requested commands separately from observed device state and
confirmed rule start. Start explanations include the future forecast minimum,
its timestamp, forecast fetch time, threshold, outdoor temperature at start and
owning rule. Extensions and stop decisions include numeric temperature grounds.
Repeated minute checks do not create duplicate progress entries. State changes
outside the rule are described as observations without guessing their actor.

Observation timestamps persist across restarts and unavailable gaps; changing
between active levels preserves the observed active timestamp. A device first
seen already active is labelled as discovered, not assigned an invented physical
start time. Rule start/adoption is a separate timestamp. Disabled rules show
paused status without promising a stop at an expired deadline. The existing
select also exposes these diagnostics as attributes.

Existing cycles retain their known timers and start_trigger_temperature_c.
Missing past forecast details and decisions are not reconstructed. Activity
retention follows the installation's Recorder filters and purge_keep_days
(default 10 days); this contribution does not change installation-wide retention.
The controller's per-room state survives restart independently of Activity purge.
The rule continues to use ordinary hourly forecast temperature, not feels-like.
