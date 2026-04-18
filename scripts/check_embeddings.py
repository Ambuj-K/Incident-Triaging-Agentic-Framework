# scripts/check_embeddings.py
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
test_sentences = [
    "Inventory sync job failed at 3am",
    "Commodity price feed not updating",
    "ML demand forecasting model producing negative values",
]

embeddings = model.encode(test_sentences)
print(f"Model loaded successfully")
print(f"Embedding dimension: {embeddings.shape[1]}")
print(f"Test sentences embedded: {len(embeddings)}")