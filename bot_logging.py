import logging
import time
import sys

current_time = time.strftime('%Y-%m-%d')

logger = logging.getLogger(__name__)

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=('%(asctime)s [%(levelname)s] > %(message)s'))
formatter = logging.Formatter('%(asctime)s [%(levelname)s] > %(message)s')

handler = logging.FileHandler('logs/bot-' + current_time.replace(':', '') + '.log', 'w', 'utf-8')
handler.setFormatter(formatter)
logger.addHandler(handler)

