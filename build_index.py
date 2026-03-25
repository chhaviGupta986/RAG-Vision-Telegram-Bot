import os
import pickle
from dotenv import load_dotenv
load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
os.environ["HF_TOKEN"] = HF_TOKEN  # do this before transformers imports/downloads

import faiss
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer


def build_chunks(text: str, splitter: RecursiveCharacterTextSplitter):
    raw_chunks = splitter.split_text(text)
    return [chunk.strip() for chunk in raw_chunks if chunk.strip()]


model = SentenceTransformer(model_name_or_path="all-MiniLM-L6-v2")
os.makedirs("db", exist_ok=True)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=450,
    chunk_overlap=100,
    length_function=len,
)

all_chunks = []
metadata = []

for file in os.listdir("data"):
    with open(os.path.join("data", file), "r", encoding="utf-8") as f:
        text = f.read()
    chunks = build_chunks(text, splitter)
    for chunk in chunks:
        all_chunks.append(chunk)
        metadata.append({"source": file, "chunk": chunk})

embeddings = model.encode(all_chunks)

index = faiss.IndexFlatL2(len(embeddings[0]))
index.add(embeddings)

faiss.write_index(index, "db/faiss.index")
with open("db/metadata.pkl", "wb") as f:
    pickle.dump(metadata, f)

with open("db/chunks_debug.txt", "w", encoding="utf-8") as debug_file:
    for entry in metadata[:50]:
        debug_file.write(f"{entry['source']} | {entry['chunk']}\n\n")
