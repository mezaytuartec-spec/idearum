#!/usr/bin/env python3
# USO:  python tools/csv_a_js.py Listado.xlsx      (o un .csv)  desde la carpeta idearum/
"""
Convierte el listado del catalogo (Excel .xlsx o CSV) en data/pistas.js.

COMO USARLO
-----------
Desde la carpeta idearum/:

    python tools/csv_a_js.py Listado_2026_COMPLETO.xlsx

Lee el Excel directamente, no hace falta exportarlo a CSV. Tambien acepta un
.csv. Solo usa la libreria estandar de Python 3: no hay que instalar nada.

COLUMNAS
--------
Se reconocen por el nombre del encabezado (sin importar mayusculas ni tildes):

    titulo  ->  "Nombre", "Titulo", "Tema" o "Cancion"
    autor   ->  "Autor", "Artista" o "Interprete"
    estilo  ->  "Estilo" o "Genero"
    propio  ->  "Propio"   (opcional)

Las demas columnas (Cliente, Pais, Tonalidad, Anio...) se ignoran y NUNCA se
publican: en la web solo aparecen titulo, autor y estilo.

QUE HACE CON LOS DATOS
----------------------
- ID: es el NUMERO DE FILA del Excel (fila 142 -> ID 0142). Asi, cuando por
  WhatsApp te piden "[ID: 0142]", vas directo a esa fila. Sacar o excluir
  filas no le cambia el ID a las demas; insertar filas en el medio, si.
  Por eso: las pistas nuevas, siempre AL FINAL de la planilla.
- Temas con "Propio" = Si: NO se publican. Son composiciones de clientes.
- Estilos: acepta plurales y variantes ("Baladas", "Boleros", "Rock/Pop",
  "Cancion del Recuerdo", "Folklore tradicional"...). "Otro" va a "Otros".
- Duplicados (mismo titulo, autor y estilo): queda solo el primero.
  El mismo tema en otro estilo se conserva: es otro arreglo.
- Texto roto por codificacion vieja ("Ma¤ana", "Caf‚", "Falc¢n"): se repara.
- Titulos todo en minuscula o todo en mayuscula: se acomodan.
- Un mismo autor escrito de varias formas ("Sergio denis" / "Sergio Denis"):
  se unifica en la mejor version.
- Orden: por estilo (en el orden de la web) y despues alfabetico.

Al terminar imprime un informe con todo lo que corrigio, para revisarlo.

OPCIONES
--------
   --salida ruta.js   escribir en otro archivo (por defecto data/pistas.js)
   --forzar           escribir aunque haya estilos que no reconoce
                      (esas filas se descartan igual)
"""

import argparse
import collections
import csv
import json
import os
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile

# Para que los avisos con tildes se vean bien en la consola de Windows.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Los estilos de la web, en el orden en que se muestran. Si agregas o sacas
# uno, cambialo tambien en js/app.js (ESTILOS) y en las pildoras de
# catalogo.html.
ESTILOS = [
    "Balada", "Rock / Pop", "Tropical", "Cuarteto", "Latino", "Románticos",
    "Canción del recuerdo", "Música cristiana", "Mariachi", "Folklore",
    "Bolero", "Tango", "Otros",
]

# Variantes que aparecen en las planillas -> estilo de la web.
ALIAS_ESTILO = {
    "baladas": "Balada",
    "boleros": "Bolero",
    "tangos": "Tango",
    "romantico": "Románticos",
    "romanticas": "Románticos",
    "romanticos": "Románticos",
    "cancionesdelrecuerdo": "Canción del recuerdo",
    "folklore tradicional": "Folklore",
    "folkloretradicional": "Folklore",
    "folclore": "Folklore",
    "cristiana": "Música cristiana",
    "cristianos": "Música cristiana",
    "rock": "Rock / Pop",
    "pop": "Rock / Pop",
    "otro": "Otros",
}

ALIAS_COLUMNA = {
    "titulo": ("titulo", "nombre", "tema", "cancion"),
    "autor": ("autor", "artista", "interprete"),
    "estilo": ("estilo", "genero"),
    "propio": ("propio",),
}

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA_POR_DEFECTO = os.path.join(RAIZ, "data", "pistas.js")

CABECERA = """/* ============================================================================
   IDEARUM - CATALOGO DE PISTAS
   Archivo generado automaticamente por tools/csv_a_js.py
   Origen: {origen}
   Pistas: {total}

   No lo edites a mano: se sobrescribe cada vez que corres el script.
   Para cambiar algo, corregilo en el Excel y volve a correr:
       python tools/csv_a_js.py {origen}

   El ID de cada pista es el numero de fila del Excel. Es lo que viaja en el
   mensaje de WhatsApp: con el ID encontras la fila exacta en la planilla.
   ============================================================================ */

window.PISTAS = ["""

