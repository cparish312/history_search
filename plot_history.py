import gc
import numpy as np
from datetime import datetime, timedelta

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

import utils
from chromadb_tools import get_chroma_collection, chroma_search_results_to_df, ingest_browser_history

gc.collect()

# chroma_collection = get_chroma_collection(collection_name="browser_history")
chroma_collection = get_chroma_collection(collection_name="history_full_text")
history = utils.get_browser_history()
# ingest_browser_history(history)

now_utc = datetime.utcnow()

yesterday_start = (now_utc - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
yesterday_end = yesterday_start + timedelta(days=1, microseconds=-1)

yesterday_start_timestamp = int(yesterday_start.timestamp())
yesterday_end_timestamp = int(yesterday_end.timestamp())

def search_history(text, distance_threshold=0.5, top_n=2000, time_bin="M"):
    if text is None or text == "":
        results_history = history.copy()
    else:
        chroma_search_results = chroma_collection.query(
                query_texts=[text],
                n_results=top_n,
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

def get_clusters(time_bin="H"):
    chroma_get_res = chroma_collection.get(include=['embeddings', 'documents'], 
                                           where={"timestamp" : {"$gte": yesterday_start_timestamp}})
    print(yesterday_start_timestamp)
    if len(chroma_get_res['ids']) == 0:
        print("No chroma results")
        return []
    
    url_hashes = list(int(i) for i in chroma_get_res['ids'])
    title_embeddings = np.array(chroma_get_res['embeddings'])

    embeddings_standardized = StandardScaler().fit_transform(title_embeddings)
    kmeansModel = KMeans(n_clusters=4).fit(embeddings_standardized)
    url_to_cluster = {u : c for u, c in zip(url_hashes, kmeansModel.labels_)}
    results_history = history.loc[history['url_hash'].isin(url_hashes)]
    results_history['cluster'] = results_history['url_hash'].map(url_to_cluster)

    results_history['time_bin'] = results_history['datetime_local'].dt.to_period(time_bin)
    month_url_counts = results_history.groupby(['time_bin', 'cluster']).agg(
                                            num_urls=('url', 'count'),       
                                            urls=('url', list),
                                            titles=('title', list)        
                                        ).reset_index()
    data_points = [(t, n, u, titles, c) for t, n, u, titles, c in zip(month_url_counts['time_bin'], month_url_counts['num_urls'], month_url_counts['urls'], month_url_counts['titles'], month_url_counts['cluster'])]
    print("Data points", len(data_points))
    return data_points
