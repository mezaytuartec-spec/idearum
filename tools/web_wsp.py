# -*- coding: utf-8 -*-
"""
Idearum — arma la SEGUNDA web: el catalogo sin precios.

    python tools/web_wsp.py

Es el mismo catalogo, identico en diseno, pero sin un solo precio y sin
ninguna salida hacia pistasparacantantes.com. Se manda por WhatsApp al
cliente, que escucha las muestras y consulta; el precio se le dice en la
conversacion y puede variar segun el caso.

Sale de catalogo-wsp/ y se publica en su propio dominio.

DE DONDE SALE
No se escribe a mano: se arma a partir de la web ya generada, sacandole las
partes con precio. Por eso hay un solo lugar donde tocar el catalogo, y las
dos webs no se pueden desincronizar. El orden es:

    python tools/csv_a_js.py Listado_2026_pistas.xlsx
    python tools/previas.py  "C:\\ruta\\a\\los\\demos"
    python tools/web_wsp.py

LAS MUESTRAS NO SE COPIAN
Los 141 MB de audio viven en un solo lugar y la web nueva los pide prestados
al .com, como un video de YouTube metido en otra pagina. El visitante no tiene
por donde ir al .com: no hay un solo link.

LA RED DE SEGURIDAD
Al final revisa archivo por archivo que no haya quedado NI UN precio ni NI UN
link al sitio original. Si aparece alguno, falla y no escribe nada. Asi, el
dia que alguien agregue un precio nuevo al catalogo, esto se rompe en vez de
filtrarlo.
"""
import io
import os
import re
import shutil
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO = os.path.join(RAIZ, "catalogo-wsp")
COM = "https://pistasparacantantes.com"

# Lo que no puede aparecer en las PAGINAS, que es lo que ve el visitante.
PROHIBIDO_HTML = [
    (r"US\$", "un precio en dolares"),
    (r"data-usd", "un precio en pesos"),
    (r"data-pagar", "un boton de pagar"),
    (r"pistasparacantantes\.com/(?!assets/audio/)", "un link al sitio original"),
    (r'href="/?index\.html', "un link a la portada original"),
    (r'href="/?como-funciona\.html', "un link a Como funciona"),
    (r'href="/?catalogo\.html', "un link al catalogo original"),
    (r"#a-medida", "un link a la seccion de precios"),
]

# Lo que no puede estar en NINGUN archivo, ni siquiera adentro del codigo.
# Aca no se persiguen las palabras sueltas —los comentarios del programa
# nombran a Mercado Pago y a PayPal y eso no le hace mal a nadie— sino los
# datos: un link de cobro de verdad, el valor del dolar, el usuario de PayPal.
PROHIBIDO_TODO = [
    (r"mpago\.la/\w", "un link de cobro de Mercado Pago"),
    (r"paypal\.me/\w", "un link de cobro de PayPal"),
    (r"DOLAR = [1-9]", "el valor del dolar"),
    (r'PAYPAL_ME = "\w', "el usuario de PayPal"),
]


def quitar(texto, desde, hasta, que):
    """Saca el bloque que va de 'desde' a 'hasta', los dos incluidos."""
    i = texto.find(desde)
    if i == -1:
        sys.exit("No encontre el principio de %s (%r).\n"
                 "La web original cambio: hay que actualizar tools/web_wsp.py"
                 % (que, desde[:60]))
    j = texto.find(hasta, i)
    if j == -1:
        sys.exit("No encontre el final de %s (%r)." % (que, hasta[:60]))
    return texto[:i] + texto[j + len(hasta):]


def cambiar(texto, viejo, nuevo, que, veces=1):
    n = texto.count(viejo)
    if n != veces:
        sys.exit("Esperaba %d vez/veces %s y encontre %d.\n   %r"
                 % (veces, que, n, viejo[:70]))
    return texto.replace(viejo, nuevo)


# --------------------------------------------------------------- cabecera

NOINDEX = (
    '<meta name="robots" content="noindex, nofollow">\n'
    "<!-- Esta web NO va a Google a proposito: es el mismo catalogo que el\n"
    "     sitio principal y, si los dos se indexaran, competirian entre si por\n"
    "     las mismas busquedas. Se manda por WhatsApp, no se busca. -->\n")


