import os
import threading
import tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from faster_whisper import WhisperModel

from app.agent.inventory_agent import ask_agent
from app.database.connection import SessionLocal
from app.services.telegram_idempotency_service import (
    start_update,
    complete_update,
    fail_update,
)


load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))


# ================================================================
# WHISPER SPEECH-TO-TEXT MODEL
# ================================================================

print("Loading Whisper speech recognition model...")

whisper_model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8",
)

print("Whisper model loaded successfully.")


# ================================================================
# RENDER HEALTH SERVER
# ================================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        self.send_response(200)

        self.send_header(
            "Content-type",
            "text/plain",
        )

        self.end_headers()

        self.wfile.write(
            b"KiranaAI Telegram bot is running."
        )

    def log_message(self, format, *args):
        return


def start_health_server():

    server = HTTPServer(
        ("0.0.0.0", PORT),
        HealthHandler,
    )

    print(
        f"Health server running on port {PORT}"
    )

    server.serve_forever()


# ================================================================
# START COMMAND
# ================================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await update.message.reply_text(
        "👋 Welcome to KiranaAI!\n\n"
        "Your grocery store assistant is ready.\n\n"
        "You can send:\n"
        "• Text messages\n"
        "• Voice messages 🎤"
    )


# ================================================================
# VOICE MESSAGE HANDLER
# ================================================================

