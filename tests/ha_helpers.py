"""Import test helpers from the package matching the installed HA version."""

try:
    from pytest_homeassistant.common import MockConfigEntry
except ModuleNotFoundError as ex:
    if ex.name != "pytest_homeassistant":
        raise
    from pytest_homeassistant_custom_component.common import MockConfigEntry

__all__ = ["MockConfigEntry"]
