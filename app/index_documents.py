
from app.ingestion import ingest_directory


if __name__ == "__main__":
    results = ingest_directory()

    if not results:
        print("No PDFs found in the data directory.")
    else:
        for result in results:
            print(result)
