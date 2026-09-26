import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = {
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "arvis_support.sqlite3"))

# Change this list without changing the bot logic.
SERVERS = [
    "Server 1", "Server 2", "Server 3", "Server 4",
    "Server 5", "Server 6", "Server 7", "Server 8",
]

CATEGORIES = [
    ("tech", "🛠 Технічна проблема"),
    ("account", "👤 Проблема з акаунтом"),
    ("donate", "💰 Донат"),
    ("game", "🎮 Проблема в грі"),
    ("bug", "🐛 Повідомити про баг"),
    ("complaint", "🚨 Скарга"),
    ("other", "💬 Інше питання"),
]

STATUS_NEW = "new"
STATUS_WORKING = "working"
STATUS_CLOSED = "closed"

STATUS_LABELS = {
    STATUS_NEW: "🟡 Новий",
    STATUS_WORKING: "🟢 В роботі",
    STATUS_CLOSED: "🔴 Закритий",
}

CATEGORY_LABELS = dict(CATEGORIES)
