"""Telegram bot handlers for the Appeals Bot."""

import logging
from typing import List

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from .config import config
from .database import get_db_manager, Appeal
from .utils import unban_service, format_user_mention, validate_appeal_text

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    welcome_message = """
🤖 **Бот F1News.ru для подачи апелляций**

Если вас заблокировали в нашей группе F1 и вы считаете это ошибкой, вы можете подать апелляцию здесь.

Используйте: `/appeal [ваше объяснение]`

**Пример:**
`/appeal Я обсуждал гоночную стратегию Хэмилтона, а не оскорблял. Мое сообщение могло показаться резким, но это была просто страстная дискуссия о F1.`

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
    if not context.args:
        await update.message.reply_text(
            "❌ Пожалуйста, предоставьте объяснение для апелляции.\n\n"
            "Пример: `/appeal Я обсуждал гоночную стратегию F1, а не оскорблял.`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    appeal_text = ' '.join(context.args)
    
    # Validate appeal text
    is_valid, error_msg = validate_appeal_text(appeal_text)
    if not is_valid:
        await update.message.reply_text(f"❌ {error_msg}")
        return
    
    # Check if user already has pending appeal
    existing_appeal = get_db_manager().get_pending_appeal(user_id)
    if existing_appeal:
        await update.message.reply_text(
            f"⏳ У вас уже есть незавершенная апелляция (#{existing_appeal.id}). "
            "Пожалуйста, дождитесь рассмотрения администратором."
        )
        return
    
    # Create new appeal
    appeal_data = {
        'user_id': user_id,
        'username': username,
        'first_name': first_name,
        'appeal_text': appeal_text
    }
    
    try:
        appeal_id = get_db_manager().create_appeal(appeal_data)
        appeal = get_db_manager().get_appeal(appeal_id)  # Get the created appeal object
        
        # Notify user
        await update.message.reply_text(
            f"✅ Апелляция подана успешно!\nID апелляции: #{appeal_id}\n\n"
            "Администраторы рассмотрят ваше дело в течение 24 часов."
        )
        
        # Notify admins
        admin_message = _format_admin_notification(appeal_id, appeal)
        await context.bot.send_message(
            chat_id=config.admin_group_id,
            text=admin_message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        logger.info(f"Appeal #{appeal_id} created for user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to create appeal: {e}")
        await update.message.reply_text(
            "❌ Не удалось подать апелляцию. Попробуйте еще раз позже."
        )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command."""
    user_id = update.effective_user.id
    appeals = get_db_manager().get_user_appeals(user_id)
    
    if not appeals:
        await update.message.reply_text("У вас нет зарегистрированных апелляций.")
        return
    
    message = "📋 **Ваши апелляции:**\n\n"
    for appeal in appeals[:5]:  # Show last 5 appeals
        status_emoji = {
            'pending': '⏳',
            'approved': '✅', 
            'rejected': '❌'
        }.get(appeal.status, '❓')
        
        message += f"{status_emoji} **#{appeal.id}** - {appeal.status.title()}\n"
        message += f"📅 {appeal.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        if appeal.admin_decision:
            message += f"💬 {appeal.admin_decision}\n"
        message += "\n"
    
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)


# Admin commands (only work in admin group)

