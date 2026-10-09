# -*- coding: utf-8 -*-
"""
Idearum — arma las muestras de 30 segundos del catalogo.

    python tools/previas.py "C:\\ruta\\a\\los\\demos" "C:\\otra\\carpeta"

Toma los MP3 completos de una o varias carpetas, los cruza con el catalogo
publicado (data/pistas.js) y deja en assets/audio/previas/ un recorte de 30
segundos por pista, con el ID como nombre: 0142.mp3.

Si el mismo audio aparece dos veces —una copia "(1)" de la descarga, o el mismo
tema en dos carpetas— se usa una sola vez. Se compara el contenido, no el
nombre: dos archivos distintos con el mismo nombre no se confunden.

Esos recortes son los que suenan en la web. El tema entero NO se sube nunca.

COMO CRUZA LOS ARCHIVOS
Primero aplica las asignaciones escritas a mano en tools/a_mano.txt, que son
para los casos que ninguna comparacion puede adivinar: dos pistas con el mismo
titulo, un archivo que se llama como otra cancion, o un audio que sirve para
dos filas del Excel.

El resto lo cruza comparando el nombre del archivo con el titulo de la pista,
salteando las marcas de siempre: "(Demo)", "(demo )", "_muestra",
"Titulo - Autor". Hace cinco pasadas, de mas segura a menos:

  1. el titulo es identico
  2. son las mismas palabras en otro orden ("La Oveja Triste" / "La triste
     oveja"), sin contar articulos ni preposiciones
  3. un titulo contiene al otro entero ("Penas y Alegrias del Amor" dentro de
     "Las Penas y Alegrias del Amor")
  4. hay una sola letra de diferencia ("Through it All" / "Throught it all")
  5. casi las mismas palabras, con una de diferencia ("Ser como Nunca Fui" /
     "Ser Quien Nunca Fui")

Las ultimas dos son las mas flojas: el informe las lista aparte para mirarlas.

Si un archivo puede ser de dos pistas distintas (dos versiones del mismo tema,
en estilos o tonalidades diferentes) NO elige ninguna: lo deja sin asignar y lo
lista al final. Para resolverlo, escribilo en tools/a_mano.txt —ahi esta
explicado el formato— y volve a correr esto.

DESPUES DE CORRER ESTO hay que volver a generar el catalogo, para que la web
sepa cuales pistas tienen muestra:

    python tools/csv_a_js.py Listado_2026_pistas.xlsx

Necesita ffmpeg. Si no esta en el PATH, se lo pasas con --ffmpeg "C:\\...\\ffmpeg.exe".
"""
import argparse
import collections
import glob
import hashlib
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
A_MANO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a_mano.txt")

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


# Palabras que no distinguen un titulo de otro.
VACIAS = {"el", "la", "los", "las", "un", "una", "de", "del", "y", "a", "en",
          "que", "mi", "tu", "su", "lo", "al", "the", "of"}


def fichas(s):
    """Las palabras que importan de un titulo, sin orden. 'La triste oveja' y
    'La Oveja Triste' dan lo mismo."""
    return frozenset(w for w in clave(s).split() if w not in VACIAS)


def sirve(f):
    """Un conjunto de palabras alcanza para comparar si tiene dos palabras, o
    una sola pero larga. Con una palabra corta se cruzaria cualquier cosa."""
    if len(f) >= 2:
        return True
    return len(f) == 1 and len(next(iter(f))) >= 4


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


def huella(ruta):
    """Identifica un audio por su contenido. El tamano alcanza para separar
    casi todos; solo se lee entero el que comparte tamano con otro."""
    return (os.path.getsize(ruta),)


COPIA = re.compile(r"\(\d+\)(?=\.[^.]+$)")


def nombre_dice_mas(ruta):
    """Para elegir entre dos copias del mismo audio. Gana el nombre que mas
    informacion trae: el que no es una copia "(1)" de la descarga y, a igual
    condicion, el mas largo, que suele ser el que trae el autor o el tono
    —y eso es justo lo que despues permite saber de que pista es."""
    base = os.path.basename(ruta)
    return (1 if COPIA.search(base) else 0, -len(base))


