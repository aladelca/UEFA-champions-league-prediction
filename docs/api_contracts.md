# API Contracts - UCL Champion Predictor

Version: `v1`  
Scope: inferencia local en modo `preseason` usando solo datos derivados de `data/raw/df.csv`.

## Reglas globales

1. La API simula siempre desde inicio de temporada.
2. No acepta estado parcial del torneo.
3. Todos los endpoints JSON responden `application/json`.

## GET /health

### Response 200

```json
{
  "status": "ok",
  "api_version": "v1",
  "inference_mode": "preseason",
  "model_version": "dev"
}
```

## POST /predict/match

Predice probabilidades de resultado para un partido.

### Request

```json
{
  "season": 2021,
  "date": "2021-09-14",
  "home_team": "Chelsea",
  "away_team": "Real Madrid",
  "home_flag": 1,
  "features": {
    "elo_home": 1620.0,
    "elo_away": 1655.0,
    "elo_diff": -35.0,
    "form_points_home_last5": 9.0,
    "form_points_away_last5": 10.0
  }
}
```

### Response 200

```json
{
  "season": 2021,
  "home_team": "Chelsea",
  "away_team": "Real Madrid",
  "p_home_win": 0.34,
  "p_draw": 0.29,
  "p_away_win": 0.37
}
```

## POST /simulate/season

Simula una temporada completa desde inicio y retorna ranking de `P(campeon)`.

### Request

```json
{
  "season": 2021,
  "n_simulations": 10000,
  "random_seed": 42
}
```

### Response 200

```json
{
  "season": 2021,
  "n_simulations": 10000,
  "results": [
    { "team": "Real Madrid", "p_champion": 0.22, "rank": 1 },
    { "team": "Bayern Munich", "p_champion": 0.15, "rank": 2 }
  ]
}
```

## POST /predict/champion

Alias funcional de `/simulate/season` con mismos campos.

## Errores

## 400 - Validation error

```json
{
  "detail": "Validation error"
}
```

## 422 - Schema error

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "season"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

## 500 - Internal error

```json
{
  "detail": "Internal server error"
}
```
