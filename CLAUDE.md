# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Repo de proyectos personales, en español. Dos proyectos independientes, sin build system, sin tests ni linter: `llavero_lis/` y `isla-a-la-deriva/`. Responde al usuario en español. Desarrolla en la rama `ccr-856efb02-s4qinc`; no abras PR salvo que se pida.

## llavero_lis (modelo 3D para imprimir)

Generador paramétrico de un llavero articulado print-in-place; la salida `llavero_LIS.stl` está versionada.

- Regenerar: `pip install trimesh shapely numpy matplotlib networkx scipy manifold3d mapbox_earcut fonttools` y luego `python3 llavero_lis/make_llavero.py [TEXTO]` (por defecto `LIS`, escribe `llavero_<TEXTO>.stl` en el directorio actual).
- Usa la fuente `/usr/share/fonts/opentype/inter/Inter-Black.otf` (ruta fija del entorno cloud).
- Cada letra es un bloque que se imprime **de pie** (z = altura) y se extruye en y (cara frontal en y=0, trasera en y=D). Entre letras hay una bisagra de pin vertical en la parte trasera: la pestaña A (z 0..4, lleva el pin con cabeza) y la B (z 4.4..9, con agujero) se solapan en z con holguras `CLEAR`/`LAYER_GAP`; ambas letras llevan "bolsillos" tallados (`POCKET_R`) para dejar sitio. Todo el diseño depende de esos z fijos (`Z_A1`, `Z_B0`, `Z_B1`, `Z_HEAD`): cámbialos juntos.
- Comprobación obligatoria tras cambiar algo: el script imprime las piezas independientes (`final.split`) y su estanqueidad; deben salir **tantas piezas como letras** y todas `watertight=True`. Si salen menos, la bisagra quedó fusionada; si hay más, una pestaña quedó flotando sin tocar su letra.
- Las medidas están en mm; ajustes de impresión (brim, pausa de color a z=16, `CLEAR` 0,4-0,45 si las bisagras se pegan) están en `llavero_lis/README.md`.

## isla-a-la-deriva (prototipo de juego)

Todo el juego es **un único archivo** `index.html` (CSS + JS inline, three.js r128 desde cdnjs). Está publicado también como Artifact de claude.ai (mismo archivo; para actualizarlo se republica la misma ruta). Reglas del Artifact: sin `<html>/<body>`, solo scripts de cdnjs, estado solo en `localStorage` (clave `isla-deriva-v1`, siempre en try/catch).

Estructura del JS (IIFE única, de arriba abajo):
1. **Datos**: `BUILD` (edificios y su `stat`), `HAZ` (peligros), `ROUTES` (rutas con eventos `{t, l}` y botín). El estado `S` = `{res, plots[6], trip, log, ...}` se serializa entero con `save()`.
2. **Reglas**: `stats()` suma solo edificios **no dañados** por tipo de `stat`; `chance(stat, lvl)` da la probabilidad de superar un peligro (se muestra en el mapa de rutas **y** se usa al resolver, mantenlas sincronizadas). `depart()` guarda `trip` con `end` y `seed`; `resolveTrip()` es determinista por `seed` y se ejecuta al arrancar si `Date.now() >= end` (el viaje avanza aunque se cierre la página).
3. **UI**: HUD, banner, dock y una única hoja inferior (`openSheet`) reutilizada por Explorar, Mejorar, Bitácora, Gente y Ruleta. Tras cualquier cambio de estado llama `refreshAll()` (HUD, banner, dock, reconstruye edificios 3D, minimapa).
4. **Escena 3D**: isla de celdas (`|x|+|z|<=4`), 6 parcelas en `PLOT_POS`; `MK[tipo]` construye cada edificio con primitivas y `rebuildBuildings()` los regenera desde `S.plots` (añade humo y "!" si `dmg`). Los toques se resuelven con raycast contra cilindros invisibles (`plotHits`); arrastrar rota la cámara.
5. `window.__isla` expone el estado y funciones para pruebas.

Peculiaridades de three.js r128: `MeshLambertMaterial` no admite `flatShading` (se usa `MeshPhongMaterial`) y no existe `CapsuleGeometry`.

### Probar en local (el entorno bloquea cdnjs y Google Fonts)

No hay comando de test; se prueba con Playwright (ya instalado) cargando el HTML por `file://` e interceptando la librería:

- Instala three desde npm en el scratchpad (`npm i three@0.128.0`) y sirve `node_modules/three/build/three.min.js` con `page.route('**/three.min.js', ...)`.
- Aborta las peticiones a `fonts.googleapis.com`/`gstatic.com` (producen un único `ERR_FAILED` esperable).
- Lanza chromium con `--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader --ignore-gpu-blocklist` para que WebGL funcione en headless.
- Para saltar un viaje, pulsa `#tfast` (Acelerar) o fija `S.trip.end` en el pasado y recarga. Selectores útiles: `#bExplore`, `#bBuild`, `#bLog`, `#bCrew`, `#sb .go`, `.opt`.
- Revisa capturas en 390x844 (móvil) y 1280x720 (escritorio); el título del banner, el minimapa `#map` y el dock se solapan fácilmente.

Hoja de ruta acordada con el usuario: fase 1 (actual) viaje + preparación + riesgo; fase 2 isla base para decorar con recursos raros (`pearls`); fase 3 ruleta/gemas/cosméticos; fase 4 versión Godot/APK con anuncios reales. El usuario quiere un estilo visual tipo 3D de juguete (referencia generada con Gemini); la vía acordada es que aporte sprites o modelos GLB y yo los integre.
