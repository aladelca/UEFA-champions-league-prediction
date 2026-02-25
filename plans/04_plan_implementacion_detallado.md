# Plan 04 - Implementacion detallada (match-level + simulacion + FastAPI)

## 1) Objetivo operativo

Implementar un sistema reproducible para estimar `P(campeon)` por equipo en Champions League con esta estrategia:

1. Entrenar un modelo de `P(resultado de partido)` usando solo informacion historica disponible antes de cada partido.
2. Simular fases y reglas del torneo para convertir probabilidades de partidos en `P(campeon)`.
3. Exponer inferencia local via API con FastAPI en modo `preseason` (inicio de torneo).

## 2) Alcance y supuestos

1. Alcance
- Datos base: `data/df.csv`.
- Modelo principal: clasificacion multiclase de partido (local/empate/visita).
- Salida final: probabilidades de campeon por temporada/equipo.
- Inferencia local: API FastAPI siempre desde inicio de temporada.

2. Supuestos
- Todo feature para un partido en fecha `t` se calcula con datos `< t`.
- Las reglas de torneo por temporada se almacenan como configuracion versionada.
- No se usan fuentes externas; solo datos derivados de `data/df.csv`.
- Para inferencia `preseason` de temporada `S`, no se usan resultados reales de temporada `S`.
- Se mantiene un baseline secundario `team-season` solo para comparacion.

## Decisiones cerradas del proyecto

1. Modo de inferencia: `preseason`.
2. Datos permitidos: solo `data/df.csv`.
3. Simulacion: incluir excepciones reales por temporada.
4. Evaluacion: particion temporal + validacion cruzada rolling-origin.
5. API: simulacion siempre desde inicio de temporada.
6. Modelado: buscar mejor modelo iterando varias opciones; CatBoost es candidato prioritario.

## 3) Estructura de carpetas propuesta

```text
repo/
  data/
    raw/
      df.csv
    interim/
      matches_unique.parquet
      feature_store_pre_match.parquet
    processed/
      train.parquet
      valid.parquet
      test.parquet
      team_season_probs.parquet
  docs/
    diccionario_datos.md
    api_contracts.md
  plans/
    01_perfilamiento_y_preparacion.md
    02_construccion_target_campeon.md
    03_metodologia_cientifica_opciones.md
    04_plan_implementacion_detallado.md
  configs/
    features.yaml
    model.yaml
    validation.yaml
    tournament_rules/
      ucl_2010.yaml
      ...
      ucl_2021.yaml
  src/
    data/
      load_raw.py
      clean_raw.py
      build_matches_unique.py
    features/
      build_pre_match_features.py
      elo.py
      validators.py
    modeling/
      train_match_model.py
      calibrate.py
      evaluate.py
      split_time.py
    simulation/
      bracket_builder.py
      monte_carlo.py
      aggregate_probs.py
    inference/
      predict_match.py
      predict_champion.py
      schemas.py
    api/
      main.py
      routers.py
      deps.py
  artifacts/
    models/
      match_model.joblib
      calibrator.joblib
    reports/
      profiling_report.md
      leakage_gates_report.md
      evaluation_report.md
  tests/
    unit/
    integration/
    leakage/
  scripts/
    run_pipeline.sh
  Makefile
  requirements.txt
```

## 4) Plan por etapas

## Etapa 0 - Bootstrap del proyecto

1. Crear estructura de carpetas y archivos base.
2. Definir `requirements.txt` con stack minimo:
- `pandas`, `numpy`, `scikit-learn`, `catboost`, `xgboost` (opcional), `pyyaml`, `joblib`, `fastapi`, `uvicorn`, `pydantic`, `pytest`.
3. Crear `Makefile` para comandos estandar.

Entregable:
- Proyecto ejecutable con comandos `make`.

## Etapa 1 - Preparacion y limpieza de datos

1. Cargar `data/raw/df.csv`.
2. Limpieza base:
- eliminar `Unnamed: 0`
- parsear `Date`
- normalizar nombres de equipos (encoding)
- tipar columnas
3. Validaciones de calidad:
- nulos, duplicados, rangos invalidos
- consistencia `result` vs `score`/`score_opp`
4. Exportar dataset limpio a `data/interim/`.

Entregables:
- `matches_raw_clean.parquet`
- `artifacts/reports/profiling_report.md`

## Etapa 2 - Reconstruccion de partido unico

1. Generar `match_id` reproducible.
2. Unificar dos filas espejo en una fila de partido:
- `home_team`, `away_team`, `home_goals`, `away_goals`, `season`, `Date`
3. Construir `y_match` multiclase.
4. Validar integridad:
- 1 etiqueta por `match_id`
- sin partidos huérfanos.

Entregable:
- `data/interim/matches_unique.parquet`

## Etapa 3 - Feature engineering pre-partido (anti-leakage)

1. Construir features por equipo para cada partido:
- forma ultimos N partidos (puntos, goles y defensa, todo derivado del CSV)
- acumulados de temporada hasta `t-1`
- Elo dinamico hasta `t-1`
- localia
2. Construir features diferenciales:
- `elo_diff`, `form_diff`, `goal_diff_rolling`, etc.
3. Aplicar guardrails:
- no usar `score`, `result` del partido objetivo
- no usar agregados de cierre de temporada del mismo `season`
4. Regla especial para inferencia `preseason`:
- para temporada `S`, inicializar features con historia de temporadas `< S` (sin usar partidos reales de `S`)
- durante simulacion, actualizar estados solo con resultados simulados
5. Guardar `feature_store_pre_match.parquet`.

Entregable:
- `data/interim/feature_store_pre_match.parquet`

## Etapa 4 - Split temporal, entrenamiento y calibracion