async def handle_voice(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.message is None:
        return

    print("🎤 VOICE MESSAGE RECEIVED")

    await update.message.reply_text(
        "🎤 I received your voice message.\n"
        "Let me understand it..."
    )

    temp_path = None

    try:

        # ========================================================
        # GET TELEGRAM VOICE FILE
        # ========================================================

        voice = update.message.voice

        if voice is None:

            print("No voice object found.")

            return

        print(
            f"Voice file ID: {voice.file_id}"
        )

        telegram_file = await context.bot.get_file(
            voice.file_id
        )

        # ========================================================
        # CREATE TEMPORARY AUDIO FILE
        # ========================================================

        with tempfile.NamedTemporaryFile(
            suffix=".ogg",
            delete=False,
        ) as temp_file:

            temp_path = temp_file.name

        print(
            f"Downloading voice to: {temp_path}"
        )

        # ========================================================
        # DOWNLOAD VOICE FILE
        # ========================================================

        await telegram_file.download_to_drive(
            custom_path=temp_path
        )

        print(
            "Voice file downloaded successfully."
        )

        # ========================================================
        # WHISPER TRANSCRIPTION
        # ========================================================

        print(
            "Starting Whisper transcription..."
        )

        segments, info = whisper_model.transcribe(
            temp_path,
            language="en",
            beam_size=5,
            vad_filter=True,
        )

        transcript_parts = []

        for segment in segments:

            text = segment.text.strip()

            if text:

                transcript_parts.append(text)

        message = " ".join(
            transcript_parts
        ).strip()

        print(
            f"🎤 TRANSCRIBED TEXT: {message}"
        )

        # ========================================================
        # EMPTY TRANSCRIPTION
        # ========================================================

        if not message:

            await update.message.reply_text(
                "Sorry, I couldn't understand "
                "your voice message.\n\n"
                "Please try speaking again."
            )

            return

        # ========================================================
        # SHOW TRANSCRIPTION
        # ========================================================

        await update.message.reply_text(
            f"📝 I understood:\n\n"
            f"{message}"
        )

        # ========================================================
        # PROCESS USING EXISTING AI AGENT
        # ========================================================

        print(
            f"Sending voice transcription to agent: "
            f"{message}"
        )

        response = ask_agent(message)

        print(
            f"Agent response: {response}"
        )

        # ========================================================
        # SEND GENERATED INVOICE PDF
        # ========================================================

        if response.startswith(
            "__INVOICE__:"
        ):

            pdf_path = response.replace(
                "__INVOICE__:",
                "",
                1,
            ).strip()

            if not os.path.exists(
                pdf_path
            ):

                await update.message.reply_text(
                    "Sorry, the invoice PDF "
                    "could not be found."
                )

                return

            with open(
                pdf_path,
                "rb",
            ) as pdf_file:

                await update.message.reply_document(
                    document=pdf_file,
                    filename=os.path.basename(
                        pdf_path
                    ),
                    caption="🧾 KiranaAI GST Invoice",
                )

            return

        # ========================================================
        # SEND GENERATED ANALYSIS PPTX
        # ========================================================

        if response.startswith(
            "__ANALYSIS_DECK__:"
        ):

            pptx_path = response.replace(
                "__ANALYSIS_DECK__:",
                "",
                1,
            ).strip()

            if not os.path.exists(
                pptx_path
            ):

                await update.message.reply_text(
                    "Sorry, the weekly analysis deck "
                    "could not be found."
                )

                return

            with open(
                pptx_path,
                "rb",
            ) as pptx_file:

                await update.message.reply_document(
                    document=pptx_file,
                    filename=os.path.basename(
                        pptx_path
                    ),
                    caption=(
                        "📊 KiranaAI "
                        "Weekly Sales Analysis"
                    ),
                )

            return

        # ========================================================
        # NORMAL AGENT RESPONSE
        # ========================================================

        await update.message.reply_text(
            response
        )

    except Exception as e:

        print(
            "❌ VOICE ERROR:",
            repr(e),
        )

        await update.message.reply_text(
            "Sorry, I couldn't process "
            "your voice message."
        )

    finally:

        # ========================================================
        # DELETE TEMPORARY AUDIO FILE
        # ========================================================

        if (
            temp_path
            and os.path.exists(temp_path)
        ):

            try:

                os.remove(temp_path)

                print(
                    "Temporary voice file deleted."
                )

            except Exception as cleanup_error:

                print(
                    "Could not delete temporary "
                    "voice file:",
                    cleanup_error,
                )


# ================================================================
# TEXT MESSAGE HANDLER
# ================================================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    # ============================================================
    # SAFETY CHECK
    # ============================================================

    if update.message is None:
        return

    message = update.message.text

    if not message:
        return

    print(
        f"Received text message: {message}"
    )

    # ============================================================
    # TELEGRAM UPDATE ID
    # ============================================================

    update_id = update.update_id

    db = SessionLocal()

    try:

        # ========================================================
        # IDEMPOTENCY CHECK
        # ========================================================

        should_process, saved_response = start_update(
            db=db,
            update_id=update_id,
        )

        # ========================================================
        # DUPLICATE UPDATE
        # ========================================================

        if not should_process:

            if saved_response is not None:

                print(
                    f"Duplicate Telegram update detected: "
                    f"{update_id}"
                )

                # ------------------------------------------------
                # SAVED INVOICE
                # ------------------------------------------------

                if saved_response.startswith(
                    "__INVOICE__:"
                ):

                    pdf_path = saved_response.replace(
                        "__INVOICE__:",
                        "",
                        1,
                    ).strip()

                    if not os.path.exists(
                        pdf_path
                    ):

                        await update.message.reply_text(
                            "The previous invoice file "
                            "could not be found."
                        )

                        return

                    with open(
                        pdf_path,
                        "rb",
                    ) as pdf_file:

                        await update.message.reply_document(
                            document=pdf_file,
                            filename=os.path.basename(
                                pdf_path
                            ),
                            caption=(
                                "🧾 KiranaAI GST Invoice"
                            ),
                        )

                    return

                # ------------------------------------------------
                # SAVED ANALYSIS DECK
                # ------------------------------------------------

                if saved_response.startswith(
                    "__ANALYSIS_DECK__:"
                ):

                    pptx_path = saved_response.replace(
                        "__ANALYSIS_DECK__:",
                        "",
                        1,
                    ).strip()

                    if not os.path.exists(
                        pptx_path
                    ):

                        await update.message.reply_text(
                            "The previous analysis deck "
                            "could not be found."
                        )

                        return

                    with open(
                        pptx_path,
                        "rb",
                    ) as pptx_file:

                        await update.message.reply_document(
                            document=pptx_file,
                            filename=os.path.basename(
                                pptx_path
                            ),
                            caption=(
                                "📊 KiranaAI "
                                "Weekly Sales Analysis"
                            ),
                        )

                    return

                # ------------------------------------------------
                # SAVED NORMAL RESPONSE
                # ------------------------------------------------

                await update.message.reply_text(
                    saved_response
                )

                return

            # ----------------------------------------------------
            # CURRENTLY PROCESSING
            # ----------------------------------------------------

            await update.message.reply_text(
                "⏳ This request is already being "
                "processed. Please wait."
            )

            return

        # ========================================================
        # PROCESS NEW TEXT UPDATE
        # ========================================================

        print(
            f"Processing Telegram update: {update_id}"
        )

        print(
            f"Sending message to AI agent: {message}"
        )

        response = ask_agent(message)

        print(
            f"Agent response: {response}"
        )

        # ========================================================
        # SAVE RESPONSE
        # ========================================================

        complete_update(
            db=db,
            update_id=update_id,
            response=response,
        )

        # ========================================================
        # SEND INVOICE PDF
        # ========================================================

        if response.startswith(
            "__INVOICE__:"
        ):

            pdf_path = response.replace(
                "__INVOICE__:",
                "",
                1,
            ).strip()

            if not os.path.exists(
                pdf_path
            ):

                await update.message.reply_text(
                    "Sorry, the invoice PDF "
                    "could not be found."
                )

                return

            with open(
                pdf_path,
                "rb",
            ) as pdf_file:

                await update.message.reply_document(
                    document=pdf_file,
                    filename=os.path.basename(
                        pdf_path
                    ),
                    caption="🧾 KiranaAI GST Invoice",
                )

            return

        # ========================================================
        # SEND ANALYSIS PPTX
        # ========================================================

        if response.startswith(
            "__ANALYSIS_DECK__:"
        ):

            pptx_path = response.replace(
                "__ANALYSIS_DECK__:",
                "",
                1,
            ).strip()

            if not os.path.exists(
                pptx_path
            ):

                await update.message.reply_text(
                    "Sorry, the weekly analysis deck "
                    "could not be found."
                )

                return

            with open(
                pptx_path,
                "rb",
            ) as pptx_file:

                await update.message.reply_document(
                    document=pptx_file,
                    filename=os.path.basename(
                        pptx_path
                    ),
                    caption=(
                        "📊 KiranaAI "
                        "Weekly Sales Analysis"
                    ),
                )

            return

        # ========================================================
        # NORMAL TEXT RESPONSE
        # ========================================================

        await update.message.reply_text(
            response
        )

    except Exception as e:

        db.rollback()

        try:

            fail_update(
                db=db,
                update_id=update_id,
            )

        except Exception as cleanup_error:

            print(
                "Unable to reset idempotency record:",
                cleanup_error,
            )

        print(
            "Agent error:",
            e,
        )

        await update.message.reply_text(
            "Sorry, I couldn't process that request."
        )

    finally:

        db.close()


# ================================================================
# MAIN
# ================================================================

def main():

    if not TOKEN:

        raise ValueError(
            "TELEGRAM_BOT_TOKEN is not configured."
        )

    # ============================================================
    # START RENDER HEALTH SERVER
    # ============================================================

    health_thread = threading.Thread(
        target=start_health_server,
        daemon=True,
    )

    health_thread.start()

    # ============================================================
    # TELEGRAM APPLICATION
    # ============================================================

    application = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    # ============================================================
    # START COMMAND
    # ============================================================

    application.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    # ============================================================
    # TEXT MESSAGES
    # ============================================================

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message,
        )
    )

    # ============================================================
    # VOICE MESSAGES
    # ============================================================

    application.add_handler(
        MessageHandler(
            filters.VOICE,
            handle_voice,
        )
    )

    # ============================================================
    # START BOT
    # ============================================================

    print(
        "KiranaAI Telegram bot is running..."
    )

    application.run_polling()


if __name__ == "__main__":
    main()
