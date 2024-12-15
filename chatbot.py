import pyodbc
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
import pandas as pd
import numpy as np

database_path = r"J:\Projetos\Chatbot\FAQS_LIMPOS.mdb" 
conn_str = (
    r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
    rf"DBQ={database_path};"
)

def load_faqs_from_db():
    """
    Carrega a tabela FAQS do banco Access em um DataFrame.
    """
    try:
        conn = pyodbc.connect(conn_str)
        query = "SELECT * FROM FAQS"
        faqs_df = pd.read_sql(query, conn)
        conn.close()
        return faqs_df
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return pd.DataFrame()

faqs_df = load_faqs_from_db()

def preprocess_text(text):
    if not isinstance(text, str):
        return ""
    return ' '.join(text.replace("\n", " ").strip().lower().split())

faqs_df['ERRO'] = faqs_df['ERRO'].apply(preprocess_text)
faqs_df['SOLUCAO'] = faqs_df['SOLUCAO'].apply(preprocess_text)

tokenizer = AutoTokenizer.from_pretrained("neuralmind/bert-base-portuguese-cased")
model = AutoModel.from_pretrained("neuralmind/bert-base-portuguese-cased")

def get_embedding(text, output_dim=128):
    if not isinstance(text, str) or not text.strip():
        return torch.zeros(output_dim)
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=128)
    with torch.no_grad():
        outputs = model(**inputs)
    embedding = outputs.last_hidden_state.mean(dim=1).squeeze()
    if embedding.size(0) > output_dim:
        return embedding[:output_dim]
    elif embedding.size(0) < output_dim:
        return torch.cat([embedding, torch.zeros(output_dim - embedding.size(0))])
    return embedding

faqs_df['embedding'] = faqs_df['ERRO'].apply(get_embedding)

def find_top_5(query, similarity_threshold=0.2):
    """
    Encontra as Top 5 FAQs mais relevantes com base em uma consulta e um limiar de similaridade.
    """
    query = preprocess_text(query)
    query_embedding = get_embedding(query)

    if query_embedding.size(0) != 128:
        raise ValueError("Dimensão do query_embedding é inconsistente.")

    query_embedding = normalize(query_embedding.unsqueeze(0).numpy(), axis=1)
    faqs_df['normalized_embedding'] = faqs_df['embedding'].apply(
        lambda x: normalize(x.unsqueeze(0).numpy(), axis=1).squeeze(0)
    )

    faqs_df['similarity'] = faqs_df['normalized_embedding'].apply(
        lambda emb: cosine_similarity(query_embedding, emb.reshape(1, -1)).item()
    )

    faqs_sorted = faqs_df.sort_values(by='similarity', ascending=False)
    faqs_top = faqs_sorted[faqs_sorted['similarity'] >= similarity_threshold].head(10)

    if not faqs_top.empty:
        return faqs_top[['ERRO', 'SOLUCAO', 'similarity']].to_dict(orient='records')
    else:
        return None

