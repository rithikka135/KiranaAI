import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from app.agent.inventory_agent import ask_agent
from app.database.connection import SessionLocal
from app.services.telegram_idempotency_service import (
    start_update,
    complete_update,
    fail_update,
)


load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "👋 Welcome to KiranaAI!\n\n"
        "Your supermarket assistant is ready."
    )


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    # ------------------------------------------------
    # SAFETY CHECK
    # ------------------------------------------------

    if update.message is None:
        return

    message = update.message.text

    if not message:
        return

    # Telegram provides a unique update_id.
    update_id = update.update_id

    db = SessionLocal()

    try:

        # ------------------------------------------------
        # IDEMPOTENCY CHECK
        # ------------------------------------------------

        should_process, saved_response = start_update(
            db=db,
            update_id=update_id,
        )

        # ------------------------------------------------
        # DUPLICATE UPDATE
        # ------------------------------------------------

        if not should_process:

            # Already completed previously.
            if saved_response is not None:

                print(
                    f"Duplicate Telegram update detected: "
                    f"{update_id}"
                )

                # ----------------------------------------
                # SAVED INVOICE RESPONSE
                # ----------------------------------------

                if saved_response.startswith(
                    "__INVOICE__:"
                ):

                    pdf_path = saved_response.replace(
                        "__INVOICE__:",
                        "",
                        1,
                    ).strip()

                    if not os.path.exists(pdf_path):

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
                            caption="🧾 KiranaAI GST Invoice",
                        )

                    return

                # ----------------------------------------
                # SAVED ANALYSIS DECK RESPONSE
                # ----------------------------------------

                if saved_response.startswith(
                    "__ANALYSIS_DECK__:"
                ):

                    pptx_path = saved_response.replace(
                        "__ANALYSIS_DECK__:",
                        "",
                        1,
                    ).strip()

                    if not os.path.exists(pptx_path):

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

                # ----------------------------------------
                # SAVED NORMAL TEXT RESPONSE
                # ----------------------------------------

                await update.message.reply_text(
                    saved_response
                )

                return

            # ------------------------------------------------
            # UPDATE CURRENTLY PROCESSING
            # ------------------------------------------------

            await update.message.reply_text(
                "⏳ This request is already being processed. "
                "Please wait."
            )

            return

        # ------------------------------------------------
        # PROCESS NEW UPDATE
        # ------------------------------------------------

        print(
            f"Processing Telegram update: {update_id}"
        )

        response = ask_agent(message)

        print(
            f"Agent response: {response}"
        )

        # ------------------------------------------------
        # SAVE RESPONSE
        # ------------------------------------------------

        complete_update(
            db=db,
            update_id=update_id,
            response=response,
        )

        # ------------------------------------------------
        # SEND GENERATED INVOICE PDF
        # ------------------------------------------------

        if response.startswith(
            "__INVOICE__:"
        ):

            pdf_path = response.replace(
                "__INVOICE__:",
                "",
                1,
            ).strip()

            if not os.path.exists(pdf_path):

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

        # ------------------------------------------------
        # SEND GENERATED ANALYSIS PPTX
        # ------------------------------------------------

        if response.startswith(
            "__ANALYSIS_DECK__:"
        ):

            pptx_path = response.replace(
                "__ANALYSIS_DECK__:",
                "",
                1,
            ).strip()

            if not os.path.exists(pptx_path):

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

        # ------------------------------------------------
        # NORMAL TEXT RESPONSE
        # ------------------------------------------------

        await update.message.reply_text(
            response
        )

    # ------------------------------------------------
    # ERROR HANDLING
    # ------------------------------------------------

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

    # ------------------------------------------------
    # CLOSE DATABASE CONNECTION
    # ------------------------------------------------

    finally:

        db.close()


def main():

    if not TOKEN:

        raise ValueError(
            "TELEGRAM_BOT_TOKEN is not configured."
        )

    application = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message,
        )
    )

    print(
        "KiranaAI Telegram bot is running..."
    )

    application.run_polling()


if __name__ == "__main__":
    main()