# Plan 03 - Metodologia cientifica (enfoque recomendado y alternativas)

## Pregunta cientifica

Como estimar de forma valida `P(campeon)` para cada equipo, minimizando leakage y maximizando calibracion probabilistica.

## Condiciones fijadas

1. Inferencia objetivo: `preseason` (inicio de torneo).
2. Fuente unica de datos: `data/df.csv`.
3. Simulacion con excepciones reales por temporada.
4. Evaluacion con validacion cruzada `rolling-origin`.
5. API de inferencia desde inicio de temporada (sin estado parcial).

## Hipotesis principal

Un modelo probabilistico de partido entrenado con features pre-partido, combinado con simulacion del torneo, produce estimaciones de campeon mas realistas y menos sesgadas que un clasificador directo `team-season`.

## Metodologia recomendada (principal)

## Opcion A - Match-level + Monte Carlo por fases (recomendada)

1. Entrenar `P(y_match)` (local/empate/visita) en validacion temporal.
2. Calibrar probabilidades (Platt/Isotonic).
3. Simular cada temporada miles de veces con reglas oficiales.
4. Obtener `P(campeon)` por equipo.
5. Evaluar contra campeon real por temporada.

Pros:
- Escala mejor con pocos campeones positivos.
- Permite actualizar probabilidades partido a partido.
- Menor riesgo de leakage si se aplica regla `t-1`.

Contras:
- Implementacion mas compleja (motor de simulacion + reglas).

## Metodologias alternativas

## Opcion B - Clasificador directo team-season (baseline secundario)

Usar una fila por equipo-temporada para predecir campeon directamente.

Pros:
- Rapida.
- Sirve como baseline de control.

Contras:
- Alto riesgo de leakage con agregados de temporada.
- Solo 12 positivos reales en el periodo.

## Opcion C - Bayesiano jerarquico + simulacion

Modelo probabilistico con efectos por equipo y temporada, integrado al motor de simulacion.

Pros:
- Incorpora incertidumbre estructural.
- Suele ser robusto con baja muestra positiva.

Contras:
- Mayor complejidad de implementacion y tuning.

## Guardrails cientificos anti-leakage (hard gates)

1. Gate temporal
- Ninguna fila de train puede tener fecha posterior a validation/test.

2. Gate de features
- Toda feature del partido `i` debe estar definida con datos previos al inicio del partido `i`.

3. Gate de transformaciones
- Encoder/scaler/winsorizer/calibrador ajustados solo en train.

4. Gate de simulacion
- En inferencia de temporada, no usar resultados reales futuros para actualizar probabilidades.

5. Gate de trazabilidad
- Cada variable debe tener etiqueta `allowed_pre_match` o `blocked_leakage`.

Si un gate falla, el experimento queda invalido.

## Diseno experimental recomendado

1. Esquema de validacion
- Rolling-origin por temporadas (ejemplo: train hasta 2016, valida 2017; train hasta 2017, valida 2018, etc.).

2. Baselines
- Baseline naive de partido (probabilidades por frecuencia global).
- Baseline de campeon uniforme por temporada (`1/32`).

3. Modelos candidatos para `P(y_match)`
- CatBoost (prioritario).
- Regresion logistica multinomial.
- Gradient boosting.
- Modelo Elo + capa probabilistica.

4. Metricas de partido
- Log loss multiclase.
- Brier score multiclase.
- Macro-F1.
- Curva de calibracion.

5. Metricas de campeon
- Log loss binario por equipo-temporada.
- Brier de campeon.
- Ranking: `Hit@1`, `Hit@4`, MRR por temporada.

## Criterio de seleccion de metodologia

Seleccionar el enfoque con mejor balance entre:

1. Validez anti-leakage (debe pasar todos los gates).
2. Calibracion probabilistica en validacion temporal.
3. Estabilidad entre temporadas.
4. Interpretabilidad operativa.

## Decision propuesta para este proyecto

1. Ejecutar Opcion A como metodo principal.
2. Mantener Opcion B como control de referencia.
3. Evaluar Opcion C solo si A no alcanza estabilidad/calibracion objetivo.

## Entregables

1. Protocolo experimental reproducible.
2. Matriz comparativa A/B/C con metrica y leakage gates.
3. Recomendacion final con justificacion cuantitativa.
