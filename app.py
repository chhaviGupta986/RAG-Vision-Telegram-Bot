import logging
import os

from dotenv import load_dotenv
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
os.environ["HF_TOKEN"] = HF_TOKEN  # do this before transformers imports/downloads

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from memory import MemoryStore
from rag import (
    answer_query,
    NoRelevantContextError,
    RagError,
    SummarizationError,
    summarize_text,
)
from vision import describe_image



memory = MemoryStore()
logger = logging.getLogger(__name__)

# ---------- COMMANDS ----------

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
Allowed Commands:
/ask <question> - Ask from knowledge base
/image - Upload an image after this command
/summarize - Summarize last response
/help - Show help
"""
    await update.message.reply_text(text)

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please provide a text query after /ask")
        return
    logger.info("Received /ask from %s", update.effective_user.id)
    query = " ".join(context.args)

    status = await update.message.reply_text("Searching the knowledge base for relevant passages...")

    async def _update_status(text: str) -> None:
        try:
            await status.edit_text(text)
        except BadRequest:
            pass

    def progress_callback(step: str) -> None:
        context.application.create_task(_update_status(step))

    history_entries = memory.get_last_n(update.effective_user.id, 3)
    conversation_history = [
        f"Q: {entry.get('query', '')} | A: {entry['text']}"
        for entry in history_entries
    ]

    try:
        try:
            response, sources = answer_query(
                query,
                progress_callback=progress_callback,
                conversation_history=conversation_history if conversation_history else None,
            )
        except NoRelevantContextError:
            await update.message.reply_text(
                "I couldn't find relevant information in the knowledge base."
            )
            return
        except RagError:
            logger.exception("Failed to answer query %s", query)
            await update.message.reply_text(
                "Sorry, I couldn't fetch an answer right now. Try again later."
            )
            return

        memory.store(update.effective_user.id, response, entry_type="chat", query=query)

        reply = f"{response}\n\nSources:\n" + "\n".join(sources)
        await update.message.reply_text(reply)
    except Exception:
        logger.exception("Unexpected /ask failure for %s", update.effective_user.id)
        await update.message.reply_text(
            "Sorry, something went wrong while processing your request."
        )
    finally:
        try:
            await status.delete()
        except BadRequest:
            pass

async def summarize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    last_entry = memory.get_last(update.effective_user.id)
    if not last_entry:
        await update.message.reply_text("No previous message to summarize. Try /ask with a question first.")
        return
    summary_input = f"{last_entry['type'].capitalize()}: {last_entry['text']}"
    logger.info("Summarizing last entry for %s", update.effective_user.id)
    status = await update.message.reply_text("📚 Gathering your last reply…")

    async def _update_status(text: str) -> None:
        try:
            await status.edit_text(text)
        except BadRequest:
            pass

    await _update_status("📝 Condensing your last reply into a bite-sized summary...")

    try:
        summary = summarize_text(summary_input)
    except SummarizationError:
        logger.exception("Summarize request failed for %s", update.effective_user.id)
        await status.edit_text("⚠️ Could not summarize that content. Please try again.")
        await status.delete()
        return
    except RagError:
        await status.edit_text("⚠️ Unable to summarize that content right now.")
        await status.delete()
        return

    await _update_status("✅ Summary ready! Sharing it now...")
    try:
        await status.delete()
    except BadRequest:
        pass
    await update.message.reply_text(
        "🎯 Summary of your last reply\n\n"
        f"{summary}"
    )
async def image_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting_image"] = True
    await update.message.reply_text("Please upload an image.")

# ---------- MESSAGE HANDLER ----------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # IMAGE FLOW
    if context.user_data.get("awaiting_image"):
        if update.message.photo:
            path = f"temp_{user_id}.jpg"
            try:
                file = await update.message.photo[-1].get_file()
                await file.download_to_drive(path)
                caption, tags = describe_image(path)
            except Exception:
                logger.exception("Failed to describe image for %s", user_id)
                await update.message.reply_text(
                    "I couldn't process that image. Please try again."
                )
                context.user_data["awaiting_image"] = False
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        logger.debug("Could not remove temp file %s", path)
                return

            memory.store(user_id, caption, entry_type="image")

            await update.message.reply_text(
                f"🔤 Caption: {caption}\n🔖 Tags: {', '.join(tags)}"
            )

            try:
                os.remove(path)
            except OSError:
                logger.debug("Could not remove temp file %s", path)
            context.user_data["awaiting_image"] = False
        else:
            await update.message.reply_text("Please upload an image, not text.")
        return

    # WRONG USAGE CASES
    if update.message.photo:
        await update.message.reply_text("Use /image before uploading an image.")
        return

    await update.message.reply_text("Use /help to see available commands.")

# ---------- MAIN ----------

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s:%(lineno)d %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("ask", ask))
    app.add_handler(CommandHandler("image", image_cmd))
    app.add_handler(CommandHandler("summarize", summarize))

    app.add_handler(MessageHandler(filters.ALL, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
