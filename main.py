import asyncio
from src.utils.logging_config import logger
from src.bot.create_bot import start_bot

async def main():
    try:
        await start_bot()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        logger.info("Bot stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot manually stopped.")