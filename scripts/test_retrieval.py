from incident_triage.retrieval.retriever import retrieve_for_incident

test_queries = [
    "Inventory sync job failed at 3am, 2400 SKUs showing incorrect stock levels",
    "Commodity price feed not updating, procurement model operating on stale data",
    "ML demand forecasting model producing negative values after retrain",
    "Duplicate purchase orders submitted to suppliers",
    "Data warehouse storage exhausted, all ingestion halted",
]

for query in test_queries:
    print(f"\n{'='*60}")
    print(f"QUERY: {query[:60]}...")
    print(f"{'='*60}")

    results = retrieve_for_incident(query, top_k=3)

    print("\nRUNBOOKS:")
    for r in results["runbooks"]:
        print(f"  [{r['similarity']:.3f}] {r['doc_id']} - {r['section']}")

    print("\nPAST INCIDENTS:")
    for r in results["past_incidents"]:
        print(f"  [{r['similarity']:.3f}] {r['doc_id']} - {r['section']}")
