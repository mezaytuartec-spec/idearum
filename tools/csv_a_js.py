#!/usr/bin/env python3
# USO:  python tools/csv_a_js.py mi_catalogo.csv      (desde la carpeta idearum/)
"""
Convierte el Excel del catalogo en data/pistas.js.

COMO USARLO
-----------
1. En Excel arma una planilla con exactamente tres columnas, con estos
   encabezados en la primera fila (en minuscula):

       titulo | autor | estilo

2. Guardala como CSV UTF-8:
       Archivo > Guardar como > "CSV UTF-8 (delimitado por comas) (*.csv)"

3. Ponete en la carpeta idearum/ y corre:

       python tools/csv_a_js.py mi_catalogo.csv

   Se reescribe data/pistas.js con los IDs numerados de 0001 en adelante.

OPCIONES
--------
   --salida ruta.js     escribir en otro archivo (por defecto data/pistas.js)
   --desde 1            numero con el que arranca el primer ID (por defecto 1)
   --forzar             escribir aunque haya filas con estilos no permitidos
                        (esas filas se descartan igual)

QUE VALIDA
----------
   - que el estilo este en la lista permitida (ver ESTILOS abajo);
   - que ni el titulo ni el autor esten vacios;
   - avisa si hay pistas duplicadas (mismo titulo + mismo autor).

IMPORTANTE
----------
Los IDs se asignan por orden de fila. Si mas adelante insertas una pista en el
medio de la planilla y volves a correr el script, los IDs posteriores cambian.
Para evitarlo, agrega las pistas nuevas siempre AL FINAL de la planilla.

Solo usa la libreria estandar de Python 3. No hay que instalar nada.
"""

import argparse
import csv
import json
import os
import sys
import unicodedata

# Para que los avisos con tildes se vean bien en la consola de Windows.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Si agregas o sacas un estilo, cambialo tambien en js/app.js (ESTILOS),
# en catalogo.html (pildoras de filtro) y en data/pistas.js.
ESTILOS = [
    "Balada", "Rock / Pop", "Tropical", "Cuarteto", "Latino", "Románticos",
    "Canción del recuerdo", "Música cristiana", "Mariachi", "Folklore",
    "Bolero", "Tango",
]

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA_POR_DEFECTO = os.path.join(RAIZ, "data", "pistas.js")

CABECERA = """/* ============================================================================
   IDEARUM - CATALOGO DE PISTAS
   Archivo generado automaticamente por tools/csv_a_js.py
   Origen: {origen}
   Pistas: {total}

   No lo edites a mano si vas a volver a correr el script: se sobrescribe.
   Los IDs son los que viajan en el mensaje de WhatsApp; no los cambies.
   ============================================================================ */

window.PISTAS = ["""

PIE = """];
"""


def abrir_csv(ruta):
    """Abre el CSV detectando el separador (coma o punto y coma) y el BOM."""
    with open(ruta, "r", encoding="utf-8-sig", newline="") as f:
        muestra = f.read(4096)
        f.seek(0)
        try:
            dialecto = csv.Sniffer().sniff(muestra, delimiters=",;\t")
        except csv.Error:
            dialecto = csv.excel
        return list(csv.DictReader(f, dialect=dialecto))


def clave(texto):
    """Normaliza un estilo para compararlo: sin tildes, sin mayusculas y sin
    signos. Asi 'Rock/Pop', 'rock / pop' y 'ROCK POP' son todos 'Rock / Pop',
    y 'Musica cristiana' encuentra 'Música cristiana'."""
    t = unicodedata.normalize("NFD", texto)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return "".join(c for c in t.lower() if c.isalnum())


def normalizar_cabeceras(fila):
    limpia = {}
    for k, v in fila.items():
        if k is None:
            continue
        limpia[k.strip().lower()] = (v or "").strip()
    return limpia


def main():
    ap = argparse.ArgumentParser(description="CSV del catalogo -> data/pistas.js")
    ap.add_argument("csv", help="archivo CSV con columnas titulo,autor,estilo")
    ap.add_argument("--salida", default=SALIDA_POR_DEFECTO)
    ap.add_argument("--desde", type=int, default=1)
    ap.add_argument("--forzar", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.csv):
        print("ERROR: no encuentro el archivo " + args.csv)
        return 2

    filas = abrir_csv(args.csv)
    if not filas:
        print("ERROR: el CSV esta vacio.")
        return 2

    faltan = [c for c in ("titulo", "autor", "estilo")
              if c not in normalizar_cabeceras(filas[0])]
    if faltan:
        print("ERROR: al CSV le faltan estas columnas: " + ", ".join(faltan))
        print("       La primera fila tiene que decir: titulo,autor,estilo")
        return 2

    estilos_ok = {clave(e): e for e in ESTILOS}

    pistas = []
    vistos = {}
    avisos = []
    errores = []
    n = args.desde

    for i, cruda in enumerate(filas, start=2):   # fila 1 = encabezados
        fila = normalizar_cabeceras(cruda)
        titulo = fila.get("titulo", "")
        autor = fila.get("autor", "")
        estilo = fila.get("estilo", "")

        if not titulo and not autor and not estilo:
            avisos.append("fila {0}: vacia, la salteo".format(i))
            continue
        if not titulo:
            errores.append("fila {0}: falta el titulo".format(i))
            continue
        if not autor:
            errores.append("fila {0}: falta el autor ({1})".format(i, titulo))
            continue
        if clave(estilo) not in estilos_ok:
            errores.append(
                "fila {0}: estilo no permitido: {1} ({2})".format(i, estilo or "vacio", titulo)
            )
            continue

        estilo = estilos_ok[clave(estilo)]
        dupe = (titulo.lower(), autor.lower())
        if dupe in vistos:
            avisos.append(
                "fila {0}: duplicada de la fila {1}: {2} - {3}".format(i, vistos[dupe], titulo, autor)
            )
        else:
            vistos[dupe] = i

        pistas.append({
            "id": "{0:04d}".format(n),
            "titulo": titulo,
            "autor": autor,
            "estilo": estilo,
        })
        n += 1

    for a in avisos:
        print("AVISO: " + a)
    for e in errores:
        print("ERROR: " + e)

    if errores and not args.forzar:
        print("")
        print("No escribi nada. Arregla esas filas y volve a correr el script,")
        print("o usa --forzar para generar el archivo descartando esas filas.")
        return 2

    if not pistas:
        print("ERROR: no quedo ninguna pista valida.")
        return 2

    os.makedirs(os.path.dirname(os.path.abspath(args.salida)), exist_ok=True)

    with open(args.salida, "w", encoding="utf-8", newline="") as f:
        print(CABECERA.format(origen=os.path.basename(args.csv), total=len(pistas)), file=f)
        for k, p in enumerate(pistas):
            coma = "," if k < len(pistas) - 1 else ""
            print('  {{ id: {0}, titulo: {1}, autor: {2}, estilo: {3} }}{4}'.format(
                json.dumps(p["id"]),
                json.dumps(p["titulo"], ensure_ascii=False),
                json.dumps(p["autor"], ensure_ascii=False),
                json.dumps(p["estilo"], ensure_ascii=False),
                coma), file=f)
        print(PIE, file=f, end="")

    print("")
    print("Listo: {0} pistas escritas en {1}".format(len(pistas), args.salida))
    print("IDs del {0:04d} al {1:04d}".format(args.desde, n - 1))
    if avisos:
        print("Revisa los {0} avisos de mas arriba.".format(len(avisos)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
