from loguru import logger
from curl_cffi import requests
import pyfiglet
import time
from datetime import datetime, timedelta
import pytz

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
    cn = pyfiglet.figlet_format("dailyclaim")
    print(cn)
    print("🌱 Season 2")
    print("🎨 by \033]8;;https://github.com/officialputuid\033\\officialputuid\033]8;;\033\\")
    print("✨ Credits: AirdropFamilyIDN")
    print('🎁 \033]8;;https://paypal.me/IPJAP\033\\Paypal.me/IPJAP\033]8;;\033\\ — \033]8;;https://trakteer.id/officialputuid\033\\Trakteer.id/officialputuid\033]8;;\033\\')

# Initialize the header
print_header()

# Read Tokens and Proxy count
def read_tokens():
    with open('tokens.txt', 'r') as file:
        tokens_content = sum(1 for line in file)
    return tokens_content

tokens_content = read_tokens()

# Print the token count
print()
print(f"🔑 Tokens: {tokens_content}.")
print()

def truncate_token(token):
    return f"{token[:4]}--{token[-4:]}"

# Function to claim reward using the provided token
def claim_reward(token):
    url = "https://api.nodepay.org/api/mission/complete-mission"
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Origin": "https://app.nodepay.ai",
        "Referer": "https://app.nodepay.ai/"
    }
    data = {"mission_id": "1"}

    retries = 3
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(url, headers=headers, json=data, impersonate="chrome110")

            if response.status_code == 200:
                response_data = response.json()
                if response_data.get('success'):
                    logger.success(f"Token: {truncate_token(token)} | Reward claimed successfully")
                    break
                else:
                    logger.info(f"Token: {truncate_token(token)} | Reward already claimed or another issue occurred")
                    break
            elif response.status_code == 403:
                logger.warning(f"Token: {truncate_token(token)} | Attempt {attempt}/{retries}: HTTP 403 Forbidden.")
                if attempt == retries:
                    logger.error(f"Token: {truncate_token(token)} | Maximum retries reached for HTTP 403.")
                else:
                    time.sleep(2)
            else:
                logger.error(f"Token: {truncate_token(token)} | Failed request, HTTP Status: {response.status_code}")
                break

        except requests.exceptions.RequestException as e:
            logger.exception(f"Token: {truncate_token(token)} | Request error: {e}")
            break

def main():
    try:
        with open('tokens.txt', 'r') as file:
            tokens = file.read().splitlines()

        for token in tokens:
            claim_reward(token)
            time.sleep(2)

        # Send a final message after all operations are done
        logger.success(f"All tokens processed. Daily claim operation completed.")

    except FileNotFoundError:
        logger.error(f"The file 'tokens.txt' was not found. Please make sure it exists.")
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")

def time_until_next_run():
    tz = pytz.timezone("Asia/Makassar")  # UTC+8
    now = datetime.now(tz)
    next_run = now.replace(hour=9, minute=0, second=0, microsecond=0)

    if now >= next_run:
        next_run += timedelta(days=1)

    time_difference = (next_run - now).total_seconds()
    return time_difference

if __name__ == "__main__":
    try:
        while True:
            main()
            next_run_seconds = time_until_next_run()
            next_run_time = datetime.now(pytz.timezone("Asia/Makassar")) + timedelta(seconds=next_run_seconds)
            logger.info(f"Next run scheduled for {next_run_time.strftime('%Y-%m-%d %H:%M:%S')} UTC+8.")
            time.sleep(next_run_seconds)
    except (KeyboardInterrupt, SystemExit):
        logger.info(f"Program terminated by user. ENJOY!\n")