def cabecera(html, titulo, desc):
    """Titulo, descripcion y las etiquetas que apuntaban al sitio original."""
    html = re.sub(r"<title>[^<]*</title>", "<title>%s</title>" % titulo, html, count=1)
    html = re.sub(r'<meta name="description" content="[^"]*">',
                  '<meta name="description" content="%s">' % desc, html, count=1)
    # Canonical y vista previa al compartir: apuntaban al .com.
    html = re.sub(r'\s*<link rel="canonical"[^>]*>', "", html, count=1)
    html = re.sub(r'\s*<meta property="og:url"[^>]*>', "", html, count=1)
    html = re.sub(r'<meta property="og:title" content="[^"]*">',
                  '<meta property="og:title" content="%s">' % titulo, html, count=1)
    html = re.sub(r'<meta property="og:description" content="[^"]*">',
                  '<meta property="og:description" content="%s">' % desc, html, count=1)
    html = re.sub(r'<meta property="og:image" content="[^"]*">',
                  '<meta property="og:image" content="assets/img/og.jpg">', html, count=1)
    html = re.sub(r'<meta name="twitter:image" content="[^"]*">',
                  '<meta name="twitter:image" content="assets/img/og.jpg">', html, count=1)
    html = html.replace('<meta charset="utf-8">',
                        '<meta charset="utf-8">\n' + NOINDEX, 1)
    return html


# El logo deja de ser un link y el menu desaparece: no hay a donde ir.
NAV_NUEVA = '''<header class="nav">
  <div class="nav__in">
    <span class="nav__logo">
      <img src="assets/img/logo.png?v=20260914-1" alt="" width="20" height="20">
      <span>Idearum</span>
    </span>
  </div>
</header>
'''

COMENTARIO = '''<!-- ==========================================================================
     ESTA PAGINA NO SE EDITA A MANO.

     La arma tools/web_wsp.py a partir del catalogo del sitio principal,
     sacandole los precios y todo link que salga de aca. Si la tocas, el
     proximo que corra el script te pisa los cambios.

     Para cambiar algo, cambialo en catalogo.html del sitio principal y
     volve a correr:   python tools/web_wsp.py
     ========================================================================== -->
'''

PIE_NUEVO = '''<footer class="footer">
  <div class="wrap">
    <div class="footer__pie">
      <p class="footer__marca"><img src="assets/img/logo.png?v=20260914-1" alt="" width="16" height="16"><span>Copyright &copy; <span data-anio>2026</span> Idearum. Todos los derechos reservados.</span></p>
      <p>Consultas y pedidos por WhatsApp, todos los d&iacute;as.</p>
    </div>
  </div>
</footer>
'''


def sin_salidas(html, prof=0):
    """Saca la barra de arriba, el menu y el pie: ahi estaban todos los links
    al sitio original. Quedan el logo (sin link) y una linea de contacto."""
    nav = NAV_NUEVA
    pie = PIE_NUEVO
    if prof:                       # las fichas viven en pista/
        nav = nav.replace('src="assets/', 'src="../assets/')
        pie = pie.replace('src="assets/', 'src="../assets/')
    html = quitar(html, "<header class=\"nav\">", "</header>\n", "la barra de arriba")
    html = html.replace("<body>\n", "<body>\n\n" + nav, 1)
    i = html.find('<div class="menu" id="menu">')
    if i != -1:
        html = quitar(html, '<div class="menu" id="menu">', "</div>\n", "el menu")
    html = quitar(html, '<footer class="footer">', "</footer>\n", "el pie")
    html = html.replace("<script src=", pie + "\n<script src=", 1)
    return html


# ------------------------------------------------------------------ catalogo

def hacer_catalogo():
    html = io.open(os.path.join(RAIZ, "catalogo.html"), encoding="utf-8").read()

    html = cabecera(
        html,
        "Cat&aacute;logo de pistas &mdash; Idearum",
        "Cat\u00e1logo de pistas de Idearum para cantantes: balada, rock, tropical, "
        "cuarteto, folklore, mariachi y m\u00e1s. Escuch\u00e1 la muestra y consultanos "
        "por WhatsApp.")

    # El comentario que documenta la pagina original: habla de los precios y
    # de archivos que en esta web no existen.
    html = quitar(html, "<!-- ==========================================================================\n     ⚠️ QUÉ HAY QUE COMPLETAR",
                  "========================================================================== -->\n",
                  "el comentario de la pagina original")
    html = html.replace("<body>\n", "<body>\n\n" + COMENTARIO, 1)

    # Precio de la cabecera.
    html = quitar(html, '<p class="cat-precio">', "</p>\n", "el precio de la cabecera")
    # Precio del cartel de "no encontramos nada".
    html = quitar(html, '<p class="vacio__precio">', "</p>\n", "el precio del cartel vacio")
    # Los packs enteros.
    html = quitar(html, '<!-- \u26a0\ufe0f PRECIOS DEL CAT\u00c1LOGO', "</section>\n", "los packs")
    # La seccion negra de cover a pedido y tema propio.
    html = quitar(html, '<!-- ---------- A medida', "</section>\n\n</main>",
                  "la seccion a medida")
    html = html.replace("  </section>\n", "  </section>\n\n</main>\n", 1) \
        if "</main>" not in html else html

    html = sin_salidas(html)
    return html


