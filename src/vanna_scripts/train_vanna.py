import os
import json
from pathlib import Path
from dotenv import load_dotenv
from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
from vanna.openai.openai_chat import OpenAI_Chat
from config import OPENAI_API_KEY, OPENAI_MODEL, CHROMA_PERSISTENCE_DIRECTORY, CHROMA_COLLECTION_NAME

# Load environment variables
load_dotenv()

# Initialize Vanna with local ChromaDB and OpenAI
api_key = OPENAI_API_KEY
model_name = OPENAI_MODEL

if not api_key or not model_name:
    raise ValueError("Please set OPENAI_API_KEY and OPENAI_MODEL in your .env file")

class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)

# Initialize Vanna with local configuration
vn = MyVanna(config={
    'api_key': api_key,
    'model': model_name,
    'collection_name': CHROMA_COLLECTION_NAME,
    'persist_directory': CHROMA_PERSISTENCE_DIRECTORY
})

def train_all():
    """Execute all training steps in sequence."""
    print("Starting Vanna training process...")
    
    # Training sources paths
    training_root = Path("data/training_sources")
    ddl_path = training_root / "ddl"
    docs_path = training_root / "documentation"
    queries_path = training_root / "example_queries"
    qa_pairs_path = training_root / "qa_pairs"
    
    # Train DDL statements
    print("\nTraining DDL statements...")
    for sql_file in ddl_path.glob("*.sql"):
        with open(sql_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                try:
                    vn.train(ddl=content)
                    print(f"✓ Trained DDL from {sql_file.name}")
                except Exception as e:
                    print(f"✗ Error training DDL from {sql_file.name}: {e}")
    
    # Train documentation
    print("\nTraining documentation...")
    for doc_file in docs_path.glob("*.md"):
        with open(doc_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                try:
                    vn.train(documentation=content)
                    print(f"✓ Trained documentation from {doc_file.name}")
                except Exception as e:
                    print(f"✗ Error training documentation from {doc_file.name}: {e}")
    
    # Train example queries
    print("\nTraining example queries...")
    for sql_file in queries_path.glob("*.sql"):
        with open(sql_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                try:
                    vn.train(sql=content)
                    print(f"✓ Trained query from {sql_file.name}")
                except Exception as e:
                    print(f"✗ Error training query from {sql_file.name}: {e}")
    
    # Train QA pairs
    print("\nTraining Q&A pairs...")
    for json_file in qa_pairs_path.glob("*.json"):
        with open(json_file, 'r', encoding='utf-8') as f:
            qa_pairs = json.load(f)
            for pair in qa_pairs:
                try:
                    vn.train(question=pair['question'], sql=pair['sql'])
                    print(f"✓ Trained Q&A pair from {json_file.name}: {pair['question'][:50]}...")
                except Exception as e:
                    print(f"✗ Error training Q&A pair from {json_file.name}: {e}")
    
    print("\nTraining process completed!")

if __name__ == "__main__":
    train_all() 