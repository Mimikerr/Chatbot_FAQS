import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
import pandas as pd
import pyodbc
import numpy as np

database_path = "J:\\Projetos\\ChatBot\\FAQS_LIMPOS.mdb"
conn_str = (
    r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
    rf"DBQ={database_path};"
)
conn = pyodbc.connect(conn_str)
query = "SELECT * FROM FAQS"
faqs_df = pd.read_sql(query, conn)
conn.close()

tokenizer = AutoTokenizer.from_pretrained("neuralmind/bert-base-portuguese-cased")
model = AutoModel.from_pretrained("neuralmind/bert-base-portuguese-cased")

def preprocess_text(text):
    """
    Remove espaços extras, converte para minúsculas e trata o texto.
    """
    return ' '.join(text.strip().lower().split())

def get_embedding(text, output_dim=128):
    """
    Gera o embedding de uma string usando BERT e ajusta para a dimensão desejada.
    """
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

faqs_df['ERRO'] = faqs_df['ERRO'].fillna("").apply(preprocess_text)
faqs_df['embedding'] = faqs_df['ERRO'].apply(get_embedding)

def find_top_3(query, similarity_threshold=0.2):
    query = preprocess_text(query)
    query_embedding = get_embedding(query)

    if query_embedding.size(0) != 128:
        raise ValueError("Dimensão do query_embedding é inconsistente.")

    faqs_df_valid = faqs_df[faqs_df['embedding'].apply(lambda x: x.size(0) == 128)]

    query_embedding = normalize(query_embedding.unsqueeze(0).numpy(), axis=1)
    faqs_df_valid['embedding'] = faqs_df_valid['embedding'].apply(
        lambda x: normalize(x.unsqueeze(0).numpy(), axis=1).squeeze(0)
    )

    faqs_df_valid['similarity'] = faqs_df_valid['embedding'].apply(
        lambda emb: cosine_similarity(query_embedding, emb.reshape(1, -1)).item()
    )

    print("Consulta do usuário:", query)
    print("Similaridades calculadas:")
    for index, row in faqs_df_valid.iterrows():
        print(f"Pergunta: {row['ERRO']}, Similaridade: {row['similarity']:.4f}")

    faqs_sorted = faqs_df_valid.sort_values(by='similarity', ascending=False)
    faqs_top = faqs_sorted[faqs_sorted['similarity'] >= similarity_threshold].head(3)

    if not faqs_top.empty:
        return faqs_top[['ERRO', 'SOLUCAO', 'similarity']].to_dict(orient='records')
    else:
        return None
