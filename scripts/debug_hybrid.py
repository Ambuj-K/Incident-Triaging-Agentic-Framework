from incident_triage.retrieval.hybrid_search import (
    keyword_search,
    vector_search,
)
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

test_queries = [
    "exit code 0 but nothing written",
    "CBOT hours grain API slow",
    "retrain MAPE 22% previous 9%",
]

for query in test_queries:
    print(f"\n{'='*60}")
    print(f"QUERY: {query}")
    print(f"{'='*60}")

    kw_results = keyword_search(query=query, doc_type="incident_report", top_k=5)
    print(f"\nKEYWORD RESULTS ({len(kw_results)} found):")
    for r in kw_results:
        print(f"  [{r['keyword_rank']:.4f}] {r['doc_id']} - {r['section']}")

    embedding = model.encode(query, convert_to_numpy=True).tolist()
    vec_results = vector_search(
        query_embedding=embedding,
        doc_type="incident_report",
        top_k=5,
    )
    print(f"\nVECTOR RESULTS:")
    for r in vec_results:
        print(f"  [{r['similarity']:.4f}] {r['doc_id']} - {r['section']}")
