import chromadb

client = chromadb.HttpClient(host="localhost", port=8001)

collections = client.list_collections()
print("Collections found:", collections)

for col_name in collections:
    col = client.get_collection(col_name.name)
    data = col.get(include=["documents", "metadatas"])
    print(f"\n--- {col_name.name} ---")
    print(f"Total records: {len(data['ids'])}")
    for i, id in enumerate(data["ids"]):
        print(f"\nID: {id}")
        print(f"Meta: {data['metadatas'][i]}")
        print(f"Doc:  {data['documents'][i]}")