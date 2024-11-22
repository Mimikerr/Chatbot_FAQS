from flask import Flask, render_template, request, jsonify
import openai
import pandas as pd
import csv
import os
from chatbot import find_top_3, faqs_df

CACHE_FILE = "cache.csv"
app = Flask(__name__)

openai.api_key = "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"

def load_cache():
    cache = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                cache[row['Pergunta'].strip().lower()] = {
                    "resposta": row['Resposta'].strip(),
                    "positivos": int(row['Feedback_Positivo']),
                    "total": int(row['Feedback_Total']),
                }
    return cache

def save_to_cache(question, answer, positive_feedback=0, total_feedback=0):
    cache = load_cache()
    question = question.strip().lower()
    cache[question] = {
        "resposta": answer.strip(),
        "positivos": positive_feedback,
        "total": total_feedback,
    }
    with open(CACHE_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["Pergunta", "Resposta", "Feedback_Positivo", "Feedback_Total"])
        writer.writeheader()
        for q, data in cache.items():
            writer.writerow({
                "Pergunta": q,
                "Resposta": data["resposta"],
                "Feedback_Positivo": data["positivos"],
                "Feedback_Total": data["total"],
            })
def process_with_chatgpt(query):
    top_3 = find_top_3(query)
    if not top_3:
        return "Desculpe, não encontramos nada relacionado a essa pergunta no FAQ."

    print("\nTop 3 FAQs selecionadas para a pergunta:")
    for faq in top_3:
        print(f"Pergunta: {faq['ERRO']}\nResposta: {faq['SOLUCAO']}\nSimilaridade: {faq['similarity']:.2f}\n")

    prompt = (
        f"Aqui estão as 3 perguntas mais relevantes do FAQ:\n\n"
        f"{top_3}\n\n"
        f"Pergunta do usuário: {query}\n\n"
        f"Baseado nisso, gere uma resposta clara e útil utilizando apenas as informacoes dos faqs."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é o chatbot do suporte técnico da empresa."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=325
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Erro ao processar a pergunta com ChatGPT: {e}")
        return "Desculpe, houve um erro ao processar sua pergunta."
print(find_top_3)
@app.route('/')
def home():
    return render_template("index.html")

@app.route('/ask', methods=['POST'])
def ask():
    query = request.get_json().get('question', '').strip().lower()
    if not query:
        return jsonify({'solution': "Por favor, envie uma pergunta válida!"})

    cache = load_cache()
    if query in cache:
        data = cache[query]
        if data["positivos"] / data["total"] * 100 >= 70:
            return jsonify({'solution': data["resposta"]})
    solution = process_with_chatgpt(query)
    save_to_cache(query, solution)
    return jsonify({'solution': solution})

@app.route('/feedback', methods=['POST'])
def feedback():
    data = request.get_json()
    question = data.get('question', '').strip().lower()
    feedback = data.get('feedback', '').strip().lower()

    if not question or feedback not in ['sim', 'não']:
        return jsonify({'status': 'Erro: Dados inválidos.'}), 400

    cache = load_cache()
    if question in cache:
        entry = cache[question]
        entry['total'] += 1
        if feedback == 'sim':
            entry['positivos'] += 1
        save_to_cache(question, entry['resposta'], entry['positivos'], entry['total'])
        return jsonify({'status': 'Feedback salvo com sucesso!'})
    else:
        return jsonify({'status': 'Erro: Pergunta não encontrada no cache.'}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