PIE = """];
"""


# ---------------------------------------------------------------- utilidades

def clave(texto):
    """Sin tildes, sin mayusculas y sin signos. Sirve para comparar."""
    t = unicodedata.normalize("NFD", texto or "")
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return "".join(c for c in t.lower() if c.isalnum())


def alfabetico(texto):
    """Clave de orden: sin tildes ni mayusculas, pero respetando las palabras."""
    t = unicodedata.normalize("NFD", texto or "")
    t = "".join(c for c in t if unicodedata.category(c) != "Mn").lower()
    return " ".join("".join(c if c.isalnum() else " " for c in t).split())


def espacios(texto):
    return " ".join((texto or "").split())


# Letras danadas por haber pasado por la codificacion de DOS (CP850) y leido
# despues como Windows-1252. Cada simbolo raro es una letra con tilde.
ROTOS = {
    chr(0xA4): "ñ",    # ¤ -> ñ
    chr(0x201A): "é",  # ‚ -> é
    chr(0xB5): "Á",    # µ -> Á
    chr(0xA3): "ú",    # £ -> ú
    chr(0xA2): "ó",    # ¢ -> ó
    chr(0xA5): "Ñ",    # ¥ -> Ñ
    chr(0xA8): "¿",    # ¨ -> ¿
}
# Estos dos existen tambien como caracteres legitimos (el signo que abre una
# exclamacion y el espacio duro): solo se reparan pegados a una letra.
ROTOS_ENTRE_LETRAS = {
    chr(0xA1): "í",    # Garc?a, Aprend? -> í
    chr(0xA0): "á",    # L?grimas (espacio duro) -> á
}


def reparar(texto):
    out = []
    for i, ch in enumerate(texto):
        if ch in ROTOS:
            out.append(ROTOS[ch])
        elif ch in ROTOS_ENTRE_LETRAS and i > 0 and texto[i - 1].isalpha():
            sig = texto[i + 1] if i + 1 < len(texto) else ""
            if sig == "" or sig.isalpha() or sig in " ,.)":
                out.append(ROTOS_ENTRE_LETRAS[ch])
            else:
                out.append(ch)
        else:
            out.append(ch)
    return "".join(out)


def acomodar_titulo(t):
    """'la flor mas bella' -> 'La flor mas bella'; 'LA FLOR' -> 'La flor'."""
    letras = [c for c in t if c.isalpha()]
    if letras and all(c.isupper() for c in letras) and len(letras) > 3:
        t = t[:1] + t[1:].lower()
    if t[:1].islower():
        t = t[:1].upper() + t[1:]
    t = re.sub(r"\(\s+", "(", t)
    t = re.sub(r"\s+\)", ")", t)
    return t


CONECTORES = {"de", "del", "la", "las", "los", "el", "y", "e", "en", "da", "di",
              "the", "of", "and"}


def titulo_propio(nombre):
    """'horacio guarany' -> 'Horacio Guarany'; respeta 'de', 'la', 'y'."""
    partes = nombre.split(" ")
    out = []
    for i, p in enumerate(partes):
        if i > 0 and p.lower() in CONECTORES:
            out.append(p.lower())
        else:
            # Mayuscula en la primera LETRA (salta "(" o comillas) y el resto
            # tal cual: respeta "NTVG" o "McCartney".
            i_letra = next((j for j, c in enumerate(p) if c.isalpha()), None)
            if i_letra is not None:
                p = p[:i_letra] + p[i_letra].upper() + p[i_letra + 1:]
            out.append(p)
    return " ".join(out)


def acomodar_autor(a):
    a = re.sub(r"-\d+$", "", a).strip()     # "Mocedades-1" -> "Mocedades"
    a = re.sub(r"\(\s+", "(", a)
    a = re.sub(r"\s+\)", ")", a)
    return titulo_propio(a) if a else a


# ---------------------------------------------------------------- lectura

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}


def _columna(ref):
    n = 0
    for c in re.match(r"[A-Z]+", ref).group(0):
        n = n * 26 + (ord(c) - 64)
    return n - 1


def leer_xlsx(ruta):
    """Primera hoja del .xlsx como lista de filas (con numero de fila real)."""
    z = zipfile.ZipFile(ruta)
    compartidas = []
    if "xl/sharedStrings.xml" in z.namelist():
        raiz = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in raiz.findall("m:si", NS):
            compartidas.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
    libro = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    destino = {r.get("Id"): r.get("Target") for r in rels}
    hoja = libro.find("m:sheets", NS)[0]
    ruta_hoja = destino[hoja.get("{%s}id" % NS["r"])].lstrip("/")
    if not ruta_hoja.startswith("xl/"):
        ruta_hoja = "xl/" + ruta_hoja

    filas = []
    for row in ET.fromstring(z.read(ruta_hoja)).iter("{%s}row" % NS["m"]):
        valores = {}
        for c in row.findall("m:c", NS):
            v = c.find("m:v", NS)
            tipo = c.get("t")
            if tipo == "inlineStr":
                txt = "".join(x.text or "" for x in c.iter("{%s}t" % NS["m"]))
            elif v is None:
                txt = ""
            elif tipo == "s":
                txt = compartidas[int(v.text)]
            else:
                txt = v.text or ""
            valores[_columna(c.get("r"))] = txt
        if valores:
            fila = [valores.get(i, "") for i in range(max(valores) + 1)]
            filas.append((int(row.get("r")), fila))
    return filas


