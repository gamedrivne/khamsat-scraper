import requests
from bs4 import BeautifulSoup
import csv
import os
import time
import logging
import re
from urllib.parse import urlparse

# ==========================================
# 1. CONFIGURATION - ADAPTÉ POUR GITHUB ACTIONS
# ==========================================

# Chemin relatif qui fonctionne sur Windows ET Linux
base_path = os.path.join(os.getcwd(), "categories")

# Création du dossier base si nécessaire
if not os.path.exists(base_path):
    os.makedirs(base_path)

input_file_xpath = os.path.join(base_path, "categories_khamsat_xpath.csv")
input_file_std = os.path.join(base_path, "categories_khamsat.csv")

# Choix automatique du fichier d'entrée
if os.path.exists(input_file_xpath):
    input_file = input_file_xpath
elif os.path.exists(input_file_std):
    input_file = input_file_std
else:
    print(f"ERREUR : Aucun fichier de catégories trouvé dans {base_path}")
    print("Veuillez d'abord créer un fichier de catégories.")
    exit()

# Dossier de sortie pour les sous-catégories
output_dir = os.path.join(base_path, "sous_categories")
log_file = os.path.join(base_path, "journal_sous_categories.log")

# Création du dossier de sortie
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Configuration du Logging
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
    encoding='utf-8'
)

def log_print(msg, level="info"):
    print(msg)
    if level == "info": logging.info(msg)
    elif level == "warning": logging.warning(msg)
    elif level == "error": logging.error(msg)

log_print(f"=== DÉMARRAGE DU SCRAPING DES SOUS-CATÉGORIES ===")
log_print(f"Lecture du fichier : {input_file}")
log_print(f"Dossier de sauvegarde : {output_dir}")

# ==========================================
# 2. CHARGEMENT DES CATÉGORIES PRINCIPALES
# ==========================================

categories_todo = []
try:
    with open(input_file, mode='r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) >= 2:
                categories_todo.append({'name': row[0], 'url': row[1]})
except Exception as e:
    log_print(f"Erreur lecture CSV : {e}", "error")
    exit()

log_print(f"{len(categories_todo)} catégories principales chargées. Début du traitement...")
log_print("-" * 40)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

# ==========================================
# 3. BOUCLE DE TRAITEMENT
# ==========================================

total_subs_extracted = 0

for i, cat in enumerate(categories_todo):
    cat_name = cat['name']
    cat_url = cat['url']
    
    safe_name = re.sub(r'[\\/*?:"<>|]', "", cat_name)
    safe_name = safe_name.replace(" ", "_")
    output_csv = os.path.join(output_dir, f"{safe_name}.csv")
    
    log_print(f"[{i+1}/{len(categories_todo)}] Traitement : {cat_name}...")

    try:
        response = requests.get(cat_url, headers=headers)
        if response.status_code != 200:
            log_print(f"   -> Erreur HTTP {response.status_code}", "error")
            continue

        soup = BeautifulSoup(response.content, 'html.parser')
        subcategories = []
        seen_links = set()

        parsed_cat_url = urlparse(cat_url)
        cat_path = parsed_cat_url.path
        
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link['href']
            text = link.get_text(strip=True)
            
            if not href.startswith('http'):
                href = "https://khamsat.com" + href
                
            if (href.startswith(cat_url) or (cat_path in href and "khamsat.com" in href)):
                if href != cat_url and "/service/" not in href and "/user/" not in href:
                    if "?" not in href and text and len(text) > 2:
                        if href not in seen_links:
                            subcategories.append([text, href])
                            seen_links.add(href)

        if subcategories:
            with open(output_csv, mode='w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["Nom sous-catégorie", "Lien"])
                writer.writerows(subcategories)
            
            count = len(subcategories)
            total_subs_extracted += count
            log_print(f"   -> Succès : {count} sous-catégories sauvegardées dans {safe_name}.csv")
        else:
            log_print(f"   -> ATTENTION : Aucune sous-catégorie trouvée pour {cat_name}", "warning")

        time.sleep(2)

    except Exception as e:
        log_print(f"   -> Exception critique : {e}", "error")

log_print("-" * 40)
log_print(f"=== FIN DU TRAITEMENT ===")
log_print(f"Total sous-catégories extraites : {total_subs_extracted}")
log_print(f"Consultez le dossier : {output_dir}")