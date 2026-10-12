/* ============================================================================
   IDEARUM — app.js
   Nav, revelados, corredor de portadas, reproductores de audio y links de
   WhatsApp.
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
  // Que hay en cada archivo hoy. Es solo una ayuda para saber cual pisar:
  // acordate de corregir esta lista cuando cambies alguna.
  //   01 Mercedes Sosa          02 Thriller             03 Los Palmeras
  //   04 Horacio Guarany        05 Luis Miguel          06 Alejandro Fernandez
  //   07 Elvis                  08 Carlos Gardel        09 Dynamo
  //   10 Sinatra                11 Vicente Fernandez    12 Sandro
  //   13 Los del Fuego
  //
  // Version de las portadas. Si pisas una portada con otra imagen (mismo
  // nombre de archivo), CAMBIA ESTE NUMERO: si no, el navegador de cada
  // visitante sigue mostrando la vieja, que guarda hasta 30 dias en cache.
  var V_PORTADAS = "20260914-2";

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

  // Los trece estilos (los doce del negocio + "Otros") viven en DOS lugares y
  // tienen que decir lo mismo: las pildoras de catalogo.html y la tabla de
  // equivalencias de tools/csv_a_js.py. Antes habia una tercera copia aca,
  // que no leia nadie: se borro para no tener que mantenerla sincronizada.

  // Filas de la vista previa del catalogo en la home. Son ocho y no seis a
  // proposito: la grilla es de dos columnas, asi que quedan seis legibles
  // (tres por lado) y la ultima fila se pierde bajo el difuminado, que es lo
  // que da a entender que la lista sigue.
  var PREVIA = 8;

  // --------------------------------------------------------------------------
  // PRECIO EN PESOS
  //
  // A quien entra desde Argentina se le muestra, debajo del precio en dolares,
  // cuanto le sale en pesos. Al resto del mundo no se le muestra nada: el
  // precio de verdad, el que manda, siempre es el que esta en dolares.
  //
  // ⚠️ ESTE ES EL NUMERO QUE HAY QUE ACTUALIZAR: cuantos pesos vale un dolar.
  // Es lo unico que hay que tocar cuando se mueve el dolar.
  //
  // Mientras valga 0, NO se muestra ningun precio en pesos. Esta asi a
  // proposito: es preferible no mostrarlo a mostrar un numero viejo: si pasan
  // meses sin actualizarlo, conviene volver a ponerlo en 0.
  //
  // Ultima actualizacion: 8 de octubre de 2026.
  var DOLAR = 1470;

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

  /* ---------- Medicion ----------------------------------------------------
     La medicion de Vercel cuenta visitas por pagina, y eso ya dice que fichas
     de pista mira la gente. Lo que no cuenta es lo que pasa DENTRO del
     catalogo, que es donde se escucha casi todo: ahi las 327 pistas viven en
     una sola pagina.

     Estos tres eventos tapan ese agujero y contestan la pregunta que importa:
     que grabar despues.

       escucha   le dieron play a una muestra
       consulta  tocaron Consultar o Pedir esta pista
       pago      tocaron un boton de pagar

     No se manda nada de la persona: solo que pista era. Si el plan de Vercel
     no incluye eventos propios, la llamada no hace nada y la web sigue igual.
     ------------------------------------------------------------------------ */

  function medir(nombre, datos) {
    try {
      // La cola oficial de Vercel: si el script todavia no cargo, el evento
      // espera ahi en vez de perderse.
      window.va = window.va || function () {
        (window.vaq = window.vaq || []).push(arguments);
      };
      window.va("event", { name: nombre, data: datos || {} });
    } catch (e) {
      /* medir nunca puede romper la pagina */
    }
  }

  // Los titulos largos se recortan: el evento viaja en la URL.
  function corto(texto) {
    texto = String(texto || "").replace(/\s+/g, " ").trim();
    return texto.length > 60 ? texto.slice(0, 60) : texto;
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
    // La tonalidad va en el mensaje a proposito: es el primer dato que se
    // termina preguntando por WhatsApp, y asi ya viene contestado.
    var entre = p.estilo + (p.tono ? ", " + p.tono : "");
    return "Hola Idearum, quiero esta pista: " + p.titulo +
           (p.autor ? " — " + p.autor : "") +
           " (" + entre + ") [ID: " + p.id + "]";
  }

  // Una fila del catalogo. Vive aca y no en catalogo.js porque la usan las
  // dos paginas: el catalogo completo y la vista previa de la home.
  // Los iconos de play y pausa, que comparten el reproductor grande y las filas.
  var ICONOS =
    '<svg class="icono-play" viewBox="0 0 12 14" aria-hidden="true"><path d="M0 0l12 7-12 7z"/></svg>' +
    '<svg class="icono-pausa" viewBox="0 0 12 14" aria-hidden="true"><path d="M0 0h4v14H0zM8 0h4v14H8z"/></svg>';

  // Una fila del catalogo. Vive aca y no en catalogo.js porque la usan las
  // dos paginas: el catalogo completo y la vista previa de la home.
  //
  // El boton de escuchar aparece solo en las pistas que tienen muestra
  // (demo: 1 en data/pistas.js). Las que no la tienen dejan el lugar vacio,
  // para que todos los titulos arranquen a la misma altura.
  function filaHTML(p) {
    var titulo = escapar(p.titulo);
    var autor = escapar(p.autor || "");
    var estilo = escapar(p.estilo);
    var href = escapar(wa(mensajePista(p)));
    var meta = (autor ? autor + " &middot; " + estilo : estilo) +
               (p.tono ? ' &middot; <span class="fila__tono">' + escapar(p.tono) + "</span>" : "");
    var play = p.demo
      ? '<button class="fila__play" type="button" data-demo="' + escapar(p.id) +
          '" aria-label="Escuchar un fragmento de ' + titulo + '">' + ICONOS + "</button>"
      : '<span class="fila__hueco" aria-hidden="true"></span>';
    // El titulo linkea a la pagina propia de la pista, que es la que tiene la
    // ficha completa y la que encuentra Google. El nombre del archivo lo
    // escribe tools/csv_a_js.py en el campo pag: asi el JavaScript no tiene
    // que adivinar como se arma y nunca queda un link roto.
    var nombre = p.pag
      ? '<a href="/pista/' + escapar(p.pag) + '">' + titulo + "</a>"
      : titulo;
    return '<div class="fila">' +
             play +
             '<div class="fila__txt">' +
               '<h3 class="fila__titulo">' + nombre + "</h3>" +
               '<p class="fila__meta meta">' + meta + "</p>" +
             "</div>" +
             '<a class="btn btn--primario btn--compacto" href="' + href +
               '" target="_blank" rel="noopener" aria-label="Consultar por ' + titulo +
               ' por WhatsApp">Consultar</a>' +
             '<span class="fila__progreso" aria-hidden="true"></span>' +
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

  // Un solo oyente para todos los links de WhatsApp de la pagina: los de las
  // filas, el de la ficha y los del menu y el pie. Lo que interesa es de que
  // pista salio la consulta.
  function initMedirConsultas() {
    document.addEventListener("click", function (e) {
      var a = e.target.closest ? e.target.closest('a[href*="wa.me/"]') : null;
      if (!a) return;
      var fila = a.closest(".fila");
      var ficha = document.querySelector(".pista-titulo");
      var de = fila
        ? (fila.querySelector(".fila__titulo") || {}).textContent
        : (ficha ? ficha.textContent : "");
      medir("consulta", { pista: corto(de) || "general" });
    });
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

  // Celular: la camara "mas cerca". Con la geometria de escritorio, en una
  // pantalla angosta los rieles se abren tan rapido que las tapas salen de
  // cuadro siendo chicas. Aca nacen mas grandes, los rieles se abren mas
  // despacio (fan mas bajo, railExit mas cerrado) y las portadas cruzan la
  // pantalla grandes antes de salir.
  var VIA_MOVIL = {};
  for (var k in VIA) { if (VIA.hasOwnProperty(k)) VIA_MOVIL[k] = VIA[k]; }
  VIA_MOVIL.birthHeight = 11;
  VIA_MOVIL.exitHeight = 80;
  VIA_MOVIL.railBirth = -7;
  VIA_MOVIL.railExit = 36;
  VIA_MOVIL.fan = 2.0;

  var TARJETAS = 13;    // tarjetas por riel a la vez (una por portada)
  // Celular: menos tarjetas por riel para que queden separadas y cada tapa se
  // vea entera (con 13 se superponian tanto que no se distinguia ninguna).
  // Los dos rieles muestran portadas distintas, asi igual aparecen las 13.
  var TARJETAS_MOVIL = 7;
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

    var movil = caja.clientWidth < 700;
    var via = movil ? VIA_MOVIL : VIA;
    var n = movil ? TARJETAS_MOVIL : TARJETAS;
    var hoja = document.createElement("style");
    hoja.textContent = keyframes(1, "corr-der", via) + keyframes(-1, "corr-izq", via);
    document.head.appendChild(hoja);

    var frag = document.createDocumentFragment();
    var rieles = ["corr-der", "corr-izq"];

    for (var r = 0; r < rieles.length; r++) {
      for (var i = 0; i < n; i++) {
        var card = document.createElement("div");
        card.className = "corredor__card";
        card.style.left = "50%";
        card.style.top = EJE + "%";
        card.style.width = via.cardWidth + "cqw";
        card.style.height = via.cardHeight + "cqw";
        card.style.marginLeft = (-via.cardWidth / 2) + "cqw";
        card.style.marginTop = (-via.cardHeight / 2) + "cqw";
        card.style.borderRadius = via.cardRadius + "cqw";
        card.style.animation = rieles[r] + " " + VELOCIDAD + "s linear infinite";
        // El retardo negativo suelta cada tarjeta a mitad de vuelo, asi el
        // corredor ya esta lleno en el primer cuadro.
        card.style.animationDelay = (-(i * VELOCIDAD) / n) + "s";

        var img = document.createElement("img");
        // Escritorio: los dos rieles en espejo. Celular: pares a la derecha,
        // impares a la izquierda, para que entren las 13 con 7 por lado.
        var cual = movil ? (i * 2 + r) % PORTADAS.length : i % PORTADAS.length;
        img.src = PORTADAS[cual] + "?v=" + V_PORTADAS;
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
     en un reproductor propio. Si el archivo no estuviera, la ficha queda
     apagada y dice "Disponible pronto" en lugar de romperse.
     Suena uno por vez: al arrancar uno se pausan los demas.

     Los seis MP3 pesan juntos casi 3 MB. El reproductor se dibuja de entrada,
     pero el audio NO se toca hasta que la seccion se acerca a la pantalla
     (o hasta que alguien aprieta play): quien entra a la home y no baja hasta
     ahi no se baja un solo byte de musica.

     Hay dos formas del mismo reproductor:
       - la completa (home): boton, nombre, reloj y barra para adelantar;
       - la corta, <div class="repro repro--mini" data-detalle="Karaoke">
         (catalogo): una pastilla que se aprieta entera y muestra el avance
         como un relleno de fondo. No tiene reloj, asi que no baja nada hasta
         que alguien aprieta play.
     ------------------------------------------------------------------------ */

  var SONANDO = null;

  function reloj(seg) {
    if (!isFinite(seg) || seg < 0) seg = 0;
    var m = Math.floor(seg / 60);
    var s = Math.floor(seg % 60);
    return m + ":" + (s < 10 ? "0" : "") + s;
  }

  // Devuelve la funcion que baja el audio, o null si no hay nada que bajar.
  function armarRepro(caja) {
    if (caja.children.length > 0) return null;   // montaje idempotente

    var src = caja.getAttribute("data-audio") || "";
    var nombre = caja.getAttribute("data-nombre") || "Pista";
    var detalle = caja.getAttribute("data-detalle") || "";
    var etiqueta = detalle ? nombre + ", " + detalle : nombre;   // para lectores de pantalla
    var iconos =
      '<svg class="icono-play" viewBox="0 0 12 14" aria-hidden="true"><path d="M0 0l12 7-12 7z"/></svg>' +
      '<svg class="icono-pausa" viewBox="0 0 12 14" aria-hidden="true"><path d="M0 0h4v14H0zM8 0h4v14H8z"/></svg>';

    if (caja.classList.contains("repro--mini")) {
      caja.innerHTML =
        '<button class="repro__pastilla" type="button" aria-label="Reproducir ' + escapar(etiqueta) + '">' +
          '<span class="repro__llena"></span>' +
          '<span class="repro__btn" aria-hidden="true">' + iconos + "</span>" +
          '<span class="repro__nombre">' + escapar(nombre) + "</span>" +
          (detalle ? '<span class="repro__detalle">' + escapar(detalle) + "</span>" : "") +
        "</button>";
    } else {
      caja.innerHTML =
        '<button class="repro__btn" type="button" aria-label="Reproducir ' + escapar(etiqueta) + '">' +
          iconos +
        "</button>" +
        '<div class="repro__cuerpo">' +
          '<div class="repro__fila">' +
            '<span class="repro__nombre">' + escapar(nombre) + "</span>" +
            '<span class="repro__t">--:--</span>' +
          "</div>" +
          '<div class="repro__barra"><span class="repro__llena"></span></div>' +
        "</div>";
    }

    var btn = caja.querySelector("button");
    var t = caja.querySelector(".repro__t");          // la corta no tiene reloj
    var barra = caja.querySelector(".repro__barra");  // ni barra para adelantar
    var llena = caja.querySelector(".repro__llena");

    function tiempo(texto) {
      if (t) t.textContent = texto;
    }

    function apagar(motivo) {
      caja.classList.add("repro--vacio");
      btn.disabled = true;
      if (t) t.textContent = motivo; else btn.title = motivo;
    }

    if (!src) { apagar("Disponible pronto"); return null; }

    var audio = null;

    // Se llama una sola vez: la primera que haga falta.
    function cargar() {
      if (audio) return audio;

      audio = new Audio();
      audio.preload = "metadata";

      // Si el MP3 faltara, el reproductor queda apagado.
      audio.addEventListener("error", function () { apagar("Disponible pronto"); });

      audio.addEventListener("loadedmetadata", function () {
        tiempo(reloj(audio.duration));
      });

      audio.addEventListener("timeupdate", function () {
        if (!audio.duration) return;
        llena.style.width = (audio.currentTime / audio.duration * 100) + "%";
        tiempo(reloj(audio.duration - audio.currentTime));
      });

      audio.addEventListener("ended", function () {
        caja.classList.remove("is-sonando");
        llena.style.width = "0";
        tiempo(reloj(audio.duration));
        if (SONANDO === audio) SONANDO = null;
      });

      audio.addEventListener("pause", function () {
        caja.classList.remove("is-sonando");
        btn.setAttribute("aria-label", "Reproducir " + etiqueta);
      });

      audio.src = src;
      return audio;
    }

    btn.addEventListener("click", function () {
      var a = cargar();
      if (a.paused) {
        if (SONANDO && SONANDO !== a) SONANDO.pause();
        soltarFila();
        SONANDO = a;
        a.play().then(null, function () { apagar("Disponible pronto"); });
        caja.classList.add("is-sonando");
        btn.setAttribute("aria-label", "Pausar " + etiqueta);

        // Solo las muestras del catalogo. Los reproductores de "antes y
        // despues" de la portada usan otros audios y no son una pista a la
        // venta: mezclarlos ensuciaria el ranking de lo mas escuchado.
        var m = /\/previas\/(\d+)\.mp3/.exec(src || "");
        if (m) medir("escucha", { pista: corto(etiqueta), id: m[1] });
      } else {
        a.pause();
      }
    });

    if (barra) {
      barra.addEventListener("click", function (e) {
        if (!audio || !audio.duration) return;
        var r = barra.getBoundingClientRect();
        audio.currentTime = Math.min(1, Math.max(0, (e.clientX - r.left) / r.width)) * audio.duration;
      });
    }

    return cargar;
  }

  function initRepros() {
    var cajas = document.querySelectorAll(".repro");
    if (!cajas.length) return;

    var pendientes = [];
    for (var i = 0; i < cajas.length; i++) {
      var cargar = armarRepro(cajas[i]);
      // La corta no muestra la duracion: no hay por que bajar nada antes del play.
      if (cargar && !cajas[i].classList.contains("repro--mini")) pendientes.push(cargar);
    }
    if (!pendientes.length) return;

    function bajarTodos() {
      for (var j = 0; j < pendientes.length; j++) pendientes[j]();
      pendientes = [];
    }

    // Sin IntersectionObserver no hay forma de saber cuando se acerca: se
    // bajan las duraciones de entrada, como antes.
    var sec = document.getElementById("ejemplos");
    if (!sec || !("IntersectionObserver" in window)) { bajarTodos(); return; }

    var obs = new IntersectionObserver(function (entradas) {
      if (!entradas[0].isIntersecting) return;
      obs.disconnect();
      bajarTodos();
    }, { rootMargin: "400px 0px" });

    obs.observe(sec);
  }

  /* ---------- Escuchar una pista del catalogo ------------------------------
     Cada fila con muestra tiene un boton de play. Suena un solo audio en toda
     la web: el mismo SONANDO que usan los reproductores de antes y despues.

     Hay UN solo elemento de audio para las 335 filas, al que se le cambia la
     fuente: 335 reproductores servirian para lo mismo y gastarian memoria de
     mas. El click se escucha en la lista entera y no fila por fila, asi
     agregar filas al dibujar mas paginas no cuesta nada.

     Los ultimos segundos bajan de volumen solos, para que la muestra no corte
     de golpe. (En iPhone el volumen no se puede tocar por software: ahi corta
     seco, que es como estaba antes.)
     ------------------------------------------------------------------------ */

  var DESVANECER = 1.4;        // segundos de bajada al final
  var audioFila = null;        // el unico <audio> de las filas
  var filaSonando = null;      // la fila que esta sonando

  function soltarFila() {
    if (!filaSonando) return;
    filaSonando.classList.remove("is-sonando");
    var barra = filaSonando.querySelector(".fila__progreso");
    if (barra) barra.style.width = "0";
    filaSonando = null;
  }

  function initFilas() {
    var listas = document.querySelectorAll(".lista");
    if (!listas.length) return;

    function crear() {
      if (audioFila) return audioFila;
      audioFila = new Audio();
      audioFila.preload = "none";

      audioFila.addEventListener("timeupdate", function () {
        if (!filaSonando || !audioFila.duration) return;
        var barra = filaSonando.querySelector(".fila__progreso");
        if (barra) {
          barra.style.width = (audioFila.currentTime / audioFila.duration * 100) + "%";
        }
        var falta = audioFila.duration - audioFila.currentTime;
        if (falta < DESVANECER) {
          try { audioFila.volume = Math.max(0, falta / DESVANECER); } catch (e) {}
        }
      });
      audioFila.addEventListener("ended", soltarFila);
      audioFila.addEventListener("pause", soltarFila);
      audioFila.addEventListener("error", function () {
        if (filaSonando) filaSonando.classList.add("fila--sin-audio");
        soltarFila();
      });
      return audioFila;
    }

    function alHacerClick(e) {
      var btn = e.target.closest ? e.target.closest(".fila__play") : null;
      if (!btn) return;
      var fila = btn.closest(".fila");
      var id = btn.getAttribute("data-demo");
      var a = crear();

      if (filaSonando === fila && !a.paused) {   // ya sonaba: se pausa
        a.pause();
        return;
      }
      if (SONANDO && !SONANDO.paused) SONANDO.pause();
      soltarFila();

      // Ruta absoluta: las filas tambien aparecen en las paginas de pista/,
      // y desde ahi una ruta relativa buscaria pista/assets/...
      var fuente = "/assets/audio/previas/" + id + ".mp3";
      if (a.src.indexOf(fuente) === -1) a.src = fuente;
      try { a.volume = 1; } catch (e2) {}
      a.currentTime = 0;
      SONANDO = a;
      filaSonando = fila;
      fila.classList.add("is-sonando");

      var tit = fila.querySelector(".fila__titulo");
      medir("escucha", { pista: corto(tit ? tit.textContent : ""), id: id });
      a.play().then(null, function () {
        fila.classList.add("fila--sin-audio");
        soltarFila();
      });
    }

    for (var i = 0; i < listas.length; i++) {
      listas[i].addEventListener("click", alHacerClick);
    }
  }

  /* ---------- Ahorro: congelar lo que no se ve -----------------------------
     El corredor de portadas y la luz que recorre el borde de "Tema propio"
     giran sin parar. Mientras su seccion esta fuera de pantalla no aportan
     nada y el navegador igual las sigue dibujando: la clase fuera-de-vista
     las pausa (el CSS hace el trabajo) y se sueltan al volver a asomar.
     ------------------------------------------------------------------------ */

  function initAhorro() {
    var cajas = document.querySelectorAll(".corredor, .precios");
    if (!cajas.length || !("IntersectionObserver" in window)) return;

    var obs = new IntersectionObserver(function (entradas) {
      for (var i = 0; i < entradas.length; i++) {
        entradas[i].target.classList.toggle("fuera-de-vista", !entradas[i].isIntersecting);
      }
    }, { rootMargin: "120px 0px" });

    for (var j = 0; j < cajas.length; j++) obs.observe(cajas[j]);
  }

  /* ---------- Precio en pesos ----------------------------------------------
     Cualquier <span data-usd="40"> se llena con el precio en pesos, redondeado
     al mil mas cercano para que no quede un numero raro, y solo si el que mira
     esta en Argentina. Se mira la zona horaria del equipo antes que el idioma:
     muchos telefonos argentinos estan en "es" o "es-419" a secas, pero la zona
     horaria casi siempre dice Argentina.
     ------------------------------------------------------------------------ */

  // Las zonas horarias argentinas tienen dos formas: la larga y moderna
  // (America/Argentina/Buenos_Aires) y la vieja, que sigue viva en un monton
  // de equipos (America/Buenos_Aires, America/Cordoba, America/Mendoza).
  // Hay que reconocer las dos: mirar solo si dice "Argentina" deja afuera a
  // media Argentina.
  var CIUDADES_AR = ["argentina", "buenos_aires", "cordoba", "mendoza",
                     "rosario", "catamarca", "jujuy", "salta", "tucuman",
                     "san_juan", "san_luis", "la_rioja", "rio_gallegos",
                     "ushuaia"];

  function esArgentina() {
    try {
      var zona = (Intl.DateTimeFormat().resolvedOptions().timeZone || "").toLowerCase();
      if (zona.indexOf("america/") === 0) {
        for (var i = 0; i < CIUDADES_AR.length; i++) {
          if (zona.indexOf(CIUDADES_AR[i]) !== -1) return true;
        }
      }
    } catch (e) {
      // Navegadores viejos sin Intl: se cae al idioma, abajo.
    }
    var idiomas = [].concat(navigator.language || [],
                            navigator.languages || []).join(" ").toLowerCase();
    return idiomas.indexOf("es-ar") !== -1;
  }

  function enPesos(usd) {
    var n = Math.round(usd * DOLAR / 1000) * 1000;
    return "$ " + String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  }

  function initPesos() {
    if (!DOLAR || !esArgentina()) return;
    var nodos = document.querySelectorAll("[data-usd]");
    for (var i = 0; i < nodos.length; i++) {
      var usd = parseFloat(nodos[i].getAttribute("data-usd"));
      if (!usd) continue;
      nodos[i].textContent = enPesos(usd) + " aprox.";
      nodos[i].hidden = false;
    }
  }

  /* ---------- Botones de pago ---------------------------------------------
     A quien entra desde Argentina se le ofrece Mercado Pago; al resto,
     PayPal. No se le muestran los dos a nadie: elegir entre medios de pago
     no ayuda a comprar, y un argentino pagando en dolares pierde plata.

     ⚠️ ACA VAN LOS LINKS DE COBRO. Mientras esten vacios no aparece ningun
     boton, igual que con DOLAR: es preferible que no este a que lleve a un
     link que no funciona.

     La llave es el precio en dolares, el mismo numero del data-usd del HTML.

     Mercado Pago: un link por monto, de Tu negocio -> Cobrar -> Link de pago.
     PayPal: si la cuenta tiene PayPal.Me alcanza con llenar PAYPAL_ME una
     sola vez y dejar los paypal vacios; el monto se agrega solo.

     Cover a pedido y Tema propio NO tienen boton a proposito: son trabajos a
     medida y primero hay que acordar el tema y la tonalidad.
     ------------------------------------------------------------------------ */

  var PAYPAL_ME = "idearum";   // -> https://paypal.me/idearum/40USD

  // Los logos de Mercado Pago y PayPal en monocromo: heredan el color del
  // boton, asi que salen blancos sobre el fondo oscuro. Son los dibujos
  // oficiales, tomados de Simple Icons 13.21.0 (simpleicons.org).
  //
  // Van en el boton porque ver un medio de pago conocido tranquiliza a quien
  // esta por mandar plata, que es el momento en que mas duda.
  var LOGOS = {
    mp: "M11.115 16.479a.93.927 0 0 1-.939-.886c-.002-.042-.006-.155-.103-.155-.04 0-.074.023-.113.059-.112.103-.254.206-.46.206a.816.814 0 0 1-.305-.066c-.535-.214-.542-.578-.521-.725.006-.038.007-.08-.02-.11l-.032-.03h-.034c-.027 0-.055.012-.093.039a.788.786 0 0 1-.454.16.7.699 0 0 1-.253-.05c-.708-.27-.65-.928-.617-1.126.005-.041-.005-.072-.03-.092l-.05-.04-.047.043a.728.726 0 0 1-.505.203.73.728 0 0 1-.732-.725c0-.4.328-.722.732-.722.364 0 .675.27.721.63l.026.195.11-.165c.01-.018.307-.46.852-.46.102 0 .21.016.316.05.434.13.508.52.519.68.008.094.075.1.09.1.037 0 .064-.024.083-.045a.746.744 0 0 1 .54-.225c.128 0 .263.03.402.09.69.293.379 1.158.374 1.167-.058.144-.061.207-.005.244l.027.013h.02c.03 0 .07-.014.134-.035.093-.032.235-.08.367-.08a.944.942 0 0 1 .94.93.936.934 0 0 1-.94.928zm7.302-4.171c-1.138-.98-3.768-3.24-4.481-3.77-.406-.302-.685-.462-.928-.533a1.559 1.554 0 0 0-.456-.07c-.182 0-.376.032-.58.095-.46.145-.918.505-1.362.854l-.023.018c-.414.324-.84.66-1.164.73a1.986 1.98 0 0 1-.43.049c-.362 0-.687-.104-.81-.258-.02-.025-.007-.066.04-.125l.008-.008 1-1.067c.783-.774 1.525-1.506 3.23-1.545h.085c1.062 0 2.12.469 2.24.524a7.03 7.03 0 0 0 3.056.724c1.076 0 2.188-.263 3.354-.795a9.135 9.11 0 0 0-.405-.317c-1.025.44-2.003.66-2.946.66-.962 0-1.925-.229-2.858-.68-.05-.022-1.22-.567-2.44-.57-.032 0-.065 0-.096.002-1.434.033-2.24.536-2.782.976-.528.013-.982.138-1.388.25-.361.1-.673.186-.979.185-.125 0-.35-.01-.37-.012-.35-.01-2.115-.437-3.518-.962-.143.1-.28.203-.415.31 1.466.593 3.25 1.053 3.812 1.089.157.01.323.027.491.027.372 0 .744-.103 1.104-.203.213-.059.446-.123.692-.17l-.196.194-1.017 1.087c-.08.08-.254.294-.14.557a.705.703 0 0 0 .268.292c.243.162.677.27 1.08.271.152 0 .297-.015.43-.044.427-.095.874-.448 1.349-.82.377-.296.913-.672 1.323-.782a1.494 1.49 0 0 1 .37-.05.611.61 0 0 1 .095.005c.27.034.533.125 1.003.472.835.62 4.531 3.815 4.566 3.846.002.002.238.203.22.537-.007.186-.11.352-.294.466a.902.9 0 0 1-.484.15.804.802 0 0 1-.428-.124c-.014-.01-1.28-1.157-1.746-1.543-.074-.06-.146-.115-.22-.115a.122.122 0 0 0-.096.045c-.073.09.01.212.105.294l1.48 1.47c.002 0 .184.17.204.395.012.244-.106.447-.35.606a.957.955 0 0 1-.526.171.766.764 0 0 1-.42-.127l-.214-.206a21.035 20.978 0 0 0-1.08-1.009c-.072-.058-.148-.112-.221-.112a.127.127 0 0 0-.094.038c-.033.037-.056.103.028.212a.698.696 0 0 0 .075.083l1.078 1.198c.01.01.222.26.024.511l-.038.048a1.18 1.178 0 0 1-.1.096c-.184.15-.43.164-.527.164a.8.798 0 0 1-.147-.012c-.106-.018-.178-.048-.212-.089l-.013-.013c-.06-.06-.602-.609-1.054-.98-.059-.05-.133-.11-.21-.11a.128.128 0 0 0-.096.042c-.09.096.044.24.1.293l.92 1.003a.204.204 0 0 1-.033.062c-.033.044-.144.155-.479.196a.91.907 0 0 1-.122.007c-.345 0-.712-.164-.902-.264a1.343 1.34 0 0 0 .13-.576 1.368 1.365 0 0 0-1.42-1.357c.024-.342-.025-.99-.697-1.274a1.455 1.452 0 0 0-.575-.125c-.146 0-.287.025-.42.075a1.153 1.15 0 0 0-.671-.564 1.52 1.515 0 0 0-.494-.085c-.28 0-.537.08-.767.242a1.168 1.165 0 0 0-.903-.43 1.173 1.17 0 0 0-.82.335c-.287-.217-1.425-.93-4.467-1.613a17.39 17.344 0 0 1-.692-.189 4.822 4.82 0 0 0-.077.494l.67.157c3.108.682 4.136 1.391 4.309 1.525a1.145 1.142 0 0 0-.09.442 1.16 1.158 0 0 0 1.378 1.132c.096.467.406.821.879 1.003a1.165 1.162 0 0 0 .415.08c.09 0 .179-.012.266-.034.086.22.282.493.722.668a1.233 1.23 0 0 0 .457.094c.122 0 .241-.022.355-.063a1.373 1.37 0 0 0 1.269.841c.37.002.726-.147.985-.41.221.121.688.341 1.163.341.06 0 .118-.002.175-.01.47-.059.689-.24.789-.382a.571.57 0 0 0 .048-.078c.11.032.234.058.373.058.255 0 .501-.086.75-.265.244-.174.418-.424.444-.637v-.01c.083.017.167.026.251.026.265 0 .527-.082.773-.242.48-.31.562-.715.554-.98a1.28 1.279 0 0 0 .978-.194 1.04 1.04 0 0 0 .502-.808 1.088 1.085 0 0 0-.16-.653c.804-.342 2.636-1.003 4.795-1.483a4.734 4.721 0 0 0-.067-.492 27.742 27.667 0 0 0-5.049 1.62zm5.123-.763c0 4.027-5.166 7.293-11.537 7.293-6.372 0-11.538-3.266-11.538-7.293 0-4.028 5.165-7.293 11.539-7.293 6.371 0 11.537 3.265 11.537 7.293zm.46.004c0-4.272-5.374-7.755-12-7.755S.002 7.277.002 11.55L0 12.004c0 4.533 4.695 8.203 11.999 8.203 7.347 0 12-3.67 12-8.204z",
    paypal: "M7.016 19.198h-4.2a.562.562 0 0 1-.555-.65L5.093.584A.692.692 0 0 1 5.776 0h7.222c3.417 0 5.904 2.488 5.846 5.5-.006.25-.027.5-.066.747A6.794 6.794 0 0 1 12.071 12H8.743a.69.69 0 0 0-.682.583l-.325 2.056-.013.083-.692 4.39-.015.087zM19.79 6.142c-.01.087-.01.175-.023.261a7.76 7.76 0 0 1-7.695 6.598H9.007l-.283 1.795-.013.083-.692 4.39-.134.843-.014.088H6.86l-.497 3.15a.562.562 0 0 0 .555.65h3.612c.34 0 .63-.249.683-.585l.952-6.031a.692.692 0 0 1 .683-.584h2.126a6.793 6.793 0 0 0 6.707-5.752c.306-1.95-.466-3.744-1.89-4.906z"
  };

  function logoPago(cual) {
    return '<svg class="pagar__logo" viewBox="0 0 24 24" aria-hidden="true" ' +
           'focusable="false"><path d="' + LOGOS[cual] + '"/></svg>';
  }

  var PAGOS = {
    40:  { mp: "https://mpago.la/2P9EHNy", paypal: "" },   // 1 Pista   $  59.000
    99:  { mp: "https://mpago.la/1kS3XxQ", paypal: "" },   // 3 Pistas  $ 146.000
    149: { mp: "https://mpago.la/293bd8b", paypal: "" },   // 5 Pistas  $ 219.000
    249: { mp: "https://mpago.la/2K35tpm", paypal: "" },   // 10 Pistas $ 366.000

    // Estos dos NO se muestran en la web a proposito: no hay ningun
    // data-pagar que los use. La pagina dice "desde US$ 150", porque un cover
    // o un tema propio se presupuestan, y primero hay que acordar la cancion
    // y la tonalidad. Quedan anotados aca para mandarlos por WhatsApp una vez
    // cerrado el trabajo.
    150: { mp: "https://mpago.la/1QTq7MG", paypal: "" },   // Cover a pedido $ 221.000
    200: { mp: "https://mpago.la/2AKaxpr", paypal: "" }    // Tema propio    $ 294.000
  };

  function linkPago(usd, cual) {
    if (cual === "paypal" && PAYPAL_ME) {
      return "https://paypal.me/" + encodeURIComponent(PAYPAL_ME) + "/" + usd + "USD";
    }
    var fila = PAGOS[usd];
    return (fila && fila[cual]) || "";
  }

  function initPagos() {
    var cajas = document.querySelectorAll("[data-pagar]");
    if (!cajas.length) return;
    var cual = esArgentina() ? "mp" : "paypal";
    var nombre = cual === "mp" ? "Mercado Pago" : "PayPal";
    var puestos = 0;

    for (var i = 0; i < cajas.length; i++) {
      var usd = parseInt(cajas[i].getAttribute("data-pagar"), 10);
      var href = linkPago(usd, cual);
      if (!href) continue;          // sin link configurado, no se muestra nada

      // El aviso de cobro dice cuanto y quien pago, pero no QUE pista: eso
      // solo lo sabe el que compro. Asi que apenas toca el boton de pagar le
      // aparece el segundo paso, con el mensaje de WhatsApp ya escrito. Sin
      // esto todo depende de que se acuerde de escribir, y no se acuerda.
      var aviso = cajas[i].getAttribute("data-pagado");
      cajas[i].insertAdjacentHTML(
        "afterbegin",
        '<a class="btn btn--primario btn--compacto pagar" href="' + escapar(href) +
          '" target="_blank" rel="noopener">' + logoPago(cual) +
          "<span>Pagar</span></a>" +
        (aviso
          ? '<a class="btn btn--secundario btn--compacto pagar pagar--aviso" href="' +
              escapar(wa(aviso)) + '" target="_blank" rel="noopener" hidden>' +
              "Ya pagué, avisar por WhatsApp</a>"
          : ""));

      if (aviso) {
        (function (caja) {
          var btn = caja.querySelector(".pagar");
          var paso2 = caja.querySelector(".pagar--aviso");
          btn.addEventListener("click", function () {
            paso2.hidden = false;
            caja.classList.add("pagar-caja--pagando");
            medir("pago", { monto: "US$ " + caja.getAttribute("data-pagar"),
                            medio: nombre });
          });
        })(cajas[i]);
      }

      cajas[i].hidden = false;
      puestos++;
    }

    // La aclaracion de "mandanos el comprobante" va una sola vez por pagina,
    // no repetida en cada tarjeta, y solo si quedo algun boton.
    if (puestos) {
      // El boton dice solo "Pagar" con el logo: el nombre del medio no entra
      // en una tarjeta de pack sin cortarse en tres lineas. Se nombra aca,
      // una vez y legible.
      var medios = document.querySelectorAll("[data-medio]");
      for (var j2 = 0; j2 < medios.length; j2++) medios[j2].textContent = nombre;
      var notas = document.querySelectorAll("[data-pagar-nota]");
      for (var k = 0; k < notas.length; k++) notas[k].hidden = false;
    }
  }

  /* ---------- Ano del footer ---------------------------------------------- */

  function initAnio() {
    var nodos = document.querySelectorAll("[data-anio]");
    for (var i = 0; i < nodos.length; i++) {
      nodos[i].textContent = String(new Date().getFullYear());
    }
  }

  /* ---------- API compartida con catalogo.js ------------------------------
     Solo estas cinco: son las que catalogo.js usa de verdad. Todo lo demas
     (wa, escapar, mensajePista) se queda adentro del archivo.
     El HTML tambien mira si existe window.IDEARUM para saber si el JS cargo.
     ------------------------------------------------------------------------ */

  window.IDEARUM = {
    slug: slug,
    normalizar: normalizar,
    pistas: pistas,
    filaHTML: filaHTML,
    safe: safe
  };

  /* ---------- Arranque ----------------------------------------------------- */

  function arrancar() {
    safe(initWsp, "initWsp");
    safe(initNav, "initNav");
    safe(initCorredor, "initCorredor");
    safe(initPrevia, "initPrevia");
    safe(initRepros, "initRepros");
    safe(initFilas, "initFilas");
    safe(initAhorro, "initAhorro");
    safe(initPesos, "initPesos");
    safe(initPagos, "initPagos");
    safe(initMedirConsultas, "initMedirConsultas");
    safe(initAnio, "initAnio");
    safe(initReveals, "initReveals");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", arrancar);
  } else {
    arrancar();
  }
})();