# -------------------------------------------------------------------- fichas

def hacer_ficha(html, nombre):
    titulo = re.search(r"<title>([^<]*)</title>", html).group(1)
    desc = re.search(r'<meta name="description" content="([^"]*)">', html).group(1)
    desc = desc.replace("Escuch\u00e1 la muestra.", "Escuch\u00e1 la muestra y consultanos.")
    html = cabecera(html, titulo, desc)

    # La ficha para Google: no va, porque esta web no se indexa y adentro
    # lleva el precio.
    html = quitar(html, '<script type="application/ld+json">', "</script>\n",
                  "los datos estructurados")

    # Precio, boton de pagar y la linea de los packs. Queda el boton de pedir
    # por WhatsApp y la garantia de tonalidad, que no dicen ningun numero.
    html = quitar(html, '<p class="pista-precio">', "</p>\n", "el precio de la ficha")
    html = quitar(html, '<p class="pagar-caja"', "</p>\n", "el boton de pagar")
    html = quitar(html, '<p class="nota">Te la mandamos por WhatsApp', "</p>\n",
                  "la linea de los packs")
    html = html.replace(
        '<p class="nota pista-garantia">',
        '<p class="nota">Te la mandamos por WhatsApp en WAV y MP3 320&nbsp;kbps.</p>\n'
        '        <p class="nota pista-garantia">', 1)

    # El bloque de "otra tonalidad" nombra el precio del cover.
    html = quitar(html, '<div class="pista-otra">', "</div>\n", "el bloque de otra tonalidad")

    # En esta web el catalogo ES la portada: no hay catalogo.html. Lo tocan
    # las migas de pan de arriba y el "Ver todo el catalogo" del final.
    html = html.replace('href="/catalogo.html#', 'href="/#')
    html = html.replace('href="/catalogo.html"', 'href="/"')

    # El audio se pide prestado al sitio original.
    html = html.replace('data-audio="/assets/audio/previas/',
                        'data-audio="%s/assets/audio/previas/' % COM)

    html = sin_salidas(html, prof=1)
    return html


# ---------------------------------------------------------------------- js

def hacer_js():
    js = io.open(os.path.join(RAIZ, "js", "app.js"), encoding="utf-8").read()

    # Las muestras se piden al sitio original.
    js = cambiar(js, '"/assets/audio/previas/" + id + ".mp3"',
                 '"%s/assets/audio/previas/" + id + ".mp3"' % COM,
                 "la ruta de las muestras")

    # Nada de precios ni de cobros: aunque no haya donde mostrarlos, no tienen
    # por que viajar en el archivo.
    js = re.sub(r"var DOLAR = \d+;", "var DOLAR = 0;        // esta web no muestra precios", js, count=1)
    # Ojo con el comentario de al lado: tenia el link de cobro escrito.
    js = re.sub(r'var PAYPAL_ME = "[^"]*";.*', 'var PAYPAL_ME = "";   // esta web no cobra',
                js, count=1)
    js = re.sub(r"var PAGOS = \{.*?\n  \};",
                "var PAGOS = {};       // esta web no cobra: se consulta por WhatsApp",
                js, count=1, flags=re.S)
    return js


# ------------------------------------------------------------------- revision

def revisar():
    """Ningun precio y ninguna salida al sitio original. Si aparece algo, se
    cancela todo: es preferible no publicar a publicar un precio."""
    fallas = []
    for base, _, archivos in os.walk(DESTINO):
        for f in archivos:
            if not f.endswith((".html", ".js", ".css", ".txt", ".json")):
                continue
            ruta = os.path.join(base, f)
            texto = io.open(ruta, encoding="utf-8").read()
            reglas = list(PROHIBIDO_TODO)
            if f.endswith(".html"):
                reglas += PROHIBIDO_HTML
            for patron, que in reglas:
                for m in re.finditer(patron, texto, re.I):
                    linea = texto.count("\n", 0, m.start()) + 1
                    corto = texto[max(0, m.start() - 45):m.start() + 45].replace("\n", " ")
                    fallas.append("%s:%d  %s\n        ...%s..."
                                  % (os.path.relpath(ruta, RAIZ), linea, que, corto))
    return fallas


