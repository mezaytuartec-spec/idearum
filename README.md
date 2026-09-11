# Idearum

Sitio estático de Idearum: pistas profesionales para cantantes, grabadas de
cero, más covers a pedido y producción de temas propios.

Toda la venta y el contacto ocurren por WhatsApp. No hay carrito, ni pasarela
de pago, ni formularios, ni backend, ni base de datos.

Sin dependencias, sin npm y sin paso de compilación: se sube la carpeta tal
cual a Hostinger o a cualquier hosting estático.

---

## Cómo verlo en local

```
python -m http.server 8765
```

Y abrir http://localhost:8765/

---

## Estructura

```
idearum/
├── index.html          home
├── catalogo.html       listado de pistas + buscador + filtros
├── .htaccess           headers de cache (obligatorio en Hostinger)
├── css/styles.css
├── js/
│   ├── app.js          nav, revelados, corredor 3D, reproductores, WhatsApp
│   └── catalogo.js     buscador, filtros y paginado del catálogo
├── data/pistas.js      EL CATÁLOGO (se genera desde el Excel, no se edita a mano)
├── tools/csv_a_js.py   convierte el Excel del catálogo a data/pistas.js
└── assets/
    ├── img/            hero, logo, favicons y portadas del corredor
    └── audio/          los MP3 del antes y después (todavía vacía)
```

---

## Qué hay que completar

### 1. Número de WhatsApp

Ya está cargado: **+54 9 2656 44-2608**. Vive en `js/app.js`, constante
`WSP`, en formato internacional sin signos:

```js
var WSP = "5492656442608";
```

Si alguna vez cambia, se toca ahí y se actualizan todos los links. Para que
también funcionen sin JavaScript, hacer además Buscar y Reemplazar del número
viejo en `index.html` y `catalogo.html`.

### 2. El catálogo

Se genera directo desde el Excel (no hace falta pasarlo a CSV):

```
python tools/csv_a_js.py Listado_2026_COMPLETO.xlsx
```

Reescribe `data/pistas.js` e imprime un informe de todo lo que corrigió.
Lee las columnas `Nombre`, `Autor`, `Estilo` y `Propio`; las demás (Cliente,
País, Tonalidad…) se ignoran y **nunca se publican**.

- **El ID de cada pista es su número de fila en el Excel.** Cuando por
  WhatsApp llega "[ID: 0142]", es la fila 142. Por eso las pistas nuevas van
  siempre **al final** de la planilla: insertar filas en el medio les cambia
  el número a las de abajo.
- Los temas con **Propio = Sí no se publican**: son composiciones de clientes.
- Duplicados (mismo tema, autor y estilo) quedan una sola vez. El mismo tema
  en otro estilo se publica: es otro arreglo.
- Repara letras dañadas por codificación ("Ma¤ana" → "Mañana"), acomoda
  mayúsculas y unifica autores escritos de varias formas.

### 3. Los audios del antes y después

Copiar seis MP3 en `assets/audio/` con estos nombres exactos:

```
ejemplo-1-antes.mp3   ejemplo-1-despues.mp3
ejemplo-2-antes.mp3   ejemplo-2-despues.mp3
ejemplo-3-antes.mp3   ejemplo-3-despues.mp3
```

Mientras no haya ningún audio subido, **la sección entera queda oculta**:
la web nunca muestra fichas vacías ni textos de relleno. Aparece sola en
cuanto se sube el primero. Los títulos y autores de las tres tarjetas se
editan en `index.html` (hoy tienen textos de ejemplo).

### 4. Textos por revisar

Los plazos de entrega y los formatos de las tarjetas de "A medida" son
estimados. Están marcados con `⚠️` dentro del HTML.

---

## Precios

