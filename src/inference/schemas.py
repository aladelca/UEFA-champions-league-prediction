from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class MatchPredictRequest(BaseModel):
    season: int
    date: date
    home_team: str
    away_team: str
    home_flag: int = Field(default=1, ge=0, le=1)
    features: Dict[str, float] = Field(default_factory=dict)


class MatchPredictResponse(BaseModel):
    season: int
    home_team: str
    away_team: str
    p_home_win: float
    p_draw: float
    p_away_win: float


class SimulateSeasonRequest(BaseModel):
    season: int
    n_simulations: int = Field(default=10000, ge=100, le=200000)
    random_seed: Optional[int] = 42


class ChampionProbItem(BaseModel):
    team: str
    p_champion: float
    rank: int


class SimulateSeasonResponse(BaseModel):
    season: int
    n_simulations: int
    results: List[ChampionProbItem]


class HealthResponse(BaseModel):
    status: str
    api_version: str
    inference_mode: str
    model_version: str
