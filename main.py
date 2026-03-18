import asyncio
import feedparser
import os
import google.generativeai as genai
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# --- SOZLAMALAR (GitHub Secrets'dan o'qiydi) ---
GEMINI_KEY = os.getenv("GEMINI_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = "@abduvoris404"  # Kanalingiz username'i
RSS_URL = "https://kun.uz/uz/news/category/tehnologiya/rss"
DB_FILE = "last_news.txt"

# Gemini konfiguratsiyasi
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')


def get_last_sent_link():
    """Fayldan oxirgi yuborilgan linkni o'qiydi"""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return f.read().strip()
    return None


def save_last_sent_link(link):
    """Yangi yuborilgan linkni faylga saqlaydi"""
    with open(DB_FILE, "w") as f:
        f.write(link)


async def rewrite_with_ai(title, summary):
    """Gemini orqali postni jozibali qilish"""
    prompt = (
        f"Quyidagi texnologik yangilikni o'zbek tilida, dasturchilar uchun "
        f"qiziqarli va professional Telegram posti ko'rinishida qayta yozib ber. "
        f"Emoji va chiroyli format ishlat: \n\n"
        f"Sarlavha: {title}\nMa'lumot: {summary}"
    )
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini xatosi: {e}")
        return f"<b>{title}</b>\n\n{summary}"


async def main():
    # Tokenlar mavjudligini tekshirish
    if not TELEGRAM_TOKEN or not GEMINI_KEY:
        print("XATO: Tokenlar topilmadi! GitHub Secrets'ni tekshiring.")
        return

    bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    print("Yangiliklar tekshirilmoqda...")
    feed = feedparser.parse(RSS_URL)

    if not feed.entries:
        print("Yangiliklar topilmadi.")
        await bot.session.close()
        return

    latest_news = feed.entries[0]
    latest_link = latest_news.link
    last_sent_link = get_last_sent_link()

    # Yangi yangilik bo'lsa
    if latest_link != last_sent_link:
        print(f"Yangi yangilik: {latest_news.title}")

        # AI orqali post tayyorlash
        final_text = await rewrite_with_ai(latest_news.title, latest_news.description)

        post_content = (
            f"🚀 <b>Yangi Texno-Xabar</b>\n\n"
            f"{final_text}\n\n"
            f"🔗 <a href='{latest_link}'>Batafsil manbada</a>\n\n"
            f"🤖 #AI #TechUz #Python"
        )

        try:
            await bot.send_message(chat_id=CHANNEL_ID, text=post_content)
            save_last_sent_link(latest_link)
            print("✅ Post yuborildi!")
        except Exception as e:
            print(f"❌ Telegram xatosi: {e}")
    else:
        print("Yangi yangilik yo'q.")

    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())