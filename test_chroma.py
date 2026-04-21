import chromadb

client = chromadb.Client()

print("Heartbeat:", client.heartbeat())

collection = client.create_collection("test")

collection.add(
    documents=["Hello world"],
    ids=["1"]
)

results = collection.query(
    query_texts=["Hello"],
    n_results=1
)

print("Query result:", results)