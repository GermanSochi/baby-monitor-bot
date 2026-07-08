# Деплой Baby Monitor Bot на Render.com

## Пошаговая инструкция

### 1. Создай аккаунт на Render.com
- Перейди на https://render.com
- Зарегистрируйся через GitHub/Google

### 2. Загрузи код на GitHub
```bash
cd C:\Claude\baby-monitor\render-bot
git init
git add .
git commit -m "Initial baby monitor bot"
git remote add origin https://github.com/ТВОЙ_USER/baby-monitor-bot.git
git push -u origin master
```

### 3. Создай сервис на Render
1. Нажми **New +** → **Web Service**
2. Подключи свой GitHub репозиторий `baby-monitor-bot`
3. Настрой:
   - **Name:** baby-monitor-bot
   - **Runtime:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn bot:app --bind 0.0.0.0:$PORT`

### 4. Добавь переменные окружения
В разделе **Environment** добавь:
- `TELEGRAM_BOT_TOKEN` = `8685994443:AAFO69GPT2uGkKV32nprc-NZBIqV-N60HNA`
- `ALERT_TOKEN` = `baby-monitor-secret-2024`

### 5. Задеплой
Нажми **Create Web Service**. Деплой займёт ~2 минуты.

### 6. Настрой Webhook
После деплоя получи URL (типа `https://baby-monitor-bot.onrender.com`)

Отправь POST запрос для настройки webhook:
```bash
curl -X POST https://baby-monitor-bot.onrender.com/setup-webhook \
  -H "Content-Type: application/json" \
  -d '{"url": "https://baby-monitor-bot.onrender.com"}'
```

### 7. Подпишись на бота
1. Открой Telegram
2. Найди своего бота
3. Нажми **Start**
4. Бот покажет твой **Chat ID**

### 8. Обнови конфиг Baby Monitor
В `config.py` заполни:
```python
RENDER_BOT_URL = "https://baby-monitor-bot.onrender.com"
RENDER_ALERT_TOKEN = "baby-monitor-secret-2024"
```

## Проверка
1. Открой https://baby-monitor-bot.onrender.com/status
2. Должно показать Connected chats: 1 (если подписался)
3. Отправь /test боту в Telegram
