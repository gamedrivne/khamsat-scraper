import requests
from bs4 import BeautifulSoup
import csv
import os
import logging
import db_writer

# ==========================================
# 1. CONFIGURATION
# ==========================================

base_path = os.path.join(os.getcwd(), "categories")

if not os.path.exists(base_path):
    os.makedirs(base_path)

output_file = os.path.join(base_path, "categories_khamsat.csv")
log_file    = os.path.join(base_path, "journal_categories.log")

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
    encoding='utf-8'
)

def log_print(msg, level="info"):
    print(msg)
    if level == "info":      logging.info(msg)
    elif level == "warning": logging.warning(msg)
    elif level == "error":   logging.error(msg)

log_print("=== DÉMARRAGE SCRAPING CATÉGORIES PRINCIPALES ===")

# ==========================================
# 2. REQUÊTE HTTP
# ==========================================

URL = "https://khamsat.com/"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

try:
    response = requests.get(URL, headers=headers)
    if response.status_code != 200:
        log_print(f"Erreur HTTP : {response.status_code}", "error")
        exit()
    log_print(f"Page chargée avec succès (status {response.status_code})")
except Exception as e:
    log_print(f"Erreur connexion : {e}", "error")
    exit()

# ==========================================
# 3. PARSING HTML
# ==========================================

soup = BeautifulSoup(response.content, 'html.parser')

grid = soup.select_one("div.row.grid-items")

if not grid:
    log_print("ERREUR : Conteneur 'div.row.grid-items' non trouvé !", "error")
    exit()

categories    = []
db_categories = []
seen          = set()

for a_tag in grid.select("a[href]"):
    href = a_tag.get("href", "").strip()
    span = a_tag.find("span")
    name = span.get_text(strip=True) if span else a_tag.get_text(strip=True)

    if href and name and href not in seen:
        full_url = "https://khamsat.com" + href
        slug     = href.strip("/").split("/")[-1]

        categories.append([name, full_url])
        db_categories.append({"name": name, "slug": slug})
        seen.add(href)
        log_print(f"   -> Trouvé : {name} | {full_url}")

# ==========================================
# 4. SAUVEGARDE CSV
# ==========================================

if categories:
    with open(output_file, mode='w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(["Nom catégorie", "Lien"])
        writer.writerows(categories)

    log_print("-" * 40)
    log_print(f"✅ {len(categories)} catégories sauvegardées dans : {output_file}")
else:
    log_print("ATTENTION : Aucune catégorie extraite !", "warning")

# ==========================================
# 5. SAUVEGARDE DB
# ==========================================

if db_categories:
    run_id = db_writer.log_pipeline_start("rac1")
    db_writer.upsert_categories(db_categories)
    db_writer.log_pipeline_end(run_id, len(db_categories))
    log_print(f"✅ {len(db_categories)} catégories envoyées à Supabase.")

log_print("=== FIN DU TRAITEMENT ===")
