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
    tono    ->  "Tonalidad" (opcional, se normaliza sola)

Las demas columnas (Cliente, Pais, Tonalidad, Anio...) se ignoran y NUNCA se
publican: en la web solo aparecen titulo, autor, estilo y tonalidad.

QUE HACE CON LOS DATOS
----------------------
- ID: es el NUMERO DE FILA del Excel (fila 142 -> ID 0142). Asi, cuando por
  WhatsApp te piden "[ID: 0142]", vas directo a esa fila. Sacar o excluir
  filas no le cambia el ID a las demas; insertar filas en el medio, si.
  Por eso: las pistas nuevas, siempre AL FINAL de la planilla.
- Temas con "Propio" = Si: NO se publican. Son composiciones de clientes.
  Lo mismo con los temas cuyo AUTOR figure en AUTORES_PROPIOS, mas abajo:
  sirve para los que quedaron sin marcar en la planilla.
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
import datetime
import csv
import json
import os
import re
import sys
import unicodedata
from urllib.parse import quote
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
    "tono": ("tonalidad", "tono"),
}

# ---------------------------------------------------------------- tonalidad
# En la planilla la tonalidad esta escrita a mano y aparece de muchas formas
# distintas para la misma nota: "Do Mayor", "Do mayor", "ReMayor", "Mi b
# Mayor", "Re menor2", "SI b Mayor". Aca se reduce todo a una sola forma.
#
# Ademas se juntan las que suenan igual aunque se escriban distinto: Re# menor
# y Mib menor son la misma tonalidad, y para un cantante da lo mismo cual de
# las dos diga. Se prefiere el bemol en las mayores y el sostenido en las
# menores, que es como estan escritas en su mayoria.

ALTURA = {
    "do": 0, "do#": 1, "reb": 1, "re": 2, "re#": 3, "mib": 3, "mi": 4,
    "fa": 5, "fa#": 6, "solb": 6, "sol": 7, "sol#": 8, "lab": 8,
    "la": 9, "la#": 10, "sib": 10, "si": 11,
}
NOMBRE_TONO = {
    0: ("Do", "Do"), 1: ("Reb", "Do#"), 2: ("Re", "Re"), 3: ("Mib", "Re#"),
    4: ("Mi", "Mi"), 5: ("Fa", "Fa"), 6: ("Fa#", "Fa#"), 7: ("Sol", "Sol"),
    8: ("Lab", "Sol#"), 9: ("La", "La"), 10: ("Sib", "Sib"), 11: ("Si", "Si"),
}


def tono_web(crudo):
    """'Mi b Mayor' -> 'Mib mayor'. Devuelve "" si no se entiende."""
    if not crudo:
        return ""
    t = unicodedata.normalize("NFD", str(crudo))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn").lower()
    t = t.replace("\ufffd", " ")
    if "guia" in t:
        return ""
    t = t.split("_")[0]                      # 'Do# menor_Fa menor' -> el primero
    t = re.sub(r"\d+", " ", t)               # 'Re menor2' -> 'Re menor'
    t = re.sub(r"[^a-z#\s]", " ", t)
    t = " ".join(t.split())
    if not t:
        return ""
    modo = "menor" if "menor" in t else ("mayor" if "mayor" in t else "")
    t = " ".join(t.replace("menor", " ").replace("mayor", " ").split())
    t = re.sub(r"\s+b\b", "b", t)
    t = re.sub(r"\s+#", "#", t).replace(" ", "")
    if t not in ALTURA:
        return ""
    alt = ALTURA[t]
    if not modo:
        return NOMBRE_TONO[alt][0]
    return "%s %s" % (NOMBRE_TONO[alt][0 if modo == "mayor" else 1], modo)


def orden_tono(t):
    """Para listarlas como las ordena un musico: mayores y despues menores."""
    if not t:
        return (9, 99)
    partes = t.split()
    nota = unicodedata.normalize("NFD", partes[0]).lower()
    nota = "".join(c for c in nota if unicodedata.category(c) != "Mn")
    modo = partes[1] if len(partes) > 1 else ""
    return ({"mayor": 0, "menor": 1}.get(modo, 2), ALTURA.get(nota, 99))



