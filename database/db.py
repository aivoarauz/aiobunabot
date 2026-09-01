import aiosqlite
import os
from datetime import datetime
from config import DATABASE_PATH, DEFAULT_GEMINI_PRICE, DEFAULT_CHANNEL_PRICE, DEFAULT_CHANNEL_LINK, REFERRAL_THRESHOLD

os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                referrer_id INTEGER,
                referrals_count INTEGER DEFAULT 0,
                joined_at TEXT,
                is_blocked INTEGER DEFAULT 0
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_number TEXT,
                card_owner TEXT,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price INTEGER NOT NULL,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                max_quantity INTEGER DEFAULT 10,
                created_at TEXT
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS subscription_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subscription_id INTEGER,
                link TEXT NOT NULL,
                is_used INTEGER DEFAULT 0,
                used_by INTEGER,
                used_at TEXT,
                FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                subscription_id INTEGER,
                quantity INTEGER DEFAULT 1,
                total_price INTEGER,
                status TEXT DEFAULT 'pending',  -- pending, waiting_check, confirmed, rejected, cancelled
                check_file_id TEXT,
                links_sent TEXT,
                created_at TEXT,
                confirmed_at TEXT,
                admin_id INTEGER
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                text TEXT,
                rating INTEGER DEFAULT 5,
                created_at TEXT,
                is_approved INTEGER DEFAULT 1
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                total_earned INTEGER DEFAULT 0,
                total_orders INTEGER DEFAULT 0,
                total_users INTEGER DEFAULT 0
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS referral_rewards (
                user_id INTEGER PRIMARY KEY,
                claimed INTEGER DEFAULT 0,
                notified INTEGER DEFAULT 0
            )
        """)
        
        # Default settings
        defaults = {
            "gemini_price": str(DEFAULT_GEMINI_PRICE),
            "channel_price": str(DEFAULT_CHANNEL_PRICE),
            "channel_link": DEFAULT_CHANNEL_LINK,
            "referral_threshold": str(REFERRAL_THRESHOLD),
            "referral_message": "Tabriklaymiz! Siz botga 10 ta odam qo'shdingiz. Adminga yozing: @{admin}",
            "help_text": "Yordam uchun adminga yozing: @{admin}",
            "welcome_text": "Assalomu alaykum! 👋\nAIVORA obuna botiga xush kelibsiz!",
            "gemini_info": """Obunaga nimalar kiradi?🤔
✅ Gemini Pro — matn yozish, tarjima qilish, dasturlash, tahlil va kundalik ishlar uchun kuchli AI yordamchi. 🧠✨
⭐ Antigravity — kod yozish, kodni tahlil qilish va murakkab dasturlash vazifalari uchun. 💻⚙️
✅ Flow — AI yordamida video yaratish. 🎬 Har oy 1000 ta kredit beriladi. 🎁
🟠 Nano Banana — rasmlar yaratish va ularni AI yordamida tahrirlash. 🎨🖌️
✅️ Veo 3 — yuqori sifatli va realistlik AI videolar yaratish. 📷🚀
✅ NotebookLM — PDF, Word va boshqa hujjatlar bilan ishlash, konspekt tuzish va savollarga javob olish. 📚🗒
✅ 5 TB xotira ⬇️
Kimlar uchun? 👇
👨‍🎓 Talabalar
🖥 Dasturchilar
🖌 Dizaynerlar
📈 Marketologlar va SMM mutaxassislari
🎥 Kontent yaratuvchilar
📱Amerika Yutubda AI Videolar Qilib Pul Ishlaydiganlar uchun✅
🚀 AI imkoniyatlaridan maksimal foydalanishni istagan har bir kishi.""",
            "guide_text": """📖 YO'RIQNOMA

1️⃣ Kanalga obuna bo'ling: @aivora_uz
2️⃣ Kerakli obunani tanlang
3️⃣ Miqdorni tanlang (1-10)
4️⃣ Kartaga to'lov qiling
5️⃣ Chek rasmini yuboring
6️⃣ Admin tasdiqlagach link olasiz

