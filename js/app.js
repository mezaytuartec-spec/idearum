/* ============================================================================
   IDEARUM — app.js
   Nav, revelados, contadores, corredor de portadas, reproductores de audio
   y links de WhatsApp.
   Patron IIFE clasico. Sin dependencias. Sin modulos.
   ============================================================================ */

(function () {
  "use strict";

  /* ==========================================================================
     CONFIGURACION — LO UNICO QUE TENES QUE EDITAR EN ESTE ARCHIVO
     ========================================================================== */

  // Numero de WhatsApp del negocio: +54 9 2656 44-2608.
  // Formato internacional y SIN signos:
  //   54   = Argentina
  //   9    = obligatorio para celulares argentinos
  //   2656 = codigo de area SIN el 0
  //   442608 = numero SIN el 15
  //
  // Al cambiarlo aca se actualizan TODOS los links de las dos paginas.
  // (Para que tambien funcionen sin JavaScript: hace Buscar y Reemplazar
  //  del numero viejo en index.html y catalogo.html.)
  var WSP = "5492656442608";

  // Portadas que viajan por el corredor 3D de la home.
  // Para cambiarlas: pisa el archivo en assets/img/portadas/ con el tuyo
  // (mismo nombre) o agrega/saca lineas de esta lista. Las tarjetas son
  // CUADRADAS: subi las portadas ya cuadradas, idealmente 640 x 640 px.
  //
  //   01 Abbey Road          02 Thriller            03 degradado
  //   04 Dark Side           05 Luis Miguel         06 Nevermind
  //   07 degradado           08 Carlos Gardel       09 Dynamo
  //   10 Sinatra             11 Vicente Fernandez   12 Atahualpa Yupanqui
  //   13 Los del Fuego
  // Version de las portadas. Si pisas una portada con otra imagen (mismo
  // nombre de archivo), CAMBIA ESTE NUMERO: si no, el navegador de cada
  // visitante sigue mostrando la vieja, que guarda hasta 30 dias en cache.
  var V_PORTADAS = "20260911-2";

  var PORTADAS = [
    "assets/img/portadas/portada-01.jpg",
    "assets/img/portadas/portada-02.jpg",
    "assets/img/portadas/portada-03.jpg",
    "assets/img/portadas/portada-04.jpg",
    "assets/img/portadas/portada-05.jpg",
    "assets/img/portadas/portada-06.jpg",
    "assets/img/portadas/portada-07.jpg",
    "assets/img/portadas/portada-08.jpg",
    "assets/img/portadas/portada-09.jpg",
    "assets/img/portadas/portada-10.jpg",
    "assets/img/portadas/portada-11.jpg",
    "assets/img/portadas/portada-12.jpg",
    "assets/img/portadas/portada-13.jpg"
  ];

  /* ========================================================================== */

  // Los estilos, en el orden en que se muestran en la web: primero los mas
  // pedidos, al final los mas de nicho y "Otros" para lo que no encaja.
  // Si tocas esta lista, tocala tambien en catalogo.html (pildoras) y en
  // tools/csv_a_js.py.
  var ESTILOS = ["Balada", "Rock / Pop", "Tropical", "Cuarteto", "Latino",
                 "Románticos", "Canción del recuerdo", "Música cristiana",
                 "Mariachi", "Folklore", "Bolero", "Tango", "Otros"];

  // Filas de la vista previa del catalogo en la home. Son ocho y no seis a
  // proposito: la grilla es de dos columnas, asi que quedan seis legibles
  // (tres por lado) y la ultima fila se pierde bajo el difuminado, que es lo
  // que da a entender que la lista sigue.
  var PREVIA = 8;

  /* ---------- Utilidades ------------------------------------------------- */

  function safe(fn, nombre) {
    try {
      fn();
    } catch (e) {
      if (window.console && console.warn) {
        console.warn("[Idearum] fallo " + nombre + ":", e);
      }
    }
  }

  function wa(mensaje) {
    return "https://wa.me/" + WSP + "?text=" + encodeURIComponent(mensaje || "");
  }

  // Rango Unicode de las marcas de acento (U+0300 a U+036F). Se construye con
  // fromCharCode para que el archivo no dependa de como se guarde la codificacion.
  var ACENTOS = new RegExp(
    "[" + String.fromCharCode(768) + "-" + String.fromCharCode(879) + "]", "g"
  );

  // "Folclore" -> "folclore" ; "Balada"  -> "balada". Sirve para el hash de la URL.
  function slug(s) {
    return String(s)
      .normalize("NFD")
      .replace(ACENTOS, "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
  }

  // "Corazon" encuentra "Corazón"; "beatles" encuentra "The Beatles".
  function normalizar(s) {
    return String(s)
      .normalize("NFD")
      .replace(ACENTOS, "")
      .toLowerCase();
  }

  function escapar(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function pistas() {
    return Array.isArray(window.PISTAS) ? window.PISTAS : [];
  }

  // Mensaje preescrito de una pista del catalogo.
  // El ID es lo que le permite al dueno saber exactamente cual le piden.
  // Algunas pistas no tienen autor cargado (en el Excel figura el genero en
  // su lugar): el mensaje y la fila se arman sin el guion colgando.
  function mensajePista(p) {
    return "Hola Idearum, quiero escuchar la pista: " + p.titulo +
           (p.autor ? " — " + p.autor : "") +
           " (" + p.estilo + ") [ID: " + p.id + "]";
  }

  // Una fila del catalogo. Vive aca y no en catalogo.js porque la usan las
  // dos paginas: el catalogo completo y la vista previa de la home.
  function filaHTML(p) {
    var titulo = escapar(p.titulo);
    var autor = escapar(p.autor || "");
    var estilo = escapar(p.estilo);
    var href = escapar(wa(mensajePista(p)));
    var meta = autor ? autor + " &middot; " + estilo : estilo;
    return '<div class="fila">' +
             '<div class="fila__txt">' +
               '<h3 class="fila__titulo">' + titulo + "</h3>" +
               '<p class="fila__meta meta">' + meta + "</p>" +
             "</div>" +
             '<a class="btn btn--primario btn--compacto" href="' + href +
               '" target="_blank" rel="noopener" aria-label="Consultar por ' + titulo +
               ' por WhatsApp">Consultar</a>' +
           "</div>";
  }

  /* ---------- Links de WhatsApp ------------------------------------------ */
  // Cualquier <a data-wsp="mensaje"> queda apuntando a wa.me con ese texto.

  function initWsp() {
    var links = document.querySelectorAll("a[data-wsp]");
    for (var i = 0; i < links.length; i++) {
      links[i].href = wa(links[i].getAttribute("data-wsp"));
      links[i].target = "_blank";
      links[i].rel = "noopener";
    }
  }

  /* ---------- Nav movil --------------------------------------------------- */

  function initNav() {
    var nav = document.querySelector(".nav");
    var burger = document.querySelector(".nav__burger");
    var menu = document.getElementById("menu");
    if (!nav || !burger || !menu) return;

    function cerrar() {
      nav.classList.remove("is-abierta");
      menu.classList.remove("is-abierto");
      burger.setAttribute("aria-expanded", "false");
      document.body.style.overflow = "";
    }

    burger.addEventListener("click", function () {
      var abierto = menu.classList.toggle("is-abierto");
      nav.classList.toggle("is-abierta", abierto);
      burger.setAttribute("aria-expanded", abierto ? "true" : "false");
      document.body.style.overflow = abierto ? "hidden" : "";
    });

    menu.addEventListener("click", function (e) {
      if (e.target.tagName === "A") cerrar();
    });

    window.addEventListener("keydown", function (e) {
      if (e.key === "Escape") cerrar();
    });

    window.addEventListener("resize", function () {
      if (window.innerWidth > 833) cerrar();
    });
  }

  /* ---------- Revelados ---------------------------------------------------
     Unica animacion de toda la web: opacidad + 20px de subida.
     No se apaga con prefers-reduced-motion a proposito (Windows lo trae
     activado por defecto en muchas maquinas y la web se veria muerta).
     ------------------------------------------------------------------------ */

  function initReveals() {
    var nodos = document.querySelectorAll(".reveal");
    if (!nodos.length) return;

    function mostrarTodo() {
      for (var i = 0; i < nodos.length; i++) nodos[i].classList.add("is-visible");
    }

    if (!("IntersectionObserver" in window)) {
      mostrarTodo();
      return;
    }

    var obs = new IntersectionObserver(function (entradas) {
      for (var i = 0; i < entradas.length; i++) {
        if (entradas[i].isIntersecting) {
          entradas[i].target.classList.add("is-visible");
          obs.unobserve(entradas[i].target);
        }
      }
    }, { threshold: 0.05, rootMargin: "0px 0px -5% 0px" });

    for (var i = 0; i < nodos.length; i++) obs.observe(nodos[i]);

    // Red de seguridad: a los 6 segundos, nada puede seguir invisible.
    window.setTimeout(mostrarTodo, 6000);
  }

  /* ---------- Contadores por estilo (home) -------------------------------- */

  function initContadores() {
    var lista = pistas();
    var total = lista.length;

    var conteo = {};
    for (var i = 0; i < lista.length; i++) {
      var k = slug(lista[i].estilo);
      conteo[k] = (conteo[k] || 0) + 1;
    }

    var nodos = document.querySelectorAll("[data-conteo]");
    for (var j = 0; j < nodos.length; j++) {
      var clave = nodos[j].getAttribute("data-conteo");
      var n = clave === "total" ? total : (conteo[clave] || 0);
      if (nodos[j].getAttribute("data-fmt") === "corto") {
        nodos[j].textContent = n === 1 ? "1 pista" : n + " pistas";
      } else {
        nodos[j].textContent = n === 1 ? "1 pista disponible" : n + " pistas disponibles";
      }
    }

    var totales = document.querySelectorAll("[data-total]");
    for (var t = 0; t < totales.length; t++) {
      totales[t].textContent = String(total);
    }
  }

  /* ---------- Corredor de portadas ----------------------------------------
     Geometria del recorrido. Todo en cqw (porcentaje del ancho del contenedor).
     Se puede tocar, pero interactua: la cinta se ve maciza mientras las
     tarjetas consecutivas se superponen. Subir exitHeight, bajar TARJETAS o
     achicar railExit abre huecos cerca del borde.
     ------------------------------------------------------------------------ */

  var VIA = {
    perspective: 30,    // fuerza de la proyeccion; mas bajo = mas dramatico
    cardWidth: 20,      // tarjetas cuadradas: son portadas de disco
    cardHeight: 20,
    cardRadius: 0.4,    // redondeo de esquina
    birthHeight: 2.4,   // alto en pantalla donde nace la tarjeta
    exitHeight: 40,     // alto en pantalla cuando sale del cuadro
    railBirth: -11,     // nace cruzada al otro lado del eje: tapa el centro
    railExit: 44,       // apertura final del riel
    fan: 3.3,           // que tan al principio se abren los rieles
    turnBirth: 6,       // giro en Y al nacer, en grados
    turnExit: 28,       // giro en Y al salir
    stops: 24           // muestras de la curva; subir solo si se ve facetado
  };

  // En pantallas angostas las medidas en cqw dejan las tapas diminutas: se
  // agrandan (alto al nacer y al salir) y se abren un poco mas los rieles.
  // La razon de tamano entre tarjetas vecinas queda igual, asi la cinta sigue
  // maciza.
  var VIA_MOVIL = {};
  for (var k in VIA) { if (VIA.hasOwnProperty(k)) VIA_MOVIL[k] = VIA[k]; }
  VIA_MOVIL.birthHeight = 4;
  VIA_MOVIL.exitHeight = 62;
  VIA_MOVIL.railExit = 50;

  var TARJETAS = 13;    // tarjetas por riel a la vez (una por portada)
  var VELOCIDAD = 18;   // segundos que tarda una tarjeta en cruzar el corredor
  var EJE = 55;         // altura del eje del corredor, en % del alto

  function keyframes(dir, nombre, p) {
    var pasos = [];
    for (var s = 0; s <= p.stops; s++) {
      var u = s / p.stops;
      // Geometrico en tamano aparente: la razon entre tarjetas vecinas es
      // constante, asi la cinta queda maciza en los dos extremos.
      var escala = (p.birthHeight / p.cardHeight) *
                   Math.pow(p.exitHeight / p.birthHeight, u);
      var z = p.perspective * (1 - 1 / escala);
      var riel = p.railExit - (p.railExit - p.railBirth) * Math.pow(1 - u, p.fan);
      var giro = p.turnBirth + (p.turnExit - p.turnBirth) * u;
      pasos.push((u * 100).toFixed(2) + "%{transform:translate3d(" +
                 (dir * riel).toFixed(2) + "cqw,0," + z.toFixed(2) + "cqw) rotateY(" +
                 (-dir * giro).toFixed(2) + "deg)}");
    }
    return "@keyframes " + nombre + "{" + pasos.join("") + "}";
  }

  function initCorredor() {
    var caja = document.querySelector(".corredor");
    if (!caja) return;

    var escena = caja.querySelector(".corredor__escena");
    if (!escena || escena.children.length > 0) return;  // montaje idempotente

    // Sin unidades de contenedor no hay corredor posible: queda la banda negra.
    if (!window.CSS || !CSS.supports || !CSS.supports("container-type", "inline-size")) return;
    if (!PORTADAS.length) return;

    var via = caja.clientWidth < 700 ? VIA_MOVIL : VIA;
    var hoja = document.createElement("style");
    hoja.textContent = keyframes(1, "corr-der", via) + keyframes(-1, "corr-izq", via);
    document.head.appendChild(hoja);

    var frag = document.createDocumentFragment();
    var rieles = ["corr-der", "corr-izq"];

    for (var r = 0; r < rieles.length; r++) {
      for (var i = 0; i < TARJETAS; i++) {
        var card = document.createElement("div");
        card.className = "corredor__card";
        card.style.left = "50%";
        card.style.top = EJE + "%";
        card.style.width = VIA.cardWidth + "cqw";
        card.style.height = VIA.cardHeight + "cqw";
        card.style.marginLeft = (-VIA.cardWidth / 2) + "cqw";
        card.style.marginTop = (-VIA.cardHeight / 2) + "cqw";
        card.style.borderRadius = VIA.cardRadius + "cqw";
        card.style.animation = rieles[r] + " " + VELOCIDAD + "s linear infinite";
        // El retardo negativo suelta cada tarjeta a mitad de vuelo, asi el
        // corredor ya esta lleno en el primer cuadro.
        card.style.animationDelay = (-(i * VELOCIDAD) / TARJETAS) + "s";

        var img = document.createElement("img");
        img.src = PORTADAS[i % PORTADAS.length] + "?v=" + V_PORTADAS;
        img.alt = "";
        // Sin lazy y con prioridad normal: el corredor ya asoma en la primera
        // pantalla del celular y las portadas pesan poco. Con prioridad baja
        // tardaban segundos en aparecer y la seccion se veia vacia.
        img.decoding = "async";
        img.draggable = false;
        card.appendChild(img);

        frag.appendChild(card);
      }
    }

    escena.appendChild(frag);
  }

  /* ---------- Vista previa del catalogo (home) ----------------------------
     Muestra unas pocas pistas con el mismo diseno y los mismos botones que el
     catalogo completo: es una muestra que funciona, no una maqueta.
     Se toman repartidas a lo largo del listado y no las primeras seis, para
     que se vean estilos distintos aunque el catalogo venga ordenado por
     genero. La seleccion es estable: no cambia entre recargas.
     ------------------------------------------------------------------------ */

  function initPrevia() {
    var caja = document.getElementById("previa-lista");
    if (!caja || caja.children.length > 0) return;

    var lista = pistas();
    if (!lista.length) return;

    var cuantas = Math.min(PREVIA, lista.length);
    var paso = lista.length / cuantas;
    var html = [];
    for (var i = 0; i < cuantas; i++) {
      html.push(filaHTML(lista[Math.floor(i * paso)]));
    }

    var buffer = document.createElement("div");
    buffer.innerHTML = html.join("");
    var frag = document.createDocumentFragment();
    while (buffer.firstChild) frag.appendChild(buffer.firstChild);
    caja.appendChild(frag);
  }

  /* ---------- Reproductores de antes y despues ----------------------------
     Cada <div class="repro" data-audio="..." data-nombre="..."> se convierte
     en un reproductor propio. Si el archivo todavia no existe, la ficha queda
     apagada y dice "Disponible pronto" en lugar de romperse.
     Suena uno por vez: al arrancar uno se pausan los demas.
     ------------------------------------------------------------------------ */

  var SONANDO = null;

  // La seccion "antes y despues" arranca oculta (atributo hidden en el HTML)
  // y aparece sola en cuanto carga al menos un audio: la web nunca muestra
  // fichas vacias ni textos de relleno.
  function mostrarSeccion(nodo) {
    var sec = nodo.closest ? nodo.closest("section") : null;
    if (sec && sec.hidden) sec.hidden = false;
  }

  function reloj(seg) {
    if (!isFinite(seg) || seg < 0) seg = 0;
    var m = Math.floor(seg / 60);
    var s = Math.floor(seg % 60);
    return m + ":" + (s < 10 ? "0" : "") + s;
  }

  function armarRepro(caja) {
    if (caja.children.length > 0) return;   // montaje idempotente

    var src = caja.getAttribute("data-audio") || "";
    var nombre = caja.getAttribute("data-nombre") || "Pista";

    caja.innerHTML =
      '<button class="repro__btn" type="button" aria-label="Reproducir ' + escapar(nombre) + '">' +
        '<svg class="icono-play" viewBox="0 0 12 14" aria-hidden="true"><path d="M0 0l12 7-12 7z"/></svg>' +
        '<svg class="icono-pausa" viewBox="0 0 12 14" aria-hidden="true"><path d="M0 0h4v14H0zM8 0h4v14H8z"/></svg>' +
      "</button>" +
      '<div class="repro__cuerpo">' +
        '<div class="repro__fila">' +
          '<span class="repro__nombre">' + escapar(nombre) + "</span>" +
          '<span class="repro__t">--:--</span>' +
        "</div>" +
        '<div class="repro__barra"><span class="repro__llena"></span></div>' +
      "</div>";

    var btn = caja.querySelector(".repro__btn");
    var t = caja.querySelector(".repro__t");
    var barra = caja.querySelector(".repro__barra");
    var llena = caja.querySelector(".repro__llena");

    function apagar(motivo) {
      caja.classList.add("repro--vacio");
      btn.disabled = true;
      t.textContent = motivo;
    }

    if (!src) { apagar("Disponible pronto"); return; }

    var audio = new Audio();
    audio.preload = "metadata";
    audio.src = src;

    // Si el MP3 no esta subido todavia, el reproductor queda apagado.
    audio.addEventListener("error", function () { apagar("Disponible pronto"); });

    audio.addEventListener("loadedmetadata", function () {
      t.textContent = reloj(audio.duration);
      mostrarSeccion(caja);
    });

    audio.addEventListener("timeupdate", function () {
      if (!audio.duration) return;
      llena.style.width = (audio.currentTime / audio.duration * 100) + "%";
      t.textContent = reloj(audio.duration - audio.currentTime);
    });

    audio.addEventListener("ended", function () {
      caja.classList.remove("is-sonando");
      llena.style.width = "0";
      t.textContent = reloj(audio.duration);
      if (SONANDO === audio) SONANDO = null;
    });

    btn.addEventListener("click", function () {
      if (audio.paused) {
        if (SONANDO && SONANDO !== audio) SONANDO.pause();
        SONANDO = audio;
        audio.play().then(null, function () { apagar("Disponible pronto"); });
        caja.classList.add("is-sonando");
        btn.setAttribute("aria-label", "Pausar " + nombre);
      } else {
        audio.pause();
      }
    });

    audio.addEventListener("pause", function () {
      caja.classList.remove("is-sonando");
      btn.setAttribute("aria-label", "Reproducir " + nombre);
    });

    barra.addEventListener("click", function (e) {
      if (!audio.duration) return;
      var r = barra.getBoundingClientRect();
      audio.currentTime = Math.min(1, Math.max(0, (e.clientX - r.left) / r.width)) * audio.duration;
    });
  }

  function initRepros() {
    var cajas = document.querySelectorAll(".repro");
    for (var i = 0; i < cajas.length; i++) armarRepro(cajas[i]);
  }

  /* ---------- Ano del footer ---------------------------------------------- */

  function initAnio() {
    var nodos = document.querySelectorAll("[data-anio]");
    for (var i = 0; i < nodos.length; i++) {
      nodos[i].textContent = String(new Date().getFullYear());
    }
  }

  /* ---------- API compartida con catalogo.js ------------------------------ */

  window.IDEARUM = {
    WSP: WSP,
    ESTILOS: ESTILOS,
    wa: wa,
    slug: slug,
    normalizar: normalizar,
    escapar: escapar,
    pistas: pistas,
    mensajePista: mensajePista,
    filaHTML: filaHTML,
    safe: safe
  };

  /* ---------- Arranque ----------------------------------------------------- */

  function arrancar() {
    safe(initWsp, "initWsp");
    safe(initNav, "initNav");
    safe(initContadores, "initContadores");
    safe(initCorredor, "initCorredor");
    safe(initPrevia, "initPrevia");
    safe(initRepros, "initRepros");
    safe(initAnio, "initAnio");
    safe(initReveals, "initReveals");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", arrancar);
  } else {
    arrancar();
  }
})();
