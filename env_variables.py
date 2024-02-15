import os

from dotenv import load_dotenv

load_dotenv()

guildId = int(os.getenv("guildId"))

clientId = os.getenv("clientId")
clientSecret = os.getenv("clientSecret")
redirectUrl = os.getenv("redirectUrl")