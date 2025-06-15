import glob
import os

from llama_index.core import (
    Settings,
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.milvus import MilvusVectorStore
from pymilvus import MilvusClient

from my_config import MY_CONFIG

# Step-1: Read Markdown files
pattern = os.path.join(MY_CONFIG.PROCESSED_DATA_DIR, "*.md")
md_file_count = len(glob.glob(pattern, recursive=True))

reader = SimpleDirectoryReader(
    input_dir=MY_CONFIG.PROCESSED_DATA_DIR, recursive=False, required_exts=[".md"]
)
documents = reader.load_data()
print(f"Loaded {len(documents)} documents from {md_file_count} files")

# Step-2: Create Chunks
parser = SentenceSplitter(
    chunk_size=MY_CONFIG.CHUNK_SIZE, chunk_overlap=MY_CONFIG.CHUNK_OVERLAP
)
nodes = parser.get_nodes_from_documents(documents)
print(f"Created {len(nodes)} chunks from {len(documents)} documents")

# Step-3: Setup Embedding Model
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

Settings.embed_model = HuggingFaceEmbedding(model_name=MY_CONFIG.EMBEDDING_MODEL)

# Step-4: Connect to Milvus
milvus_client = MilvusClient(MY_CONFIG.DB_URI)
print("✅ Connected to Milvus instance: ", MY_CONFIG.DB_URI)

if milvus_client.has_collection(collection_name=MY_CONFIG.COLLECTION_NAME):
    milvus_client.drop_collection(collection_name=MY_CONFIG.COLLECTION_NAME)
    print("✅ Cleared collection :", MY_CONFIG.COLLECTION_NAME)

# Connect llama-index to vector db
vector_store = MilvusVectorStore(
    uri=MY_CONFIG.DB_URI,
    dim=MY_CONFIG.EMBEDDING_LENGTH,
    collection_name=MY_CONFIG.COLLECTION_NAME,
    overwrite=True,
)
storage_context = StorageContext.from_defaults(vector_store=vector_store)
print("✅ Connected Llama-index to Milvus instance: ", MY_CONFIG.DB_URI)

# Step-5: Save to DB
# Save chunks into vector db
index = VectorStoreIndex(
    nodes=nodes,
    storage_context=storage_context,
)

print(
    f"✅ Successfully stored {len(nodes)} chunks in Milvus collection '{MY_CONFIG.COLLECTION_NAME}'"
)

milvus_client.close()
