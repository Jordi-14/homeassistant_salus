# Installation and Migration Through HACS

`Jordi-14/homeassistant_salus` is now included in the default HACS catalog.
The repository URL determines whether you need to migrate, even if HACS shows
both repositories under the same **Salus iT600** name.

| Starting point | Path |
|---|---|
| No Salus integration installed | [New users](#new-users) |
| Old default listing: `epoplavskis/homeassistant_salus` | [Switch from the old default](#from-the-old-hacs-default-epoplavskis) |
| This repository added through Custom repositories | [Keep the existing installation](#from-this-repository-added-as-a-hacs-custom-repository) |

## New Users

Follow [Installation in the README](../README.md#installation), then configure
Salus iT600 in **Settings** > **Devices & Services**. No custom repository is
needed.

## Before Migrating

1. Back up your Home Assistant configuration.
2. Open the installed Salus repository in HACS and check its GitHub URL.
3. Note the installed version.
4. Download diagnostics from **Settings** > **Devices & Services** >
   **Salus iT600**, if your installed version supports diagnostics.

The integration domain remains `salus`. Keep the existing entry in
**Settings** > **Devices & Services** so the gateway configuration and existing
entity registry records can be reused. Changing the HACS download source is
separate from deleting that Home Assistant entry.

## From the Old HACS Default (epoplavskis)

These steps also apply if you added `epoplavskis/homeassistant_salus` or another
older fork as a custom repository.

1. In HACS, open the installed Salus repository and confirm its URL is the old
   fork, rather than `Jordi-14/homeassistant_salus`.
2. Use that repository's menu to remove its HACS download. This can remove the
   installed integration files. Keep the Salus entry under **Settings** >
   **Devices & Services**, and do not restart Home Assistant yet.
3. If the old fork was added as a custom repository, remove its URL from
   HACS's **Custom repositories** list too.
4. Search HACS for **Salus iT600**, clearing any downloaded-only filter.
   Select the default listing for `Jordi-14/homeassistant_salus` and download
   the latest stable release. Do not add it as a custom repository.
5. Once the new download finishes successfully, restart Home Assistant.
6. Open **Settings** > **Devices & Services** and check the existing Salus
   integration. Do not add a second gateway entry.

Both repositories install to `custom_components/salus`. Finish removing the old
HACS download before downloading the new one; removing the old download
later could delete the newly installed files. Do not keep both forks installed.

The shared domain allows reuse of the existing configuration, but entity
coverage and unique IDs can differ between versions. Check the entities and
automations after restarting, as described below.

## From This Repository Added as a HACS Custom Repository

If the installed repository URL is already `Jordi-14/homeassistant_salus`, you
already have the correct integration. Inclusion in the default catalog does
not require a reinstall or a new gateway setup.

1. Keep the existing HACS download and Home Assistant integration entry.
2. Continue installing updates from the same repository in HACS and restart
   Home Assistant after an integration update, as usual.
3. Allow HACS to refresh its catalog. The repository can then be recognized as
   a default entry rather than a custom one.

You do not need to remove the custom repository registration manually. Do not
remove the installed download just to change its label. If your custom URL
points to a different fork, use the old-default migration steps above instead.

## After Restart

Check the integration before changing entity IDs:

- All expected devices are present.
- Climate, sensor, binary sensor, switch, cover, and lock entities become available after polling.
- Existing automations still reference the intended entities.
- Diagnostics download still works.
- Logs do not show repeated setup, polling, or duplicate unique ID errors.

For duplicate-looking entities:

1. Compare the old and new entity state, device class, unit, and attributes.
2. Check which entity your dashboards and automations currently use.
3. Disable the unused entity first if you are not sure.
4. Delete old registry entries only after confirming they are not used.
5. Rename the kept entity if you need to preserve the old dashboard or automation name.

## When To Open An Issue

Open a Support / Bug issue if migration leaves missing devices, unavailable
entities, duplicate unique ID warnings, or command failures. Attach diagnostics
and include:

- The old fork URL.
- The old and new `homeassistant_salus` versions if known.
- Home Assistant version.
- Gateway model, such as UGE600 or UG800.
- A list of affected entity IDs.

## Rollback

If you need to roll back, reinstall the previous fork from HACS and restart
Home Assistant. Restore your Home Assistant backup if the migration changed
entity registry data in a way you cannot easily undo from the UI.
