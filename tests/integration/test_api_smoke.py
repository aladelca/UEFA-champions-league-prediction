from fastapi.testclient import TestClient

from src.api.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["inference_mode"] == "preseason"


def test_predict_match_endpoint() -> None:
    client = TestClient(app)
    payload = {
        "season": 2021,
        "date": "2021-09-14",
        "home_team": "Chelsea",
        "away_team": "Real Madrid",
        "home_flag": 1,
        "features": {
            "elo_home": 1600,
            "elo_away": 1580,
            "elo_diff": 20,
            "form_points_home_last5": 8,
            "form_points_away_last5": 7,
            "goal_diff_home_last5": 4,
            "goal_diff_away_last5": 2,
        },
    }
    res = client.post("/predict/match", json=payload)
    assert res.status_code == 200
    body = res.json()
    p_total = body["p_home_win"] + body["p_draw"] + body["p_away_win"]
    assert abs(p_total - 1.0) < 1e-6


def test_simulate_season_endpoint() -> None:
    client = TestClient(app)
    res = client.post(
        "/simulate/season",
        json={"season": 2021, "n_simulations": 120, "random_seed": 7},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["season"] == 2021
    assert len(body["results"]) == 32
