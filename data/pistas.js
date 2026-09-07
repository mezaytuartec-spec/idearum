/* ============================================================================
   IDEARUM — CATÁLOGO DE PISTAS
   ============================================================================

   ⚠️ CÓMO REEMPLAZAR ESTO POR TU CATÁLOGO REAL

   Este archivo define UNA sola variable global: window.PISTAS.
   Es un array de objetos, uno por pista, con cuatro campos obligatorios:

       id      → identificador único de 4 dígitos, como texto ("0001").
                 NUNCA lo cambies una vez publicado: es lo que te llega
                 en el mensaje de WhatsApp para saber qué pista te piden.
       titulo  → nombre de la canción.
       autor   → intérprete o autor original.
       estilo  → tiene que ser exactamente uno de los estilos de la lista
                 de abajo (respetando mayúsculas y tildes).

   ESTILOS PERMITIDOS (si agregás uno nuevo, actualizalo también en
   index.html, en catalogo.html, en js/app.js y en tools/csv_a_js.py):

       Balada · Rock / Pop · Tropical · Cuarteto · Latino · Románticos
       Canción del recuerdo · Música cristiana · Mariachi · Folklore
       Bolero · Tango

   FORMA RÁPIDA (recomendada):
   1. En Excel, armá una planilla con tres columnas: titulo, autor, estilo.
   2. Guardala como CSV (UTF-8): Archivo > Guardar como > CSV UTF-8.
   3. Corré:  python tools/csv_a_js.py mi_catalogo.csv
      El script reescribe este archivo con los IDs numerados automáticamente.

   FORMA MANUAL:
   Editá el array de abajo a mano, respetando comillas y comas.

   Las 60 pistas que siguen son SOLO DE EJEMPLO, cinco por estilo, para poder
   probar el buscador y los filtros con volumen. Borralas cuando cargues las
   tuyas. El orden acá adentro no importa: la web agrupa y filtra sola.
   ============================================================================ */

