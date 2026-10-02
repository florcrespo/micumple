# Crucigrama Flopicretense 🎉

Juego para el celular: cada invitado completa el crucigrama y los 2 primeros en terminarlo ganan.

- `index.html`: el juego.
- `index.html?ranking`: el ranking en vivo (para mirarlo o proyectarlo).
- `index.html?sala=prueba`: una sala aparte para probar sin ensuciar el ranking real.

El ranking usa [ntfy.sh](https://ntfy.sh), que guarda los resultados durante 12 horas.

## Cambiar palabras

Editá `tools/palabras.json` y corré `python3 tools/generar.py 4` (el número es la semilla; probá otras si la grilla queda muy ancha). Eso regenera `crucigrama.js`.
