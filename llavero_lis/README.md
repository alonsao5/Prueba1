# Llavero articulado 3D LIS

- `llavero_LIS.stl`: listo para Cura. 55 x 11 x 24 mm. Letras gruesas (11 mm) que se aguantan de pie.
- `make_llavero.py`: generador paramétrico (`python3 make_llavero.py NOMBRE`). Medidas al inicio del script.
- `vista_previa.png`: vista frontal, desde arriba y en perspectiva.

## Cómo funciona
Cada letra es una pieza. Entre letras, por detrás, hay una bisagra de pin vertical impresa ya montada,
así que el llavero se curva en horizontal. Se imprime tal cual está (de pie), sin soportes.

## Ajustes recomendados en Cura (PLA)
- Capa 0,15-0,2 mm, 3 paredes, relleno 15-20 %, sin soportes, adhesión con **brim** (la base de la S es curva).
- Si las bisagras salen pegadas, sube `CLEAR` a 0,4-0,45 en el script y regenera. Dóblalas a mano para soltarlas.
- Dos colores (como en la foto): *Extensions > Post Processing > Pause at Height* en z = 16 mm y cambia de filamento.
- Pasa la anilla de llavero por el agujero de la izquierda.
