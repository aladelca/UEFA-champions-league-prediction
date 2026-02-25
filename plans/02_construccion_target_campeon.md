# Plan 02 - Construccion de targets y simulacion de campeon

## Objetivo

Construir un esquema en dos niveles:

1. Target de entrenamiento: `y_match` (resultado de partido).
2. Objetivo final: `P(campeon)` por equipo via simulacion de fases/reglas.

## Condiciones aplicadas

1. La inferencia oficial es `preseason`.
2. La simulacion arranca siempre desde inicio de temporada.
3. Solo se usa informacion derivada de `data/df.csv`.

## Nivel A - Target de partido (`y_match`)

## Definicion

Para cada partido unico:

- `y_match = 1` si gana local
- `y_match = 0` si empata
- `y_match = -1` si gana visita

Derivado solo de `score` y `score_opp` del partido.

## Verificacion de consistencia

- `result=2` coincide con empates en el dataset.
- Debe existir una sola etiqueta por `match_id`.

## Nivel B - Objetivo final de campeon

## Definicion

Para cada temporada y equipo:

`P(campeon)` = frecuencia de veces que el equipo gana el torneo en simulaciones Monte Carlo.

## Label real para evaluacion

`champion_real` se obtiene del ganador del ultimo partido (final) de cada temporada.

## Pipeline de construccion

1. Reconstruir calendario de partidos unicos por temporada.
2. Identificar fase de cada partido:
- Group Stage
- Round of 16
- Quarterfinals
- Semifinals
- Final
3. Ajustar modelo de `P(y_match)` con datos pre-partido.
4. Simular torneo completo por temporada con reglas oficiales.
5. Estimar `P(campeon)` por equipo (proporcion de campeonatos simulados).

## Como reconstruir fases/reglas

Dado que el CSV no trae una columna explicita de fase en el extracto actual, usar:

1. Reglas del formato UCL por temporada (archivo de configuracion de reglas).
2. Orden cronologico de fechas.
3. Patron de cruces ida/vuelta en eliminatorias.
4. Final a partido unico.

Si una temporada no se puede reconstruir de forma determinista, marcarla como "cobertura parcial" y excluirla de evaluacion de simulacion exacta.

## Guardrails anti-leakage (obligatorios)

1. Separacion por horizonte temporal
- Entrenar `P(y_match)` solo con partidos anteriores al bloque de test.

2. Features solo pre-partido
- Prohibido usar cualquier variable calculada con el resultado del partido objetivo.

3. Simulacion ciega
- Para toda temporada en inferencia preseason, usar probabilidades predichas desde el primer partido; no usar resultados reales de esa temporada.

4. Sin contaminacion intra-temporada
- No actualizar features de un partido con informacion de otro partido del mismo dia que ocurre despues.

5. Sin data snooping de reglas
- Las reglas del torneo deben venir de un archivo externo fijo por temporada, no inferidas usando resultados objetivo.

## Manejo de desbalance

1. A nivel partido (`y_match`)
- Menor desbalance que target de campeon directo.
- Evaluar macro-F1, log loss multiclase y calibracion.

2. A nivel campeon (`champion_real`)
- Clase positiva extremadamente rara.
- Evaluar ranking probabilistico por temporada:
  - `Hit@k` del campeon real
  - log loss por equipo-temporada
  - Brier score de campeon

## Entregables de esta etapa

1. Tabla `matches_unique` con `y_match`.
2. Config de fases/reglas por temporada.
3. Motor de simulacion con semilla reproducible.
4. Tabla final `team_season_probs` con `P(campeon)` y `champion_real`.
