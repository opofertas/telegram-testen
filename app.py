import os
import time
import threading
import random
import logging
import requests
from flask import Flask, request, jsonify
import telebot

# ---------------------------
# Config / Environment
# ---------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "real-time-amazon-data.p.rapidapi.com")

# Intervalo aleatório em segundos (60 a 180)
MIN_INTERVAL = int(os.getenv("MIN_INTERVAL", 60))
MAX_INTERVAL = int(os.getenv("MAX_INTERVAL", 180))

# Lista fixa de palavras-chave (eletrônicos / peças de PC)
KEYWORDS = [
    "ssd",
    "placa de video",
    "processador ryzen",
    "processador intel",
    "memoria ram",
    "fonte 80 plus",
    "monitor gamer",
    "placa mae",
    "hd ssd nvme",
    "cooler cpu",
    "gabinete gamer",
    "ssd 1tb",
    "rx 6600",
    "geforce gtx 1660",
    "ssd nvme 500gb"
]

# Filtro mínimo de desconto (%) para considerar "promoção real" (opcional)
MIN_DISCOUNT_PERCENT = float(os.getenv("MIN_DISCOUNT_PERCENT", 0.0))  # 0 = qualquer cupom/desconto

# ---------------------------
# Validations
# ---------------------------
if not BOT_TOKEN:
    raise Exception("BOT_TOKEN não configurado!")
if not CHAT_ID:
    raise Exception("CHAT_ID não configurado!")
if not RAPIDAPI_KEY:
    raise Exception("RAPIDAPI_KEY não configurado! (adicione no Render)")

try:
    CHAT_ID = int(CHAT_ID)
except Exception:
    raise Exception("CHAT_ID inválido. Deve ser número, ex: -1001234567890")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ---------------------------
# Helpers de API (RapidAPI - Amazon)
# ---------------------------
SEARCH_ENDPOINT = f"https://{RAPIDAPI_HOST}/search"
PRODUCT_ENDPOINT = f"https://{RAPIDAPI_HOST}/product-details"  # caso queira detalhes por ASIN

HEADERS = {
    "x-rapidapi-host": RAPIDAPI_HOST,
    "x-rapidapi-key": RAPIDAPI_KEY
}

