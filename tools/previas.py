# -*- coding: utf-8 -*-
"""
Idearum — arma las muestras de 30 segundos del catalogo.

    python tools/previas.py "C:\\ruta\\a\\la\\carpeta\\de\\demos"

Toma los MP3 completos de una carpeta, los cruza con el catalogo publicado
(data/pistas.js) y deja en assets/audio/previas/ un recorte de 30 segundos
por pista, con el ID como nombre: 0142.mp3.

Esos recortes son los que suenan en la web. El tema entero NO se sube nunca.

COMO CRUZA LOS ARCHIVOS
Compara el nombre del archivo con el titulo de la pista, salteando las marcas
de siempre: "(Demo)", "(demo )", "_muestra", "Titulo - Autor". Hace tres
pasadas, de mas segura a menos:

  1. el titulo es identico
  2. un titulo contiene al otro entero ("Penas y Alegrias del Amor" dentro de
     "Las Penas y Alegrias del Amor")
  3. hay una sola letra de diferencia ("Through it All" / "Throught it all")

Si un archivo puede ser de dos pistas distintas (dos versiones del mismo tema,
en estilos o tonalidades diferentes) NO elige ninguna: lo deja sin asignar y lo
lista al final. Para resolverlo, agregale el autor al nombre del archivo
—"(Demo) Abrazame - Jorge Vazquez.mp3"— y volve a correr esto.

DESPUES DE CORRER ESTO hay que volver a generar el catalogo, para que la web
sepa cuales pistas tienen muestra:

    python tools/csv_a_js.py Listado_2026_pistas.xlsx

Necesita ffmpeg. Si no esta en el PATH, se lo pasas con --ffmpeg "C:\\...\\ffmpeg.exe".
"""
import argparse
import collections
import glob
import os
import re
import subprocess
import sys
import unicodedata

SEGUNDOS = 30        # cuanto dura cada muestra
DESDE = 0            # desde que segundo del demo se recorta
KBPS = 128           # calidad de la muestra (el producto final va en WAV y 320)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PISTAS_JS = os.path.join(RAIZ, "data", "pistas.js")
DESTINO = os.path.join(RAIZ, "assets", "audio", "previas")

FILA = re.compile(
    r'\{\s*id:\s*"(\d+)",\s*titulo:\s*"((?:[^"\\]|\\.)*)",\s*autor:\s*"((?:[^"\\]|\\.)*)",'
    r'\s*estilo:\s*"((?:[^"\\]|\\.)*)",\s*tono:\s*"((?:[^"\\]|\\.)*)"')

# Donde suele estar ffmpeg si no esta en el PATH.
CANDIDATOS_FFMPEG = [
    "ffmpeg",
    r"C:\Program Files\Wondershare\Wondershare UniConverter 16 for Windows\ffmpeg.exe",
]


# ------------------------------------------------------------------ utilidades

def clave(s):
    """Para comparar: sin tildes, sin signos, sin mayusculas."""
    t = unicodedata.normalize("NFD", s or "")
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = t.lower().replace("ñ", "n")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", t).split())


def pegado(s):
    return clave(s).replace(" ", "")


def distancia(a, b):
    """Cuantas letras hay que cambiar para pasar de a a b."""
    if abs(len(a) - len(b)) > 2:
        return 9
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


MARCA_INI = re.compile(r"^\s*[\(\[]\s*(demo|final|muestra)[^)\]]*[\)\]]\s*", re.I)
MARCA_FIN = re.compile(r"[\s_\-]*[\(\[]?\s*(demo|muestra)\s*[\)\]]?\s*$", re.I)
MARCA_SOLA = re.compile(r"^\s*(demo|muestra)[\s_]+", re.I)
PAREN = re.compile(r"\s*[\(\[][^)\]]*[\)\]]\s*")


def variantes(nombre):
    """Del nombre del archivo saca candidatos a titulo, del mas completo al mas pelado."""
    n = nombre
    for ext in (".mp3.mpeg", ".mpeg", ".mp3", ".MP3"):
        if n.lower().endswith(ext.lower()):
            n = n[: -len(ext)]
            break
    n = MARCA_INI.sub("", n)
    n = MARCA_SOLA.sub("", n)
    n = MARCA_FIN.sub("", n)
    n = n.replace("_", " ").strip()
    n = re.sub(r"-\s*\d+\s*$", "", n).strip()
    v = [n]
    sp = PAREN.sub(" ", n).strip()
    if sp and sp != n:
        v.append(sp)
    for base in list(v):
        if " - " in base:
            v.append(base.split(" - ")[0].strip())
    return [x for x in dict.fromkeys(v) if x]


def buscar_ffmpeg(pedido):
    for c in ([pedido] if pedido else []) + CANDIDATOS_FFMPEG:
        try:
            subprocess.run([c, "-version"], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, check=True)
            return c
        except (OSError, subprocess.CalledProcessError):
            continue
    return None


