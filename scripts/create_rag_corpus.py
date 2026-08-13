import sys
import vertexai
from vertexai import rag

PROJECT_ID = "qwiklabs-gcp-04-4af6105616e2"
LOCATION = "us-east1"
GCS_PATH = "gs://warhammer-book-concierge-covers-qwiklabs-gcp-04-4af6105616e2/rag/black_library_reference.txt"

def main():
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    print("Creating RAG corpus 'black-library-40k-corpus' in us-east1...")
    try:
        corpus = rag.create_corpus(
            display_name="black-library-40k-corpus",
            embedding_model_config=rag.EmbeddingModelConfig(
                publisher_model="publishers/google/models/text-embedding-005"
            ),
        )
        print(f"CORPUS_NAME={corpus.name}")
    except Exception as e:
        print(f"Error creating corpus in {LOCATION}: {e}")
        # Try us-central1 as fallback
        LOCATION_ALT = "us-central1"
        print(f"Trying fallback location {LOCATION_ALT}...")
        vertexai.init(project=PROJECT_ID, location=LOCATION_ALT)
        corpus = rag.create_corpus(
            display_name="black-library-40k-corpus",
            embedding_model_config=rag.EmbeddingModelConfig(
                publisher_model="publishers/google/models/text-embedding-005"
            ),
        )
        print(f"CORPUS_NAME={corpus.name}")

    print(f"Importing document from {GCS_PATH}...")
    resp = rag.import_files(
        corpus_name=corpus.name,
        paths=[GCS_PATH],
        transformation_config=rag.TransformationConfig(
            chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
        ),
    )
    print(f"Import finished. Imported files: {resp.imported_rag_files_count}")

if __name__ == "__main__":
    main()
