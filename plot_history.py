import mlx
import gc
import pandas as pd
import numpy as np
import networkx as nx

from collections import defaultdict

import plotly.graph_objects as go

from mlx_embedding_models.embedding import EmbeddingModel
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from sklearn.metrics.pairwise import cosine_similarity, pairwise_distances

import utils
from chromadb_tools import get_chroma_collection, query_chroma, chroma_search_results_to_df, MLX_EMBDEDDING_MODEL
gc.collect()
mlx.core.metal.clear_cache()

chroma_collection = get_chroma_collection(collection_name="browser_history")
history = utils.get_firefox_history()

def create_initial_data_points():
    history['month_year'] = history['datetime_local'].dt.to_period('M')
    month_url_counts = history.groupby('month_year').agg(
                            num_urls=('url', 'count'),       
                            urls=('url', list),
                            titles=('title', list)    
                        ).reset_index()
    data_points = [(t, n, u, titles) for t, n, u, titles in zip(month_url_counts['month_year'], month_url_counts['num_urls'], month_url_counts['urls'], month_url_counts['titles'])]
    return data_points

def search_history(text, distance_threshold=0.5, top_n=2000, time_bin="M"):
    chroma_search_results = chroma_collection.query(
            query_texts=[text],
            n_results=top_n
    )
    results_df = chroma_search_results_to_df(chroma_search_results=chroma_search_results)
    results_df = results_df.loc[results_df['distance'] <= distance_threshold]

    results_history = history.loc[history['url'].isin(results_df['url'])]
    results_history['time_bin'] = results_history['datetime_local'].dt.to_period(time_bin)
    month_url_counts = results_history.groupby('time_bin').agg(
                                            num_urls=('url', 'count'),       
                                            urls=('url', list),
                                            titles=('title', list)        
                                        ).reset_index()
    data_points = [(t, n, u, titles) for t, n, u, titles in zip(month_url_counts['time_bin'], month_url_counts['num_urls'], month_url_counts['urls'], month_url_counts['titles'])]
    return data_points