# Autores que en realidad son clientes: el tema lo compusieron ellos, asi que
# NO se publica, aunque en el Excel la columna "Propio" haya quedado vacia.
# Se compara sin tildes, sin mayusculas y sin signos, asi que da igual escribir
# "Martin Gonzalez" o "Martín González".
#
# Ojo: esto mira la columna AUTOR, no la de Cliente. Que alguien figure como
# cliente de un cover de Charly Garcia no saca ese cover del catalogo.
AUTORES_PROPIOS = (
    "Martin Gonzalez",
)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA_POR_DEFECTO = os.path.join(RAIZ, "data", "pistas.js")

# Donde viven las muestras de 30 segundos, una por pista, con el nombre del ID.
PREVIAS = os.path.join(RAIZ, "assets", "audio", "previas")

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

# ============================================================================
# UNA PAGINA POR PISTA
# ============================================================================
# Nadie busca "pistas para cantantes": busca "pista de El dia que me quieras".
# Con las pistas metidas todas adentro de catalogo.html, Google no tiene nada
# que mostrar para esa busqueda. Por eso cada pista tiene ademas su propia
# pagina, con su titulo, su autor y su tonalidad, y todas juntas van al
# sitemap.xml. Se generan solas desde el Excel: no se tocan a mano.

DOMINIO = "https://pistasparacantantes.com"
WSP_WEB = "5492656442608"      # el mismo que esta en js/app.js
CARPETA_PAGINAS = "pista"


def slug_url(texto):
    """'El Día que me Quieras' -> 'el-dia-que-me-quieras'"""
    t = unicodedata.normalize("NFD", texto or "")
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = t.lower().replace("ñ", "n")
    t = re.sub(r"[^a-z0-9]+", "-", t)
    return t.strip("-")[:60] or "pista"


def esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


