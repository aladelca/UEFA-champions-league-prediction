# Diccionario de datos - Dataset de futbol

Este documento organiza el glosario del dataset como diccionario de datos.

## Notas generales

- `Date` y `Time` estan en horario local del estadio.
- `Time` usa formato de 24 horas.
- `xG` incluye penales, pero no tandas de penales (salvo que se indique lo contrario).
- Un valor subrayado indica partido con dato faltante pendiente de actualizacion.
- `Score`: numeros entre parentesis indican goles en tanda de penales.

## Fixtures

| Variable | Descripcion |
|---|---|
| `Round` | Ronda o fase de la competicion. |
| `Wk` | Numero de jornada (`Matchweek Number`). |
| `Day` | Dia de la semana del partido. |
| `Date` | Fecha del partido (hora local). |
| `Time` | Hora del partido (hora local, formato 24h). |
| `xG` | Goles esperados (Expected Goals), provisto por Opta. |
| `Score` | Marcador final; parentesis para goles en tanda de penales. |

## Squad Standard Stats

| Variable | Descripcion | Notas |
|---|---|---|
| `Pl` | Numero de jugadores usados en partidos. | Conteo de jugadores utilizados por el equipo. |
| `Age` | Edad promedio. | Ponderada por minutos jugados. |
| `Poss` | Posesion. | Porcentaje de pases intentados. |

## Playing Time (general)

| Variable | Descripcion | Formula / Notas |
|---|---|---|
| `MP` | Partidos jugados. | Por jugador o equipo. |
| `Starts` | Partidos iniciados como titular. | - |
| `Min` | Minutos jugados. | - |
| `90s` | Bloques de 90 minutos jugados. | `Min / 90` |

## Performance (jugador/equipo)

| Variable | Descripcion |
|---|---|
| `Gls` | Goles anotados o concedidos (segun contexto). |
| `Ast` | Asistencias. |
| `G+A` | Goles + asistencias. |
| `G-PK` | Goles sin penales. |
| `PK` | Penales convertidos. |
| `PKatt` | Penales intentados. |
| `CrdY` | Tarjetas amarillas. |
| `CrdR` | Tarjetas rojas. |

## Goalkeeping

| Variable | Descripcion | Formula / Notas |
|---|---|---|
| `GA` | Goles en contra. | - |
| `GA90` | Goles en contra por 90 minutos. | - |
| `SoTA` | Tiros a puerta recibidos. | - |
| `Save%` | Porcentaje de atajadas (arquero). | `(SoTA - GA) / SoTA`; no incluye penales. |
| `W` | Victorias. | - |
| `D` | Empates. | - |
| `L` | Derrotas. | - |
| `CS` | Vallas invictas. | Partidos completos del arquero sin recibir gol. |
| `CS%` | Porcentaje de vallas invictas. | - |
| `PKatt` | Penales enfrentados. | Penalty Kicks Attempted. |
| `PKA` | Penales convertidos por rival. | Penalty Kicks Allowed. |
| `PKsv` | Penales atajados. | - |
| `PKm` | Penales fallados por rival. | Penalty Kicks Missed. |
| `Save% (PK)` | Porcentaje de atajadas en penales. | Basado en penales al arco; penales fuera no cuentan. |

## Shooting

| Variable | Descripcion | Formula / Notas |
|---|---|---|
| `Gls` | Goles. | - |
| `Sh` | Tiros totales. | No incluye penales. |
| `SoT` | Tiros al arco. | No incluye penales. |
| `SoT%` | Porcentaje de tiros al arco. | Requisito lideres: minimo `0.395` tiros por partido del equipo. |
| `Sh/90` | Tiros por 90. | Requisito lideres: minimo 30 min jugados por partido del equipo. |
| `SoT/90` | Tiros al arco por 90. | Requisito lideres: minimo 30 min jugados por partido del equipo; sin penales. |
| `G/Sh` | Goles por tiro. | Requisito lideres: minimo `0.395` tiros por partido del equipo. |
| `G/SoT` | Goles por tiro al arco. | Requisito lideres: minimo `0.111` tiros al arco por partido del equipo; sin penales. |
| `Dist` | Distancia promedio del tiro (yardas). | No incluye penales; requisito lideres: minimo `0.395` tiros por partido del equipo. |
| `PK` | Penales convertidos. | - |
| `PKatt` | Penales intentados. | - |

## Playing Time (detalle)

| Variable | Descripcion | Formula / Notas |
|---|---|---|
| `MP` | Partidos jugados. | Por jugador o equipo. |
| `Min` | Minutos jugados. | - |
| `Mn/MP` | Minutos por partido jugado. | - |
| `Min%` | Porcentaje de minutos del equipo jugados por el jugador. | `Min del jugador / Min totales del equipo`; requisito lideres: minimo 30 min jugados por partido del equipo. |
| `90s` | Bloques de 90 minutos jugados. | `Min / 90` |
| `Starts` | Partidos iniciados. | - |
| `Mn/Start` | Minutos por partido iniciado. | Requisito lideres: minimo 30 min jugados por partido del equipo. |
| `Compl` | Partidos completos jugados. | - |
| `Subs` | Partidos entrando como suplente. | Partidos no iniciados. |
| `Mn/Sub` | Minutos por ingreso desde el banco. | Requisito lideres: minimo 30 min jugados por partido del equipo. |
| `unSub` | Partidos como suplente sin ingresar. | - |

## Team Success

| Variable | Descripcion | Formula / Notas |
|---|---|---|
| `PPM` | Puntos por partido. | Promedio de puntos del equipo en partidos donde el jugador participo; requisito lideres: minimo 30 min jugados por partido del equipo. |
| `onG` | Goles del equipo con el jugador en cancha. | - |
| `onGA` | Goles recibidos con el jugador en cancha. | - |
| `+/-` | Plus/Minus. | `onG - onGA` |
| `+/-90` | Plus/Minus por 90 minutos. | `(onG - onGA) / 90s`; requisito lideres: minimo 30 min jugados por partido del equipo. |

## Miscellaneous Stats

| Variable | Descripcion |
|---|---|
| `CrdY` | Tarjetas amarillas. |
| `CrdR` | Tarjetas rojas. |
| `2CrdY` | Segunda amarilla. |
| `Fls` | Faltas cometidas. |

