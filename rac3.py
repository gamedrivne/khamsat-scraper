import csv
import time
import os
import sys
import json
import logging
import glob
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ==========================================
# 1. CONFIGURATION POUR GITHUB ACTIONS
# ==========================================

# Dossier de base (relatif, fonctionne sur Windows ET Linux)
base_dir = os.path.join(os.getcwd(), "categories")
sous_cat_dir = os.path.join(base_dir, "sous_categories")
resultats_dir = os.path.join(base_dir, "resultats")
progress_dir = os.path.join(base_dir, "progress")

# Création des dossiers nécessaires
for directory in [resultats_dir, progress_dir]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Log principal
log_file = os.path.join(base_dir, "journal_scraping_services.log")

# Configuration du Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

def log_print(msg, level="info"):
    if level == "info": 
        logging.info(msg)
    elif level == "warning": 
        logging.warning(msg)
    elif level == "error": 
        logging.error(msg)
    elif level == "success": 
        logging.info(f"✅ {msg}")

log_print("=" * 50)
log_print("🚀 DÉMARRAGE DU SCRAPER DE SERVICES KHAMSAT")
log_print("=" * 50)

# ==========================================
# 2. RÉCUPÉRATION DES FICHIERS CSV
# ==========================================

# Trouve tous les CSV dans le dossier sous_categories
csv_files = glob.glob(os.path.join(sous_cat_dir, "*.csv"))

if not csv_files:
    log_print(f"❌ ERREUR : Aucun fichier CSV trouvé dans {sous_cat_dir}", "error")
    sys.exit(1)

log_print(f"📂 {len(csv_files)} fichiers CSV trouvés à traiter")

# ==========================================
# 3. GESTION DE LA PROGRESSION
# ==========================================
def load_progress(filename):
    progress_file = os.path.join(progress_dir, f"progress_{filename}.json")
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()

def save_progress(filename, processed_set):
    progress_file = os.path.join(progress_dir, f"progress_{filename}.json")
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(list(processed_set), f, ensure_ascii=False)

# ==========================================
# 4. INITIALISATION SELENIUM (MODE HEADLESS)
# ==========================================
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Mode sans interface
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

# ==========================================
# 5. FONCTIONS DE SCRAPING
# ==========================================
def load_infinite_scroll(driver, wait, max_clicks=50):
    """Clique sur 'Voir plus' jusqu'à la fin (limite à 50 clics)."""
    click_count = 0
    while click_count < max_clicks:
        try:
            load_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="load_more_content"]'))
            )
            driver.execute_script("arguments[0].scrollIntoView();", load_btn)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", load_btn)
            click_count += 1
            log_print(f"   ⏳ Chargement page {click_count}...")
            time.sleep(2)
        except:
            break
    
    if click_count > 0:
        log_print(f"   📄 {click_count} pages chargées")

def extract_page_data(driver, category_name):
    """Extrait les données des services."""
    services = driver.find_elements(By.XPATH, "//div[starts-with(@id,'service-')]")
    extracted_rows = []

    for svc in services:
        try:
            link_elem = svc.find_element(By.XPATH, ".//div/div[2]/h4/a")
            title = link_elem.text.strip()
            link = link_elem.get_attribute("href").strip()
            
            try:
                img_elem = svc.find_element(By.XPATH, ".//div/div[1]//img")
                img_src = img_elem.get_attribute("src").strip()
            except:
                img_src = "N/A"

            extracted_rows.append([category_name, title, link, img_src])
        except:
            continue
    
    return extracted_rows

# ==========================================
# 6. TRAITEMENT DE CHAQUE FICHIER CSV
# ==========================================
def process_csv_file(csv_path, driver, wait):
    """Traite un fichier CSV de sous-catégories."""
    
    input_filename = os.path.splitext(os.path.basename(csv_path))[0]
    output_csv = os.path.join(resultats_dir, f"Resultats_{input_filename}.csv")
    
    log_print(f"\n{'='*50}")
    log_print(f"📁 Traitement : {input_filename}")
    log_print(f"{'='*50}")
    
    # Chargement de la progression
    processed_urls = load_progress(input_filename)
    if processed_urls:
        log_print(f"🔄 Reprise : {len(processed_urls)} catégories déjà traitées")
    
    # Initialisation du CSV de sortie
    file_exists = os.path.exists(output_csv)
    if not file_exists:
        with open(output_csv, mode='w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(["Catégorie", "Titre du Service", "Lien du Service", "Image URL"])
    
    # Lecture des sous-catégories
    try:
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader, None)  # Sauter l'en-tête
            rows = list(reader)
    except Exception as e:
        log_print(f"❌ Erreur lecture {csv_path}: {e}", "error")
        return 0
    
    total_rows = len(rows)
    total_services = 0
    
    # Traitement de chaque sous-catégorie
    for i, row in enumerate(rows):
        if len(row) < 2:
            continue
        
        cat_name = row[0]
        cat_url = row[1]
        
        # Vérifier si déjà traité
        if cat_url in processed_urls:
            continue
        
        log_print(f"➡️ [{i+1}/{total_rows}] {cat_name}")
        
        try:
            driver.get(cat_url)
            time.sleep(2)
            
            # Charger toutes les pages
            load_infinite_scroll(driver, wait)
            
            # Extraire les données
            data = extract_page_data(driver, cat_name)
            count = len(data)
            total_services += count
            
            if count > 0:
                # Sauvegarder dans le CSV
                with open(output_csv, mode='a', newline='', encoding='utf-8-sig') as f_out:
                    writer = csv.writer(f_out)
                    writer.writerows(data)
                
                log_print(f"   ✅ {count} services récupérés", "success")
            else:
                log_print(f"   ⚠️ 0 service trouvé", "warning")
            
            # Marquer comme traité
            processed_urls.add(cat_url)
            save_progress(input_filename, processed_urls)
            
            # Pause anti-ban
            time.sleep(3)
            
        except Exception as e:
            log_print(f"   ❌ Erreur : {e}", "error")
            continue
    
    log_print(f"\n{'='*50}")
    log_print(f"📊 {input_filename} : {total_services} services au total")
    log_print(f"{'='*50}")
    
    return total_services

# ==========================================
# 7. BOUCLE PRINCIPALE
# ==========================================

driver = None
grand_total = 0

try:
    driver = init_driver()
    wait = WebDriverWait(driver, 10)
    
    for csv_file in csv_files:
        try:
            total = process_csv_file(csv_file, driver, wait)
            grand_total += total
        except Exception as e:
            log_print(f"❌ Erreur critique sur {csv_file}: {e}", "error")
            continue

except KeyboardInterrupt:
    log_print("\n🛑 Interruption utilisateur", "warning")

except Exception as e:
    log_print(f"❌ Erreur globale : {e}", "error")

finally:
    if driver:
        driver.quit()
    
    # RAPPORT FINAL
    log_print("\n" + "=" * 50)
    log_print("       📊 RAPPORT FINAL")
    log_print("=" * 50)
    log_print(f"📁 Dossier résultats : {resultats_dir}")
    log_print(f"🎯 TOTAL GÉNÉRAL : {grand_total} services extraits")
    log_print("=" * 50)
