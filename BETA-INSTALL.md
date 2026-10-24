# Floor Comfort beta 0.9.11b2

This fork beta adds the Off / Level 1 / Level 2 / Level 3 configuration select.
It replaces the code in `custom_components/salus`; do not run two integrations
with the `salus` domain or let two HACS repositories manage that directory.
Do not delete the configured Salus integration, its devices or its entity registry.

## Before installation

1. Record your Home Assistant version, current SALUS repository and installed
   version. This beta's Linux test matrix covers HA 2024.11.0, 2026.5.4 and
   2026.9.4. Compatibility with an unknown installed fork is not established.
2. Create and download a full Home Assistant backup that includes configuration.
   Separately copy the entire existing `custom_components/salus` directory to a
   folder outside `custom_components` and record the existing manifest version.
3. Save gateway connection details privately. Do not upload `.storage`, raw
   gateway captures or Home Assistant backups to GitHub.

## HACS installation

1. Add `https://github.com/MichaelBusackBertelsen/homeassistant_salus` as a custom
   repository, category **Integration**.
2. If another HACS repository already manages Salus, resolve that ownership
   before downloading this fork. Keep your configured integration and registry;
   do not uninstall blindly. Manual installation below avoids that ambiguity.
3. On the repository download/version screen enable prerelease/beta versions,
   select **v0.9.11b2**, and download. The release asset is `salus.zip`.
   Do not select the default branch, which does not contain this beta.
4. Restart Home Assistant once. The manifest installs the checksum-pinned fork
   client wheel automatically; no Python/Git installation or manual library edits
   are needed. Internet access to the public GitHub release is required.
5. Check the existing thermostat entities and Home Assistant logs first. Enable
   only Hall's disabled **Comfort Warm Floor / Gulvkomfort** entity under the
   device's entities. Test one change and compare the app, then enable other rooms.
   Do not edit the same thermostat in the app during a Home Assistant command.

HACS instructions follow https://www.hacs.xyz/docs/publish/integration/ and
https://www.hacs.xyz/docs/faq/custom_repositories/ . UI labels may vary by HACS version.

## Manual installation

Download the release's `salus.zip`. Extract its contents into
`/config/custom_components/salus/` (manifest.json must be directly in that
folder). Replace the previous integration directory completely after making the
backup; merging files can leave obsolete modules behind. Restart Home Assistant
and follow step 5 above. Never extract the ZIP directly into `custom_components`
or create a nested `salus/salus` directory.

## Backups, confirmation and error handling

Every actual write first saves the complete fresh device snapshot to a private
atomic private file named `.storage/salus_floor_backup_<hash>.json`. This is
**the latest pre-write snapshot per thermostat**, not an unlimited history or a
full Home Assistant backup. Storage failure prevents the command.

The client sends a command at most once, then checks exact reported settings and
successful echo for up to 120 seconds. The entity displays reported state only.
A lost reply is resolved by reading, not replaying. If other settings changed,
the command times out or a result is unrecognized, it reports an error and
retains the backup. It does not blindly write an old snapshot back. A previous
comfort level may be restored only using fresh validated state and a new counter.
There is no automatic restore service in this first beta.

## Scope and remaining limitation

Only SQ610RFNH firmware `00000054`, heating mode, a paired underfloor wiring
centre, no TRVs, matching known settings aliases/tail and the observed no-PIN
encoding are enabled. This does not make arbitrary SQ610 settings writable.

77 real writes have been confirmed, including the 75-write trial and the two
subsequent requested changes. Hardware evidence reaches counter **35**. The
beta uses PR54's sequence equations for current counter 0..254 / next 1..255.
Counters **36..255 are source-derived and untested on hardware**. Exhaustive
encoding tests do not prove device acceptance in that range.

At counter 255 the select becomes unavailable to prevent an untested rollover.
The beta never resets/wraps the counter. PIN variants, rollover and other firmware
are unfinished. Use the vendor app for unsupported states; do not change counters
or remove validation as a workaround. This beta is not a complete daily-use release.

## Return to your previous integration

1. Keep the recorded previous version and folder backup. Stop any automation
   using the new select and restore its previous comfort level through fresh
   validated state if desired; restoring integration code does not change the
   thermostat's current comfort level.
2. Reinstall the exact recorded release from the previous HACS repository, or
   replace `/config/custom_components/salus/` with the backed-up directory.
3. Restart Home Assistant. The old manifest restores its own dependency pin.
   Verify the existing entities and logs. Do not delete the config entry.
4. If configuration or registry changed unexpectedly, restore the full Home
   Assistant backup. Keep the new select disabled while investigating.

No running Home Assistant was changed while preparing this release.