def leer_catalogo():
    if not os.path.exists(PISTAS_JS):
        sys.exit("No encuentro %s. Genera primero el catalogo con tools/csv_a_js.py" % PISTAS_JS)
    js = open(PISTAS_JS, encoding="utf-8").read()
    pistas = [{"id": m.group(1), "titulo": m.group(2), "autor": m.group(3),
               "estilo": m.group(4), "tono": m.group(5)} for m in FILA.finditer(js)]
    if not pistas:
        sys.exit("No pude leer ninguna pista de data/pistas.js")
    return pistas


# ----------------------------------------------------------------- el cruce

def cruzar(pistas, archivos):
    """Devuelve (asignadas, dudosos, repetidos, sin_pista)."""
    por_titulo = collections.defaultdict(list)
    for p in pistas:
        por_titulo[clave(p["titulo"])].append(p)

    tomadas = {}
    asignadas = []      # (archivo, pista, como)
    dudosos, repetidos, pendientes = [], [], []

    def desempatar(base, libres):
        """Cuando varias pistas compiten por el mismo archivo, gana la que tenga
        el autor o la tonalidad escritos en el nombre del archivo. Si ninguna
        destaca, devuelve None y el archivo queda sin asignar."""
        texto = clave(base)
        punt = []
        for p in libres:
            s = sum(2 for w in clave(p["autor"]).split() if len(w) > 3 and w in texto)
            if p["tono"] and clave(p["tono"]) in texto:
                s += 3
            # Entre dos titulos que contienen al del archivo, gana el mas
            # parecido en largo: "Quedate en Buenos Aires" es mucho mas
            # "Adonde Vas, Quedate en Buenos Aires" que "Quedate".
            cercania = -abs(len(clave(p["titulo"])) - len(texto)) / 1000.0
            punt.append((s + cercania, p))
        punt.sort(key=lambda x: -x[0])
        if len(punt) == 1 or punt[0][0] > punt[1][0]:
            return punt[0][1]
        return None

    def elegir(base, opciones):
        libres = [p for p in opciones if p["id"] not in tomadas]
        if not libres:
            repetidos.append((base, opciones[0]["titulo"]))
            return None
        if len(libres) == 1:
            return libres[0]
        p = desempatar(base, libres)
        if p:
            return p
        dudosos.append((base, libres))
        return None

    # 1. titulo identico
    for ruta in archivos:
        base = os.path.basename(ruta)
        encontrado = False
        for cand in variantes(base):
            ops = por_titulo.get(clave(cand))
            if ops:
                p = elegir(base, ops)
                if p:
                    tomadas[p["id"]] = base
                    asignadas.append((ruta, p, "identico"))
                encontrado = True
                break
        if not encontrado:
            pendientes.append(ruta)

    # 2. un titulo contiene al otro
    quedan = []
    for ruta in pendientes:
        base = os.path.basename(ruta)
        cands = [clave(c) for c in variantes(base)]
        hall = []
        for p in pistas:
            if p["id"] in tomadas:
                continue
            ct = clave(p["titulo"])
            if len(ct) < 6:
                continue
            for cc in cands:
                if len(cc) >= 6 and ((" %s " % cc) in (" %s " % ct) or (" %s " % ct) in (" %s " % cc)):
                    hall.append(p)
                    break
        hall = list({p["id"]: p for p in hall}.values())
        if len(hall) == 1:
            tomadas[hall[0]["id"]] = base
            asignadas.append((ruta, hall[0], "contiene"))
        elif len(hall) > 1:
            p = desempatar(base, hall)
            if p:
                tomadas[p["id"]] = base
                asignadas.append((ruta, p, "contiene"))
            else:
                dudosos.append((base, hall))
        else:
            quedan.append(ruta)

    # 3. una letra de diferencia
    sin_pista = []
    for ruta in quedan:
        base = os.path.basename(ruta)
        cands = [pegado(c) for c in variantes(base)]
        hall = []
        for p in pistas:
            if p["id"] in tomadas:
                continue
            pt = pegado(p["titulo"])
            for pc in cands:
                if len(pc) >= 7 and len(pt) >= 7 and distancia(pc, pt) <= 1:
                    hall.append(p)
                    break
        hall = list({p["id"]: p for p in hall}.values())
        if len(hall) == 1:
            tomadas[hall[0]["id"]] = base
            asignadas.append((ruta, hall[0], "una letra"))
        elif len(hall) > 1:
            p = desempatar(base, hall)
            if p:
                tomadas[p["id"]] = base
                asignadas.append((ruta, p, "una letra"))
            else:
                dudosos.append((base, hall))
        else:
            sin_pista.append(base)

    return asignadas, dudosos, repetidos, sin_pista


# -------------------------------------------------------------------- recorte

def recortar(ff, origen, destino):
    cmd = [ff, "-y", "-hide_banner", "-loglevel", "error",
           "-ss", str(DESDE), "-t", str(SEGUNDOS), "-i", origen,
           "-vn", "-map_metadata", "-1",
           "-c:a", "libmp3lame", "-b:a", "%dk" % KBPS, "-ar", "44100",
           destino]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0 or not os.path.exists(destino) or os.path.getsize(destino) < 2000:
        return r.stderr.decode("utf-8", "replace").strip()[:200] or "salio un archivo vacio"
    return None