def search_amazon(keyword, country="US", page=1):
    """Faz uma busca simples por keyword. Retorna JSON ou None."""
    try:
        params = {"keyword": keyword, "country": country, "page": page}
        resp = requests.get(SEARCH_ENDPOINT, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logging.warning("Erro na search_amazon: %s", e)
        return None

def extract_products_from_search(json_data):
    """Tenta extrair uma lista de produtos do JSON retornado pela API.
       A resposta varia conforme a API; tentamos várias chaves comuns."""
    if not json_data:
        return []
    # Possíveis nomes de campos onde podem vir os produtos
    for key in ("results", "products", "items", "data", "searchResults"):
        if key in json_data and isinstance(json_data[key], list):
            return json_data[key]
    # fallback: se a própria resposta já é lista
    if isinstance(json_data, list):
        return json_data
    # tentativas adicionais: procurar por qualquer lista interna
    for v in json_data.values() if isinstance(json_data, dict) else []:
        if isinstance(v, list):
            return v
    return []

def normalize_product(prod):
    """Tenta extrair título, price, original_price, coupon, link de um objeto produto (flexível)."""
    title = prod.get("title") or prod.get("name") or prod.get("product_title") or prod.get("titleText") or ""
    # preços
    price = None
    original_price = None
    for k in ("price", "current_price", "price_string", "priceFormatted", "offer_price"):
        if k in prod and prod[k]:
            price = prod[k]
            break
    for k in ("original_price", "list_price", "previous_price", "strike_price", "price_old"):
        if k in prod and prod[k]:
            original_price = prod[k]
            break
    # coupon / discount
    coupon = prod.get("coupon") or prod.get("discount") or prod.get("promo") or prod.get("deal")
    # link
    link = prod.get("link") or prod.get("url") or prod.get("product_url") or prod.get("detailPageURL")
    # try asin to build link if missing
    asin = prod.get("asin") or prod.get("ASIN")
    if not link and asin:
        link = f"https://www.amazon.com/dp/{asin}"
    # normalize price strings (keep as-is, but ensure strings)
    price_str = str(price) if price is not None else ""
    orig_str = str(original_price) if original_price is not None else ""
    return {
        "title": title.strip(),
        "price": price_str,
        "original_price": orig_str,
        "coupon": coupon if coupon else None,
        "link": link if link else None,
        "raw": prod
    }

def is_promo_real(prod):
    """Decide se é promoção real: cupom presente OR preço < original_price com desconto minimo."""
    if prod.get("coupon"):
        return True
    try:
        p = float(''.join(c for c in prod.get("price","") if (c.isdigit() or c=='.' or c==',' )).replace(',','.'))
        o = prod.get("original_price","")
        if o:
            o_f = float(''.join(c for c in o if (c.isdigit() or c=='.' or c==',' )).replace(',','.'))
            if o_f > 0:
                discount_percent = (o_f - p) / o_f * 100
                if discount_percent >= MIN_DISCOUNT_PERCENT:
                    return True
    except Exception:
        # se parsing falhar, não bloqueamos caso já tenha cupom
        pass
    return False

# ---------------------------
# Loop principal (envio)
# ---------------------------
def choose_and_send():
    """Escolhe uma keyword aleatória, busca, filtra e envia um produto se houver promoção real."""
    keyword = random.choice(KEYWORDS)
    logging.info("Buscando por keyword: %s", keyword)
    data = search_amazon(keyword)
    prods = extract_products_from_search(data)
    random.shuffle(prods)  # embaralha pra não sempre pegar o primeiro
    for p in prods:
        normalized = normalize_product(p)
        # se não tiver título ou link ou price, ignora
        if not normalized["title"] or not normalized["link"] or not normalized["price"]:
            continue
        if is_promo_real(normalized):
            # Formata a mensagem simples
            title = normalized["title"]
            price = normalized["price"]
            coupon = normalized["coupon"] or "—"
            link = normalized["link"]
            msg = f"{title}\nPreço: {price}\nCupom: {coupon}\nLink: {link}"
            try:
                bot.send_message(CHAT_ID, msg)
                logging.info("Enviado cupom: %s | %s", title, coupon)
                return True  # enviou um produto, finaliza ciclo atual
            except Exception as e:
                logging.warning("Erro ao enviar mensagem: %s", e)
                return False
    logging.info("Nenhuma promoção real encontrada para keyword: %s", keyword)
    return False

def loop_worker():
    while True:
        try:
            sent = choose_and_send()
            # sleep aleatório entre MIN_INTERVAL e MAX_INTERVAL
            wait = random.uniform(MIN_INTERVAL, MAX_INTERVAL)
            logging.info("Aguardando %.1f segundos até próxima tentativa", wait)
            time.sleep(wait)
        except Exception as e:
            logging.exception("Erro no loop_worker: %s", e)
            time.sleep(10)

# inicia thread do loop
threading.Thread(target=loop_worker, daemon=True).start()

# ---------------------------
# Rotas HTTP (insomnia)
# ---------------------------
@app.route('/', methods=['GET'])
def home():
    return "Bot Amazon de cupons rodando!"

@app.route('/add', methods=['POST'])
def add_cupom():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Envie JSON"}), 400
    required = ["titulo", "descricao", "cupom", "detalhes"]
    if not all(k in data for k in required):
        return jsonify({"error": "Campos faltando"}), 400
    # Mantém compatibilidade: adiciona à fila de CUPONS CUSTOMIZADOS (memória)
    # Caso queira interoperar com SEARCH, mantemos uma lista simples.
    # Aqui apenas confirmamos recebimento.
    return jsonify({"status": "Recebido (mas neste modo o bot prioriza promoções Amazon)"}), 200

# ---------------------------
# Run
# ---------------------------
if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