1. Particion temporal oficial:
- `test` final: temporada mas reciente (por defecto 2021)
- `train+validation`: temporadas previas
2. Validacion cruzada `rolling-origin` sobre `train+validation`.
3. Entrenar modelos candidatos (busqueda iterativa del mejor):
- CatBoost (prioritario)
- regresion logistica multinomial
- gradient boosting (XGBoost/HistGradientBoosting)
- Elo + capa probabilistica (baseline fuerte)
4. Calibrar probabilidades (`Platt` o `Isotonic`) con validacion temporal.
5. Seleccionar modelo final por:
- log loss multiclase (metrica principal)
- brier multiclase
- estabilidad temporal en folds rolling
- leakage gates pass
- ranking de campeon tras simulacion.

Entregables:
- `artifacts/models/match_model.joblib`
- `artifacts/models/calibrator.joblib`
- `artifacts/reports/evaluation_report.md`

## Etapa 5 - Simulacion de torneo y `P(campeon)`

1. Cargar reglas por temporada desde `configs/tournament_rules/*.yaml`.
2. Modelar excepciones reales por temporada (obligatorio), por ejemplo:
- 2019-2020: cuartos y semis a partido unico
- 2021-2022: eliminacion de regla de gol de visitante
3. Para cada simulacion:
- recorrer calendario/fases
- muestrear resultado de cada partido desde `P(y_match)`
- resolver clasificaciones y cruces segun reglas
4. Ejecutar N simulaciones por temporada (ej. 10,000).
5. Agregar probabilidades por equipo:
- `P(campeon)`, `P(final)`, `P(semis)` (opcional).

Entregables:
- `data/processed/team_season_probs.parquet`
- reporte de validacion de campeon real vs probabilidades.

## Etapa 6 - API local de inferencia con FastAPI

## Objetivo API

Servir inferencia de:

1. Probabilidad de resultado de un partido.
2. Probabilidad de campeon por equipo para una temporada simulada desde inicio.

## Endpoints propuestos

1. `GET /health`
- estado de servicio y version de modelo.

2. `POST /predict/match`
- Input: datos pre-partido estructurados (equipos, fecha, localia, features).
- Output: `p_home_win`, `p_draw`, `p_away_win`.

3. `POST /simulate/season`
- Input: `season`, `n_simulations`, `random_seed` (opcional).
- Output: tabla con `team`, `p_champion` y ranking.

4. `POST /predict/champion`
- Alias de alto nivel para ejecutar simulacion preseason con parametros por defecto.

## Contratos API (obligatorio documentar)

1. Mantener `docs/api_contracts.md` con:
- schemas request/response
- ejemplos JSON validos
- codigos de error y mensajes
- versionado de contrato (`api_version`)

## Reglas de implementacion API

1. Cargar modelo y calibrador al inicio (`startup event`).
2. Validar schemas con Pydantic.
3. Registrar version de modelo y hash de features.
4. Respuestas deterministicas opcionales con `random_seed`.
5. No aceptar payload de "estado parcial del torneo"; el flujo oficial es solo desde inicio.

Entregables:
- `src/api/main.py` funcional.
- `uvicorn src.api.main:app --reload` corriendo localmente.
- `docs/api_contracts.md` versionado.

## Etapa 7 - Testing, QA y hardening

1. Unit tests
- limpieza, reconstruccion de partido, features `t-1`, simulador.

2. Leakage tests (obligatorios)
- detectar columnas prohibidas
- verificar dependencia temporal
- asegurar fit de transformaciones solo en train.

3. Integration tests
- pipeline completo de train -> artifacts -> API.

4. Smoke test de API
- `/health`, `/predict/match`, `/simulate/season`.

Entregable:
- suite `pytest` pasando.

## Etapa 8 - Operacion local y ciclo de retraining

1. Pipeline batch local
- comando unico para refrescar datos, reentrenar y regenerar artifacts.

2. Versionado de modelos
- guardar timestamp, metricas y config usada.

3. Frecuencia recomendada
- retrain por temporada completa o cuando haya nuevo bloque de partidos.

Entregable:
- flujo reproducible de mantenimiento local.

## 5) Guardrails anti-leakage (criterio de aprobacion)

Un experimento solo se considera valido si cumple todo:

1. Guardrail temporal
- Train < Validation < Test en fecha.

2. Guardrail de features
- Cada feature del partido `i` usa solo historia previa al partido `i`.

3. Guardrail de transformaciones
- Cualquier `fit` se ejecuta solo en train.

4. Guardrail de simulacion
- Nunca se usan resultados reales futuros durante inferencia/simulacion.

5. Guardrail de trazabilidad
- Lista versionada de features permitidas y bloqueadas.

6. Guardrail de fuente de datos
- Solo se permite `data/df.csv` y transformaciones derivadas de ese CSV.

7. Guardrail de preseason
- Para temporada objetivo `S`, prohibido usar resultados reales de `S` en inferencia.

8. Guardrail de reproducibilidad
- Semillas fijas y config versionada por corrida.

## 6) Plan de ejecucion sugerido (secuencia)

1. Implementar Etapas 0-2.
2. Implementar Etapa 3 y leakage tests.
3. Implementar Etapa 4 y seleccionar modelo.
4. Implementar Etapa 5 y validar `P(campeon)`.
5. Implementar Etapa 6 (FastAPI).
6. Cerrar con Etapas 7-8.

## 7) Criterio de exito del proyecto

1. Pipeline completo reproducible de extremo a extremo.
2. Todas las corridas productivas pasan leakage gates.
3. API local responde inferencias coherentes y trazables.
4. Probabilidades de campeon calibradas y evaluadas temporalmente.
