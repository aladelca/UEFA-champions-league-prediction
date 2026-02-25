from fastapi import APIRouter, HTTPException

from src.api.deps import get_runtime
from src.inference.predict_champion import simulate_season_from_start
from src.inference.predict_match import predict_match_probabilities
from src.inference.schemas import (
    HealthResponse,
    MatchPredictRequest,
    MatchPredictResponse,
    SimulateSeasonRequest,
    SimulateSeasonResponse,
)


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    runtime = get_runtime()
    return HealthResponse(
        status="ok",
        api_version=runtime.api_version,
        inference_mode=runtime.inference_mode,
        model_version=runtime.model_version,
    )


@router.post("/predict/match", response_model=MatchPredictResponse)
def predict_match(payload: MatchPredictRequest) -> MatchPredictResponse:
    probs = predict_match_probabilities(home_flag=payload.home_flag, features=payload.features)
    return MatchPredictResponse(
        season=payload.season,
        home_team=payload.home_team,
        away_team=payload.away_team,
        p_home_win=probs["p_home_win"],
        p_draw=probs["p_draw"],
        p_away_win=probs["p_away_win"],
    )


@router.post("/simulate/season", response_model=SimulateSeasonResponse)
def simulate_season(payload: SimulateSeasonRequest) -> SimulateSeasonResponse:
    try:
        result = simulate_season_from_start(
            season=payload.season,
            n_simulations=payload.n_simulations,
            random_seed=payload.random_seed if payload.random_seed is not None else 42,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return SimulateSeasonResponse(**result)


@router.post("/predict/champion", response_model=SimulateSeasonResponse)
def predict_champion(payload: SimulateSeasonRequest) -> SimulateSeasonResponse:
    return simulate_season(payload)