❗ Har bir link faqat 1 marta beriladi.
📞 Yordam: @{admin}""",
            "required_channel": "@aivora_uz",
            "admin_username": "ABDRFV_11"
        }
        
        for key, value in defaults.items():
            await db.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
        
        # Default subscriptions
        async with db.execute("SELECT COUNT(*) FROM subscriptions") as cursor:
            count = (await cursor.fetchone())[0]
        
        if count == 0:
            await db.execute(
                "INSERT INTO subscriptions (name, price, description, max_quantity, created_at) VALUES (?, ?, ?, ?, ?)",
                ("Gemini Pro", DEFAULT_GEMINI_PRICE, "Gemini Pro obunasi (1 oylik)", 10, datetime.now().isoformat())
            )
            await db.execute(
                "INSERT INTO subscriptions (name, price, description, max_quantity, created_at) VALUES (?, ?, ?, ?, ?)",
                ("AI Videolar Yopiq Kanal", DEFAULT_CHANNEL_PRICE, "AI videolar yaratishni o'rgatadigan yopiq kanal", 1, datetime.now().isoformat())
            )
            # Add default channel link
            await db.execute(
                "INSERT INTO subscription_links (subscription_id, link) VALUES (?, ?)",
                (2, DEFAULT_CHANNEL_LINK)
            )
        
        await db.execute("INSERT OR IGNORE INTO stats (id, total_earned, total_orders, total_users) VALUES (1, 0, 0, 0)")
        
        await db.commit()


async def get_setting(key: str, default: str = "") -> str:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else default


async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        await db.commit()


async def get_user(user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()


async def add_user(user_id: int, username: str, full_name: str, referrer_id: int = None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
            exists = await cursor.fetchone()
        
        if not exists:
            await db.execute(
                "INSERT INTO users (user_id, username, full_name, referrer_id, joined_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, full_name, referrer_id, datetime.now().isoformat())
            )
            await db.execute("UPDATE stats SET total_users = total_users + 1 WHERE id = 1")
            
            if referrer_id and referrer_id != user_id:
                await db.execute(
                    "UPDATE users SET referrals_count = referrals_count + 1 WHERE user_id = ?",
                    (referrer_id,)
                )
            await db.commit()
            return True
        return False


async def get_referrals_count(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT referrals_count FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def get_active_cards():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM cards WHERE is_active = 1") as cursor:
            return await cursor.fetchall()


async def add_card(card_number: str, card_owner: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO cards (card_number, card_owner, is_active) VALUES (?, ?, 1)",
            (card_number, card_owner)
        )
        await db.commit()


async def update_card(card_id: int, card_number: str = None, card_owner: str = None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        if card_number:
            await db.execute("UPDATE cards SET card_number = ? WHERE id = ?", (card_number, card_id))
        if card_owner:
            await db.execute("UPDATE cards SET card_owner = ? WHERE id = ?", (card_owner, card_id))
        await db.commit()


async def delete_card(card_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM cards WHERE id = ?", (card_id,))
        await db.commit()


async def get_subscriptions(active_only: bool = True):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM subscriptions"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY id"
        async with db.execute(query) as cursor:
            return await cursor.fetchall()


async def get_subscription(sub_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM subscriptions WHERE id = ?", (sub_id,)) as cursor:
            return await cursor.fetchone()


async def add_subscription(name: str, price: int, description: str, max_quantity: int = 10):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO subscriptions (name, price, description, max_quantity, created_at) VALUES (?, ?, ?, ?, ?)",
            (name, price, description, max_quantity, datetime.now().isoformat())
        )
        await db.commit()
        return cursor.lastrowid


async def update_subscription(sub_id: int, name: str = None, price: int = None, description: str = None, is_active: int = None, max_quantity: int = None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        if name is not None:
            await db.execute("UPDATE subscriptions SET name = ? WHERE id = ?", (name, sub_id))
        if price is not None:
            await db.execute("UPDATE subscriptions SET price = ? WHERE id = ?", (price, sub_id))
        if description is not None:
            await db.execute("UPDATE subscriptions SET description = ? WHERE id = ?", (description, sub_id))
        if is_active is not None:
            await db.execute("UPDATE subscriptions SET is_active = ? WHERE id = ?", (is_active, sub_id))
        if max_quantity is not None:
            await db.execute("UPDATE subscriptions SET max_quantity = ? WHERE id = ?", (max_quantity, sub_id))
        await db.commit()


async def add_subscription_links(sub_id: int, links: list):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        for link in links:
            link = link.strip()
            if link:
                await db.execute(
                    "INSERT INTO subscription_links (subscription_id, link) VALUES (?, ?)",
                    (sub_id, link)
                )
        await db.commit()


async def get_available_links_count(sub_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM subscription_links WHERE subscription_id = ? AND is_used = 0",
            (sub_id,)
        ) as cursor:
            return (await cursor.fetchone())[0]


async def get_and_mark_links(sub_id: int, quantity: int, user_id: int) -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, link FROM subscription_links WHERE subscription_id = ? AND is_used = 0 LIMIT ?",
            (sub_id, quantity)
        ) as cursor:
            rows = await cursor.fetchall()
        
        if len(rows) < quantity:
            return []
        
        links = []
        now = datetime.now().isoformat()
        for row in rows:
            await db.execute(
                "UPDATE subscription_links SET is_used = 1, used_by = ?, used_at = ? WHERE id = ?",
                (user_id, now, row["id"])
            )
            links.append(row["link"])
        await db.commit()
        return links


async def create_order(user_id: int, sub_id: int, quantity: int, total_price: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO orders (user_id, subscription_id, quantity, total_price, status, created_at) VALUES (?, ?, ?, ?, 'pending', ?)",
            (user_id, sub_id, quantity, total_price, datetime.now().isoformat())
        )
        await db.commit()
        return cursor.lastrowid


async def update_order(order_id: int, **kwargs):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        for key, value in kwargs.items():
            await db.execute(f"UPDATE orders SET {key} = ? WHERE id = ?", (value, order_id))
        await db.commit()


async def get_order(order_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)) as cursor:
            return await cursor.fetchone()


async def get_pending_orders():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM orders WHERE status IN ('pending', 'waiting_check') ORDER BY created_at DESC") as cursor:
            return await cursor.fetchall()


async def add_review(user_id: int, username: str, text: str, rating: int = 5):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO reviews (user_id, username, text, rating, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, username, text, rating, datetime.now().isoformat())
        )
        await db.commit()


async def get_reviews(limit: int = 20):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM reviews WHERE is_approved = 1 ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ) as cursor:
            return await cursor.fetchall()


async def get_stats():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM stats WHERE id = 1") as cursor:
            return await cursor.fetchone()


async def add_earned(amount: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE stats SET total_earned = total_earned + ?, total_orders = total_orders + 1 WHERE id = 1",
            (amount,)
        )
        await db.commit()


async def get_all_users_count() -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            return (await cursor.fetchone())[0]


async def get_users_list(limit: int = 100):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users ORDER BY joined_at DESC LIMIT ?", (limit,)) as cursor:
            return await cursor.fetchall()
