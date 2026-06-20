from backend.app.launcher import enrich_games_with_emulators, route_for_game


def test_enrich_games_maps_platforms_to_detected_emulators():
    games = [
        {"id": 1, "name": "Gran Turismo 4", "platform": "PlayStation 2"},
        {"id": 2, "name": "Demon's Souls", "platform": "PlayStation 3"},
        {"id": 3, "name": "F-Zero GX", "platform": "Nintendo GameCube"},
        {"id": 4, "name": "Wii Sports", "platform": "Nintendo Wii"},
        {"id": 5, "name": "Sonic", "platform": "Mega Drive"},
    ]
    discovery = {
        "emulators": [
            {"key": "pcsx2", "browser_url": "http://unraid:3000"},
            {"key": "rpcs3", "browser_url": "http://unraid:3001"},
            {"key": "dolphin", "browser_url": "http://unraid:3002"},
        ]
    }

    enriched = enrich_games_with_emulators(games, discovery)

    assert [game["emulator_key"] for game in enriched] == ["pcsx2", "rpcs3", "dolphin", "dolphin", None]
    assert enriched[0]["launch_url"] == "http://unraid:3000"
    assert enriched[4]["launch_url"] is None


def test_route_for_game_returns_launch_plan_for_supported_game():
    game = {"id": 1, "name": "Gran Turismo 4", "platform": "PS2"}
    discovery = {"emulators": [{"key": "pcsx2", "browser_url": "http://unraid:3000"}]}

    route = route_for_game(game, discovery)

    assert route == {
        "supported": True,
        "action": "open_emulator",
        "emulator_key": "pcsx2",
        "launch_url": "http://unraid:3000",
        "message": "Open PCSX2 for Gran Turismo 4. Direct ROM launch is not implemented yet.",
    }


def test_route_for_game_reports_unsupported_platform():
    game = {"id": 1, "name": "Sonic", "platform": "Mega Drive"}
    discovery = {"emulators": []}

    route = route_for_game(game, discovery)

    assert route["supported"] is False
    assert route["emulator_key"] is None
