import os
import time
import threading
from flask import Flask, request, jsonify
import telebot

# ================================
# CONFIGURAÇÕES
# ================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
INTERVALO_ENVIO = 30  # segundos entre cupons

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN não configurado!")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ================================
# CUPONS PADRÃO
# ================================
CUPONS = [
    {
        "titulo": "🔥 OFERTA RELÂMPAGO!",
        "descricao": "Cupom válido por tempo LIMITADO!",
        "cupom": "DESCONTO10",
        "detalhes": "Use e ganhe 10% OFF em qualquer produto da loja."
    },
    {
        "titulo": "💥 SUPER DESCONTO EXCLUSIVO",
        "descricao": "Os melhores preços você só vê aqui!",
        "cupom": "LOUCURA20",
        "detalhes": "Ganhe 20% OFF direto no carrinho!"
    },
    {
        "titulo": "🎁 CUPOM PREMIADO",
        "descricao": "Somente seguidores VIP recebem esse presente!",
        "cupom": "VIP30",
        "detalhes": "30% OFF para os primeiros 50 usos!"
    }
]

# ================================
# FORMATADOR DE CUPONS
# ================================
def formatar_cupom(data):
    return (
        f"{data['titulo']}\n"
        f"{data['descricao']}\n\n"
        f"🎟 CUPOM: *{data['cupom']}*\n"
        f"📌 Detalhes: {data['detalhes']}\n"
        f"⏰ Aproveite enquanto ainda está ativo!"
    )

# ================================
# LOOP DE ENVIO AUTOMÁTICO
# ================================
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
            print("ERRO AO ENVIAR CUPOM:", e)
            time.sleep(5)


threading.Thread(target=loop_cupons, daemon=True).start()

# ================================
# API PARA ADICIONAR CUPONS
# ================================
@app.route('/add', methods=['POST'])
def add_cupom():
    data = request.get_json()

    required = ["titulo", "descricao", "cupom", "detalhes"]
    if not data or not all(k in data for k in required):
        return jsonify({"error": "Campos incompletos"}), 400

    CUPONS.append(data)
    return jsonify({"status": "Cupom adicionado com sucesso!"})

# ================================
# HOME
# ================================
@app.route('/')
def home():
    return "Bot de cupons está rodando!"

# ================================
# INICIAR SERVIDOR
# ================================
if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