| Producto | Precio | Dónde está |
|---|---|---|
| Pista del catálogo | US$ 40 una · US$ 100 tres | `index.html` (corredor) y `catalogo.html` |
| Cover a pedido | desde US$ 150 | `index.html` y `catalogo.html` |
| Tema propio | desde US$ 200 | `index.html` y `catalogo.html` |

---

## Estilos musicales

En el orden en que se muestran, de los más pedidos a los más de nicho:

`Balada` · `Rock / Pop` · `Tropical` · `Cuarteto` · `Latino` · `Románticos` ·
`Canción del recuerdo` · `Música cristiana` · `Mariachi` · `Folklore` ·
`Bolero` · `Tango` · `Otros`

`Otros` junta lo que en el Excel figura como "Otro".

Si se agrega o saca uno, hay que tocarlo en tres lugares: la constante
`ESTILOS` de `js/app.js`, las píldoras de filtro de `catalogo.html` y la lista
`ESTILOS` de `tools/csv_a_js.py`.

El script compara los estilos sin tildes, mayúsculas, signos ni plurales:
en el Excel se puede escribir `Baladas`, `Rock/Pop`, `Cancion del Recuerdo`
o `Folklore tradicional` y los reconoce igual.

---

## Imágenes

- **Hero**: `assets/img/hero-1800.jpg` (escritorio), `hero-900.jpg` (tablet)
  y `hero-movil.jpg` (celular: la foto a escala normal con el fondo celeste y
  blanco del estudio extendido hacia arriba, fundido sin corte, para que el
  texto vaya encima de la foto también en el teléfono). Están
  recortadas para que el bombo con el logo caiga en el eje exacto de la
  página. Si se cambia la foto, los dos tercios de arriba tienen que quedar
  limpios: ahí va el texto.
- **Portadas del corredor**: `assets/img/portadas/portada-01.jpg` a la 13.
  Van cuadradas, ideal 640 × 640 px. La lista está en `js/app.js`, constante
  `PORTADAS`. Para reemplazar una se pisa el archivo con el mismo nombre y
  **se cambia `V_PORTADAS`** en `js/app.js`: si no, el navegador de quien ya
  entró sigue mostrando la portada vieja (la guarda hasta 30 días).
- La foto del hero tiene su propia versión en `css/styles.css` (`?v=` al lado
  de `hero-1800.jpg` y `hero-900.jpg`): si se cambia la foto, se cambia eso.

Las portadas de discos que hay hoy son de terceros y están puestas como
referencia visual. Antes de usar el sitio comercialmente conviene
reemplazarlas por material propio.

---

## Subir a producción

1. Bumpear el `?v=AAAAMMDD` de cada `<link>` y `<script>` en los dos HTML.
   Sin eso, Hostinger puede seguir sirviendo el CSS y el JS viejos.
2. Subir el contenido de la carpeta por FTP o por el administrador de
   archivos, incluido el `.htaccess`.

---

## Decisiones que conviene no deshacer

- **Los audios del catálogo no se suben.** Solo el listado. Cada pista tiene
  un botón que abre WhatsApp con un mensaje preescrito y el ID; el audio se
  manda a mano. Eso evita hostear y proteger cientos de archivos.
- **`data/pistas.js` es un script clásico que define `window.PISTAS`**, no un
  JSON con `fetch()`: así funciona también abriendo el archivo directamente y
  no hace falta manejar estados de carga.
- **Nada de `<script type="module">`.** Se rompe en algunos hosting.
- **La home muestra una vista previa real del catálogo**, con las mismas
  filas y los mismos botones que `catalogo.html`. El HTML de la fila lo arma
  `filaHTML()` en `js/app.js` y lo usan las dos páginas, para que no se
  puedan desincronizar.
- **El amarillo `#FFDE21` aparece en tres lugares y nada más**: el subrayado
  del título del hero, la píldora de filtro activa y los dos botones
  "Escribinos". Sobre blanco tiene 1,3:1 de contraste, así que no se usa
  nunca para texto chico, bordes finos ni iconos.
