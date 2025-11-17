import os
import time
import threading
from flask import Flask, request, jsonify
import telebot


# =======================================================
# CONFIGURAÇÕES (usando variáveis do Render)
# =======================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
INTERVALO_ENVIO = 30 # segundos


if not BOT_TOKEN:
raise Exception("BOT_TOKEN não configurado no Render")
if not CHAT_ID:
raise Exception("CHAT_ID não configurado no Render")


CHAT_ID = int(CHAT_ID) # garantir número


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
# FORMATA MENSAGEM
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
# LOOP DE ENVIO AUTOMÁTICO (SEM ERROS DUPLOS)
# =======================================================
def loop_cupons():
i = 0
while True:
try:
cupom = CUPONS[i % len(CUPONS)]
msg = formatar_cupom(cupom)
bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
app.run(host='0.0.0.0', port=port)
