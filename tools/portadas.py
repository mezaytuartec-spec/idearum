# -*- coding: utf-8 -*-
"""
Idearum — deja las portadas del corredor listas para la web.

    python tools/portadas.py

Trabaja sobre assets/img/portadas/*.jpg, pisando los archivos:

  1. Las que no son cuadradas las recorta por el centro (las tarjetas del
     corredor son cuadradas: lo que sobra se perdería igual).
  2. Las de más de 640 px las achica a 640. Más que eso no se llega a ver
     ni en un celular bueno, y pesa el doble.
  3. Las comprime todas con la misma calidad.

NUNCA agranda una portada chica: eso suma bytes sin sumar nitidez. Si la que
conseguiste es de 300 px, va a verse blanda cuando la tarjeta pasa cerca;
conviene buscarla de 640 o más.

Tampoco deja un archivo más pesado del que había: si la portada ya estaba
bien y comprimirla de nuevo no mejora, la deja como está (volver a comprimir
un JPEG una y otra vez lo va ensuciando).

DESPUÉS DE CORRER ESTO hay que cambiar V_PORTADAS en js/app.js. Si no, el
navegador de quien ya entró a la web sigue mostrando las portadas viejas,
que guarda hasta 30 días.

Necesita Pillow:  python -m pip install pillow
"""
import io
import os
import sys
import glob

try:
    from PIL import Image
except ImportError:
    sys.exit("Falta Pillow. Instalalo con:  python -m pip install pillow")

LADO = 640        # ancho y alto maximos
CALIDAD = 82      # pareja para todas; a este tamano no se distingue de q92
MEJORA = 0.97     # solo se pisa el archivo si el nuevo pesa al menos 3% menos

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA = os.path.join(RAIZ, "assets", "img", "portadas")


def main():
    rutas = sorted(glob.glob(os.path.join(CARPETA, "*.jpg")))
    if not rutas:
        sys.exit("No encontre ninguna portada en %s" % CARPETA)

    total_antes = total_despues = 0
    tocadas = 0

    for ruta in rutas:
        nombre = os.path.basename(ruta)
        antes = os.path.getsize(ruta)

        im = Image.open(ruta)
        im.load()
        im = im.convert("RGB")
        w, h = im.size
        notas = []
        geometria = False

        if w != h:
            lado = min(w, h)
            izq, arr = (w - lado) // 2, (h - lado) // 2
            im = im.crop((izq, arr, izq + lado, arr + lado))
            notas.append("recortada %dx%d -> %dx%d" % (w, h, lado, lado))
            w = h = lado
            geometria = True

        if w > LADO:
            im = im.resize((LADO, LADO), Image.LANCZOS)
            notas.append("achicada %d -> %d" % (w, LADO))
            geometria = True

        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=CALIDAD, optimize=True,
                progressive=True, subsampling=2)
        nuevo = buf.getvalue()

        if geometria or len(nuevo) < antes * MEJORA:
            with open(ruta, "wb") as f:
                f.write(nuevo)
            despues = len(nuevo)
            notas.append("comprimida q%d" % CALIDAD)
            tocadas += 1
        else:
            despues = antes
            notas.append("ya estaba bien, no se toco")

        if w < LADO:
            notas.append("OJO: es de %d px, menos de los %d ideales" % (w, LADO))

        total_antes += antes
        total_despues += despues
        print("  %-16s %7.1f KB -> %7.1f KB   %s"
              % (nombre, antes / 1024.0, despues / 1024.0, ", ".join(notas)))

    print("\n  %d portadas, %d modificadas" % (len(rutas), tocadas))
    print("  Peso total: %.0f KB -> %.0f KB" % (total_antes / 1024.0,
                                                total_despues / 1024.0))
    if tocadas:
        print("\n  FALTA UN PASO: cambia V_PORTADAS en js/app.js por la fecha de hoy,")
        print("  si no, el que ya entro a la web sigue viendo las portadas viejas.")


if __name__ == "__main__":
    main()
