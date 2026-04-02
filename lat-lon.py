import pandas as pd
import time
import re
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from tqdm import tqdm
import json
import os

# Fichiers
input_file = "listecondamnation.csv"
output_file = "listecondamnation_geocoded.csv"
cache_file = "geocode_cache.json"

# Charger CSV original
df_original = pd.read_csv(input_file)

# 🔁 Si fichier géocodé existe → reprendre
if os.path.exists(output_file):
    df = pd.read_csv(output_file)
    print("🔁 Reprise du fichier existant")
else:
    df = df_original.copy()
    df["Latitude"] = None
    df["Longitude"] = None
    print("🆕 Nouveau traitement")

# Géocodeur
geolocator = Nominatim(user_agent="mapaq_quebec_app", timeout=10)

# Cache
if os.path.exists(cache_file):
    with open(cache_file, "r") as f:
        cache = json.load(f)
else:
    cache = {}


def save_cache():
    with open(cache_file, "w") as f:
        json.dump(cache, f)


def clean_address(address):
    if pd.isna(address):
        return ""

    address = str(address)
    address = re.sub(r"\(QC\)", "", address)
    address = re.sub(r"\s+[A-Z]?\d{1,4}\b", "", address)
    address = re.sub(r"\s+", " ", address).strip()

    return address


from geopy.exc import GeocoderTimedOut, GeocoderRateLimited
import time

def geocode_with_retry(address, max_retries=10):
    delay = 2  # délai initial

    for attempt in range(max_retries):
        try:
            return geolocator.geocode(address)

        except (GeocoderTimedOut):
            print("⏳ Timeout → retry...")
            time.sleep(delay)

        except GeocoderRateLimited:
            print("🚫 429 → pause LONGUE (cooldown)")
            time.sleep(60)  # 🔥 IMPORTANT : vraie pause
            delay = min(delay * 2, 120)  # backoff

        except Exception as e:
            print(f"⚠️ Autre erreur: {e}")
            time.sleep(5)

    return None

# 🔍 Trouver les lignes à traiter
rows_to_process = df[
    df["Latitude"].isna() | df["Longitude"].isna()
]

print(f"🚀 Lignes restantes à traiter: {len(rows_to_process)}")

# 🔥 tqdm
for i in tqdm(rows_to_process.index):

    row = df.loc[i]

    raw_address = row.get("Adresse_lieu_infraction", "")
    cleaned = clean_address(raw_address)
    full_address = f"{cleaned}, Quebec, Canada"

    if not cleaned:
        continue

    # ⚡ Cache
    if full_address in cache:
        lat, lon = cache[full_address]

        # ⚠️ IGNORER les résultats invalides
        if lat is not None and lon is not None:
            df.at[i, "Latitude"] = lat
            df.at[i, "Longitude"] = lon
            continue

    # 🌍 Géocodage
    location = geocode_with_retry(full_address)

    if location:
        lat, lon = location.latitude, location.longitude
        df.at[i, "Latitude"] = lat
        df.at[i, "Longitude"] = lon
        cache[full_address] = (lat, lon)
    else:
        cache[full_address] = (None, None)

    # 💾 Sauvegarde régulière
    if i % 50 == 0:
        df.to_csv(output_file, index=False)
        save_cache()

    time.sleep(1.0)

# 💾 Sauvegarde finale
df.to_csv(output_file, index=False)
save_cache()

print("\n🎯 Terminé / repris avec succès !")