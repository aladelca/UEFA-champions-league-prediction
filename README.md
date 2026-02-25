# UCL Champion Prediction (sin leakage)

Proyecto para estimar `P(campeon)` de Champions League usando:

1. Modelo de `P(resultado de partido)` con features pre-partido (`t-1`).
2. Simulacion Monte Carlo de fases/reglas por temporada.

## Fuente de datos

- Dataset base: `data/df.csv`
- Diccionario de datos: `docs/diccionario_datos.md`

## Enfoque metodologico

- Unidad de modelado principal: `match-level` (no `team-season` como enfoque principal).
- Inferencia objetivo: `preseason` (desde inicio del torneo).
- Validacion: particion temporal + `rolling-origin` cross-validation.
- Guardrails anti-leakage en construccion y validacion de features.

## Estructura principal

- `src/data`: limpieza y estandarizacion.
- `src/features`: feature engineering pre-partido + validadores de leakage.
- `src/modeling`: splits temporales, experimentacion y seleccion del modelo principal.
- `src/simulation`: reglas por temporada y simulacion de torneo.
- `src/api`: API local con FastAPI.
- `configs/tournament_rules`: reglas 2010-2021 (incluye excepciones reales).
- `plans/`: plan maestro y tablero de tickets tipo Jira.

## Ejecucion rapida

1. Crear entorno:
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

2. Correr pipeline E2E:
```bash
bash scripts/run_pipeline.sh
```

3. Correr tests:
```bash
make test
```

4. Levantar API:
```bash
uvicorn src.api.main:app --reload
```

## Artefactos y reportes

- Modelo principal: `artifacts/models/match_model.joblib`
- Probabilidades por temporada: `data/processed/team_season_probs.csv`
- Reportes: `artifacts/reports/`
  - `experiments_comparison.md`
  - `evaluation_report.md`
  - `leakage_gates_report.md`
  - `time_split_report.md`

## Documentacion de apoyo

- Planes: `plans/01..05_*.md`
- Runbook de inferencia: `docs/runbook_predicciones.md`
- Contratos API: `docs/api_contracts.md`

## Nota de versionado

Los archivos `.csv` y `.joblib` se excluyen del versionado via `.gitignore` para evitar subir datasets y artefactos de modelo al repositorio.
