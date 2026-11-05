import json

import pytest

import web.app as web_app
from algorithms.cbs import CBSResult


@pytest.fixture
def client(tmp_path, monkeypatch):
    scenarios_dir = tmp_path / "scenarios"
    scenarios_dir.mkdir()
    monkeypatch.setattr(web_app, "PROJECT_ROOT", tmp_path)
    web_app.app.config.update(TESTING=True)

    with web_app.app.test_client() as test_client:
        yield test_client


def scenario_payload():
    return {
        "grid": [[0] * 12 for _ in range(12)],
        "robots": [
            {"id": 1, "start": [0, 0], "goal": [2, 0]},
        ],
    }


@pytest.mark.parametrize("value", [None, "", "0", "false", "no"])
def test_flask_debug_is_disabled_by_default(client, monkeypatch, value):
    if value is None:
        monkeypatch.delenv("FLASK_DEBUG", raising=False)
    else:
        monkeypatch.setenv("FLASK_DEBUG", value)

    assert web_app._debug_enabled() is False


@pytest.mark.parametrize("value", ["1", "true", "yes", " TRUE "])
def test_flask_debug_can_be_enabled_explicitly(client, monkeypatch, value):
    monkeypatch.setenv("FLASK_DEBUG", value)

    assert web_app._debug_enabled() is True


def test_home_only_offers_saved_and_custom_scenarios(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"My Saved Scenario" in response.data
    assert b"Create Custom Scenario" in response.data
    assert b"Predefined Scenario" not in response.data
    assert client.get("/predefined").status_code == 404


def test_custom_pages_render_without_saved_scenario(client):
    assert client.get("/custom").status_code == 200
    response = client.get("/custom/edit")

    assert response.status_code == 200
    assert b"Create Custom Scenario" in response.data


def test_saved_page_explains_missing_scenario(client):
    response = client.get("/saved")

    assert response.status_code == 200
    assert b"No Saved Scenario" in response.data


def test_saved_page_explains_search_limit(client, tmp_path, monkeypatch):
    (tmp_path / "scenarios" / "dynamic.json").write_text(
        json.dumps(scenario_payload()),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        web_app,
        "cbs_search",
        lambda *_args, **_kwargs: CBSResult(
            False, {}, 30.0, 0, 0, 50000,
            failure_reason="node_limit",
        ),
    )

    response = client.get("/saved")

    assert response.status_code == 200
    assert b"50,000-node search limit" in response.data


def test_saved_page_explains_unreachable_robot(client, tmp_path):
    grid = [[1] * 12 for _ in range(12)]
    grid[0][0] = 0
    grid[0][2] = 0
    payload = {
        "grid": grid,
        "robots": [
            {"id": 1, "start": [0, 0], "goal": [2, 0]},
        ],
    }
    (tmp_path / "scenarios" / "dynamic.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    response = client.get("/saved")

    assert response.status_code == 200
    assert b"At least one robot has no path to its goal" in response.data


def test_custom_save_rejects_non_12_by_12_grid(client):
    response = client.post(
        "/custom/save",
        json={"grid": [[0]], "robots": []},
    )

    assert response.status_code == 400
    assert response.json["success"] is False


def test_custom_save_persists_valid_scenario(client, tmp_path):
    payload = scenario_payload()
    response = client.post("/custom/save", json=payload)

    assert response.status_code == 200
    assert response.json["success"] is True
    saved_data = json.loads(
        (tmp_path / "scenarios" / "dynamic.json").read_text(encoding="utf-8")
    )
    assert saved_data == payload

    saved_page = client.get("/saved")
    assert saved_page.status_code == 200
    assert b"Saved Warehouse" in saved_page.data


def test_dynamic_obstacle_rejects_invalid_request(client):
    response = client.post("/dynamic-obstacle", json={"x": 1})

    assert response.status_code == 400
    assert response.json["success"] is False


def test_dynamic_obstacle_replans_and_avoids_obstacle(client, tmp_path):
    scenarios_dir = tmp_path / "scenarios"
    (scenarios_dir / "dynamic.json").write_text(
        json.dumps(scenario_payload()),
        encoding="utf-8",
    )

    response = client.post(
        "/dynamic-obstacle",
        json={
            "x": 1,
            "y": 0,
            "currentTime": 0,
            "animationPaths": {"1": [[0, 0], [1, 0], [2, 0]]},
        },
    )

    assert response.status_code == 200
    assert response.json["success"] is True
    assert response.json["activeObstacles"] == [{"x": 1, "y": 0}]
    assert [1, 0] not in response.json["animationPaths"]["1"]


def test_dynamic_obstacle_reports_cbs_time_limit(client, tmp_path, monkeypatch):
    (tmp_path / "scenarios" / "dynamic.json").write_text(
        json.dumps(scenario_payload()),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        web_app,
        "cbs_search",
        lambda *_args, **_kwargs: CBSResult(
            False, {}, 10.0, 0, 0, 12,
            timed_out=True,
            failure_reason="time_limit",
        ),
    )

    response = client.post(
        "/dynamic-obstacle",
        json={
            "x": 1,
            "y": 0,
            "currentTime": 0,
            "animationPaths": {"1": [[0, 0], [1, 0], [2, 0]]},
        },
    )

    assert response.status_code == 409
    assert response.json["failureReason"] == "time_limit"
    assert response.json["timedOut"] is True
    assert "time limit" in response.json["message"]
