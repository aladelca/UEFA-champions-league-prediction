# Plan 05 - Tickets de implementacion (estilo Jira)

Fecha de inicio: 2026-02-25  
Objetivo: ejecutar la metodologia `match-level + simulacion + FastAPI` con guardrails anti-leakage.

## Reglas de estado

- `TODO`: pendiente.
- `IN_PROGRESS`: en ejecucion activa.
- `DONE`: completado con evidencia en repo.
- `BLOCKED`: requiere decision externa.

## Backlog de tickets

| Ticket | Epic | Tarea | Estado | Dependencias | Criterio de cierre (DoD) |
|---|---|---|---|---|---|
| UCL-001 | Bootstrap | Crear estructura base de carpetas del proyecto | DONE | - | Existen carpetas `src/`, `configs/`, `artifacts/`, `tests/`, `scripts/`, `skills/` y subcarpetas definidas en plan 04 |
| UCL-002 | Bootstrap | Crear `requirements.txt` y `Makefile` con comandos estandar | DONE | UCL-001 | Dependencias y targets base (`setup`, `train`, `simulate`, `api`, `test`) definidos |
| UCL-003 | Bootstrap | Crear `configs/features.yaml`, `configs/model.yaml`, `configs/validation.yaml` | DONE | UCL-001 | Configs iniciales con placeholders operativos y guardrails |
| UCL-004 | API | Documentar contrato API en `docs/api_contracts.md` | DONE | UCL-001 | Contratos request/response y errores definidos para endpoints |
| UCL-005 | API | Implementar esqueleto FastAPI (`/health`, `/predict/match`, `/simulate/season`, `/predict/champion`) | DONE | UCL-002, UCL-004 | API levanta localmente y valida schemas |
| UCL-006 | Bootstrap | Crear script de pipeline `scripts/run_pipeline.sh` | DONE | UCL-002 | Script ejecuta flujo base por etapas con flags |
| UCL-007 | Skill | Crear skill reusable para ejecucion por tickets con actualizacion de estado | DONE | UCL-001 | Skill creado y validado con `quick_validate.py` |
| UCL-008 | Data | Implementar `src/data/load_raw.py` y `clean_raw.py` | DONE | UCL-001, UCL-003 | Carga limpia y escribe `data/interim/matches_raw_clean.(parquet|csv)` |
| UCL-009 | Data | Implementar `src/data/build_matches_unique.py` | DONE | UCL-008 | Genera `matches_unique.(parquet|csv)` y `y_match` |
| UCL-010 | Features | Implementar `src/features/build_pre_match_features.py` | DONE | UCL-009 | Genera features `t-1` sin leakage |
| UCL-019 | Bootstrap | Crear venv local e instalar dependencias del proyecto | DONE | UCL-002 | `.venv` creado e instalacion de `requirements.txt` completada |
| UCL-011 | Leakage | Implementar validadores en `src/features/validators.py` | DONE | UCL-010 | Reglas anti-leakage ejecutables + reporte |
| UCL-012 | Modeling | Implementar split temporal rolling en `src/modeling/split_time.py` | DONE | UCL-010 | CV rolling reproducible |
| UCL-013 | Modeling | Implementar entrenamiento multmodelo con CatBoost prioritario | DONE | UCL-012 | Ranking de modelos por metrica principal |
| UCL-014 | Modeling | Implementar calibracion probabilistica | DONE | UCL-013 | Desactivado por decision de usuario; no se ejecuta en pipeline principal |
| UCL-015 | Simulation | Implementar motor de simulacion Monte Carlo | DONE | UCL-013 | Simulador por fases (grupos + KO) y `P(campeon)` por temporada |
| UCL-016 | Rules | Crear reglas por temporada en `configs/tournament_rules/*.yaml` incluyendo excepciones | DONE | UCL-015 | Reglas completas 2010-2021 con excepciones reales |
| UCL-017 | QA | Crear tests unitarios e integracion iniciales | DONE | UCL-005, UCL-009, UCL-011 | `pytest` pasa en smoke suite |
| UCL-018 | Reporting | Generar reportes iniciales (`profiling`, `evaluation`, `leakage_gates`) | DONE | UCL-011, UCL-013, UCL-015 | Reportes en `artifacts/reports/` |
| UCL-020 | Modeling | Ejecutar ronda extensiva de experimentacion y fijar principal | DONE | UCL-013 | Reporte comparativo completo y modelo principal seleccionado |

## Sprint actual (ejecucion inmediata)