def sin_repetidos(archivos):
    """Devuelve (los que se usan, [(repetido, del que es copia)]).

    Un mismo audio puede llegar dos veces: la copia "(1)" que deja el navegador
    al bajar dos veces lo mismo, o el mismo tema en dos carpetas. Se usa una
    sola vez, y de los nombres se queda el que mas dice."""
    por_tamano = collections.defaultdict(list)
    for ruta in archivos:
        por_tamano[os.path.getsize(ruta)].append(ruta)

    # Solo se lee entero el que comparte tamano con otro.
    por_huella = collections.OrderedDict()
    for ruta in archivos:
        if len(por_tamano[os.path.getsize(ruta)]) == 1:
            h = ruta
        else:
            with open(ruta, "rb") as f:
                h = hashlib.md5(f.read()).hexdigest()
        por_huella.setdefault(h, []).append(ruta)

    elegidas, repes = set(), []
    for grupo in por_huella.values():
        queda = min(grupo, key=nombre_dice_mas)
        elegidas.add(queda)
        for r in grupo:
            if r != queda:
                repes.append((r, queda))
    # Se respeta el orden original: el cruce depende de el.
    return [r for r in archivos if r in elegidas], repes


def leer_catalogo():
    if not os.path.exists(PISTAS_JS):
        sys.exit("No encuentro %s. Genera primero el catalogo con tools/csv_a_js.py" % PISTAS_JS)
    js = open(PISTAS_JS, encoding="utf-8").read()
    pistas = [{"id": m.group(1), "titulo": m.group(2), "autor": m.group(3),
               "estilo": m.group(4), "tono": m.group(5)} for m in FILA.finditer(js)]
    if not pistas:
        sys.exit("No pude leer ninguna pista de data/pistas.js")
    return pistas


def nombre_clave(n):
    """Para buscar un archivo por nombre: no distingue mayusculas ni espacios
    de mas, pero SI los acentos, porque hay archivos que solo se diferencian
    en eso ("Abrazame.mp3" y "Abrazame.mp3" con tilde son dos temas)."""
    return " ".join((n or "").split()).lower()


def leer_a_mano():
    """Lee tools/a_mano.txt. Devuelve [(linea, archivo, titulo, autor)].
    titulo None = la linea esta mal escrita."""
    if not os.path.exists(A_MANO):
        return []
    filas = []
    with open(A_MANO, encoding="utf-8") as f:
        for n, linea in enumerate(f, 1):
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            if "=" not in linea:
                filas.append((n, linea, None, None))
                continue
            arch, _, pista = linea.partition("=")
            titulo, _, autor = pista.partition("|")
            filas.append((n, arch.strip(), titulo.strip(), autor.strip()))
    return filas


# ----------------------------------------------------------------- el cruce

