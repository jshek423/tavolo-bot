import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# 設定日誌
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 讀取環境變數
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
KIMI_API_KEY = os.getenv("KIMI_API_KEY")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL") or "https://tavolo-bot.onrender.com/webhook"
PORT = int(os.getenv("PORT", 8443))

# 初始化 Kimi 客戶端
client = OpenAI(
    api_key=KIMI_API_KEY,
    base_url="https://api.moonshot.cn/v1"
)

# 儲存對話歷史
user_histories = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("你好！我是 Tavolo 智能助手。有什麼可以幫你？")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    
    if user_id not in user_histories:
        user_histories[user_id] = [
            {"role": "system", "content": "你是 Tavolo Kids Living 的智能客服助手，專業友善，使用繁體中文回答。公司主營高品質兒童家具，提供送貨安裝服務。"}
        ]
    
    user_histories[user_id].append({"role": "user", "content": user_message})
    
    try:
        response = client.chat.completions.create(
            model="moonshot-v1-8k",
            messages=user_histories[user_id],
            temperature=0.7
        )
        
        ai_reply = response.choices[0].message.content
        user_histories[user_id].append({"role": "assistant", "content": ai_reply})
        
        # 限制歷史長度
        if len(user_histories[user_id]) > 20:
            user_histories[user_id] = user_histories[user_id][-20:]
        
        await update.message.reply_text(ai_reply)
        
    except Exception as e:
        logger.error(f"Kimi API Error: {e}")
        await update.message.reply_text("抱歉，處理時出現問題，請稍後再試。")

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # 判斷環境：Render 用 Webhook，本地用 Polling
    if RENDER_EXTERNAL_URL:
        logger.info(f"Starting webhook on {RENDER_EXTERNAL_URL}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"{RENDER_EXTERNAL_URL}/webhook",
            secret_token=os.getenv("WEBHOOK_SECRET", "tavolo-secret")  # 可選：增加安全性
        )
    else:
        logger.info("Starting polling (local development)")
        application.run_polling()

if __name__ == "__main__":
    main()




