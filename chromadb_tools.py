import os
import sqlite3
import shutil
import pandas as pd
from pathlib import Path

import chromadb
from chromadb import Documents, Embeddings, EmbeddingFunction

from mlx_embedding_models.embedding import EmbeddingModel

from utils import get_firefox_history

BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = BASE_DIR /  "data"
chromadb_path = os.path.join(DATA_DIR, "chromadb")

MLX_EMBDEDDING_MODEL = "bge-large"

class MLXEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model_id=MLX_EMBDEDDING_MODEL):
        self.embedding_model = EmbeddingModel.from_registry(model_id)

    def __call__(self, input: Documents) -> Embeddings:
        return self.embedding_model.encode(input).tolist()

def get_chroma_collection(collection_name="browser_history", model_id=MLX_EMBDEDDING_MODEL):
    """Returns chromadb collections."""
    embedding_function = MLXEmbeddingFunction(model_id=model_id)
    chroma_client = chromadb.PersistentClient(path=chromadb_path)
    chroma_collection = chroma_client.get_or_create_collection(collection_name, embedding_function=embedding_function)
    return chroma_collection

def chroma_search_results_to_df(chroma_search_results):
    """Converts results from chromadb query to a pandas DataFrame"""
    results_l = list()
    for i in range(len(chroma_search_results['ids'])):
        for j in range(len(chroma_search_results['ids'][i])):
            d = {"chroma_query_id" : i, "id" : chroma_search_results['ids'][i][j],
                 "distance" : chroma_search_results['distances'][i][j]}
            
            if chroma_search_results['embeddings']:
                d["embedding"] = chroma_search_results['embeddings'][i][j]
            if chroma_search_results['documents']:
                d["document"] = chroma_search_results['documents'][i][j]
            d.update(chroma_search_results['metadatas'][i][j])
            results_l.append(d)
    return pd.DataFrame(results_l)

def query_chroma(query_text: str, utc_milliseconds_start_date=None, utc_milliseconds_end_date=None, 
                 max_chroma_results=200, chroma_collection=None):
    """Queries chromadb with the query_text and the provided constraints.
    Args:
        query_text (str): Text to query chromadb of OCR results from user screenshots

    returns query results from chroma collection
    """
    chroma_collection = get_chroma_collection() if chroma_collection is None else chroma_collection

    conditions = []
    if utc_milliseconds_start_date is not None:
        conditions.append({"timestamp": {"$gte": int(utc_milliseconds_start_date)}})
    
    if utc_milliseconds_end_date is not None:
        conditions.append({"timestamp": {"$lte": int(utc_milliseconds_end_date)}})
    
    if len(conditions) > 1:
        chroma_search_results = chroma_collection.query(
            query_texts=[query_text],
            n_results=max_chroma_results,
            where={
                "$and": conditions
            }
        )
    elif len(conditions) == 1:
        chroma_search_results = chroma_collection.query(
            query_texts=[query_text],
            n_results=max_chroma_results,
            where=conditions[0]
        )
    else:
        chroma_search_results = chroma_collection.query(
            query_texts=[query_text],
            n_results=max_chroma_results,
        )
    return chroma_search_results

def get_browser_history_chromadb_metadata(row):
    metadata_d = {"url" : row['url'], "title" : row['title'], "timestamp" : row['last_visit_date'], 
            "visit_count" : row['visit_count'], "preview_image_url" : row["preview_image_url"]}
    metadata_d_cleaned = {} # Values cannot be None
    for k, v in metadata_d.items():
        if v is None:
            metadata_d_cleaned[k] = ""
        else:
            metadata_d_cleaned[k] = v
    return metadata_d_cleaned

def run_chroma_ingest(df, chroma_collection):
    documents = list()
    metadatas = list()
    ids = list()
    for i, row in df.iterrows():
        documents.append(row['title_description'])
        metadatas.append(get_browser_history_chromadb_metadata(row))
        ids.append(row['url'])

    if len(documents) == 0:
        return
    chroma_collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    print(f"Successfully added {len(documents)} documents to chromadb")

def run_chroma_ingest_batched(df, chroma_collection, batch_size=1000):
    """Runs chromadb ingest in a batched fashion to balance efficiency and reliability."""
    num_batches = len(df) // batch_size + (1 if len(df) % batch_size > 0 else 0)
    for i in range(num_batches):
        print("Batch", i)
        start_index = i * batch_size
        end_index = start_index + batch_size
        batch_df = df.iloc[start_index:end_index]
        run_chroma_ingest(df=batch_df, chroma_collection=chroma_collection)

def ingest_browser_history(history):
    news_collection = get_chroma_collection(collection_name="browser_history")
    ingested_urls = set(news_collection.get()['ids'])
    total_num_urls = len(history)
    history = history.loc[~(history['url'].isin(ingested_urls))]
    print(f"Ingesting {len(history)} new urls out of {total_num_urls} total urls")
    run_chroma_ingest_batched(history, news_collection)

if __name__ == "__main__":
    history_df = get_firefox_history()
    ingest_browser_history(history=history_df)