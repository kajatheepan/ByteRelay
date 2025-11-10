import os
from dotenv import load_dotenv
load_dotenv()

class Configs(object):
    #Bot configs
    API_ID = int(os.getenv('API_ID', 0))
    API_HASH = os.getenv('API_HASH', '')
    BOT_TOKEN = os.getenv('BOT_TOKEN', '')
    MAX_CONCURRENT_TRANSMISSIONS = int(os.getenv('MAX_CONCURRENT_TRANSMISSIONS') or 4)
    WORKERS = int(os.getenv('WORKERS') or 4)
    COOLDOWN_SECONDS = int(os.getenv('COOLDOWN_SECONDS',30))
    UPLOAD_POINT = os.getenv('UPLOAD_POINT',"https://dms.uom.lk/remote.php/webdav/")