def leer_csv(ruta):
    with open(ruta, "r", encoding="utf-8-sig", newline="") as f:
        muestra = f.read(4096)
        f.seek(0)
        try:
            dialecto = csv.Sniffer().sniff(muestra, delimiters=",;\t")
        except csv.Error:
            dialecto = csv.excel
        return [(i, fila) for i, fila in enumerate(csv.reader(f, dialecto), start=1)]


def mapear_columnas(encabezado):
    idx = {}
    claves = [clave(h) for h in encabezado]
    for campo, nombres in ALIAS_COLUMNA.items():
        for n in nombres:
            if n in claves:
                idx[campo] = claves.index(n)
                break
    return idx


def estilo_web(crudo):
    k = clave(crudo)
    por_clave = {clave(e): e for e in ESTILOS}
    if k in por_clave:
        return por_clave[k]
    for alias, destino in ALIAS_ESTILO.items():
        if clave(alias) == k:
            return destino
    return None


# ---------------------------------------------------------------- principal

def main():
    ap = argparse.ArgumentParser(description="Listado del catalogo -> data/pistas.js")
    ap.add_argument("archivo", help="Excel (.xlsx) o CSV con titulo, autor y estilo")
    ap.add_argument("--salida", default=SALIDA_POR_DEFECTO)
    ap.add_argument("--forzar", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.archivo):
        print("ERROR: no encuentro el archivo " + args.archivo)
        return 2

    if args.archivo.lower().endswith(".xlsx"):
        filas = leer_xlsx(args.archivo)
    else:
        filas = leer_csv(args.archivo)
    if len(filas) < 2:
        print("ERROR: la planilla esta vacia.")
        return 2

    _, encabezado = filas[0]
    col = mapear_columnas(encabezado)
    faltan = [c for c in ("titulo", "autor", "estilo") if c not in col]
    if faltan:
        print("ERROR: no encuentro estas columnas: " + ", ".join(faltan))
        print("       Encabezados leidos: " + ", ".join(encabezado))
        return 2

    def celda(fila, campo):
        i = col.get(campo)
        return fila[i] if i is not None and i < len(fila) else ""

    informe = collections.defaultdict(list)
    candidatas = []
    genericos = ({clave(e) for e in ESTILOS} | {clave(a) for a in ALIAS_ESTILO} |
                 {"himno", "himnos", "gospel", "cumbia", "cristiano", "cristiana",
                  "tradicional", "anonimo", "varios"})

    for nro, fila in filas[1:]:
        titulo_crudo = celda(fila, "titulo")
        autor_crudo = celda(fila, "autor")
        titulo_c = espacios(titulo_crudo)
        autor_c = espacios(autor_crudo)
        estilo_c = espacios(celda(fila, "estilo"))

        if not (titulo_c or autor_c or estilo_c):
            continue
        if not titulo_c or not autor_c:
            informe["error"].append("fila %d: falta el %s" % (nro, "titulo" if not titulo_c else "autor"))
            continue

        if clave(celda(fila, "propio")) in ("si", "x", "1", "true"):
            informe["propio"].append("fila %d: %s - %s" % (nro, titulo_c, autor_c))
            continue

        estilo = estilo_web(estilo_c)
        if estilo is None:
            informe["error"].append("fila %d: estilo que no reconozco: %r (%s)" % (nro, estilo_c, titulo_c))
            continue
        if clave(estilo_c) != clave(estilo):
            informe["estilo"].append((estilo_c, estilo))

        titulo = espacios(reparar(titulo_crudo))
        autor = espacios(reparar(autor_crudo))
        if titulo != titulo_c or autor != autor_c:
            informe["reparado"].append("fila %d: %s - %s  ->  %s - %s" % (nro, titulo_c, autor_c, titulo, autor))

        t2 = acomodar_titulo(titulo)
        if t2 != titulo:
            informe["titulo"].append("fila %d: %r -> %r" % (nro, titulo, t2))
        a2 = acomodar_autor(autor)
        if a2 != autor:
            informe["autor"].append("fila %d: %r -> %r" % (nro, autor, a2))
        if clave(a2) in genericos:
            informe["generico"].append("fila %d: %s  (autor %r)" % (nro, t2, a2))
            a2 = ""

        candidatas.append({"nro": nro, "titulo": t2, "autor": a2, "estilo": estilo})

    # Un mismo autor escrito de varias formas: se queda la version mas
    # completa (la que tiene tildes y mayusculas).
    variantes = collections.defaultdict(collections.Counter)
    for p in candidatas:
        variantes[clave(p["autor"])][p["autor"]] += 1

    def puntaje(nombre):
        return (sum(1 for c in nombre if ord(c) > 127),
                sum(1 for c in nombre if c.isupper()))

    canon = {}
    for k, cnt in variantes.items():
        mejor = max(cnt, key=lambda n: (puntaje(n), cnt[n]))
        canon[k] = mejor
        if len(cnt) > 1 and k:
            informe["unificado"].append(" / ".join(sorted(cnt)) + "  ->  " + mejor)
    for p in candidatas:
        p["autor"] = canon[clave(p["autor"])]

    # Duplicados: mismo titulo + autor + estilo.
    vistas = {}
    pistas = []
    misma_cancion = collections.defaultdict(list)
    for p in candidatas:
        k = (clave(p["titulo"]), clave(p["autor"]), p["estilo"])
        if k in vistas:
            informe["duplicado"].append("fila %d igual a la fila %d: %s - %s (%s)"
                                        % (p["nro"], vistas[k], p["titulo"], p["autor"], p["estilo"]))
            continue
        vistas[k] = p["nro"]
        pistas.append(p)
        misma_cancion[(clave(p["titulo"]), clave(p["autor"]))].append(p)

    for grupo in misma_cancion.values():
        if len(grupo) > 1:
            informe["dos_estilos"].append("%s - %s: %s" % (
                grupo[0]["titulo"], grupo[0]["autor"],
                ", ".join("%s (fila %d)" % (g["estilo"], g["nro"]) for g in grupo)))

    # ------------------------------------------------------------ informe
    def seccion(titulo, lineas):
        if lineas:
            print("\n%s (%d)" % (titulo, len(lineas)))
            for l in lineas:
                print("   " + l)

    print("Leidas: %d filas" % (len(filas) - 1))
    seccion("NO SE PUBLICAN — temas propios de clientes", informe["propio"])
    seccion("DUPLICADOS — quedo solo el primero", informe["duplicado"])
    seccion("TEXTO REPARADO — letras danadas por codificacion", informe["reparado"])
    seccion("TITULOS ACOMODADOS", informe["titulo"])
    seccion("AUTORES ACOMODADOS", informe["autor"])
    seccion("AUTORES UNIFICADOS", informe["unificado"])
    seccion("AUTOR QUE ES UN GENERO — se muestra solo el estilo (completar en el Excel)",
            informe["generico"])
    cambios = collections.Counter(informe["estilo"])
    seccion("ESTILOS TRADUCIDOS", ["%-24r -> %s  (x%d)" % (a, b, n) for (a, b), n in sorted(cambios.items())])
    seccion("MISMO TEMA EN DOS ESTILOS — se publican los dos (revisar)", informe["dos_estilos"])
    seccion("ERRORES", informe["error"])

    if informe["error"] and not args.forzar:
        print("\nNo escribi nada. Corregi esas filas en el Excel y volve a correr,")
        print("o usa --forzar para generar igual descartandolas.")
        return 2
    if not pistas:
        print("\nERROR: no quedo ninguna pista.")
        return 2

    # ------------------------------------------------------------ salida
    orden = {e: i for i, e in enumerate(ESTILOS)}
    pistas.sort(key=lambda p: (orden[p["estilo"]], alfabetico(p["titulo"]), alfabetico(p["autor"])))

    os.makedirs(os.path.dirname(os.path.abspath(args.salida)), exist_ok=True)
    with open(args.salida, "w", encoding="utf-8", newline="\n") as f:
        print(CABECERA.format(origen=os.path.basename(args.archivo), total=len(pistas)), file=f)
        for i, p in enumerate(pistas):
            coma = "," if i < len(pistas) - 1 else ""
            print('  {{ id: {0}, titulo: {1}, autor: {2}, estilo: {3} }}{4}'.format(
                json.dumps("%04d" % p["nro"]),
                json.dumps(p["titulo"], ensure_ascii=False),
                json.dumps(p["autor"], ensure_ascii=False),
                json.dumps(p["estilo"], ensure_ascii=False),
                coma), file=f)
        print(PIE, file=f, end="")

    print("\nPOR ESTILO")
    cuenta = collections.Counter(p["estilo"] for p in pistas)
    for e in ESTILOS:
        print("   %-22s %4d" % (e, cuenta.get(e, 0)))
    print("\nListo: %d pistas publicadas en %s" % (len(pistas), args.salida))
    return 0


if __name__ == "__main__":
    sys.exit(main())