window.PISTAS = [
  { id: "0001", titulo: "Historia de un amor", autor: "Carlos Eleta Almarán", estilo: "Balada" },
  { id: "0002", titulo: "El triste", autor: "José José", estilo: "Balada" },
  { id: "0003", titulo: "Hoy tengo ganas de ti", autor: "Miguel Gallardo", estilo: "Balada" },
  { id: "0004", titulo: "Amor eterno", autor: "Juan Gabriel", estilo: "Balada" },
  { id: "0005", titulo: "Te amo", autor: "Umberto Tozzi", estilo: "Balada" },

  { id: "0006", titulo: "De música ligera", autor: "Soda Stereo", estilo: "Rock / Pop" },
  { id: "0007", titulo: "Yesterday", autor: "The Beatles", estilo: "Rock / Pop" },
  { id: "0008", titulo: "Rasguña las piedras", autor: "Sui Generis", estilo: "Rock / Pop" },
  { id: "0009", titulo: "Color esperanza", autor: "Diego Torres", estilo: "Rock / Pop" },
  { id: "0010", titulo: "Corazón partío", autor: "Alejandro Sanz", estilo: "Rock / Pop" },

  { id: "0011", titulo: "Olvídala", autor: "Los Palmeras", estilo: "Tropical" },
  { id: "0012", titulo: "Bombón asesino", autor: "Los Palmeras", estilo: "Tropical" },
  { id: "0013", titulo: "Nunca me faltes", autor: "Antonio Ríos", estilo: "Tropical" },
  { id: "0014", titulo: "La pollera colorá", autor: "Wilson Choperena", estilo: "Tropical" },
  { id: "0015", titulo: "Cariñito", autor: "Los Hijos del Sol", estilo: "Tropical" },

  { id: "0016", titulo: "Qué bello", autor: "La Mona Jiménez", estilo: "Cuarteto" },
  { id: "0017", titulo: "Beso a beso", autor: "La Mona Jiménez", estilo: "Cuarteto" },
  { id: "0018", titulo: "Ocho cuarenta", autor: "Rodrigo", estilo: "Cuarteto" },
  { id: "0019", titulo: "Soy cordobés", autor: "Rodrigo", estilo: "Cuarteto" },
  { id: "0020", titulo: "Lo mejor del amor", autor: "Rodrigo", estilo: "Cuarteto" },

  { id: "0021", titulo: "Vivir mi vida", autor: "Marc Anthony", estilo: "Latino" },
  { id: "0022", titulo: "Burbujas de amor", autor: "Juan Luis Guerra", estilo: "Latino" },
  { id: "0023", titulo: "La bilirrubina", autor: "Juan Luis Guerra", estilo: "Latino" },
  { id: "0024", titulo: "Propuesta indecente", autor: "Romeo Santos", estilo: "Latino" },
  { id: "0025", titulo: "Bailando", autor: "Enrique Iglesias", estilo: "Latino" },

  { id: "0026", titulo: "La incondicional", autor: "Luis Miguel", estilo: "Románticos" },
  { id: "0027", titulo: "Abrázame muy fuerte", autor: "Juan Gabriel", estilo: "Románticos" },
  { id: "0028", titulo: "Por debajo de la mesa", autor: "Luis Miguel", estilo: "Románticos" },
  { id: "0029", titulo: "Vivir así es morir de amor", autor: "Camilo Sesto", estilo: "Románticos" },
  { id: "0030", titulo: "Volver a amar", autor: "Cristian Castro", estilo: "Románticos" },

  { id: "0031", titulo: "Fly Me to the Moon", autor: "Frank Sinatra", estilo: "Canción del recuerdo" },
  { id: "0032", titulo: "My Way", autor: "Frank Sinatra", estilo: "Canción del recuerdo" },
  { id: "0033", titulo: "Unchained Melody", autor: "The Righteous Brothers", estilo: "Canción del recuerdo" },
  { id: "0034", titulo: "Somewhere Over the Rainbow", autor: "Judy Garland", estilo: "Canción del recuerdo" },
  { id: "0035", titulo: "Cuando calienta el sol", autor: "Los Hermanos Rigual", estilo: "Canción del recuerdo" },

  { id: "0036", titulo: "Cuán grande es Él", autor: "Himno tradicional", estilo: "Música cristiana" },
  { id: "0037", titulo: "Sublime gracia", autor: "Himno tradicional", estilo: "Música cristiana" },
  { id: "0038", titulo: "Alabaré", autor: "Himno tradicional", estilo: "Música cristiana" },
  { id: "0039", titulo: "Renuévame", autor: "Marcos Witt", estilo: "Música cristiana" },
  { id: "0040", titulo: "Tu fidelidad", autor: "Marcos Witt", estilo: "Música cristiana" },

  { id: "0041", titulo: "El rey", autor: "José Alfredo Jiménez", estilo: "Mariachi" },
  { id: "0042", titulo: "Volver, volver", autor: "Vicente Fernández", estilo: "Mariachi" },
  { id: "0043", titulo: "Cielito lindo", autor: "Quirino Mendoza", estilo: "Mariachi" },
  { id: "0044", titulo: "México lindo y querido", autor: "Jorge Negrete", estilo: "Mariachi" },
  { id: "0045", titulo: "El son de la negra", autor: "Tradicional mexicano", estilo: "Mariachi" },

  { id: "0046", titulo: "Zamba de mi esperanza", autor: "Jorge Cafrune", estilo: "Folklore" },
  { id: "0047", titulo: "Luna tucumana", autor: "Atahualpa Yupanqui", estilo: "Folklore" },
  { id: "0048", titulo: "Alfonsina y el mar", autor: "Mercedes Sosa", estilo: "Folklore" },
  { id: "0049", titulo: "El arriero", autor: "Atahualpa Yupanqui", estilo: "Folklore" },
  { id: "0050", titulo: "Entre a mi pago sin golpear", autor: "Los Nocheros", estilo: "Folklore" },

  { id: "0051", titulo: "Bésame mucho", autor: "Consuelo Velázquez", estilo: "Bolero" },
  { id: "0052", titulo: "Sabor a mí", autor: "Álvaro Carrillo", estilo: "Bolero" },
  { id: "0053", titulo: "Contigo aprendí", autor: "Armando Manzanero", estilo: "Bolero" },
  { id: "0054", titulo: "Somos novios", autor: "Armando Manzanero", estilo: "Bolero" },
  { id: "0055", titulo: "La barca", autor: "Roberto Cantoral", estilo: "Bolero" },

  { id: "0056", titulo: "Por una cabeza", autor: "Carlos Gardel", estilo: "Tango" },
  { id: "0057", titulo: "La cumparsita", autor: "Gerardo Matos Rodríguez", estilo: "Tango" },
  { id: "0058", titulo: "El día que me quieras", autor: "Carlos Gardel", estilo: "Tango" },
  { id: "0059", titulo: "Volver", autor: "Carlos Gardel", estilo: "Tango" },
  { id: "0060", titulo: "Balada para un loco", autor: "Ástor Piazzolla", estilo: "Tango" }
];
