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
   index.html, en catalogo.html y en tools/csv_a_js.py):

       Rock, Blues, Pop, Cumbia, Folclore, Jazz, Bolero, Reggae, Balada, Tango

   FORMA RÁPIDA (recomendada):
   1. En Excel, armá una planilla con tres columnas: titulo, autor, estilo.
   2. Guardala como CSV (UTF-8): Archivo > Guardar como > CSV UTF-8.
   3. Corré:  python tools/csv_a_js.py mi_catalogo.csv
      El script reescribe este archivo con los IDs numerados automáticamente.

   FORMA MANUAL:
   Editá el array de abajo a mano, respetando comillas y comas.

   Las 60 pistas que siguen son SOLO DE EJEMPLO, para que puedas probar el
   buscador y los filtros con volumen real. Borralas cuando cargues las tuyas.
   ============================================================================ */

window.PISTAS = [
  { id: "0001", titulo: "Yesterday", autor: "The Beatles", estilo: "Rock" },
  { id: "0002", titulo: "De música ligera", autor: "Soda Stereo", estilo: "Rock" },
  { id: "0003", titulo: "Matador", autor: "Los Fabulosos Cadillacs", estilo: "Rock" },
  { id: "0004", titulo: "Rasguña las piedras", autor: "Sui Generis", estilo: "Rock" },
  { id: "0005", titulo: "Mil horas", autor: "Los Abuelos de la Nada", estilo: "Rock" },
  { id: "0006", titulo: "La balsa", autor: "Los Gatos", estilo: "Rock" },

  { id: "0007", titulo: "The Thrill Is Gone", autor: "B.B. King", estilo: "Blues" },
  { id: "0008", titulo: "Pride and Joy", autor: "Stevie Ray Vaughan", estilo: "Blues" },
  { id: "0009", titulo: "Sweet Home Chicago", autor: "Robert Johnson", estilo: "Blues" },
  { id: "0010", titulo: "Hoochie Coochie Man", autor: "Muddy Waters", estilo: "Blues" },
  { id: "0011", titulo: "Born Under a Bad Sign", autor: "Albert King", estilo: "Blues" },
  { id: "0012", titulo: "Moscato, pizza y fainá", autor: "Memphis La Blusera", estilo: "Blues" },

  { id: "0013", titulo: "La incondicional", autor: "Luis Miguel", estilo: "Pop" },
  { id: "0014", titulo: "Color esperanza", autor: "Diego Torres", estilo: "Pop" },
  { id: "0015", titulo: "Corazón partío", autor: "Alejandro Sanz", estilo: "Pop" },
  { id: "0016", titulo: "Bailando", autor: "Enrique Iglesias", estilo: "Pop" },
  { id: "0017", titulo: "Me gustas tú", autor: "Manu Chao", estilo: "Pop" },
  { id: "0018", titulo: "A Dios le pido", autor: "Juanes", estilo: "Pop" },

  { id: "0019", titulo: "Olvídala", autor: "Los Palmeras", estilo: "Cumbia" },
  { id: "0020", titulo: "Bombón asesino", autor: "Los Palmeras", estilo: "Cumbia" },
  { id: "0021", titulo: "Nunca me faltes", autor: "Antonio Ríos", estilo: "Cumbia" },
  { id: "0022", titulo: "La pollera colorá", autor: "Wilson Choperena", estilo: "Cumbia" },
  { id: "0023", titulo: "Colegiala", autor: "Rodolfo y su Típica", estilo: "Cumbia" },
  { id: "0024", titulo: "Cariñito", autor: "Los Hijos del Sol", estilo: "Cumbia" },

  { id: "0025", titulo: "Zamba de mi esperanza", autor: "Jorge Cafrune", estilo: "Folclore" },
  { id: "0026", titulo: "Luna tucumana", autor: "Atahualpa Yupanqui", estilo: "Folclore" },
  { id: "0027", titulo: "Alfonsina y el mar", autor: "Mercedes Sosa", estilo: "Folclore" },
  { id: "0028", titulo: "El arriero", autor: "Atahualpa Yupanqui", estilo: "Folclore" },
  { id: "0029", titulo: "Como pájaros en el aire", autor: "Peteco Carabajal", estilo: "Folclore" },
  { id: "0030", titulo: "Entre a mi pago sin golpear", autor: "Los Nocheros", estilo: "Folclore" },

  { id: "0031", titulo: "Autumn Leaves", autor: "Joseph Kosma", estilo: "Jazz" },
  { id: "0032", titulo: "Take Five", autor: "Dave Brubeck", estilo: "Jazz" },
  { id: "0033", titulo: "So What", autor: "Miles Davis", estilo: "Jazz" },
  { id: "0034", titulo: "Fly Me to the Moon", autor: "Frank Sinatra", estilo: "Jazz" },
  { id: "0035", titulo: "Summertime", autor: "George Gershwin", estilo: "Jazz" },
  { id: "0036", titulo: "Blue Bossa", autor: "Kenny Dorham", estilo: "Jazz" },

  { id: "0037", titulo: "Bésame mucho", autor: "Consuelo Velázquez", estilo: "Bolero" },
  { id: "0038", titulo: "Sabor a mí", autor: "Álvaro Carrillo", estilo: "Bolero" },
  { id: "0039", titulo: "Contigo aprendí", autor: "Armando Manzanero", estilo: "Bolero" },
  { id: "0040", titulo: "Somos novios", autor: "Armando Manzanero", estilo: "Bolero" },
  { id: "0041", titulo: "La barca", autor: "Roberto Cantoral", estilo: "Bolero" },
  { id: "0042", titulo: "Perfidia", autor: "Alberto Domínguez", estilo: "Bolero" },

  { id: "0043", titulo: "No Woman No Cry", autor: "Bob Marley", estilo: "Reggae" },
  { id: "0044", titulo: "Could You Be Loved", autor: "Bob Marley", estilo: "Reggae" },
  { id: "0045", titulo: "Is This Love", autor: "Bob Marley", estilo: "Reggae" },
  { id: "0046", titulo: "Y qué pasó", autor: "Los Cafres", estilo: "Reggae" },
  { id: "0047", titulo: "Párate y mira", autor: "Los Pericos", estilo: "Reggae" },
  { id: "0048", titulo: "Three Little Birds", autor: "Bob Marley", estilo: "Reggae" },

  { id: "0049", titulo: "Historia de un amor", autor: "Carlos Eleta Almarán", estilo: "Balada" },
  { id: "0050", titulo: "Te amo", autor: "Umberto Tozzi", estilo: "Balada" },
  { id: "0051", titulo: "Hoy tengo ganas de ti", autor: "Miguel Gallardo", estilo: "Balada" },
  { id: "0052", titulo: "El triste", autor: "José José", estilo: "Balada" },
  { id: "0053", titulo: "Amor eterno", autor: "Juan Gabriel", estilo: "Balada" },
  { id: "0054", titulo: "Detalles", autor: "Roberto Carlos", estilo: "Balada" },

  { id: "0055", titulo: "Por una cabeza", autor: "Carlos Gardel", estilo: "Tango" },
  { id: "0056", titulo: "La cumparsita", autor: "Gerardo Matos Rodríguez", estilo: "Tango" },
  { id: "0057", titulo: "El día que me quieras", autor: "Carlos Gardel", estilo: "Tango" },
  { id: "0058", titulo: "Volver", autor: "Carlos Gardel", estilo: "Tango" },
  { id: "0059", titulo: "Adiós Nonino", autor: "Ástor Piazzolla", estilo: "Tango" },
  { id: "0060", titulo: "Balada para un loco", autor: "Ástor Piazzolla", estilo: "Tango" }
];