def cruzar(pistas, archivos, a_mano=(), alias=None):
    """Devuelve (asignadas, dudosos, repetidos, sin_pista, errores_a_mano)."""
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

    # 0. lo escrito a mano en a_mano.txt. Va primero y no se discute: si una
    # linea esta mal, el que esta mal es el archivo de texto, y se avisa.
    errores = []
    # Los repetidos tambien se pueden nombrar en a_mano.txt: apuntan al que
    # quedo, que es el mismo audio.
    por_nombre = collections.defaultdict(set)
    por_nombre_flojo = collections.defaultdict(set)

    def anotar(nombre, ruta):
        por_nombre[nombre_clave(nombre)].add(ruta)
        por_nombre_flojo[clave(nombre)].add(ruta)

    for ruta in archivos:
        anotar(os.path.basename(ruta), ruta)
    for repetido, queda in (alias or {}).items():
        anotar(os.path.basename(repetido), queda)

    fijados = set()
    for n, nombre, titulo, autor in a_mano:
        if titulo is None:
            errores.append("linea %d: le falta el signo = ... %s" % (n, nombre))
            continue
        rutas = sorted(por_nombre.get(nombre_clave(nombre))
                       or por_nombre_flojo.get(clave(nombre)) or [])
        if not rutas:
            errores.append("linea %d: en la carpeta no hay ningun archivo %r" % (n, nombre))
            continue
        if len(rutas) > 1:
            errores.append("linea %d: %r puede ser %d audios distintos; aclara la carpeta"
                           % (n, nombre, len(rutas)))
            continue
        ruta = rutas[0]
        ops = [p for p in pistas if clave(p["titulo"]) == clave(titulo)
               and (not autor or clave(p["autor"]) == clave(autor))]
        comoquien = "%r de %r" % (titulo, autor) if autor else "%r" % titulo
        if not ops:
            errores.append("linea %d: en el catalogo no hay ninguna pista %s" % (n, comoquien))
            continue
        if len(ops) > 1:
            errores.append("linea %d: hay %d pistas %s; agregale el autor"
                           % (n, len(ops), comoquien))
            continue
        p = ops[0]
        if p["id"] in tomadas:
            errores.append("linea %d: %s ya tiene la muestra de %s"
                           % (n, p["titulo"], tomadas[p["id"]]))
            continue
        tomadas[p["id"]] = os.path.basename(ruta)
        asignadas.append((ruta, p, "a mano"))
        fijados.add(ruta)

    # Los que resolvio a mano no entran en las comparaciones automaticas.
    archivos = [r for r in archivos if r not in fijados]

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

    # 2. las mismas palabras en otro orden
    pendientes2 = []
    for ruta in pendientes:
        base = os.path.basename(ruta)
        cands = [fichas(c) for c in variantes(base)]
        cands = [c for c in cands if sirve(c)]
        hall = {}
        for p in pistas:
            if p["id"] in tomadas:
                continue
            fp = fichas(p["titulo"])
            if sirve(fp) and any(fp == c for c in cands):
                hall[p["id"]] = p
        hall = list(hall.values())
        if len(hall) == 1:
            tomadas[hall[0]["id"]] = base
            asignadas.append((ruta, hall[0], "otro orden"))
        elif len(hall) > 1:
            p = desempatar(base, hall)
            if p:
                tomadas[p["id"]] = base
                asignadas.append((ruta, p, "otro orden"))
            else:
                dudosos.append((base, hall))
        else:
            pendientes2.append(ruta)
    pendientes = pendientes2

    # 3. un titulo contiene al otro
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

    # 4. una letra de diferencia
    quedan2 = []
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
            quedan2.append(ruta)

    # 5. casi las mismas palabras: una de diferencia. Es la mas floja de todas,
    # por eso pide tres palabras en comun como minimo y va al final.
    sin_pista = []
    for ruta in quedan2:
        base = os.path.basename(ruta)
        cands = [c for c in (fichas(x) for x in variantes(base)) if len(c) >= 3]
        hall = {}
        for p in pistas:
            if p["id"] in tomadas:
                continue
            fp = fichas(p["titulo"])
            if len(fp) < 3:
                continue
            for c in cands:
                comun = len(fp & c)
                if comun >= 3 and comun >= max(len(fp), len(c)) - 1:
                    hall[p["id"]] = p
                    break
        hall = list(hall.values())
        if len(hall) == 1:
            tomadas[hall[0]["id"]] = base
            asignadas.append((ruta, hall[0], "casi iguales"))
        elif len(hall) > 1:
            p = desempatar(base, hall)
            if p:
                tomadas[p["id"]] = base
                asignadas.append((ruta, p, "casi iguales"))
            else:
                dudosos.append((base, hall))
        else:
            sin_pista.append(base)

    return asignadas, dudosos, repetidos, sin_pista, errores


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
    ap.add_argument("carpetas", nargs="+", help="carpeta(s) con los MP3 completos")
    ap.add_argument("--ffmpeg", default=None, help="ruta a ffmpeg.exe si no esta en el PATH")
    ap.add_argument("--rehacer", action="store_true", help="rehace las muestras que ya existen")
    ap.add_argument("--probar", action="store_true", help="solo muestra el cruce, no genera nada")
    ap.add_argument("--limpiar", action="store_true",
                    help="borra las muestras de pistas que ya no tienen audio asignado")
    args = ap.parse_args()

    for c in args.carpetas:
        if not os.path.isdir(c):
            sys.exit("No existe la carpeta %s" % c)

    pistas = leer_catalogo()
    archivos = []
    for c in args.carpetas:
        archivos += sorted(f for f in glob.glob(os.path.join(c, "*"))
                           if os.path.splitext(f)[1].lower() in (".mp3", ".mpeg", ".m4a", ".wav"))
    if not archivos:
        sys.exit("No encontre audios en %s" % ", ".join(args.carpetas))

    total_archivos = len(archivos)
    archivos, copias = sin_repetidos(archivos)
    alias = dict(copias)

    a_mano = leer_a_mano()
    asignadas, dudosos, repetidos, sin_pista, errores = cruzar(pistas, archivos, a_mano, alias)

    print("=" * 74)
    print("  audios en las carpetas ...... %d%s"
          % (total_archivos,
             "  (%d son copias del mismo audio)" % len(copias) if copias else ""))
    print("  pistas en el catalogo ....... %d" % len(pistas))
    print("  pistas con muestra .......... %d" % len(asignadas))
    for como in ("a mano", "identico", "otro orden", "contiene", "una letra", "casi iguales"):
        n = sum(1 for a in asignadas if a[2] == como)
        if n:
            print("       %-20s %4d%s"
                  % (como, n, "" if como in ("identico", "a mano") else "   <- conviene revisar"))
    print("  dudosos (sin asignar) ....... %d" % len(dudosos))
    print("  audio repetido .............. %d" % len(repetidos))
    print("  sin pista en el catalogo .... %d" % len(sin_pista))
    print("=" * 74)

    if errores:
        print("\nOJO — %d linea(s) de tools/a_mano.txt no se pudieron aplicar:" % len(errores))
        for e in errores:
            print("   %s" % e)

    amano = [a for a in asignadas if a[2] == "a mano"]
    if amano:
        print("\nASIGNADOS A MANO (%d) — de tools/a_mano.txt:" % len(amano))
        for ruta, p, _ in amano:
            print("   %-46s -> %s (%s)" % (os.path.basename(ruta)[:46], p["titulo"], p["autor"] or "sin autor"))

    for como, titulo in (("otro orden", "ASIGNADOS POR LAS MISMAS PALABRAS EN OTRO ORDEN"),
                         ("contiene", "ASIGNADOS PORQUE UN TITULO CONTIENE AL OTRO"),
                         ("una letra", "ASIGNADOS POR UNA LETRA DE DIFERENCIA"),
                         ("casi iguales", "ASIGNADOS POR CASI LAS MISMAS PALABRAS")):
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

    if copias:
        print("\nEL MISMO AUDIO DOS VECES (%d) — se usa uno solo:" % len(copias))
        for repetido, queda in copias:
            print("   %-46s = %s" % (os.path.basename(repetido)[:46], os.path.basename(queda)))

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

    # Muestras de pistas que ya no tienen audio asignado: quedan de un cruce
    # anterior. Hay que sacarlas, porque el generador del catalogo decide si
    # una pista "se puede escuchar" mirando si el archivo existe, y entonces
    # una muestra vieja hace que la web prometa algo que no corresponde.
    # No se borran solas: si esto se corrio con una carpeta de menos, TODAS
    # las demas parecerian sobrar. Se avisa, y se borran con --limpiar.
    asignados = set(p["id"] for _, p, _ in asignadas)
    sobran = sorted(f for f in os.listdir(DESTINO)
                    if f.endswith(".mp3") and f[:-4] not in asignados)
    if sobran:
        if args.limpiar:
            for f in sobran:
                os.remove(os.path.join(DESTINO, f))
            print("\n  BORRADAS %d muestras que ya no corresponden a ninguna pista: %s"
                  % (len(sobran), ", ".join(sobran)))
        else:
            print("\n  OJO: sobran %d muestras, de pistas que ahora no tienen audio"
                  " asignado:\n   %s" % (len(sobran), ", ".join(sobran)))
            print("  Si corriste esto con TODAS las carpetas de demos, borralas"
                  " con --limpiar.")

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
