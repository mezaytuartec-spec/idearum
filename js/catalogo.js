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

  var $input, $buscador, $limpiar, $lista, $mas, $vacio, $pills;
  var timer = null;

  /* ---------- Indice normalizado (una sola vez) --------------------------- */

  function construirIndice() {
    var lista = API.pistas();
    indice = new Array(lista.length);
    for (var i = 0; i < lista.length; i++) {
      var p = lista[i];
      // El campo de busqueda dice "Buscar por autor" porque es lo mas comun,
      // pero el indice incluye tambien el titulo y el estilo: quien escriba
      // "tango" o el nombre de la cancion igual encuentra.
      indice[i] = {
        p: p,
        estilo: API.slug(p.estilo),
        busca: API.normalizar(p.titulo) + " " +
               API.normalizar(p.autor) + " " +
               API.normalizar(p.estilo)
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

  // El HTML de la fila lo arma app.js: lo comparten el catalogo y la vista
  // previa de la home, asi las dos se ven y se comportan igual.
  var filaHTML = API.filaHTML;

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

  // La web nunca dice cuantas pistas hay: el boton solo aparece o desaparece.
  function actualizarBotonMas() {
    $mas.hidden = estado.pagina * POR_PAGINA >= filtradas.length;
  }

  function render() {
    filtradas = filtrar();
    estado.pagina = 1;
    $lista.textContent = "";
    dibujarPagina(1);

    var sinResultados = filtradas.length === 0;
    $vacio.hidden = !sinResultados;
    $lista.hidden = sinResultados;

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
