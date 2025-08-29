"""Telegram bot handlers for the Appeals Bot."""

import logging

from telegram import Update, Message
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from .config import config
from .database import get_db_manager, Appeal
from .services import unban_service
from .utils import format_user_mention, validate_appeal_text, format_datetime

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if not update.message or not update.effective_user:
        return

    welcome_message = """
🤖 **Бот F1News.ru для подачи апелляций**

Если вас заблокировали в нашей группе F1 и вы считаете это ошибкой, вы можете подать апелляцию здесь.

Используйте: `/appeal [ваше объяснение]`

**Пример:**
`/appeal Я обсуждал гоночную стратегию Хэмилтона, а не оскорблял. Это была просто страстная дискуссия о F1.`

Апелляции рассматриваются администраторами в течение 24 часов.

**Команды:**
• `/appeal [текст]` - Подать апелляцию
• `/status` - Проверить статус апелляций
• `/help` - Показать это справочное сообщение
    """

    await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)
    logger.info(f"Start command used by user {update.effective_user.id}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    await start_command(update, context)


async def appeal_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /appeal command."""
    if not update.message:
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Пожалуйста, предоставьте объяснение для апелляции.\n\n"
            "Пример: `/appeal Я обсуждал гоночную стратегию F1, а не оскорблял.`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    appeal_text = " ".join(context.args)
    await _handle_appeal_submission(update.message, context, appeal_text)


async def _handle_appeal_submission(
    message: Message, context: ContextTypes.DEFAULT_TYPE, appeal_text: str
) -> None:
    """Common logic for processing an appeal submission from a message."""
    user = message.from_user
    if not user:
        return

    user_id = user.id
    username = user.username
    first_name = user.first_name

    # Validate appeal text
    is_valid, error_msg = validate_appeal_text(appeal_text)
    if not is_valid:
        await message.reply_text(f"❌ {error_msg}")
        return

    # Check if user is actually banned in the main group
    try:
        chat_member = await context.bot.get_chat_member(config.main_group_id, user_id)
        if chat_member.status != "kicked":
            await message.reply_text(
                "ℹ️ Вы не заблокированы в группе F1News.ru. "
                "Апелляции могут подавать только заблокированные пользователи."
            )
            return
    except Exception as e:
        logger.error(f"Failed to check user ban status: {e}")
        await message.reply_text(
            "❌ Не удалось проверить ваш статус в группе. Попробуйте еще раз позже."
        )
        return

    # Check if user already has pending appeal
    existing_appeal = get_db_manager().get_pending_appeal(user_id)
    if existing_appeal:
        await message.reply_text(
            f"⏳ У вас уже есть незавершенная апелляция (#{existing_appeal.id}). "
            "Пожалуйста, дождитесь рассмотрения администратором."
        )
        return

    # Create new appeal
    appeal_data = {
        "user_id": user_id,
        "username": username,
        "first_name": first_name,
        "appeal_text": appeal_text,
    }

    try:
        appeal_id = get_db_manager().create_appeal(appeal_data)
        appeal = get_db_manager().get_appeal(appeal_id)  # Get the created appeal object

        # Notify user
        await message.reply_text(
            f"✅ Апелляция подана успешно!\nID апелляции: #{appeal_id}\n\n"
            "Администраторы рассмотрят ваше дело в течение 24 часов."
        )

        # Notify admins
        if appeal:  # Check if appeal is not None
            admin_message = _format_admin_notification(appeal_id, appeal)
            await context.bot.send_message(
                chat_id=config.admin_group_id,
                text=admin_message,
                parse_mode=ParseMode.MARKDOWN,
            )

        logger.info(f"Appeal #{appeal_id} created for user {user_id}")

    except Exception as e:
        logger.error(f"Failed to create appeal: {e}")
        await message.reply_text(
            "❌ Не удалось подать апелляцию. Попробуйте еще раз позже."
        )


async def edited_message_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """React to edits of messages; process edited /appeal submissions."""
    if not update.edited_message or not update.edited_message.text:
        return
    text = update.edited_message.text.strip()
    if not text.startswith("/appeal"):
        return

    # Extract text after the command, supporting forms like /appeal@BotName
    first_token = text.split(maxsplit=1)[0]
    appeal_text = text[len(first_token):].strip()

    if not appeal_text:
        await update.edited_message.reply_text(
            "❌ Пожалуйста, добавьте текст апелляции после команды `/appeal`.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    await _handle_appeal_submission(update.edited_message, context, appeal_text)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command."""
    if not update.effective_user or not update.message:
        return

    user_id = update.effective_user.id
    appeals = get_db_manager().get_user_appeals(user_id)

    if not appeals:
        await update.message.reply_text("У вас нет зарегистрированных апелляций.")
        return

    message = "📋 **Ваши апелляции:**\n\n"
    for appeal in appeals[:5]:  # Show last 5 appeals
        status_emoji = {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(
            appeal.status, "❓"
        )

        message += f"{status_emoji} **#{appeal.id}** - {appeal.status.title()}\n"
        message += f"📅 {format_datetime(appeal.created_at)}\n"
        if appeal.admin_decision:
            message += f"💬 {appeal.admin_decision}\n"
        message += "\n"

    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)


# Admin commands (only work in admin group)


async def approve_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /approve command (admin only)."""
    if not update.effective_chat or not update.message or not update.effective_user:
        return

    if update.effective_chat.id != config.admin_group_id:
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Укажите ID апелляции: `/approve 123`", parse_mode=ParseMode.MARKDOWN
        )
        return

    try:
        appeal_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Неверный ID апелляции.")
        return

    # Get appeal details
    appeal = get_db_manager().get_appeal(appeal_id)
    if not appeal:
        await update.message.reply_text("❌ Апелляция не найдена.")
        return

    if appeal.status != "pending":
        await update.message.reply_text(
            f"❌ Апелляция #{appeal_id} уже {appeal.status}."
        )
        return

    # Try to unban user using PTB API via service
    unban_result = await unban_service.unban_user(context.bot, appeal.user_id)

    if unban_result.get("ok"):
        # Update appeal status
        admin_decision = "Одобрена"
        success = get_db_manager().update_appeal_status(
            appeal_id, "approved", admin_decision
        )

        if success:
            await update.message.reply_text(
                f"✅ Апелляция #{appeal_id} одобрена. Пользователь {appeal.first_name} разблокирован."
            )

            # Notify user
            if appeal:  # Check if appeal is not None
                await _notify_user_decision(context, appeal, "approved", admin_decision)
        else:
            await update.message.reply_text("❌ Не удалось обновить статус апелляции.")
    else:
        error_msg = unban_result.get("description", "Unknown error")
        await update.message.reply_text(f"❌ Failed to unban user. Error: {error_msg}")


async def reject_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /reject command (admin only)."""
    if not update.effective_chat or not update.message or not update.effective_user:
        return

    if update.effective_chat.id != config.admin_group_id:
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Укажите ID апелляции: `/reject 123 [причина]`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    try:
        appeal_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Неверный ID апелляции.")
        return

    reason = (
        " ".join(context.args[1:]) if len(context.args) > 1 else "Причина не указана"
    )

    # Get appeal details
    appeal = get_db_manager().get_appeal(appeal_id)
    if not appeal:
        await update.message.reply_text("❌ Апелляция не найдена.")
        return

    if appeal.status != "pending":
        await update.message.reply_text(
            f"❌ Апелляция #{appeal_id} уже {appeal.status}."
        )
        return

    # Update appeal status
    # Do not expose admin identity to users; store neutral decision text only
    admin_decision = f"Отклонена: {reason}"
    success = get_db_manager().update_appeal_status(
        appeal_id, "rejected", admin_decision
    )

    if success:
        await update.message.reply_text(f"❌ Апелляция #{appeal_id} отклонена.")

        # Notify user
        if appeal:  # Check if appeal is not None
            await _notify_user_decision(context, appeal, "rejected", admin_decision)
    else:
        await update.message.reply_text("❌ Не удалось обновить статус апелляции.")


async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /info command (admin only)."""
    if not update.effective_chat or not update.message:
        return

    if update.effective_chat.id != config.admin_group_id:
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Please provide appeal ID: `/info 123`", parse_mode=ParseMode.MARKDOWN
        )
        return

    try:
        appeal_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Неверный ID апелляции.")
        return

    # Get appeal details
    appeal = get_db_manager().get_appeal(appeal_id)
    if not appeal:
        await update.message.reply_text("❌ Апелляция не найдена.")
        return

    info_message = _format_appeal_info(appeal)
    await update.message.reply_text(info_message, parse_mode=ParseMode.MARKDOWN)


async def pending_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /pending command (admin only)."""
    if not update.effective_chat or not update.message:
        return

    if update.effective_chat.id != config.admin_group_id:
        return

    pending_appeals = get_db_manager().get_pending_appeals()

    if not pending_appeals:
        await update.message.reply_text("✅ No pending appeals.")
        return

    message = "⏳ **Pending Appeals:**\n\n"
    for appeal in pending_appeals:
        user_mention = format_user_mention(appeal.first_name, appeal.username)
        message += (
            f"#{appeal.id} - {user_mention} - {format_datetime(appeal.created_at)}\n"
        )

    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command (admin only)."""
    if not update.effective_chat or not update.message:
        return

    if update.effective_chat.id != config.admin_group_id:
        return

    stats = get_db_manager().get_appeals_stats()

    message = (
        f"📊 **Appeals Statistics**\n\n**Total Appeals:** {stats.get('total', 0)}\n\n"
    )

    for status in ["pending", "approved", "rejected"]:
        count = stats.get(status, 0)
        if count > 0:
            emoji = {"pending": "⏳", "approved": "✅", "rejected": "❌"}[status]
            message += f"{emoji} **{status.title()}:** {count}\n"

    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)


# Helper functions


def _format_admin_notification(appeal_id: int, appeal: Appeal) -> str:
    """Format admin notification message."""
    user_mention = format_user_mention(appeal.first_name, appeal.username)

    return f"""
🆕 **Новая апелляция** #{appeal_id}

👤 **Пользователь:** {user_mention}
🆔 **ID:** `{appeal.user_id}`
📝 **Апелляция:** {appeal.appeal_text}

**Действия:**
• `/approve {appeal_id}` - Разблокировать пользователя
• `/reject {appeal_id} [причина]` - Отклонить апелляцию
• `/info {appeal_id}` - Подробности
    """


def _format_appeal_info(appeal: Appeal) -> str:
    """Format appeal information message."""
    user_mention = format_user_mention(appeal.first_name, appeal.username)

    info = f"""
📋 **Appeal #{appeal.id}**

👤 **User:** {user_mention}
🆔 **User ID:** `{appeal.user_id}`
📅 **Submitted:** {format_datetime(appeal.created_at)} UTC
📝 **Appeal Text:** {appeal.appeal_text}
🔄 **Status:** {appeal.status}
    """

    if appeal.admin_decision:
        info += f"⚖️ **Admin Decision:** {appeal.admin_decision}\n"

    if appeal.processed_at:
        info += (
            f"✅ **Processed:** {appeal.processed_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
        )

    return info


async def _notify_user_decision(
    context: ContextTypes.DEFAULT_TYPE,
    appeal: Appeal,
    decision: str,
    admin_decision: str,
) -> None:
    """Notify user about appeal decision."""
    try:
        if decision == "approved":
            message = f"""
✅ Отличные новости! Ваша апелляция #{appeal.id} была одобрена.

Теперь вы можете присоединиться к группе F1News.ru. Пожалуйста, соблюдайте правила сообщества.
            """
        else:  # rejected
            reason = (
                admin_decision.split(": ", 1)[1]
                if ": " in admin_decision
                else "Конкретная причина не указана"
            )
            message = f"""
❌ Ваша апелляция #{appeal.id} была отклонена.

**Причина:** {reason}

Вы можете подать новую апелляцию, если у вас есть дополнительная информация.
            """

        await context.bot.send_message(
            chat_id=appeal.user_id, text=message, parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        logger.error(f"Failed to notify user {appeal.user_id}: {e}")
