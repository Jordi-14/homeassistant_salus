# HomeAssistant - Salus Controls iT600 Smart Home Custom Component

Fork maintained at `https://github.com/Jordi-14/homeassistant_salus`.

# What This Is

This custom component lets you control and monitor Salus iT600 smart home devices locally through a Salus Controls UGE600 universal gateway.

# Supported devices

See the [readme of underlying pyit600 library](https://github.com/epoplavskis/pyit600/blob/master/README.md).

This fork adds improved Home Assistant thermostat handling for SQ610 Quantum thermostats, including:
- correct Heat/Cool mode exposure
- direct standby handling
- simplified manual hold controls in Home Assistant

# Installation and Configuration

## HACS (recommended)

Add `https://github.com/Jordi-14/homeassistant_salus` as a custom repository in [HACS](https://hacs.xyz/) with category `Integration`, then install `Salus iT600`.
*HACS is a third party community store and is not included in Home Assistant out of the box.*

## Manual install
Copy the `custom_components` folder from this repository to `/config` of your Home Assistant installation.

To configure the integration, go to the Home Assistant web interface, then `Settings -> Devices & Services -> Add Integration`, and select `Salus iT600`.

When configuration is complete, your devices will appear under the integration entities.

# SQ610 Notes

For SQ610 Quantum thermostats this fork exposes the following Home Assistant controls:
- target temperature
- mode: `Heat` / `Cool`
- preset: `Permanent Hold` / `Standby` / `Follow Salus Schedule`

Selecting `Follow Salus Schedule` in Home Assistant returns the thermostat to the Salus app schedule.

# Troubleshooting

If you can't connect using EUID written down on the bottom of your gateway (which looks something like `001E5E0D32906128`), try using `0000000000000000` as EUID.

Also check if you have "Local Wifi Mode" enabled:
* Open Smart Home app on your phone
* Sign in
* Double tap your Gateway to open info screen
* Press gear icon to enter configuration
* Scroll down a bit and check if "Disable Local WiFi Mode" is set to "No"
* Scroll all the way down and save settings
* Restart Gateway by unplugging/plugging USB power

# Code origin

This code is a fork from https://github.com/epoplavskis/homeassistant_salus , whish is a fork from https://github.com/konradb3/homeassistant_salus .