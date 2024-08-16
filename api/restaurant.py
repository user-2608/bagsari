from fastapi import FastAPI, HTTPException
import aiohttp
import asyncio
import re
import json
import random
import uuid
import time
import os

app = FastAPI()

# Function to generate UUID
def new_uuid():
    return str(uuid.uuid4())

# Function to generate a random integer for parts of the cookie
def random_integer(length=6):
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])

# Function to generate a timestamp or random float for dynamic values
def random_float():
    return str(random.uniform(0, 1))

# Function to generate epoch time for cookie values
def current_epoch():
    return str(int(time.time()))

# Function to generate dynamic cookies
def generate_cookies():
    return {
        'fre': random_integer(1),
        'rd': random_integer(7),
        'zl': 'en',
        'fbtrack': new_uuid(),
        '_gcl_au': random_float(),
        '_ga': f'GA1.1.{random_integer(10)}.{current_epoch()}',
        'G_ENABLED_IDPS': 'google',
        'cid': new_uuid(),
        'dpr': random_integer(1),
        'expab': random_integer(1),
        'PHPSESSID': new_uuid(),
        'csrf': new_uuid(),
        'fbcity': random_integer(2),
        'ltv': random_integer(2),
        'lty': random_integer(2),
        'locus': f'%7B%22addressId%22%3A0%2C%22lat%22%3A{random.uniform(22, 24):.6f}%2C%22lng%22%3A{random.uniform(72, 74):.6f}%2C%22cityId%22%3A11%2C%22ltv%22%3A11%2C%22lty%22%3A%22city%22%2C%22fetchFromGoogle%22%3Afalse%2C%22dszId%22%3A3720%2C%22fen%22%3A%22Ahmedabad%22%7D',
        'ak_bmsc': f'{random_integer(10)}A84BFFF6D87263152CA10~000000000000000000000000000000',
        '_abck': f'{new_uuid()}~-1~YAAQb40sMTgWTTSRAQAAwOf0VAzLEJf7zUvc',
        'bm_sz': f'{random_integer(10)}~YAAQDtjIF1fH8CGRAQAAQQP8VBhN',
        'AWSALBTG': new_uuid(),
        'AWSALBTGCORS': new_uuid(),
        '_ga_2XVFHLPTVP': f'GS1.1.{current_epoch()}.16.1.{random_integer(10)}.31.0.0',
    }

# Headers dictionary
headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9,en-IN;q=0.8',
    'cache-control': 'max-age=0',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
}

# Regex pattern to capture JSON inside window.__PRELOADED_STATE__
json_pattern = r'window\.__PRELOADED_STATE__\s*=\s*JSON\.parse\("(?P<json_data>.*?)"\);'

# Function to get restaurant details
def get_res_details(response_text: str, res_id: int, res_url: str = None):
    match = re.search(json_pattern, response_text)
    if match:
        json_data = match.group('json_data').encode('utf-8').decode('unicode_escape')
        preloaded_state = json.loads(json_data)
        res_contact = preloaded_state.get('pages', {}).get('restaurant', {}).get(f'{res_id}', {}).get('sections', {}).get('SECTION_RES_CONTACT', {})
        if res_contact:
            res_contact.update(res_contact.get('phoneDetails', {}))
            res_contact.pop('phoneDetails', None)
            res_contact.update({'res_id': res_id, 'url': res_url})
            return res_contact
    return None

# Async function to fetch restaurant details
async def fetch_restaurant_details(session, res_id):
    async with session.get(f'http://zoma.to/r/{res_id}') as response:
        if response.status == 200:
            if 'restaurants' not in str(response.url):
                text = await response.text()
                return get_res_details(text, res_id, str(response.url))
        elif response.status == 404:
            return {"error": f"Restaurant {res_id} not found"}
        else:
            return {"error": f"Failed with status code: {response.status}"}

# Main API route
@app.get("/restaurant/{res_id}")
async def restaurant(res_id: int):
    async with aiohttp.ClientSession(cookies=generate_cookies(), headers=headers) as session:
        res_data = await fetch_restaurant_details(session, res_id)
        if res_data:
            return res_data
        else:
            raise HTTPException(status_code=404, detail="Restaurant not found")