PAGINA = """<!DOCTYPE html>
<html lang="es" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{TITLE}}</title>
<meta name="description" content="{{DESC}}">
<meta name="theme-color" content="#ffffff">
<link rel="canonical" href="{{URL}}">

<meta property="og:type" content="website">
<meta property="og:locale" content="es_AR">
<meta property="og:site_name" content="Idearum">
<meta property="og:title" content="Idearum &mdash; Pistas profesionales para cantantes">
<meta property="og:description" content="{{DESC}}">
<meta property="og:url" content="{{URL}}">
<meta property="og:image" content="{{DOM}}/assets/img/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{{DOM}}/assets/img/og.jpg">

<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" type="image/png" sizes="96x96" href="/assets/img/favicon-96-dark.png?v={{V}}" media="(prefers-color-scheme: dark)">
<link rel="icon" type="image/png" sizes="96x96" href="/assets/img/favicon-96.png?v={{V}}">
<link rel="apple-touch-icon" sizes="180x180" href="/assets/img/apple-touch-icon.png?v=20260914-1">

<link rel="stylesheet" href="/css/styles.css?v={{V}}">

<script>
  document.documentElement.classList.remove("no-js");
  setTimeout(function () {
    if (!window.IDEARUM) document.documentElement.classList.add("no-js");
  }, 5000);
</script>

<script type="application/ld+json">{{JSONLD}}</script>
</head>

<body>

<header class="nav">
  <div class="nav__in">
    <a class="nav__logo" href="/index.html">
      <img src="/assets/img/logo.png?v=20260914-1" alt="" width="20" height="20">
      <span>Idearum</span>
    </a>
    <nav class="nav__links" aria-label="Principal">
      <a href="/catalogo.html">Cat&aacute;logo</a>
      <a href="/como-funciona.html">C&oacute;mo funciona</a>
      <a href="/index.html#a-medida">Cover a pedido</a>
      <a href="https://wa.me/{{WSP}}" data-wsp="Hola Idearum, quiero hacer una consulta." target="_blank" rel="noopener">Contacto</a>
    </nav>
    <button class="nav__burger" type="button" aria-label="Abrir men&uacute;" aria-expanded="false" aria-controls="menu">
      <span></span><span></span>
    </button>
  </div>
</header>

<div class="menu" id="menu">
  <a href="/index.html">Inicio</a>
  <a href="/catalogo.html">Cat&aacute;logo</a>
  <a href="/como-funciona.html">C&oacute;mo funciona</a>
  <a href="/index.html#a-medida">Cover a pedido</a>
  <a href="/index.html#a-medida">Tema propio</a>
  <a href="https://wa.me/{{WSP}}" data-wsp="Hola Idearum, quiero hacer una consulta." target="_blank" rel="noopener">Contacto</a>
</div>

<main>
  <section class="pista-cab">
    <div class="wrap">
      <nav class="miga" aria-label="D&oacute;nde estoy">
        <a href="/catalogo.html">Cat&aacute;logo</a>
        <span aria-hidden="true">&rsaquo;</span>
        <a href="/catalogo.html#estilo={{ESTILOSLUG}}">{{ESTILO}}</a>
      </nav>

      <h1 class="pista-titulo">{{TITULO}}</h1>
      <p class="pista-autor">{{AUTOR_TXT}}</p>

      <dl class="pista-datos">
        <div><dt>Estilo</dt><dd>{{ESTILO}}</dd></div>
        {{TONO_DATO}}
        <div><dt>Formato</dt><dd>WAV y MP3 320&nbsp;kbps</dd></div>
        <div><dt>C&oacute;digo</dt><dd>{{ID}}</dd></div>
      </dl>

      <p class="pista-karaoke">&iquest;Buscabas el <strong>karaoke de {{TITULO}}</strong>? Es para lo mismo:
         suena sin voz para que cantes vos. La diferencia es que est&aacute; grabada de
         cero con m&uacute;sicos e instrumentos reales, no es un karaoke armado con
         sonidos de computadora.</p>

      {{MUESTRA}}

      <div class="pista-compra">
        <p class="pista-precio"><span>US$</span><span class="num">40</span><span class="en-pesos" data-usd="40" hidden></span></p>
        <a class="btn btn--primario btn--grande"
           href="https://wa.me/{{WSP}}?text={{MSG}}"
           target="_blank" rel="noopener">Pedir esta pista</a>
        <p class="nota">Te la mandamos por WhatsApp en WAV y MP3. Tres por US$&nbsp;99, diez por US$&nbsp;249.</p>
        <p class="nota pista-garantia">Si la tonalidad no te sirve, te devolvemos la plata o la cambi&aacute;s por otra del cat&aacute;logo.</p>
      </div>

      <div class="pista-otra">
        <h2>&iquest;La necesit&aacute;s en otra tonalidad?</h2>
        <p>Esta pista se entrega en el tono que dice arriba. Para cantarla en otro
           hay que volver a grabarla de cero, con m&uacute;sicos e instrumentos reales:
           eso es un cover a medida, desde US$&nbsp;150 y con entrega en 7 a 10 d&iacute;as.</p>
        <a class="chev" href="/index.html#a-medida">Ver c&oacute;mo es un cover a medida</a>
      </div>
    </div>
  </section>

  {{RELACIONADAS}}
</main>

<footer class="footer">
  <div class="wrap">
    <div class="footer__cols">
      <div>
        <h4>Cat&aacute;logo</h4>
        <ul>
          <li><a href="/catalogo.html">Todas las pistas</a></li>
          <li><a href="/catalogo.html#estilo={{ESTILOSLUG}}">{{ESTILO}}</a></li>
        </ul>
      </div>
      <div>
        <h4>A medida</h4>
        <ul>
          <li><a href="/index.html#a-medida">Cover a pedido</a></li>
          <li><a href="/index.html#a-medida">Tema propio</a></li>
        </ul>
      </div>
      <div>
        <h4>Contacto</h4>
        <ul>
          <li><a href="https://wa.me/{{WSP}}" data-wsp="Hola Idearum, quiero hacer una consulta." target="_blank" rel="noopener">Escribinos por WhatsApp</a></li>
          <li>Consultas y pedidos, todos los d&iacute;as.</li>
        </ul>
      </div>
    </div>
    <div class="footer__pie">
      <p class="footer__marca"><img src="/assets/img/logo.png?v=20260914-1" alt="" width="16" height="16"><span>Copyright &copy; <span data-anio>2026</span> Idearum. Todos los derechos reservados.</span></p>
      <p>Producci&oacute;n musical.</p>
    </div>
  </div>
</footer>

<script src="/js/app.js?v={{V}}" defer></script>

</body>
</html>
"""


