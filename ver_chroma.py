"""
Mirar adentro de ChromaDB: qué colecciones hay, qué textos guardó y cómo son los vectores.

    uv run python ver_chroma.py
"""

import chromadb

cliente = chromadb.PersistentClient(path="indice_chroma")

for col in cliente.list_collections():
    datos = col.get(include=["documents", "metadatas", "embeddings"])
    print("=" * 78)
    print(f"COLECCIÓN: {col.name}   ·   {col.count()} fragmentos")
    print("=" * 78)
    for id_, texto, meta, vector in zip(datos["ids"], datos["documents"],
                                       datos["metadatas"], datos["embeddings"]):
        print(f"\n🆔 {id_}")
        print(f"   metadatos: {meta}")
        print(f"   texto:     {texto[:100]}{'…' if len(texto) > 100 else ''}")
        print(f"   vector:    {len(vector)} números → [{', '.join(f'{x:.3f}' for x in vector[:5])}, …]")
    print()
