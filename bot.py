import asyncpg
import discord
from discord.ext import commands
from dotenv import load_dotenv
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

load_dotenv()
import asyncio
import datetime
import logging
import os
import subprocess
import traceback

from config import config
from replit_support import start
from sqls.wrap import SQL_Wrapper

formatting = logging.Formatter("[%(asctime)s] - [%(levelname)s] [%(name)s] %(message)s")

logging.basicConfig(
    level=logging.NOTSET,
    format="[%(asctime)s] - [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
)

log = logging.getLogger("Snowflaking")
log.setLevel(logging.NOTSET)

try:
    os.mkdir("logs")
except FileExistsError:
    pass
with open("logs/bot.log", "w") as f:
    f.write("")
fg = logging.FileHandler("logs/bot.log", "w")
fg.setFormatter(formatting)
log.addHandler(fg)

logging.getLogger("discord").setLevel(logging.WARNING)  # mute

bot = commands.Bot(command_prefix=config.prefix, intents=discord.Intents.all())
bot.log = log

observer = Observer()


class FileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        log.info(f"File changed: {event.src_path}")
        if event.src_path.endswith(".py"):
            log.info("Reloading...")
            path = event.src_path.replace("\\", "/").replace("/", ".")[:-3]
            try:
                asyncio.run(bot.reload_extension(path))
                log.info(f"Reloaded {path}")
            except Exception as e:
                log.error(f"Failed to reload {path}")
                log.error(e)
                log.error(traceback.format_exc())


observer.schedule(FileHandler(), path="src", recursive=False)


def get_git_revision_short_hash() -> str:
    return (
        subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
        .decode("ascii")
        .strip()
    )


def get_version():
    is_updated = subprocess.check_output("git status", shell=True).decode("ascii")

    if "modified" in is_updated:
        is_updated = None
    elif (
        "up to date" in is_updated
        or "nothing to commit, working tree clean" in is_updated
    ):
        is_updated = True
    else:
        is_updated = False

    if is_updated:
        bot.version_ = f"latest ({get_git_revision_short_hash()})"
    elif is_updated is None:
        bot.version_ = f"{get_git_revision_short_hash()} (modified)"
    else:
        bot.version_ = f"old ({get_git_revision_short_hash()}) - not up to date"


@bot.event
async def on_ready():
    log.info("Logged in as")
    log.info(bot.user.name)
    log.info(bot.user.id)
    log.info("------")
    await bot.change_presence(activity=discord.Game(name=f"{config.prefix}help"))
    await bot.tree.sync()


async def main():
    try:
        started = False
        while not started:
            async with bot:
                bot.db = await asyncpg.create_pool(
                    config.database_url, ssl="prefer"
                )  # just knew perfer option!
                log.debug("Connected to database")
                bot.db = SQL_Wrapper(bot.db)
                await bot.db.execute(open("sqls/schema.sql").read())
                log.info("Created tables")
                for extension in os.listdir("src"):
                    if extension.endswith(".py") and not extension.startswith("_"):
                        await bot.load_extension(f"src.{extension[:-3]}")
                        log.info(f"Loaded extension {extension[:-3]}")
                await bot.load_extension("jishaku")
                log.info("Loaded jishaku")
                bot._enable_debug_events = True
                observer.start()
                log.info("Started file watcher")
                bot.start_time = datetime.datetime.utcnow()
                get_version()
                log.info(
                    f"Started with version {bot.version_} and started at {bot.start_time}"
                )
                if os.environ.get("IS_REPLIT"):
                    start()
                    log.info("REPLIT detected opening webserver for recieve pinging")
                try:
                    await bot.start(config.token)
                except discord.errors.HTTPException:
                    log.exception("You likely got ratelimited or bot's token is wrong")
                started = True  # break loop
    except KeyboardInterrupt:
        log.info("Exiting...")


async def runner():  # a runner for bot and watch every exceptions and `close` db properly
    try:
        await main()
    except Exception:
        print(traceback.format_exc())
        await bot.db.close()


if __name__ == "__main__":
    asyncio.run(runner())