async def approve_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /approve command (admin only)."""
    if update.effective_chat.id != config.admin_group_id:
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Укажите ID апелляции: `/approve 123`", 
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        appeal_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Неверный ID апелляции.")
        return
    
    admin_name = format_user_mention(
        update.effective_user.first_name,
        update.effective_user.username
    )
    
    # Get appeal details
    appeal = get_db_manager().get_appeal(appeal_id)
    if not appeal:
        await update.message.reply_text("❌ Апелляция не найдена.")
        return
    
    if appeal.status != 'pending':
        await update.message.reply_text(f"❌ Апелляция #{appeal_id} уже {appeal.status}.")
        return
    
    # Try to unban user
    unban_result = await unban_service.unban_user(appeal.user_id)
    
    if unban_result.get('ok'):
        # Update appeal status
        admin_decision = f"Одобрена {admin_name}"
        success = get_db_manager().update_appeal_status(appeal_id, 'approved', admin_decision)
        
        if success:
            await update.message.reply_text(
                f"✅ Апелляция #{appeal_id} одобрена. Пользователь {appeal.first_name} разблокирован."
            )
            
            # Notify user
            await _notify_user_decision(context, appeal, 'approved', admin_decision)
        else:
            await update.message.reply_text("❌ Не удалось обновить статус апелляции.")
    else:
        error_msg = unban_result.get('description', 'Unknown error')
        await update.message.reply_text(f"❌ Failed to unban user. Error: {error_msg}")


async def reject_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /reject command (admin only)."""
    if update.effective_chat.id != config.admin_group_id:
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Укажите ID апелляции: `/reject 123 [причина]`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        appeal_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Неверный ID апелляции.")
        return
    
    reason = ' '.join(context.args[1:]) if len(context.args) > 1 else 'Причина не указана'
    admin_name = format_user_mention(
        update.effective_user.first_name,
        update.effective_user.username
    )
    
    # Get appeal details
    appeal = get_db_manager().get_appeal(appeal_id)
    if not appeal:
        await update.message.reply_text("❌ Апелляция не найдена.")
        return
    
    if appeal.status != 'pending':
        await update.message.reply_text(f"❌ Апелляция #{appeal_id} уже {appeal.status}.")
        return
    
    # Update appeal status
    admin_decision = f"Отклонена {admin_name}: {reason}"
    success = get_db_manager().update_appeal_status(appeal_id, 'rejected', admin_decision)
    
    if success:
        await update.message.reply_text(f"❌ Апелляция #{appeal_id} отклонена.")
        
        # Notify user
        await _notify_user_decision(context, appeal, 'rejected', admin_decision)
    else:
        await update.message.reply_text("❌ Не удалось обновить статус апелляции.")


async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /info command (admin only)."""
    if update.effective_chat.id != config.admin_group_id:
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide appeal ID: `/info 123`",
            parse_mode=ParseMode.MARKDOWN
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
    if update.effective_chat.id != config.admin_group_id:
        return
    
    pending_appeals = get_db_manager().get_pending_appeals()
    
    if not pending_appeals:
        await update.message.reply_text("✅ No pending appeals.")
        return
    
    message = "⏳ **Pending Appeals:**\n\n"
    for appeal in pending_appeals:
        user_mention = format_user_mention(appeal.first_name, appeal.username)
        message += f"#{appeal.id} - {user_mention} - {appeal.created_at.strftime('%Y-%m-%d %H:%M')}\n"
    
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command (admin only)."""
    if update.effective_chat.id != config.admin_group_id:
        return
    
    stats = get_db_manager().get_appeals_stats()
    
    message = f"📊 **Appeals Statistics**\n\n**Total Appeals:** {stats.get('total', 0)}\n\n"
    
    for status in ['pending', 'approved', 'rejected']:
        count = stats.get(status, 0)
        if count > 0:
            emoji = {'pending': '⏳', 'approved': '✅', 'rejected': '❌'}[status]
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
📅 **Submitted:** {appeal.created_at.strftime('%Y-%m-%d %H:%M UTC')}
📝 **Appeal Text:** {appeal.appeal_text}
🔄 **Status:** {appeal.status}
    """
    
    if appeal.admin_decision:
        info += f"⚖️ **Admin Decision:** {appeal.admin_decision}\n"
    
    if appeal.processed_at:
        info += f"✅ **Processed:** {appeal.processed_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
    
    return info


async def _notify_user_decision(
    context: ContextTypes.DEFAULT_TYPE,
    appeal: Appeal,
    decision: str,
    admin_decision: str
) -> None:
    """Notify user about appeal decision."""
    try:
        if decision == 'approved':
            message = f"""
✅ Отличные новости! Ваша апелляция #{appeal.id} была одобрена.

Теперь вы можете присоединиться к группе F1News.ru. Пожалуйста, соблюдайте правила сообщества.
            """
        else:  # rejected
            reason = admin_decision.split(': ', 1)[1] if ': ' in admin_decision else 'Конкретная причина не указана'
            message = f"""
❌ Ваша апелляция #{appeal.id} была отклонена.

**Причина:** {reason}

Вы можете подать новую апелляцию, если у вас есть дополнительная информация.
            """
        
        await context.bot.send_message(
            chat_id=appeal.user_id,
            text=message,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Failed to notify user {appeal.user_id}: {e}")