def escribir_paginas(pistas, version):
    """Deja una pagina por pista en pista/ y devuelve la lista de URLs."""
    import shutil
    carpeta = os.path.join(RAIZ, CARPETA_PAGINAS)
    if os.path.isdir(carpeta):
        shutil.rmtree(carpeta)      # se regenera entera: no quedan paginas viejas
    os.makedirs(carpeta)

    por_estilo = collections.defaultdict(list)
    for p in pistas:
        por_estilo[p["estilo"]].append(p)

    urls = []
    for p in pistas:
        ident = "%04d" % p["nro"]
        archivo = p["pag"]
        url = "%s/%s/%s" % (DOMINIO, CARPETA_PAGINAS, archivo)
        autor = p["autor"]
        tono = p["tono"]

        trozos = ["Pista de %s" % p["titulo"]]
        if autor:
            trozos.append(autor)
        titulo_pagina = "%s | Idearum" % " — ".join(trozos)
        if tono:
            titulo_pagina = "Pista de %s%s (%s) | Idearum" % (
                p["titulo"], (" — " + autor) if autor else "", tono)

        # La descripcion que muestra Google. Incluye "karaoke" porque es la
        # palabra con la que la gente busca esto, aunque el producto sea mejor
        # que un karaoke: si la pagina no la dice, no aparece en esa busqueda.
        desc = ("Pista de %s%s para cantar%s, estilo %s. Karaoke profesional "
                "grabado con músicos reales. Escuchá la muestra."
                % (p["titulo"], (" de " + autor) if autor else "",
                   (" en " + tono) if tono else "", p["estilo"]))

        mensaje = "Hola Idearum, quiero esta pista: %s%s (%s%s) [ID: %s]" % (
            p["titulo"], (" — " + autor) if autor else "", p["estilo"],
            (", " + tono) if tono else "", ident)

        tiene = p["demo"]
        if tiene:
            muestra = ('<div class="pista-muestra">\n'
                       '        <p class="etiqueta">Escuch&aacute; 30 segundos</p>\n'
                       '        <div class="repro" data-audio="/assets/audio/previas/%s.mp3" data-nombre="%s"></div>\n'
                       '      </div>' % (ident, esc(p["titulo"])))
        else:
            muestra = ('<p class="pista-sin-muestra">Esta pista todav&iacute;a no tiene muestra en l&iacute;nea. '
                       'Escribinos y te la mandamos para que la escuches antes de comprarla.</p>')

        # Otras del mismo estilo, para que Google (y la gente) sigan navegando.
        otras = [o for o in por_estilo[p["estilo"]] if o["nro"] != p["nro"]][:6]
        if otras:
            filas = []
            for o in otras:
                ometa = " &middot; ".join(x for x in [esc(o["autor"]), esc(o["estilo"])] if x)
                if o["tono"]:
                    ometa += ' &middot; <span class="fila__tono">%s</span>' % esc(o["tono"])
                filas.append(
                    '<div class="fila">'
                    '<span class="fila__hueco" aria-hidden="true"></span>'
                    '<div class="fila__txt">'
                    '<h3 class="fila__titulo"><a href="/%s/%s">%s</a></h3>'
                    '<p class="fila__meta meta">%s</p>'
                    '</div></div>'
                    % (CARPETA_PAGINAS, o["pag"], esc(o["titulo"]), ometa))
            relacionadas = (
                '<section class="seccion pista-mas">\n    <div class="wrap">\n'
                '      <h2 class="h-seccion">M&aacute;s de %s</h2>\n'
                '      <div class="lista lista--una">%s</div>\n'
                '      <p class="centro"><a class="chev" href="/catalogo.html#estilo=%s">Ver todo el cat&aacute;logo</a></p>\n'
                '    </div>\n  </section>' % (esc(p["estilo"]), "".join(filas), slug_url(p["estilo"])))
        else:
            relacionadas = ""

        jsonld = json.dumps({
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "Pista musical de %s" % p["titulo"],
            "description": desc,
            "category": p["estilo"],
            "sku": ident,
            "brand": {"@type": "Brand", "name": "Idearum"},
            "offers": {
                "@type": "Offer",
                "url": url,
                "price": "40",
                "priceCurrency": "USD",
                "availability": "https://schema.org/InStock",
            },
        }, ensure_ascii=False)

        tono_dato = ("<div><dt>Tonalidad</dt><dd>%s</dd></div>" % esc(tono)) if tono else ""
        autor_txt = esc(autor) if autor else "Autor no identificado"

        html = PAGINA
        for marca, valor in (
            ("{{TITLE}}", esc(titulo_pagina)), ("{{DESC}}", esc(desc)),
            ("{{URL}}", url), ("{{DOM}}", DOMINIO), ("{{V}}", version),
            ("{{JSONLD}}", jsonld), ("{{TITULO}}", esc(p["titulo"])),
            ("{{AUTOR_TXT}}", autor_txt), ("{{ESTILO}}", esc(p["estilo"])),
            ("{{ESTILOSLUG}}", slug_url(p["estilo"])), ("{{TONO_DATO}}", tono_dato),
            ("{{ID}}", ident), ("{{MUESTRA}}", muestra),
            ("{{RELACIONADAS}}", relacionadas), ("{{WSP}}", WSP_WEB),
            ("{{MSG}}", quote(mensaje, safe="")),
        ):
            html = html.replace(marca, valor)

        with open(os.path.join(carpeta, archivo), "w", encoding="utf-8", newline="\n") as f:
            f.write(html)
        urls.append(url)

    return urls


