"""Bundled module registration and real HTTP delivery without gateway traffic."""

import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL
from homeassistant.setup import async_setup_component

import custom_components.salus.frontend as frontend


async def test_registration_is_once_for_concurrent_gateway_setups(monkeypatch):
    hass = SimpleNamespace(
        data={}, http=SimpleNamespace(async_register_static_paths=AsyncMock())
    )
    add = Mock()
    monkeypatch.setattr(frontend, "add_extra_js_url", add)
    await asyncio.gather(
        frontend.async_register_room_card(hass), frontend.async_register_room_card(hass)
    )
    hass.http.async_register_static_paths.assert_awaited_once()
    config = hass.http.async_register_static_paths.call_args.args[0][0]
    assert config.url_path == frontend.CARD_PATH
    assert Path(config.path).is_file()
    assert config.cache_headers is False
    add.assert_called_once_with(hass, frontend.CARD_URL)


async def test_failed_registration_can_retry_without_marking_success(monkeypatch):
    hass = SimpleNamespace(
        data={},
        http=SimpleNamespace(
            async_register_static_paths=AsyncMock(side_effect=[OSError("disk"), None])
        ),
    )
    add = Mock()
    monkeypatch.setattr(frontend, "add_extra_js_url", add)
    with pytest.raises(OSError):
        await frontend.async_register_room_card(hass)
    add.assert_not_called()
    await frontend.async_register_room_card(hass)
    add.assert_called_once()


async def test_domain_setup_loads_and_serves_card_without_gateway_entry(
    hass, hass_client
):
    assert await async_setup_component(hass, "salus", {})
    urls = hass.data[DATA_EXTRA_MODULE_URL]
    assert frontend.CARD_URL in getattr(urls, "urls", urls)
    client = await hass_client()
    response = await client.get(frontend.CARD_URL)
    assert response.status == 200
    content = await response.text()
    assert "class SalusRoomCard extends HTMLElement" in content
    assert "class SalusRoomCardEditor extends HTMLElement" in content
    assert f"Card {frontend.CARD_VERSION}" in content


async def test_module_registration_retry_does_not_duplicate_static_route(monkeypatch):
    hass = SimpleNamespace(
        data={}, http=SimpleNamespace(async_register_static_paths=AsyncMock())
    )
    add = Mock(side_effect=[RuntimeError("frontend not ready"), None])
    monkeypatch.setattr(frontend, "add_extra_js_url", add)
    with pytest.raises(RuntimeError):
        await frontend.async_register_room_card(hass)
    await frontend.async_register_room_card(hass)
    hass.http.async_register_static_paths.assert_awaited_once()
    assert add.call_count == 2
