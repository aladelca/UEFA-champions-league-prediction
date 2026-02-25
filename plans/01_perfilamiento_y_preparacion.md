# Plan 01 - Perfilamiento y preparacion (enfoque match-level)

## Objetivo

Preparar un dataset confiable para entrenar `P(resultado de partido)` con features pre-partido, base necesaria para simular `P(campeon)`.

## Condiciones aplicadas

1. Inferencia objetivo: `preseason`.
2. Fuente de datos permitida: solo `data/df.csv`.
3. Las features deben ser compatibles con simulacion desde inicio de temporada.

## Insumos

- `docs/diccionario_datos.md`
- `data/df.csv`

## Hallazgos actuales relevantes

| Chequeo | Resultado observado | Impacto en plan |
|---|---|---|
| Filas / columnas | 2922 filas, 89 columnas | Se puede procesar completo sin muestreo. |
| Nulos | 0 | No hay imputacion por faltantes. |
| Duplicados exactos | 0 | Sin duplicados literales. |
| Granularidad | fila = equipo-partido (dos perspectivas por partido) | Necesita deduplicacion a partido unico para modelado. |
| `result` | {0,1,2} | Target natural para clasificacion 3 clases. |
| Agregados de temporada | muchas columnas son constantes por `team-season` | Alto riesgo de leakage si se usan directo en el mismo partido/temporada. |
| `Unnamed: 0` | indice sobrante | Eliminar. |
| Codificacion de texto | mojibake en algunos equipos | Normalizar nombres de equipos. |
| Outlier de dominio | `Save%` llega a 116.7 | Revisar formula y reglas de cap/recalculo. |

## Unidad analitica y datasets intermedios

1. `matches_raw_team_view`
- Fuente original (dos filas por partido, una por equipo).

2. `matches_unique`
- Una fila por partido (home vs away), con `match_id` reproducible.

3. `feature_store_pre_match`
- Features construidas solo con informacion previa al partido (`t-1`).

4. `simulation_inputs`
- Calendario y estructura de fases/reglas por temporada para Monte Carlo.

## Perfilamiento a ejecutar

1. Perfil estructural
- Tipos de datos (parseo estricto de `Date`).
- Cardinalidades por columna y consistencia de codigos (`day_code`, `opp_code`).
- Reglas de unicidad para `match_id`.

2. Perfil de calidad
- Integridad de resultados: consistencia `result` vs `score` y `score_opp`.
- Coherencia de rangos (porcentajes, conteos, tasas).
- Validacion de cobertura por temporada y fechas.

3. Perfil de representacion de partidos
- Reconstruccion de partido unico desde dos filas espejo.
- Verificacion de que cada partido tenga una sola representacion final.

4. Perfil de leakage
- Identificar columnas prohibidas para prediccion pre-partido en misma temporada.
- Confirmar que features rolling/lag no usen informacion del propio partido.

## Tratamiento de datos propuesto

1. Limpieza base
- Eliminar `Unnamed: 0`.
- Estandarizar texto de equipos.
- Parsear fechas y ordenar por `season`, `Date`, `match_id`.

2. Reconstruccion de partidos unicos
- Generar `match_id` canonico por temporada-fecha-equipos-localia.
- Consolidar en formato partido: `home_team`, `away_team`, `home_goals`, `away_goals`, `y_match`.

3. Feature engineering pre-partido
- Features permitidas:
  - localia (`home=1`)
  - forma reciente (ultimos N partidos hasta `t-1`)
  - goles a favor/en contra acumulados hasta `t-1`
  - puntos por partido acumulados hasta `t-1`
  - rating dinamico (Elo) actualizado secuencialmente
- Features no permitidas en misma temporada:
  - agregados de cierre de temporada sin lag (`Gls`, `W`, `GA`, `PPM`, `onG`, etc.)

4. Escalado y encoding
- Ajustar transformaciones solo con train de cada fold temporal.
- Aplicar al validation/test sin refit.

## Guardrails anti-leakage (obligatorios)

1. Split temporal estricto
- Nunca random split por filas.
- Train siempre con fechas/temporadas anteriores a validation/test.

2. Regla `t-1` para features
- Toda feature de partido en fecha `t` debe construirse con datos `< t`.
- Si hay varios partidos mismo dia, no usar resultados del mismo dia para otros partidos.

3. No usar variables post-partido en `X`
- Prohibido incluir `score`, `score_opp`, `result` del partido objetivo.

4. No usar agregados de cierre de temporada del mismo `season`
- Solo permitidos si vienen laggeados de temporadas previas.

5. Pipelines cerrados por fold
- Winsorizacion, escalado, encoding y calibracion se ajustan solo en train.

6. Auditoria automatica de leakage
- Test unitario: detectar columnas con correlacion imposible o dependencia temporal invalida.
- Gate de calidad: si falla una regla, no se entrena modelo.
7. Regla preseason
- Para temporada objetivo `S`, no usar resultados reales de `S` en construccion de features de inferencia.

## Entregables de esta etapa

1. Reporte de perfilamiento y calidad de datos.
2. Tabla `matches_unique` validada.
3. Especificacion de features permitidas/prohibidas.
4. Checklist de guardrails con estado pass/fail.
