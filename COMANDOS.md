# Comandos para probar — Clase 5

Todos se corren desde la carpeta del proyecto. Copiá y pegá de a uno.

## 0. Comprobar que todo anda

```bash
uv run python -m pytest
```

Tienen que pasar las 71 pruebas.

## 1. El workflow completo

```bash
uv run python app.py
```

Corre los 12 casos del lote, cada uno con su traza.

## 2. La búsqueda semántica (qué recupera el RAG)

```bash
uv run python app.py buscar "¿El flete a Córdoba lo pagan ustedes?"
uv run python app.py buscar "¿Tienen cuotas sin interés?"
uv run python app.py buscar "¿Qué papeles necesito para abrir cuenta corriente?"
uv run python app.py buscar "¿Aceptan pagos con criptomonedas?"
```

La última no tiene regla en la normativa: ningún fragmento debería superar el umbral.

Sin filtro de vigencia (aparecen también las reglas derogadas):

```bash
uv run python app.py buscar "¿Tienen cuotas sin interés?" --todas
```

## 3. Sin RAG vs. con RAG

```bash
uv run python app.py comparar
```

⚠️ Necesita la key de Gemini activa en `.env`. Sin key no se ve al modelo inventar. Puede tardar varios minutos.

## 4. El ejemplo del teórico (catálogo de telas)

```bash
uv run python app.py telas
uv run python app.py telas "algo abrigado para invierno"
uv run python app.py telas "tela elegante para un vestido de fiesta"
```

## 5. Mirar adentro de ChromaDB (los vectores)

```bash
uv run python ver_chroma.py
```

Muestra cada fragmento guardado con su texto, sus metadatos y su vector (768 números).

## 5b. Consultas SQL a ChromaDB (desde la extensión de VS Code)

Conectá la extensión de base de datos como **SQLite** al archivo `indice_chroma/chroma.sqlite3`. Usala solo para **mirar**: si editás filas, el índice se rompe (se arregla con `uv run python app.py indexar`).

Cómo guarda Chroma los datos: `embeddings` tiene una fila por fragmento, y `embedding_metadata` tiene **una fila por cada dato** de ese fragmento (clave → valor). Por eso casi todas las consultas hacen un `JOIN` entre las dos.

**Cuántos fragmentos hay en cada colección**

```sql
SELECT c.name AS coleccion, COUNT(e.id) AS fragmentos
FROM collections c
JOIN segments s   ON s.collection = c.id
JOIN embeddings e ON e.segment_id = s.id
GROUP BY c.name;
```

**Todas las reglas de la normativa, con vigencia y versión**

```sql
SELECT e.embedding_id AS regla,
       MAX(CASE WHEN m.key='vigente' THEN m.bool_value END)   AS vigente,
       MAX(CASE WHEN m.key='version' THEN m.string_value END) AS version,
       substr(MAX(CASE WHEN m.key='chroma:document' THEN m.string_value END), 1, 50) AS texto
FROM embeddings e JOIN embedding_metadata m ON m.id = e.id
WHERE e.embedding_id LIKE 'NOR-%'
GROUP BY e.id ORDER BY regla;
```

**Solo las reglas derogadas** (las que el filtro `vigente = True` deja afuera)

```sql
SELECT e.embedding_id AS regla,
       MAX(CASE WHEN m.key='version' THEN m.string_value END) AS version
FROM embeddings e JOIN embedding_metadata m ON m.id = e.id
WHERE e.id IN (SELECT id FROM embedding_metadata WHERE key='vigente' AND bool_value = 0)
GROUP BY e.id;
```

**Las reglas agrupadas por sección**

```sql
SELECT e.embedding_id AS regla,
       MAX(CASE WHEN m.key='seccion' THEN m.string_value END) AS seccion
FROM embeddings e JOIN embedding_metadata m ON m.id = e.id
WHERE e.embedding_id LIKE 'NOR-%'
GROUP BY e.id ORDER BY seccion;
```

**El texto completo de una regla** (cambiá `NOR-ZONA` por la que quieras)

```sql
SELECT e.embedding_id AS regla, m.string_value AS texto
FROM embeddings e JOIN embedding_metadata m ON m.id = e.id
WHERE m.key = 'chroma:document' AND e.embedding_id = 'NOR-ZONA';
```

**Todos los datos guardados de un fragmento** (así se ve la estructura clave → valor)

```sql
SELECT m.key, m.string_value, m.bool_value
FROM embeddings e JOIN embedding_metadata m ON m.id = e.id
WHERE e.embedding_id = 'TELA-001';
```

**Búsqueda por palabra exacta** (para comparar con la búsqueda semántica)

```sql
SELECT e.embedding_id AS id, substr(m.string_value, 1, 60) AS texto
FROM embeddings e JOIN embedding_metadata m ON m.id = e.id
WHERE m.key = 'chroma:document' AND m.string_value LIKE '%flete%';
```

Probá después `LIKE '%camión%'`: SQL no encuentra nada, porque la palabra no aparece en ningún texto. En cambio, `uv run python app.py buscar "¿Quién paga el camión que me trae la mercadería?"` sí encuentra la regla del flete (NOR-ZONA, similitud 0.44), porque busca por significado y no por palabras.

**Las telas del catálogo**

```sql
SELECT e.embedding_id AS tela,
       MAX(CASE WHEN m.key='titulo' THEN m.string_value END)       AS titulo,
       MAX(CASE WHEN m.key='linea_textil' THEN m.string_value END) AS linea,
       MAX(CASE WHEN m.key='en_stock' THEN m.bool_value END)       AS en_stock
FROM embeddings e JOIN embedding_metadata m ON m.id = e.id
WHERE e.embedding_id LIKE 'TELA-%'
GROUP BY e.id ORDER BY tela;
```

**Dónde están los vectores** (cada uno ocupa 3072 bytes = 768 números × 4 bytes)

```sql
SELECT seq_id, id, length(vector) AS bytes
FROM embeddings_queue LIMIT 5;
```

El contenido de `vector` es binario y no se puede leer. Para ver los números: `uv run python ver_chroma.py`.

## 6. Repaso de la Clase 4: el paso 2 como cadena LCEL

```bash
uv run python app.py lcel
```

## 7. Rehacer los índices (el paso offline)

```bash
uv run python app.py indexar
```

---

**Modo simulación vs. LLM real:** si en `.env` las líneas `GEMINI_API_KEY` y `GEMINI_MODEL` están comentadas (con `#`), todo corre en simulación: la búsqueda funciona de verdad, pero el LLM no redacta. Para usar Gemini, sacales el `#`.