def main():
    ap = argparse.ArgumentParser(description="Arma las muestras de 30 s del catalogo.")
    ap.add_argument("carpeta", help="carpeta con los MP3 completos")
    ap.add_argument("--ffmpeg", default=None, help="ruta a ffmpeg.exe si no esta en el PATH")
    ap.add_argument("--rehacer", action="store_true", help="rehace las muestras que ya existen")
    ap.add_argument("--probar", action="store_true", help="solo muestra el cruce, no genera nada")
    args = ap.parse_args()

    if not os.path.isdir(args.carpeta):
        sys.exit("No existe la carpeta %s" % args.carpeta)

    pistas = leer_catalogo()
    archivos = sorted(f for f in glob.glob(os.path.join(args.carpeta, "*"))
                      if os.path.splitext(f)[1].lower() in (".mp3", ".mpeg", ".m4a", ".wav"))
    if not archivos:
        sys.exit("No encontre audios en %s" % args.carpeta)

    asignadas, dudosos, repetidos, sin_pista = cruzar(pistas, archivos)

    print("=" * 74)
    print("  audios en la carpeta ........ %d" % len(archivos))
    print("  pistas en el catalogo ....... %d" % len(pistas))
    print("  cruzados .................... %d" % len(asignadas))
    for como in ("identico", "contiene", "una letra"):
        n = sum(1 for a in asignadas if a[2] == como)
        if n:
            print("       %-20s %4d%s" % (como, n, "" if como == "identico" else "   <- conviene revisar"))
    print("  dudosos (sin asignar) ....... %d" % len(dudosos))
    print("  audio repetido .............. %d" % len(repetidos))
    print("  sin pista en el catalogo .... %d" % len(sin_pista))
    print("=" * 74)

    for como, titulo in (("contiene", "ASIGNADOS PORQUE UN TITULO CONTIENE AL OTRO"),
                         ("una letra", "ASIGNADOS POR UNA LETRA DE DIFERENCIA")):
        filas = [a for a in asignadas if a[2] == como]
        if filas:
            print("\n%s (%d) — revisar:" % (titulo, len(filas)))
            for ruta, p, _ in filas:
                print("   %-46s -> %s (%s)" % (os.path.basename(ruta)[:46], p["titulo"], p["autor"]))

    if dudosos:
        print("\nDUDOSOS — no les pongo muestra (%d)." % len(dudosos))
        print("Para resolverlos, agregale el autor al nombre del archivo y volve a correr esto:")
        for base, ops in dudosos:
            print("   %s" % base)
            for p in ops:
                print("        id %s | %-28s | %-22s | %s" % (p["id"], p["titulo"], p["autor"], p["estilo"]))

    if repetidos:
        print("\nAUDIO REPETIDO, no se usa (%d):" % len(repetidos))
        for base, t in repetidos:
            print("   %-46s ya hay muestra de %s" % (base[:46], t))

    if sin_pista:
        print("\nSIN PISTA EN EL CATALOGO (%d) — temas propios o que no estan en el Excel:" % len(sin_pista))
        for base in sin_pista:
            print("   %s" % base)

    if args.probar:
        print("\n(--probar: no genere ningun archivo)")
        return 0

    # ------------------------------------------------------------- generar
    ff = buscar_ffmpeg(args.ffmpeg)
    if not ff:
        sys.exit("\nNo encuentro ffmpeg. Instalalo o pasame la ruta con --ffmpeg")

    os.makedirs(DESTINO, exist_ok=True)
    hechas = saltadas = 0
    fallidas = []
    total = len(asignadas)
    for i, (ruta, p, _) in enumerate(asignadas, 1):
        destino = os.path.join(DESTINO, p["id"] + ".mp3")
        if os.path.exists(destino) and not args.rehacer:
            saltadas += 1
            continue
        err = recortar(ff, ruta, destino)
        if err:
            fallidas.append((os.path.basename(ruta), err))
        else:
            hechas += 1
        if i % 25 == 0 or i == total:
            print("   recortando... %d/%d" % (i, total))

    peso = sum(os.path.getsize(os.path.join(DESTINO, f))
               for f in os.listdir(DESTINO) if f.endswith(".mp3"))
    cuantas = len([f for f in os.listdir(DESTINO) if f.endswith(".mp3")])
    print("\n  muestras nuevas: %d   ya estaban: %d   fallaron: %d" % (hechas, saltadas, len(fallidas)))
    for base, err in fallidas:
        print("   ! %s: %s" % (base, err))
    print("  en assets/audio/previas/ hay %d muestras, %.1f MB en total"
          % (cuantas, peso / 1024.0 / 1024.0))
    print("\n  FALTA UN PASO: volve a generar el catalogo para que la web sepa")
    print("  cuales pistas tienen muestra:")
    print("      python tools/csv_a_js.py Listado_2026_pistas.xlsx")
    return 0


if __name__ == "__main__":
    sys.exit(main())
