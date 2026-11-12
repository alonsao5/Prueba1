# Llavero articulado LIS

- `llavero_LIS.stl`: modelo listo para Cura (55 x 20,5 x 7 mm).
- `make_llavero.py`: generador paramétrico. `python3 make_llavero.py NOMBRE` crea otro llavero.
  Medidas ajustables al inicio del script (alto de letra, grosor, holgura de bisagra).

## Ajustes recomendados en Cura
- Imprimir **plano**, tal como viene (la cama es z = 0). Material: PLA.
- Altura de capa 0,15-0,2 mm, 3 paredes, relleno 20 %, **sin soportes**, adhesión: falda o ninguna.
- Si las bisagras salen pegadas, sube `CLEAR` a 0,4-0,45 en el script y regenera.
  Tras imprimir, dobla las letras con la mano para soltarlas.
- Dos colores (como en la foto): extensión *Post Processing > Pause at Height* en z = 4 mm y cambia filamento
  (en una Ultimaker S5 puedes usar dos extrusores).
- Pasa una anilla de llavero por el agujero de la izquierda.
