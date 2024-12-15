from flask import Flask, render_template, request, jsonify
from chatbot import find_top_5
import openai

app = Flask(__name__)

openai.api_key = "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"

def process_with_chatgpt(query):
    top_5 = find_top_5(query)
    if not top_5:
        return "Desculpe, não encontramos nada relacionado a essa pergunta no FAQ."

    print("\nTop 3 FAQs selecionadas:")
    for faq in top_5:
        print(f"Pergunta: {faq['ERRO']}, Similaridade: {faq['similarity']:.2f}")

    faqs_text = "\n\n".join(
        [f"Pergunta: {faq['ERRO']}\nResposta: {faq['SOLUCAO']}" for faq in top_5]
    )
    prompt = (
        f"Aqui estão as 3 perguntas mais relevantes do FAQ:\n\n"
        f"{faqs_text}\n\n"
        f"Pergunta do usuário: {query}\n\n"
        f"Baseado nisso,escolha a melhor e gere uma resposta clara, útil,mais humanizada e sem caracteres especias desnecessarios."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é o chatbot do suporte técnico da empresa."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=400
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Erro ao processar a pergunta com ChatGPT: {e}")
        return "Desculpe, houve um erro ao processar sua pergunta."

import csv
import os

CACHE_FILE = "cache_feedback.csv" 

def load_cache():
    """
    Carrega o cache de respostas e feedbacks do arquivo.
    """
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
    """
    Salva ou atualiza uma entrada no cache.
    """
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

@app.route('/feedback', methods=['POST'])
def feedback():
    """
    Recebe e processa o feedback do usuário.
    """
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



@app.route('/')
def home():
    return render_template("index.html")

@app.route('/ask', methods=['POST'])
def ask():
    query = request.get_json().get('question', '').strip()
    if not query:
        return jsonify({'solution': "Por favor, envie uma pergunta válida!"})

    try:
        cache = load_cache()

        
        if query in cache:
            data = cache[query]
            positivos, total = data["positivos"], data["total"]
            valid_percentage = (positivos / total) * 100 if total > 0 else 100

           
            if valid_percentage < 70:
                solution = process_with_chatgpt(query)
                save_to_cache(query, solution) 
            else:
                solution = data["resposta"]
        else:
            solution = process_with_chatgpt(query)
            save_to_cache(query, solution)  

        return jsonify({'solution': solution})
    except Exception as e:
        return jsonify({'solution': f"Erro ao processar a pergunta: {e}"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
