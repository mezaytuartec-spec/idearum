/* ============================================================================
   IDEARUM — catalogo.js
   Buscador, filtro por estilo, paginado y links de consulta por WhatsApp.
   Requiere data/pistas.js y js/app.js cargados antes que este archivo.
   ============================================================================ */

(function () {
  "use strict";

  var API = window.IDEARUM;
  if (!API) return; // app.js no cargo: la pagina igual muestra su estructura.

  var POR_PAGINA = 60;   // cuantas filas se dibujan de una vez
  var DEBOUNCE = 150;    // ms de espera antes de buscar

  var indice = [];       // catalogo precalculado, se arma una sola vez
  var filtradas = [];    // resultado actual
  var estado = { q: "", estilo: "todos", pagina: 1 };

  var $input, $buscador, $limpiar, $lista, $conteo, $mas, $vacio, $pills;
  var timer = null;

  /* ---------- Indice normalizado (una sola vez) --------------------------- */

  function construirIndice() {
    var lista = API.pistas();
    indice = new Array(lista.length);
    for (var i = 0; i < lista.length; i++) {
      var p = lista[i];
      indice[i] = {
        p: p,
        estilo: API.slug(p.estilo),
        busca: API.normalizar(p.titulo) + " " + API.normalizar(p.autor)
      };
    }
  }

  /* ---------- Filtrado ----------------------------------------------------- */

  function filtrar() {
    var q = API.normalizar(estado.q).trim();
    var e = estado.estilo;
    var out = [];
    for (var i = 0; i < indice.length; i++) {
      var it = indice[i];
      if (e !== "todos" && it.estilo !== e) continue;
      if (q && it.busca.indexOf(q) === -1) continue;
      out.push(it.p);
    }
    return out;
  }

  /* ---------- Dibujado ----------------------------------------------------- */

  function filaHTML(p) {
    var titulo = API.escapar(p.titulo);
    var autor = API.escapar(p.autor);
    var estilo = API.escapar(p.estilo);
    var href = API.escapar(API.wa(API.mensajePista(p)));
    return '<div class="fila">' +
             '<div class="fila__txt">' +
               '<h3 class="fila__titulo">' + titulo + "</h3>" +
               '<p class="fila__meta meta">' + autor + " &middot; " + estilo + "</p>" +
             "</div>" +
             '<a class="btn btn--primario btn--compacto" href="' + href +
               '" target="_blank" rel="noopener" aria-label="Consultar por ' + titulo +
               ' por WhatsApp">Consultar</a>' +
           "</div>";
  }

  // Un solo parseo y un solo appendChild por pagina. Nada de innerHTML += en bucle.
  function dibujarPagina(n) {
    var desde = (n - 1) * POR_PAGINA;
    var hasta = Math.min(desde + POR_PAGINA, filtradas.length);
    if (desde >= hasta) return;

    var html = [];
    for (var i = desde; i < hasta; i++) html.push(filaHTML(filtradas[i]));

    var buffer = document.createElement("div");
    buffer.innerHTML = html.join("");

    var frag = document.createDocumentFragment();
    while (buffer.firstChild) frag.appendChild(buffer.firstChild);
    $lista.appendChild(frag);
  }

  function actualizarConteo() {
    var n = filtradas.length;
    $conteo.textContent = n === 1 ? "1 pista" : n + " pistas";
  }

  function actualizarBotonMas() {
    var mostradas = Math.min(estado.pagina * POR_PAGINA, filtradas.length);
    var quedan = filtradas.length - mostradas;
    if (quedan > 0) {
      $mas.hidden = false;
      $mas.querySelector("[data-restantes]").textContent = String(quedan);
    } else {
      $mas.hidden = true;
    }
  }

  function render() {
    filtradas = filtrar();
    estado.pagina = 1;
    $lista.textContent = "";
    dibujarPagina(1);

    var sinResultados = filtradas.length === 0;
    $vacio.hidden = !sinResultados;
    $lista.hidden = sinResultados;

    actualizarConteo();
    actualizarBotonMas();
  }

  /* ---------- Filtro de estilo + hash de la URL ---------------------------- */

  function pintarPills() {
    var botones = $pills.querySelectorAll(".pill");
    for (var i = 0; i < botones.length; i++) {
      var activo = botones[i].getAttribute("data-estilo") === estado.estilo;
      botones[i].classList.toggle("is-activa", activo);
      botones[i].setAttribute("aria-pressed", activo ? "true" : "false");
    }
  }

  function leerHash() {
    var m = /(?:^|[#&])estilo=([a-z0-9-]+)/i.exec(window.location.hash || "");
    return m ? m[1].toLowerCase() : "todos";
  }

  function escribirHash() {
    var url = window.location.pathname + window.location.search +
              (estado.estilo === "todos" ? "" : "#estilo=" + estado.estilo);
    try {
      window.history.replaceState(null, "", url);
    } catch (e) {
      // Navegadores viejos o file:// — el filtro sigue funcionando igual.
    }
  }

  function aplicarEstilo(slugEstilo, tocarHash) {
    estado.estilo = slugEstilo || "todos";
    pintarPills();
    if (tocarHash) escribirHash();
    render();
  }

  /* ---------- Init ---------------------------------------------------------- */

  function initCatalogo() {
    $lista = document.getElementById("lista");
    $conteo = document.getElementById("conteo");
    $mas = document.getElementById("cargar-mas");
    $vacio = document.getElementById("vacio");
    $pills = document.getElementById("filtros");
    $buscador = document.getElementById("buscador");
    $input = document.getElementById("q");
    $limpiar = document.getElementById("limpiar");
    if (!$lista || !$pills || !$input) return;

    construirIndice();

    // Estilo inicial tomado del hash: catalogo.html#estilo=rock
    estado.estilo = leerHash();
    pintarPills();
    render();

    $pills.addEventListener("click", function (e) {
      var b = e.target.closest ? e.target.closest(".pill") : null;
      if (!b) return;
      aplicarEstilo(b.getAttribute("data-estilo"), true);
      window.scrollTo({ top: 0, behavior: "smooth" });
    });

    window.addEventListener("hashchange", function () {
      var h = leerHash();
      if (h !== estado.estilo) aplicarEstilo(h, false);
    });

    $input.addEventListener("input", function () {
      $buscador.classList.toggle("tiene-texto", $input.value.length > 0);
      if (timer) window.clearTimeout(timer);
      timer = window.setTimeout(function () {
        estado.q = $input.value;
        render();
      }, DEBOUNCE);
    });

    $limpiar.addEventListener("click", function () {
      $input.value = "";
      estado.q = "";
      $buscador.classList.remove("tiene-texto");
      render();
      $input.focus();
    });

    $mas.addEventListener("click", function () {
      estado.pagina++;
      dibujarPagina(estado.pagina);
      actualizarBotonMas();
    });
  }

  function arrancar() {
    API.safe(initCatalogo, "initCatalogo");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", arrancar);
  } else {
    arrancar();
  }
})();