# ----------------------------------------------------------------------- main

def main():
    for falta in ("catalogo.html", "js/app.js", "data/pistas.js"):
        if not os.path.exists(os.path.join(RAIZ, falta)):
            sys.exit("Falta %s. Genera primero la web principal." % falta)

    if os.path.isdir(DESTINO):
        shutil.rmtree(DESTINO)     # se rehace entera: no quedan restos viejos
    os.makedirs(os.path.join(DESTINO, "pista"))

    # 1. el catalogo
    io.open(os.path.join(DESTINO, "index.html"), "w", encoding="utf-8",
            newline="\n").write(hacer_catalogo())

    # 2. las fichas
    origen = os.path.join(RAIZ, "pista")
    fichas = sorted(f for f in os.listdir(origen) if f.endswith(".html"))
    for f in fichas:
        html = io.open(os.path.join(origen, f), encoding="utf-8").read()
        io.open(os.path.join(DESTINO, "pista", f), "w", encoding="utf-8",
                newline="\n").write(hacer_ficha(html, f))

    # 3. lo que se copia tal cual
    os.makedirs(os.path.join(DESTINO, "js"))
    io.open(os.path.join(DESTINO, "js", "app.js"), "w", encoding="utf-8",
            newline="\n").write(hacer_js())
    shutil.copy2(os.path.join(RAIZ, "js", "catalogo.js"),
                 os.path.join(DESTINO, "js", "catalogo.js"))
    os.makedirs(os.path.join(DESTINO, "css"))
    shutil.copy2(os.path.join(RAIZ, "css", "styles.css"),
                 os.path.join(DESTINO, "css", "styles.css"))
    os.makedirs(os.path.join(DESTINO, "data"))
    shutil.copy2(os.path.join(RAIZ, "data", "pistas.js"),
                 os.path.join(DESTINO, "data", "pistas.js"))

    # Imagenes: todo menos el audio, que se pide prestado.
    shutil.copytree(os.path.join(RAIZ, "assets", "img"),
                    os.path.join(DESTINO, "assets", "img"))
    for f in ("favicon.ico",):
        shutil.copy2(os.path.join(RAIZ, f), os.path.join(DESTINO, f))

    # 4. que no la indexen
    io.open(os.path.join(DESTINO, "robots.txt"), "w", encoding="utf-8",
            newline="\n").write(
        "# Este catalogo se manda por WhatsApp, no se busca en Google.\n"
        "# Si se indexara, competiria con el sitio principal por las mismas\n"
        "# busquedas: es el mismo catalogo.\n"
        "User-agent: *\nDisallow: /\n")

    io.open(os.path.join(DESTINO, "vercel.json"), "w", encoding="utf-8",
            newline="\n").write(
        '{\n'
        '  "$schema": "https://openapi.vercel.sh/vercel.json",\n'
        '  "headers": [\n'
        '    {\n'
        '      "source": "/(.*)",\n'
        '      "headers": [\n'
        '        { "key": "X-Robots-Tag", "value": "noindex, nofollow" },\n'
        '        { "key": "X-Content-Type-Options", "value": "nosniff" },\n'
        '        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }\n'
        '      ]\n'
        '    },\n'
        '    {\n'
        '      "source": "/assets/img/(.*)",\n'
        '      "headers": [\n'
        '        { "key": "Cache-Control", "value": "public, max-age=2592000" }\n'
        '      ]\n'
        '    }\n'
        '  ]\n'
        '}\n')

    # 5. la revision, que es lo que hace confiable a todo lo de arriba
    fallas = revisar()
    print("=" * 70)
    print("  catalogo-wsp/  —  el catalogo sin precios")
    print("=" * 70)
    print("  fichas de pista ....... %d" % len(fichas))
    peso = sum(os.path.getsize(os.path.join(b, f))
               for b, _, fs in os.walk(DESTINO) for f in fs)
    print("  peso total ............ %.1f MB (el audio no se copia)" % (peso / 1048576.0))
    if fallas:
        print("\n  SE CANCELA: quedaron %d cosas que no pueden estar:" % len(fallas))
        for f in fallas[:20]:
            print("   " + f)
        shutil.rmtree(DESTINO)
        return 1
    print("  revision .............. sin precios y sin links al sitio original")
    print("\n  Listo. Se publica como un proyecto aparte de Vercel, con la")
    print("  carpeta catalogo-wsp como raiz.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
