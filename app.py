import os
def formatar_cupom(data):
return (
f"{data['titulo']}
"
f"{data['descricao']}


"
f"🎟 CUPOM: *{data['cupom']}*
"
f"📌 Detalhes: {data['detalhes']}
"
f"⏰ Aproveite enquanto ainda está ativo!"
)


# =======================================================
# LOOP DE ENVIO AUTOMÁTICO
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
print(f"ERRO AO ENVIAR CUPOM: {e}")
time.sleep(5)


threading.Thread(target=loop_cupons, daemon=True).start()


# =======================================================
# ROTA PARA ADICIONAR CUPONS VIA INSOMNIA
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


# =======================================================
# HOME
# =======================================================
@app.route('/')
def home():
return "Bot avançado de cupons rodando!"


# =======================================================
# INICIAR FLASK (NECESSÁRIO PARA RENDER)
# =======================================================
if __name__ == '__main__':
port = int(os.getenv('PORT', 5000))
app.run(host='0.0.0.0', port=port)
