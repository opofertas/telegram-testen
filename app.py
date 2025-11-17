import os
import time
import threading
from flask import Flask, request, jsonify
import telebot

# =======================================================
# CONFIGURAÇÕES GERAIS
# =======================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
INTERVALO_ENVIO = 30  # tempo entre cupons

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# =======================================================
# LISTA DE CUPONS PERSONALIZADOS
# =======================================================
CUPONS = [
    {
        "titulo": "🔥 OFERTA RELÂMPAGO!",
        "descricao": "Cupom válido por tempo LIMITADO!",
        "cupom": "DESCONTO10",
        "detalhes": "Use esse cupom para ganhar 10% OFF em qualquer produto da loja."
    },
    {
        "titulo": "💥 SUPER DESCONTO EXCLUSIVO",
        "descricao": "Os melhores preços você só vê aqui!",
        "cupom": "LOUCURA20",
        "detalhes": "Aplique o cupom e ganhe 20% de desconto direto no carrinho."
    },
    {
        "titulo": "🎁 CUPOM PREMIADO",
        "descricao": "Somente os seguidores VIP recebem esse presente!",
        "cupom": "VIP30",
        "detalhes": "30% de desconto para os primeiros 50 usos! Corre!"
    }
]

# =======================================================
# FUNÇÃO DE FORMATAÇÃO DAS MENSAGENS
# =======================================================
def formatar_cupom(data):
    return (
        f"{data['titulo']}\n"
        f"{data['descricao']}\n\n"
        f"🎟 CUPOM: *{data['cupom']}*\n"
        f"📌 Detalhes: {data['detalhes']}\n"
        f"⏰ Aproveite enquanto ainda está ativo!"
    )

# =======================================================
# ENVIO AUTOMÁTICO EM LOOP
# =======================================================
def loop_cupons():
    i = 0
    while True:
        try:
            cupom = CUPONS[i % len(CUPONS)]
            msg = formatar_cupom(cupom)
            bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
            i += 1
            time.sleep(INTERVALO_ENVIO)
        except Exception as e:
            print(f"Erro ao enviar cupom: {e}")
            time.sleep(5)

# Inicia thread paralela
threading.Thread(target=loop_cupons, daemon=True).start()

# =======================================================
# ROTAS PARA PERMITIR EDIÇÃO VIA INSOMNIA
# =======================================================
@app.route('/add', methods=['POST'])
def add_cupom():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Envie JSON"}), 400

    required = ["titulo", "descricao", "cupom", "detalhes"]
    if not all(k in data for k in required):
        return jsonify({"error": "Campos faltando"}), 400

    CUPONS.append(data)
    return jsonify({"status": "Cupom adicionado com sucesso!"}), 200


@app.route('/')
def home():
    return "Bot avançado de cupons rodando!"


# =======================================================
# EXECUTA FLASK (necessário para o Render)
# =======================================================
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)