def escribir_sitemap(urls):
    hoy = datetime.date.today().isoformat()
    partes = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u, pri in [(DOMINIO + "/", "1.0"), (DOMINIO + "/catalogo.html", "0.9"),
                   (DOMINIO + "/como-funciona.html", "0.7")]:
        partes.append("  <url><loc>%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>" % (u, hoy, pri))
    for u in urls:
        partes.append("  <url><loc>%s</loc><lastmod>%s</lastmod><priority>0.6</priority></url>" % (u, hoy))
    partes.append("</urlset>")
    with open(os.path.join(RAIZ, "sitemap.xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(partes) + "\n")


def main():
    ap = argparse.ArgumentParser(description="Listado del catalogo -> data/pistas.js")
    ap.add_argument("archivo", help="Excel (.xlsx) o CSV con titulo, autor y estilo")
    ap.add_argument("--salida", default=SALIDA_POR_DEFECTO)
    ap.add_argument("--forzar", action="store_true")
    ap.add_argument("--sin-paginas", action="store_true",
                    help="no regenera la carpeta pista/ ni el sitemap")
    ap.add_argument("--version", default="20261006-2",
                    help="el ?v= que llevan el CSS y el JS en las paginas generadas")
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
    propios = {clave(a) for a in AUTORES_PROPIOS}
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

        if clave(a2) in propios:
            informe["propio"].append("fila %d: %s - %s  (autor en AUTORES_PROPIOS)"
                                     % (nro, t2, a2))
            continue

        tono_c = espacios(celda(fila, "tono"))
        tono = tono_web(tono_c)
        if tono_c and not tono:
            informe["tono"].append("fila %d: no entiendo la tonalidad %r (%s)" % (nro, tono_c, t2))

        candidatas.append({"nro": nro, "titulo": t2, "autor": a2,
                           "estilo": estilo, "tono": tono})

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

    # El mismo tema del mismo autor cargado en dos estilos distintos es casi
    # siempre un error de la planilla, no dos arreglos diferentes: hay un solo
    # audio para los dos. Queda la fila mas vieja (la de numero mas chico) y se
    # avisa cual se saco, para corregirlo en el Excel si quedo el estilo que no
    # va. Publicar las dos ensucia el catalogo y deja el audio sin asignar,
    # porque el script no puede saber a cual de las dos corresponde.
    sobran = set()
    for grupo in misma_cancion.values():
        if len(grupo) > 1:
            grupo.sort(key=lambda x: x["nro"])
            queda = grupo[0]
            for p in grupo[1:]:
                sobran.add(p["nro"])
                informe["dos_estilos"].append(
                    "%s - %s: queda %s (fila %d), se saca %s (fila %d)"
                    % (p["titulo"], p["autor"], queda["estilo"], queda["nro"],
                       p["estilo"], p["nro"]))
    if sobran:
        pistas = [p for p in pistas if p["nro"] not in sobran]

    for grupo in []:
        if len(grupo) > 1:
            informe["_viejo"].append("%s - %s: %s" % (
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
    seccion("MISMO TEMA EN DOS ESTILOS — se publica uno solo (revisar el Excel)",
            informe["dos_estilos"])
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

    # Marcar cuales tienen muestra y cual es el archivo de su pagina.
    for p in pistas:
        ident = "%04d" % p["nro"]
        p["demo"] = os.path.exists(os.path.join(PREVIAS, ident + ".mp3"))
        p["pag"] = "%s-%s.html" % (slug_url(p["titulo"]), ident)

    # Primero las que se pueden escuchar. Una pista muda compite en desventaja:
    # nadie paga un audio que no escucho, asi que las que suenan van arriba,
    # tanto en "Todos" como dentro de cada estilo.
    pistas.sort(key=lambda p: (0 if p["demo"] else 1, orden[p["estilo"]],
                               alfabetico(p["titulo"]), alfabetico(p["autor"])))

    os.makedirs(os.path.dirname(os.path.abspath(args.salida)), exist_ok=True)
    with open(args.salida, "w", encoding="utf-8", newline="\n") as f:
        print(CABECERA.format(origen=os.path.basename(args.archivo), total=len(pistas)), file=f)
        for i, p in enumerate(pistas):
            coma = "," if i < len(pistas) - 1 else ""
            ident = "%04d" % p["nro"]
            # demo: 1 avisa que existe assets/audio/previas/<id>.mp3, para que
            # la web dibuje el boton de escuchar solo donde hay algo que sonar.
            # pag es el archivo de la pagina propia de la pista: lo escribe el
            # script para que el titulo de cada fila pueda linkear ahi sin que
            # el JavaScript tenga que adivinar como se arma el nombre.
            demo = ",  demo: 1" if p["demo"] else ""
            print('  {{ id: {0}, titulo: {1}, autor: {2}, estilo: {3}, tono: {4}, pag: {5}{6} }}{7}'.format(
                json.dumps(ident),
                json.dumps(p["titulo"], ensure_ascii=False),
                json.dumps(p["autor"], ensure_ascii=False),
                json.dumps(p["estilo"], ensure_ascii=False),
                json.dumps(p["tono"], ensure_ascii=False),
                json.dumps(p["pag"], ensure_ascii=False),
                demo,
                coma), file=f)
        print(PIE, file=f, end="")

    seccion("TONALIDADES QUE NO ENTENDI", informe["tono"])

    con_tono = sum(1 for p in pistas if p["tono"])
    con_demo = sum(1 for p in pistas
                   if os.path.exists(os.path.join(PREVIAS, "%04d.mp3" % p["nro"])))
    print("\nTONALIDAD: %d de %d pistas la tienen (%.0f%%), en %d tonalidades distintas"
          % (con_tono, len(pistas), 100.0 * con_tono / len(pistas),
             len(set(p["tono"] for p in pistas if p["tono"]))))
    print("MUESTRAS DE 30 s: %d de %d pistas tienen una (%.0f%%)"
          % (con_demo, len(pistas), 100.0 * con_demo / len(pistas)))

    print("\nPOR ESTILO")
    cuenta = collections.Counter(p["estilo"] for p in pistas)
    for e in ESTILOS:
        print("   %-22s %4d" % (e, cuenta.get(e, 0)))
    if args.sin_paginas:
        print("\n(--sin-paginas: no toque la carpeta pista/ ni el sitemap)")
    else:
        urls = escribir_paginas(pistas, args.version)
        escribir_sitemap(urls)
        print("\nPAGINAS: una por pista en %s/  (%d archivos) + sitemap.xml"
              % (CARPETA_PAGINAS, len(urls)))

    print("\nListo: %d pistas publicadas en %s" % (len(pistas), args.salida))
    return 0


if __name__ == "__main__":
    sys.exit(main())
