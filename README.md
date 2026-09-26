# Arvis Online Support Bot

Повноцінний Telegram-бот технічної підтримки Arvis Online на Python + python-telegram-bot + SQLite.

## Можливості

- профіль гравця з сервером, номером аккаунта та нікнеймом;
- SQLite збереження користувачів, тикетів, повідомлень, операторів та історії;
- унікальні номери `#ARVIS-0001`, `#ARVIS-0002` тощо;
- категорії звернень;
- статуси: 🟡 Новий / 🟢 В роботі / 🔴 Закритий;
- адміністративна панель тільки для `ADMIN_IDS`;
- взяття тикета оператором у роботу;
- двосторонній чат;
- текст, фото, відео, документи та анімації;
- історія повідомлень;
- пошук за номером тикета, Telegram ID, нікнеймом, номером аккаунта або сервером;
- статистика;
- збереження даних після перезапуску;
- polling, без веб-сервера.

## Важливо про Telegram-бота

Username `@ArvisOnlineSupportBot` можна встановити в BotFather, якщо він доступний. Назву бота встановіть як `Arvis Online Support`.

Не вставляйте токен у Python-файли та не надсилайте його в чат. Він зберігається тільки у `.env`.

## Запуск на Android / Termux

### 1. Встановити Termux

Рекомендовано використовувати актуальний Termux з надійного джерела.

### 2. Перейти в папку

Розпакуйте ZIP, відкрийте Termux і виконайте:

```bash
cd ~/storage/downloads/arvis_online_support_bot
```

Якщо Termux ще не має доступу до сховища:

```bash
termux-setup-storage
```

### 3. Python

```bash
pkg update -y
pkg install python -y
```

Перевірка:

```bash
python --version
```

### 4. Встановити залежності

```bash
pip install -r requirements.txt
```

### 5. Створити `.env`

```bash
cp .env.example .env
nano .env
```

Вкажіть:

```env
BOT_TOKEN=ТОКЕН_ВІД_BOTFATHER
ADMIN_IDS=123456789,987654321
DB_PATH=arvis_support.sqlite3
```

`ADMIN_IDS` — Telegram ID операторів через кому.

Токен не потрібно передавати розробнику або ChatGPT.

### 6. Запуск

```bash
python bot.py
```

У консолі має з'явитися повідомлення про запуск.

Відкрийте Telegram, знайдіть бота та введіть:

```text
/start
```

### 7. Перезапуск

Зупинити:

```text
CTRL+C
```

Запустити знову:

```bash
python bot.py
```

SQLite-файл `arvis_support.sqlite3` не видаляйте — у ньому зберігаються користувачі, тикети та історія.

### 8. Запуск у фоні

Найпростіший варіант:

```bash
nohup python bot.py > bot.log 2>&1 &
```

Перевірити лог:

```bash
tail -f bot.log
```

Знайти процес:

```bash
ps -A | grep python
```

Зупинити конкретний процес:

```bash
kill PID
```

Для довготривалої роботи Android може присипляти Termux. Для стабільної роботи не обмежуйте Termux у налаштуваннях батареї Android. За потреби використовуйте `tmux`:

```bash
pkg install tmux -y
tmux
python bot.py
```

Від'єднатися від сесії:

```text
CTRL+B, потім D
```

Повернутися:

```bash
tmux attach
```

## Додавання серверів

Відкрийте `config.py` і змініть:

```python
SERVERS = [
    "Server 1",
    "Server 2",
    "Server 3",
    "Server 4",
    "Server 5",
    "Server 6",
    "Server 7",
    "Server 8",
]
```

Кількість серверів не прив'язана до логіки бази даних.

## Додавання адміністратора

Є два способи.

1. Додати ID у `.env`:

```env
ADMIN_IDS=123456789,987654321
```

2. Після запуску можна також використовувати функції SQLite, якщо ви адмініструєте базу вручну.

При старті бот автоматично синхронізує ID з `ADMIN_IDS` у таблицю `admins`.

## Безпека

- `.env` не додавайте у Git;
- не публікуйте `arvis_support.sqlite3`, якщо база містить персональні дані;
- не публікуйте Telegram ID та історію тикетів;
- після компрометації токена відкличте його через BotFather і створіть новий.


## Поведінка після перезапуску

SQLite зберігає профілі, тикети, повідомлення та статуси. Якщо гравець після перезапуску бота надсилає повідомлення без повторного відкриття меню, бот автоматично прив'язує його до останнього незакритого тикета цього гравця.

## Структура

```text
arvis_online_support_bot/
├── bot.py
├── config.py
├── database.py
├── requirements.txt
├── .env.example
├── README.md
├── handlers/
│   ├── start.py
│   ├── profile.py
│   ├── tickets.py
│   ├── admin.py
│   └── messages.py
├── keyboards/
│   ├── user.py
│   └── admin.py
└── services/
    ├── ticket_service.py
    └── message_service.py
```

## Перевірка

Після встановлення залежностей:

```bash
python -m compileall .
```

Команда не повинна показувати SyntaxError.

Потім:

```bash
python bot.py
```

Бот працює через polling і не потребує відкритого порту на телефоні.
