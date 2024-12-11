import asyncio
import cloudscraper
import time
from loguru import logger
from concurrent.futures import ThreadPoolExecutor
from curl_cffi import requests
import pyfiglet

logger.remove()
logger.add(
    sink=lambda msg: print(msg, end=''),
    format=(
        "<green>{time:DD/MM/YY HH:mm:ss}</green> | "
        "<level>{level:8} | {message}</level>"
    ),
    colorize=True
)
# main.py
def print_header():
    cn = pyfiglet.figlet_format("xNodepayBot")
    print(cn)
    print("🌱 Season 2")
    print("🎨 by \033]8;;https://github.com/officialputuid\033\\officialputuid\033]8;;\033\\")
    print("✨ Credits: IDWR2016, im-hanzou, AirdropFamilyIDN")
    print('🎁 \033]8;;https://paypal.me/IPJAP\033\\Paypal.me/IPJAP\033]8;;\033\\ — \033]8;;https://trakteer.id/officialputuid\033\\Trakteer.id/officialputuid\033]8;;\033\\')

# Initialize the header
print_header()

# Read Tokens and Proxy count
def read_tokens_and_proxy():
    with open('tokens.txt', 'r') as file:
        tokens_content = sum(1 for line in file)

    with open('proxy.txt', 'r') as file:
        proxy_count = sum(1 for line in file)

    return tokens_content, proxy_count

tokens_content, proxy_count = read_tokens_and_proxy()

print()
print(f"🔑 Tokens: {tokens_content}.")
print(f"🌐 Loaded {proxy_count} proxies.")
print(f"🧩 Nodepay limits only 3 connections per account. Using multiple proxies is unnecessary.")
print()

PING_INTERVAL = 60
KEEP_ALIVE_INTERVAL = 300

DOMAIN_API = {
    "SESSION": "http://api.nodepay.ai/api/auth/session",
    "PING": ["https://nw.nodepay.org/api/network/ping"]
}

CONNECTION_STATES = {
    "CONNECTED": 1,
    "DISCONNECTED": 2,
    "NONE_CONNECTION": 3
}

# Global variables for KeepAlive
wakeup = None
isFirstStart = False
isAlreadyAwake = False
firstCall = None
lastCall = None
timer = None

def letsStart():
    global wakeup, isFirstStart, isAlreadyAwake, firstCall, lastCall, timer

    if wakeup is None:
        isFirstStart = True
        isAlreadyAwake = True
        firstCall = time.time()
        lastCall = firstCall
        timer = KEEP_ALIVE_INTERVAL

        wakeup = asyncio.get_event_loop().call_later(timer, keepAlive)

def keepAlive():
    global lastCall, timer, wakeup

    now = time.time()
    lastCall = now

    wakeup = asyncio.get_event_loop().call_later(timer, keepAlive)

class AccountInfo:
    def __init__(self, token, proxies):
        self.token = token
        self.proxies = proxies
        self.status_connect = CONNECTION_STATES["NONE_CONNECTION"]
        self.account_data = {}
        self.retries = 0
        self.last_ping_status = 'Waiting...'
        self.browser_id = {
            'ping_count': 0,
            'successful_pings': 0,
            'score': 0,
            'start_time': time.time(),
            'last_ping_time': None
        }

    def reset(self):
        self.status_connect = CONNECTION_STATES["NONE_CONNECTION"]
        self.account_data = {}
        self.retries = 3

scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

async def load_tokens():
    try:
        with open('tokens.txt', 'r') as file:
            tokens = file.read().splitlines()
        return tokens
    except Exception as e:
        logger.error(f"Failed to load tokens: {e}")
        raise SystemExit("Exiting due to failure in loading tokens")

def truncate_token(token):
    return f"{token[:4]}--{token[-4:]}"

def truncate_proxy(proxy):
    return f"{proxy[:6]}--{proxy[-10:]}"

async def call_api(url, data, account_info, proxy):
    headers = {
        "Authorization": f"Bearer {account_info.token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://app.nodepay.ai/",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "chrome-extension://lgmpfmgeabnnlemejacfljbmonaomfmm"
    }

    proxy_config = {
        "http": proxy,
        "https": proxy
    }

    try:
        response = scraper.post(url, json=data, headers=headers, proxies=proxy_config, timeout=60)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Token: {truncate_token(account_info.token)} | Error during API call | Proxy: {truncate_proxy(proxy)}")
        logger.error(f"Token: {truncate_token(account_info.token)} | {e}")
        raise ValueError(f"Failed API call to {url}")

    return response.json()

async def render_profile_info(account_info):
    try:
        for proxy in account_info.proxies:
            try:
                response = await call_api(DOMAIN_API["SESSION"], {}, account_info, proxy)
                if response.get("code") == 0:
                    account_info.account_data = response["data"]
                    if account_info.account_data.get("uid"):
                        await start_ping(account_info)
                        return
                else:
                    logger.warning(f"Token: {truncate_token(account_info.token)} | Session failed | Proxy: {truncate_proxy(proxy)}")
            except Exception as e:
                logger.error(f"Token: {truncate_token(account_info.token)} | Failed to render profile info | Proxy: {truncate_proxy(proxy)}")
                logger.error(f"Token: {truncate_token(account_info.token)} | {e}")

        logger.error(f"Token: {truncate_token(account_info.token)} | All proxies failed")
    except Exception as e:
        logger.error(f"Token: {truncate_token(account_info.token)} | Error in render_profile_info")
        logger.error(f"Token: {truncate_token(account_info.token)} | {e}")

async def start_ping(account_info):
    try:
        logger.info(f"Token: {truncate_token(account_info.token)} | Starting PING, ENJOY!")
        while True:
            for proxy in account_info.proxies:
                try:
                    await asyncio.sleep(PING_INTERVAL)
                    await ping(account_info, proxy)
                except Exception as e:
                    logger.error(f"Token: {truncate_token(account_info.token)} | Ping failed | Proxy: {truncate_proxy(proxy)}")
                    logger.error(f"Token: {truncate_token(account_info.token)} | {e}")
    except asyncio.CancelledError:
        logger.info(f"Token: {truncate_token(account_info.token)} | Ping task was cancelled")
    except Exception as e:
        logger.error(f"Token: {truncate_token(account_info.token)} | Error in start_ping{e}")
        logger.error(f"Token: {truncate_token(account_info.token)} | {e}")

async def ping(account_info, proxy):
    for url in DOMAIN_API["PING"]:
        try:
            data = {
                "id": account_info.account_data.get("uid"),
                "browser_id": account_info.browser_id,
                "timestamp": int(time.time())
            }
            response = await call_api(url, data, account_info, proxy)
            if response["code"] == 0:
                logger.success(f"Token: {truncate_token(account_info.token)} | Ping successful | Proxy: {truncate_proxy(proxy)}")
                return
        except Exception as e:
            logger.error(f"Token: {truncate_token(account_info.token)} | Ping failed | Proxy: {truncate_proxy(proxy)}")
            logger.error(f"Token: {truncate_token(account_info.token)} | {e}")

def process_account(token, proxies):
    account_info = AccountInfo(token, proxies)
    asyncio.run(render_profile_info(account_info))

async def main():
    letsStart()
    tokens = await load_tokens()

    try:
        with open('proxy.txt', 'r') as file:
            proxies = file.read().splitlines()
    except Exception as e:
        logger.error(f"Failed to load proxies: {e}")
        raise SystemExit("Exiting due to failure in loading proxies")

    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = []
        for token in tokens:
            futures.append(executor.submit(process_account, token, proxies))

        for future in futures:
            future.result()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info(f"Program terminated by user. ENJOY!\n")
