import asyncio
import feedparser
import os
import google.generativeai as genai
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# --- SOZLAMALAR ---
GEMINI_KEY = "AIzaSyDqNF9HEBEVmFmtcQAhZaHmkWCAWHcIhSI"
TELEGRAM_TOKEN = "7687147020:AAHg9Eil5eAG-GRK0_GkNEVnTUTTis0WJjk"
CHANNEL_ID = "@abduvoris404"
RSS_URL = "https://kun.uz/uz/news/category/tehnologiya/rss"
DB_FILE = "last_news.txt"  # Oxirgi linkni saqlash uchun
CHECK_INTERVAL = 1800  # 30 daqiqa (sekundlarda)

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
    """Gemini orqali postni chiroyli qilish"""
    prompt = (
        f"Quyidagi texnologik yangilikni o'zbek tilida, dasturchilar uchun "
        f"qiziqarli va professional Telegram posti ko'rinishida qayta yozib ber: \n\n"
        f"Sarlavha: {title}\nMa'lumot: {summary}"
    )
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return f"<b>{title}</b>\n\n{summary}"  # Xatolik bo'lsa xom holatda yuboradi


async def check_and_post():
    bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    print("Yangiliklar tekshirilmoqda...")
    feed = feedparser.parse(RSS_URL)

    if not feed.entries:
        await bot.session.close()
        return

    latest_news = feed.entries[0]
    latest_link = latest_news.link
    last_sent_link = get_last_sent_link()

    # Agar yangilik yangi bo'lsa (fayldagidan farq qilsa)
    if latest_link != last_sent_link:
        print(f"Yangi yangilik topildi: {latest_news.title}")

        final_text = await rewrite_with_ai(latest_news.title, latest_news.description)

        post_content = (
            f"🚀 <b>AI & Texno Yangiliklar</b>\n\n"
            f"{final_text}\n\n"
            f"🔗 <a href='{latest_link}'>Batafsil manbada</a>\n\n"
            f"#AI #Python #TechNews"
        )

        try:
            await bot.send_message(chat_id=CHANNEL_ID, text=post_content)
            save_last_sent_link(latest_link)  # Linkni eslab qolamiz
            print("✅ Kanalga muvaffaqiyatli yuborildi.")
        except Exception as e:
            print(f"❌ Telegram xatoligi: {e}")
    else:
        print("Yangi yangilik yo'q.")

    await bot.session.close()


async def main():
    print("🚀 Bot ishga tushdi! Avtomatik tekshirish yoqilgan.")
    while True:
        try:
            await check_and_post()
        except Exception as e:
            print(f"Kutilmagan xato: {e}")

        print(f"Kutish rejimi: {CHECK_INTERVAL} sekund...")
        await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())