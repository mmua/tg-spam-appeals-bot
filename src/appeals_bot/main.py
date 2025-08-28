"""Main entry point for the Appeals Bot."""

import logging
import sys
from pathlib import Path

from telegram.ext import Application, CommandHandler

from .config import config
from .handlers import (
    start_command,
    help_command,
    appeal_command,
    status_command,
    approve_command,
    reject_command,
    info_command,
    pending_command,
    stats_command,
)


def setup_logging() -> None:
    """Set up logging configuration."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Add file handler if log file is specified
    if config.log_file:
        # Ensure log directory exists
        log_path = Path(config.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(config.log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)


def create_application() -> Application:
    """Create and configure the bot application."""
    application = Application.builder().token(config.appeals_bot_token).build()
    
    # User commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("appeal", appeal_command))
    application.add_handler(CommandHandler("status", status_command))
    
    # Admin commands
    application.add_handler(CommandHandler("approve", approve_command))
    application.add_handler(CommandHandler("reject", reject_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("pending", pending_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    return application


def main() -> None:
    """Main function to run the bot."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Create and run the application
        application = create_application()
        logger.info("F1 Appeals Bot started successfully")
        application.run_polling()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
