"""
Baby Monitor Telegram Bot для Render.com
Запускается на бесплатном тире Render.com
Принимает алерты от Baby Monitor и пересылает в Telegram

Deploy: см. render.yaml
"""
import os
import logging
import requests
from flask import Flask, request, jsonify
from threading import Lock

# ==========================================
# Конфигурация
# ==========================================
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8685994443:AAFO69GPT2uGkKV32nprc-NZBIqV-N60HNA')
ALLOWED_TOKEN = os.getenv('ALERT_TOKEN', 'baby-monitor-secret-2024')
TELEGRAM_API = f'https://api.telegram.org/bot{BOT_TOKEN}'

app = Flask(__name__)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Хранилище chat_id пользователей
chat_ids = set()
chat_ids_lock = Lock()

# ==========================================
# Telegram API
# ==========================================
def send_telegram(chat_id, text, parse_mode='HTML'):
    """Отправка сообщения в Telegram"""
    url = f'{TELEGRAM_API}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': parse_mode
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        logger.error(f'Telegram send error: {e}')
        return False

def send_telegram_photo(chat_id, photo_bytes, caption=''):
    """Отправка фото в Telegram"""
    url = f'{TELEGRAM_API}/sendPhoto'
    files = {'photo': ('alert.jpg', photo_bytes, 'image/jpeg')}
    data = {'chat_id': chat_id, 'caption': caption}
    try:
        resp = requests.post(url, files=files, data=data, timeout=15)
        return resp.status_code == 200
    except Exception as e:
        logger.error(f'Telegram photo error: {e}')
        return False

# ==========================================
# Webhook от Telegram
# ==========================================
@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработка обновлений от Telegram"""
    data = request.get_json()

    if not data or 'message' not in data:
        return jsonify({'ok': True})

    message = data['message']
    chat_id = message.get('chat', {}).get('id')
    text = message.get('text', '')
    user = message.get('from', {})

    if not chat_id:
        return jsonify({'ok': True})

    # Сохраняем chat_id
    with chat_ids_lock:
        chat_ids.add(chat_id)

    logger.info(f'Message from {user.get("first_name", "?")} ({chat_id}): {text}')

    # Обработка команд
    if text == '/start':
        send_telegram(chat_id,
            '🍼 <b>Baby Monitor Bot</b>\n\n'
            'Я пересылаю уведомления от Baby Monitor.\n\n'
            'Команды:\n'
            '/status - статус мониторинга\n'
            '/test - тестовое уведомление\n'
            '/help - помощь'
        )
    elif text == '/status':
        send_telegram(chat_id, '✅ Baby Monitor Bot активен\n'
                               f'Подключено чатов: {len(chat_ids)}')
    elif text == '/test':
        send_telegram(chat_id,
            '🧪 <b>Тестовое уведомление</b>\n\n'
            'Если вы видите это - бот работает!'
        )
    elif text == '/help':
        send_telegram(chat_id,
            '📖 <b>Помощь</b>\n\n'
            'Этот бот пересылает уведомления от Baby Monitor.\n\n'
            'Baby Monitor отправляет алерты на этот сервер,\n'
            'а сервер пересылает их вам в Telegram.\n\n'
            'Номер вашего чата: <code>' + str(chat_id) + '</code>'
        )
    else:
        send_telegram(chat_id, f'Неизвестная команда: {text}\nВведите /help')

    return jsonify({'ok': True})

# ==========================================
# API для Baby Monitor
# ==========================================
@app.route('/alert', methods=['POST'])
def alert():
    """Получение алерта от Baby Monitor"""
    # Проверка токена
    token = request.headers.get('X-Alert-Token', '')
    if token != ALLOWED_TOKEN:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400

    title = data.get('title', 'Baby Monitor Alert')
    message = data.get('message', '')
    photo_b64 = data.get('photo')  # base64 encoded JPEG

    # Формируем сообщение
    text = f'🚨 <b>{title}</b>\n\n{message}\n\n⏰ {__import__("datetime").datetime.now().strftime("%H:%M:%S")}'

    # Отправляем всем подключенным чатам
    sent = 0
    with chat_ids_lock:
        targets = list(chat_ids)

    for cid in targets:
        if send_telegram(cid, text):
            sent += 1

    logger.info(f'Alert sent to {sent}/{len(targets)} chats')
    return jsonify({'ok': True, 'sent': sent})

@app.route('/status', methods=['GET'])
def status():
    """Статус бота"""
    return jsonify({
        'status': 'ok',
        'connected_chats': len(chat_ids),
        'chat_ids': list(chat_ids)
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint для keep-alive"""
    return jsonify({'status': 'ok', 'timestamp': __import__('time').time()})

@app.route('/', methods=['GET'])
def index():
    """Корневой маршрут"""
    return jsonify({
        'name': 'Baby Monitor Bot',
        'status': 'running',
        'endpoints': {
            '/webhook': 'POST - Telegram webhook',
            '/alert': 'POST - Receive alerts from Baby Monitor',
            '/status': 'GET - Bot status',
            '/health': 'GET - Health check (keep-alive)'
        }
    })

# ==========================================
# Настройка Webhook
# ==========================================
@app.route('/setup-webhook', methods=['POST'])
def setup_webhook():
    """Настройка webhook для Telegram (вызывается при деплое)"""
    data = request.get_json()
    render_url = data.get('url', '')

    if not render_url:
        return jsonify({'error': 'No URL provided'}), 400

    webhook_url = f'{render_url}/webhook'
    url = f'{TELEGRAM_API}/setWebhook'
    payload = {'url': webhook_url}

    try:
        resp = requests.post(url, json=payload, timeout=10)
        result = resp.json()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