| Ticket | Estado actual | Nota de ejecucion |
|---|---|---|
| UCL-001 | DONE | Estructura base creada |
| UCL-002 | DONE | `requirements.txt` y `Makefile` listos |
| UCL-003 | DONE | Configs iniciales creadas |
| UCL-004 | DONE | Contrato API documentado |
| UCL-005 | DONE | API FastAPI funcional con endpoints base |
| UCL-006 | DONE | Pipeline script funcional |
| UCL-007 | DONE | Skill `jira-ticket-executor` creado y validado |
| UCL-008 | DONE | Limpieza base implementada |
| UCL-009 | DONE | Construccion de partidos unicos implementada |
| UCL-010 | DONE | Features `t-1` implementadas (season/global + Elo + same-day batch guardrail) |
| UCL-011 | DONE | Leakage gates ejecutables implementados con reporte |
| UCL-012 | DONE | Split temporal rolling-origin implementado con reporte |
| UCL-013 | DONE | Entrenamiento multmodelo implementado y seleccionado por `log_loss` |
| UCL-014 | DONE | Desactivado por decision de usuario en pipeline principal |
| UCL-020 | DONE | Experimentos extensivos ejecutados y principal actualizado |
| UCL-015 | DONE | Simulador por fases/reglas implementado y conectado a API |
| UCL-016 | DONE | Reglas YAML 2010-2021 implementadas y verificadas por carga de configuracion |
| UCL-017 | DONE | Tests unitarios/leakage/API smoke implementados (`7 passed`) |
| UCL-018 | DONE | Reportes y runbook final creados; pipeline actualizado con etapa `evaluate` |
| UCL-019 | DONE | venv creado y dependencias instaladas |

## Registro de progreso

- 2026-02-25: Backlog creado y sprint inicial definido.
- 2026-02-25: UCL-001 a UCL-007 completados.
- 2026-02-25: UCL-008 y UCL-009 completados, con fallback parquet/csv para portabilidad.
- 2026-02-25: UCL-019 completado (`.venv` creado + dependencias instaladas).
- 2026-02-25: UCL-010 movido a `IN_PROGRESS`.
- 2026-02-25: UCL-010 completado (`build_pre_match_features.py` real `t-1`, sin columnas post-partido).
- 2026-02-25: UCL-011 completado (`validators.py` + `artifacts/reports/leakage_gates_report.md`).
- 2026-02-25: UCL-012 completado (`split_time.py` + `artifacts/reports/time_split_report.md`).
- 2026-02-25: UCL-013 movido a `IN_PROGRESS`.
- 2026-02-25: UCL-013 completado (`train_match_model.py` multmodelo con CatBoost prioritario + ranking en `evaluation_report.md`).
- 2026-02-25: UCL-014 completado (`calibrate.py` con calibracion multiclase y `calibrator.joblib`).
- 2026-02-25: UCL-015 movido a `IN_PROGRESS`.
- 2026-02-25: UCL-020 completado (`run_experiments.py` con 24 experimentos, rolling temporal y reporte comparativo).
- 2026-02-25: Pipeline principal ajustado para usar directamente el mejor modelo (sin etapa de calibracion).
- 2026-02-25: UCL-015 completado (motor Monte Carlo por fases + API `simulate/season` funcionando con 32 equipos).
- 2026-02-25: UCL-016 movido a `IN_PROGRESS` para completar archivos YAML por temporada.
- 2026-02-25: UCL-016 completado (`configs/tournament_rules/ucl_2010..2021.yaml` + validacion de carga de reglas por temporada).
- 2026-02-25: UCL-017 completado (tests en `tests/unit`, `tests/leakage`, `tests/integration`; evidencia `7 passed` con `python -m pytest`).
- 2026-02-25: UCL-018 completado (`src/modeling/evaluate.py`, `docs/runbook_predicciones.md`, `scripts/predict_season.py`, reportes en `artifacts/reports/`).
- 2026-02-25: Smoke de inferencia CLI validado (`scripts/predict_season.py --season 2021`) con salida `artifacts/reports/predictions_2021_smoke.csv`.
- 2026-02-25: `scripts/run_pipeline.sh` actualizado a 8 etapas con `evaluate`; `Makefile` ajustado para `$(PYTHON) -m pytest`.
- 2026-02-25: Pipeline end-to-end validado (`bash scripts/run_pipeline.sh`) con salida `data/processed/team_season_probs.csv` y seleccion principal `EXP-021`.
