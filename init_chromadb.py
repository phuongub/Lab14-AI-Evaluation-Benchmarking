"""Quick ChromaDB initialization script"""
import chromadb
from pathlib import Path

CHROMA_DB_DIR = Path(__file__).parent / "chroma_db"

# Create the directory if it doesn't exist
CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)

# Initialize a persistent client
print(f"Initializing ChromaDB at {CHROMA_DB_DIR}")
client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

# Create the collection (this initializes the database properly)
try:
    client.delete_collection("rag_lab")
    print("Deleted existing rag_lab collection")
except:
    pass

collection = client.get_or_create_collection(
    name="rag_lab",
    metadata={"hnsw:space": "cosine"}
)

print("✓ ChromaDB initialized successfully!")
print(f"✓ Collection 'rag_lab' created")
print("\nNow you can run: python index.py")
