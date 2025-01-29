import os
from  dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
API_WET= os.getenv('API_WEATHER')
API_TR = os.getenv('API_TRAINING')
if not TOKEN:
    raise ValueError("BOT_TOKEN не установлен.")
elif not API_WET:
    raise ValueError("API_WEATHER не установлен.")
elif not API_TR:
    raise ValueError("API_TRAINING не установлен.")