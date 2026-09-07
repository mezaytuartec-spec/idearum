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
├── data/pistas.js      EL CATÁLOGO (hoy son 60 pistas de ejemplo)
├── tools/csv_a_js.py   convierte el Excel del catálogo a data/pistas.js
└── assets/
    ├── img/            hero, logo, favicons y portadas del corredor
    └── audio/          los MP3 del antes y después (todavía vacía)
```

---

## Qué hay que completar

### 1. Número de WhatsApp

En `js/app.js`, constante `WSP` (arriba de todo). Formato internacional sin
signos: `54` + `9` + código de área sin el 0 + número sin el 15.

```js
var WSP = "5492664XXXXXX";
```

Cambiarlo ahí actualiza todos los links de las dos páginas. Opcionalmente,
para que también funcionen sin JavaScript, hacer Buscar y Reemplazar de
`5492664XXXXXX` en `index.html` y `catalogo.html`.

### 2. El catálogo real

1. Armar en Excel una planilla con tres columnas: `titulo`, `autor`, `estilo`.
2. Guardarla como CSV UTF-8.
3. Correr:

```
python tools/csv_a_js.py mi_catalogo.csv
```

Reescribe `data/pistas.js` con los IDs numerados de 0001 en adelante. El
script avisa si hay filas vacías, duplicadas o con un estilo no permitido.

**Los IDs no se cambian una vez publicados**: son los que viajan en el mensaje
de WhatsApp y permiten saber qué pista están pidiendo.

### 3. Los audios del antes y después

Copiar seis MP3 en `assets/audio/` con estos nombres exactos:

```
ejemplo-1-antes.mp3   ejemplo-1-despues.mp3
ejemplo-2-antes.mp3   ejemplo-2-despues.mp3
ejemplo-3-antes.mp3   ejemplo-3-despues.mp3
```

Hasta que existan, cada reproductor se muestra apagado y dice
"Disponible pronto". Los títulos y autores de las tres tarjetas se editan
en `index.html`.

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
`Bolero` · `Tango`

Si se agrega o saca uno, hay que tocarlo en cuatro lugares: `data/pistas.js`,
la constante `ESTILOS` de `js/app.js`, las píldoras de filtro de
`catalogo.html` y la lista `ESTILOS` de `tools/csv_a_js.py`.

El script del CSV compara los estilos sin tildes ni mayúsculas ni signos, así
que en el Excel se puede escribir `Rock/Pop`, `rock / pop` o `Musica cristiana`
y los reconoce igual.

---

## Imágenes

- **Hero**: `assets/img/hero-1800.jpg` (escritorio) y `hero-900.jpg` (móvil).
  Están recortadas para que el bombo con el logo caiga en el eje exacto de la
  página. Si se cambia la foto, los dos tercios de arriba tienen que quedar
  limpios: ahí va el texto.
- **Portadas del corredor**: `assets/img/portadas/portada-01.jpg` a la 12.
  Van cuadradas, ideal 640 × 640 px. Para reemplazar una, se pisa el archivo
  con el mismo nombre. La lista está en `js/app.js`, constante `PORTADAS`.

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
  manda a mano. Eso evita hostear y proteger 500 archivos.
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
