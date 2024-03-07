import os
import time
from hashlib import md5
import requests as rq
import json
import psycopg2
from psycopg2.extras import execute_batch
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_characters(public_key, private_key, db_connection_string):
    ts = str(time.time())
    hash_str = md5(f"{ts}{private_key}{public_key}".encode("utf8")).hexdigest()

    params = {
        "apikey": public_key,
        "ts": ts,
        "hash": hash_str,
        "orderBy": "name",
        "limit": 100
    }

    characters = []
    total_characters = None
    offset = 0

    while total_characters is None or len(characters) < total_characters:
        params["offset"] = offset
        try:
            response = rq.get('https://gateway.marvel.com:443/v1/public/characters', params=params)
            response.raise_for_status()  # This will raise an exception for HTTP error codes
        except Exception as e:
            logging.error(f"Failed to fetch data: {e}")
            return False, e
        else:
            data = response.json()
            if total_characters is None:
                total_characters = data['data']['total']
            characters.extend([(char['id'], char['name'], char['description'], char['comics']['available']) for char in data['data']['results']])
            offset += params["limit"]

    try:
        with psycopg2.connect(db_connection_string) as conn:
            with conn.cursor() as cur:
                execute_batch(cur,
                              "INSERT INTO marvel_characters (character_id, name, description, comics_appeared_in) VALUES (%s, %s, %s, %s) ON CONFLICT (character_id) DO NOTHING;",
                              characters)
            conn.commit()
        logging.info(f"Data for {len(characters)} characters saved successfully.")
        return True, f"Data for {len(characters)} characters saved successfully."
    except Exception as e:
        logging.error(f"Failed to save data to database: {e}")
        return False, e

# Use environment variables for sensitive information
public_key = os.getenv('MARVEL_API_PUBLIC_KEY')
private_key = os.getenv('MARVEL_API_PRIVATE_KEY')
db_connection_string = os.getenv('DATABASE_CONNECTION_STRING')

status, message = get_characters(public_key, private_key, db_connection_string)
logging.info(message)
