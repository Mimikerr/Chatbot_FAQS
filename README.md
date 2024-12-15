# Chatbot_FAQS
##Funcionalidades
Responde perguntas com base nos dados do FAQ.

Seleciona as 3 respostas mais relevantes da base e utiliza o ChatGPT para escolher ou combinar a melhor.

Salva respostas no cache (cache.csv) apenas se receberem feedback positivo.

Permite que usuários forneçam feedback (positivo ou negativo) para melhorar a qualidade das respostas.

Interface responsiva para interação com o chatbot.

Requisitos de Instalação
Certifique-se de ter instalado o Python 3.8 ou superior.

Instale as Bibliotecas Necessárias: Execute o seguinte comando para instalar todas as dependências do projeto:

bash

pip install flask torch transformers pandas scikit-learn pyodbc openai
Configuração Adicional:

Banco de Dados: Certifique-se de ter o Microsoft Access instalado ou o driver ODBC correto configurado no sistema para acesso ao arquivo FAQS_LIMPOS.mdb.
API GPT: Obtenha uma chave API válida do OpenAI em https://platform.openai.com/ e insira no arquivo app.py:
python
openai.api_key = "SUA_API_KEY"
Driver ODBC: Verifique se o driver Microsoft Access Driver (*.mdb, *.accdb) está instalado no sistema.
Certifique-se do Espaço em Disco:

O modelo Hugging Face (neuralmind/bert-base-portuguese-cased) será baixado automaticamente, ocupando aproximadamente 500MB no cache.
Se tiver problemas com a instalação, entre em contato com o responsável técnico do projeto. 😊
