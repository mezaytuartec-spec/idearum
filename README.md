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
├── tools/
│   ├── csv_a_js.py     convierte el Excel del catálogo a data/pistas.js
│   └── portadas.py     deja las portadas cuadradas, de 640 px y comprimidas
└── assets/
    ├── img/            hero, logo, favicons y portadas del corredor
    │   └── origen/     originales y variantes que la web NO usa (no hace
    │                   falta subirlos al hosting)
    └── audio/          los seis MP3 del antes y después
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

Ya están cargados. Son seis MP3 en `assets/audio/`:

```
ejemplo-1-antes.mp3   ejemplo-1-despues.mp3    cover a pedido
ejemplo-2-antes.mp3   ejemplo-2-despues.mp3    tema propio
ejemplo-3-antes.mp3   ejemplo-3-despues.mp3    tema propio
```

Para cambiar un ejemplo se pisa el archivo con el mismo nombre y se sube el
`?v=` de los `<script>` del final de `index.html`.

Los títulos de las tres tarjetas describen qué se escucha ("De un karaoke a
una pista grabada"). Si se quiere poner el nombre real de cada canción, se
edita el `<h3 class="ejemplo__titulo">` de cada una en `index.html`.

Si algún archivo llegara a faltar, ese reproductor queda apagado y dice
"Disponible pronto": no rompe nada.

Los mismos seis audios suenan también **arriba del catálogo**, debajo del
buscador, en una versión corta: seis botones ("Antes · Karaoke", "Después ·
Pista grabada"…) sin reloj ni barra. Lo que dice cada uno está en el
`data-nombre` y el `data-detalle` de `catalogo.html`. Ahí no se descarga ningún
audio hasta que alguien aprieta play, así el catálogo carga igual de rápido.

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

Si se agrega o saca uno, hay que tocarlo en dos lugares: las píldoras de
filtro de `catalogo.html` y la lista `ESTILOS` de `tools/csv_a_js.py`.

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
  Van **cuadradas**, ideal 640 × 640 px. La lista está en `js/app.js`,
  constante `PORTADAS`, y arriba hay un comentario que dice qué disco es cada
  número. Para reemplazar una se pisa el archivo con el mismo nombre y
  **se cambia `V_PORTADAS`** en `js/app.js`: si no, el navegador de quien ya
  entró sigue mostrando la portada vieja (la guarda hasta 30 días).

  Si la que conseguiste no es cuadrada o es más grande de 640 px, pasala por:

  ```
  python tools/portadas.py
  ```

  Recorta las que no son cuadradas, achica las que se pasan de 640 y deja
  todas con la misma calidad. No agranda las chicas: eso suma peso sin sumar
  nitidez, así que conviene buscarlas de 640 px o más.
- Las tres fotos del hero se nombran **en un solo lugar**: el `<picture>` de
  `index.html`. El CSS ya no sabe cómo se llaman, sólo qué forma tienen en
  cada pantalla. Si se cambia una foto, se sube el `?v=` de esa línea.

Las portadas de discos que hay hoy son de terceros y están puestas como
referencia visual. Antes de usar el sitio comercialmente conviene
reemplazarlas por material propio.

Todas las imágenes están recomprimidas al máximo que aguantan sin que se note
(JPEG progresivo; los PNG quedaron pixel por pixel idénticos). Si se reemplaza
alguna, conviene volver a pasarla por un compresor antes de subirla.

---

## Subir a producción

1. Bumpear el `?v=AAAAMMDD` del `<link>` del CSS y de los `<script>` en los
   dos HTML. Sin eso, Hostinger puede seguir sirviendo el CSS y el JS viejos.

   El `?v=` que va al lado de una **imagen** es distinto: ese se toca **solo
   cuando pisás esa imagen**. Subirlo por costumbre obliga a todos los que ya
   entraron a bajar de nuevo una foto que no cambió. Para las trece portadas
   juntas, el que manda es `V_PORTADAS` en `js/app.js`.
2. Subir el contenido de la carpeta por FTP o por el administrador de
   archivos, incluido el `.htaccess`.
3. `assets/img/origen/` y `tools/` no se usan desde el navegador: se pueden
   dejar sin subir.

---

## Qué se hizo para que vaya liviana

Sin librerías, sin compilación y sin cambiar nada de lo que se ve:

- **La foto del hero es un `<picture>` y no un fondo de CSS.** Es la imagen
  más grande de la primera pantalla; como fondo, el navegador recién se
  enteraba de que existía después de leer todo el CSS. Así la encuentra
  mientras lee el HTML y empieza a bajarla enseguida.
- **El corredor de portadas y la luz del borde de "Tema propio" se congelan
  cuando su sección no está en pantalla.** Son las dos únicas animaciones que
  corren solas; pausarlas ahorra batería en el teléfono y no se nota.
- **Los seis MP3 (casi 3 MB) no se tocan hasta que la sección se acerca.**
  Quien entra a la home y no baja hasta ahí no descarga ni un byte de música.
- **Imágenes recomprimidas**: el hero pesa un 12 % menos y el ícono de iOS un
  32 %, sin diferencia visible.
- **Compresión en el servidor**: `.htaccess` pide Brotli y, si el hosting no
  lo tiene, gzip. El CSS y el JS viajan a un cuarto de su peso, así que **no
  están minificados a propósito**: se ganan unos pocos KB y se pierde poder
  leerlos y corregirlos desde el administrador de archivos de Hostinger.

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
