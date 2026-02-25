# Runbook - Generacion de Predicciones

Este runbook explica como generar predicciones de Champions League en modo `preseason` usando el modelo principal actual, sin calibracion en el pipeline principal.

## 1) Prerrequisitos

1. Estar en la raiz del repo:
`/Users/adrianalarcon/Documents/cibertec_2026/machine_learning_m_j_enero/repo`

2. Tener venv creado:
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## 2) Construir artefactos (data + features + modelo principal)

Ejecutar pipeline principal:
```bash
bash scripts/run_pipeline.sh
```

Salida esperada:
- `data/interim/*.csv|parquet`
- `artifacts/models/match_model.joblib`
- `data/processed/team_season_probs.csv`
- reportes en `artifacts/reports/`

## 3) Ejecutar prediccion de campeon por temporada (CLI)

Generar probabilidades de campeon para una temporada:
```bash
.venv/bin/python scripts/predict_season.py --season 2021 --n-simulations 10000 --random-seed 42 --output artifacts/reports/predictions_2021.csv
```

Archivo de salida:
- `artifacts/reports/predictions_2021.csv`

Columnas:
- `team`
- `p_champion`
- `rank`

## 4) Levantar API local

```bash
uvicorn src.api.main:app --reload
```

## 5) Predicciones via API

## 5.1 Salud del servicio

```bash
curl -s http://127.0.0.1:8000/health | jq
```

## 5.2 Probabilidad de resultado de partido

```bash
curl -s -X POST "http://127.0.0.1:8000/predict/match" \
  -H "Content-Type: application/json" \
  -d '{
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
      "goal_diff_away_last5": 2
    }
  }' | jq
```

Respuesta:
- `p_home_win`
- `p_draw`
- `p_away_win`

## 5.3 Simulacion de campeon desde inicio de temporada

```bash
curl -s -X POST "http://127.0.0.1:8000/simulate/season" \
  -H "Content-Type: application/json" \
  -d '{"season": 2021, "n_simulations": 10000, "random_seed": 42}' | jq
```

Respuesta:
- `results[]` con `team`, `p_champion`, `rank`

## 6) Verificacion rapida

1. `p_home_win + p_draw + p_away_win ~= 1`
2. `sum(p_champion de los 32 equipos) ~= 1`
3. Los reportes existen:
- `artifacts/reports/profiling_report.md`
- `artifacts/reports/leakage_gates_report.md`
- `artifacts/reports/experiments_comparison.md`
- `artifacts/reports/evaluation_report.md`

## 7) Solucion de problemas

1. Error de import/parquet:
- Reinstalar dependencias en `.venv`.
- El pipeline soporta fallback a CSV si no hay engine parquet.

2. Error por temporada:
- Verificar que exista en `data/raw/df.csv` y reglas en `configs/tournament_rules/`.

3. Modelo no encontrado:
- Ejecutar `bash scripts/run_pipeline.sh` para regenerar artefactos.
