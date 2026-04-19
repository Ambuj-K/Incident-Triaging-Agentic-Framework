from pathlib import Path
from incident_triage.retrieval.ingestion import run_ingestion

if __name__ == "__main__":
    data_dir = Path("data")
    run_ingestion(data_dir=data_dir, clear_existing=True)
