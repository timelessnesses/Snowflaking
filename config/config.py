from dotenv import load_dotenv

load_dotenv()
import os
import subprocess

token = os.getenv("SNOWFLAKING_BOT_TOKEN")
prefix = os.getenv("SNOWFLAKING_PREFIX")
database_ssl = True if bool(int(os.getenv("SNOWFLAKING_DATABASE_SSL", 0))) else False
database_url = os.getenv("SNOWFLAKING_POSTGRESQL_URL")
git_repo = (
    subprocess.check_output("git config --get remote.origin.url".split(" "))
    .decode("ascii")
    .strip()
)[:-4]

if not database_url:
    raise ValueError("No database url provided")
