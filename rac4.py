import csv
import time
import os
import json
import glob
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# ============================
# 1️⃣ CONFIGURATION
# ============================

base_dir      = os.path.join(os.getcwd(), "categories")
resultats_dir = os.path.join(base_dir, "resultats")
details_dir   = os.path.join(base_dir, "details_services")
progress_dir  = os.path.join(base_dir, "progress_details")

NB_WORKERS    = 4
csv_lock      = threading.Lock()
progress_lock = threading.Lock()

for directory in [details_dir, progress_dir]:
    if not os.path.exists(directory):
        os.makedirs(directory)

log_file = os.path.join(base_dir, "journal_details_services.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def log_print(msg, level="info"):
    if level == "info":      logging.info(msg)
    elif level == "warning": logging.warning(msg)
    elif level == "error":   logging.error(msg)
    elif level == "success": logging.info(f"✅ {msg}")

log_print("=" * 60)
log_print(f"🚀 DÉMARRAGE EXTRACTION DÉTAILS — {NB_WORKERS} WORKERS PARALLÈLES")
log_print("=" * 60)

# ============================
# 2️⃣ RÉCUPÉRATION DES FICHIERS
# ============================

result_files = glob.glob(os.path.join(resultats_dir, "Resultats_*.csv"))

if not result_files:
    log_print(f"❌ Aucun fichier résultat trouvé dans {resultats_dir}", "error")
    exit(1)

log_print(f"📂 {len(result_files)} fichiers résultats trouvés")

# ============================
# 3️⃣ GESTION DE LA PROGRESSION
# ============================

def load_progress(filename):
    progress_file = os.path.join(progress_dir, f"progress_{filename}.json")
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_progress(filename, processed_set):
    with progress_lock:
        progress_file = os.path.join(progress_dir, f"progress_{filename}.json")
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(list(processed_set), f, ensure_ascii=False)

# ============================
# 4️⃣ INITIALISATION SELENIUM
# ============================

def init_driver(worker_id):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(f"--user-data-dir=/tmp/chrome_worker_{worker_id}")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

# ============================
# 5️⃣ EXTRACTION D'UN SERVICE
# ============================

def get_text(driver, wait, xpath, default="Non trouvé"):
    try:
        element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        return element.get_attribute("textContent").strip()
    except:
        return default

def extract_service_details(driver, wait, link):
    try:
        driver.get(link)
        time.sleep(0.8)

        title  = get_text(driver, wait, '//h1')
        owner  = get_text(driver, wait, '//div[@id="service_owner"]//a[contains(@class, "sidebar_user")]')
        buyers = get_text(driver, wait, '//div[contains(@class, "col-6")][span[contains(text(), "المشترين")]]/following-sibling::div[1]/span')

        votes = get_text(driver, wait, '//div[contains(@class, "col-6")][span[contains(text(), "التقييمات")]]/following-sibling::div[1]//li[contains(@class, "info")]')
        votes = votes.replace("(", "").replace(")", "")

        last_date = get_text(driver, wait, '//*[@id="reviews-section"]//div[contains(@class, "review_section")][1]//div[contains(@class, "meta--date")]/span[2]', "Aucun avis")

        try:
            tags_elements = driver.find_elements(By.XPATH, '//ul[contains(@class, "c-list--tags")]//li//a')
            tags_list = [tag.text.strip() for tag in tags_elements if tag.text.strip()]
            keywords  = ", ".join(tags_list) if tags_list else "Aucun tag"
        except:
            keywords = "Erreur Tags"

        cat_main = get_text(driver, wait, '//ol[contains(@class, "breadcrumb")]//li[2]//a', "Inconnu")
        cat_sub  = get_text(driver, wait, '//ol[contains(@class, "breadcrumb")]//li[3]//a', "Inconnu")

        return {
            "title": title, "owner": owner, "buyers": buyers,
            "votes": votes, "last_date": last_date,
            "cat_main": cat_main, "cat_sub": cat_sub,
            "keywords": keywords, "link": link, "status": "success"
        }

    except Exception as e:
        log_print(f"   ❌ Worker erreur {link}: {e}", "error")
        return {
            "title": "Erreur", "owner": "Erreur", "buyers": "0",
            "votes": "0", "last_date": "0", "cat_main": "Erreur",
            "cat_sub": "Erreur", "keywords": "Erreur",
            "link": link, "status": "error"
        }

# ============================
# 6️⃣ WORKER — TRAITE UN CHUNK
# ============================

def worker_process(worker_id, links_chunk, output_csv, base_name, processed_links_shared):
    log_print(f"🔧 Worker {worker_id} démarré → {len(links_chunk)} services")

    driver        = None
    local_success = 0
    local_errors  = 0

    try:
        driver = init_driver(worker_id)
        wait   = WebDriverWait(driver, 15)

        for i, link in enumerate(links_chunk, 1):

            with progress_lock:
                if link in processed_links_shared:
                    continue

            result = extract_service_details(driver, wait, link)

            with csv_lock:
                with open(output_csv, "a", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        result["title"], result["owner"], result["buyers"],
                        result["votes"], result["last_date"], result["cat_main"],
                        result["cat_sub"], result["keywords"], result["link"]
                    ])

            with progress_lock:
                processed_links_shared.add(link)

            if i % 50 == 0:
                save_progress(base_name, processed_links_shared)
                log_print(f"   Worker {worker_id} → {i}/{len(links_chunk)} traités")

            if result["status"] == "success":
                local_success += 1
            else:
                local_errors += 1

            time.sleep(0.3)

    except Exception as e:
        log_print(f"❌ Worker {worker_id} erreur critique : {e}", "error")

    finally:
        if driver:
            driver.quit()

    log_print(f"✅ Worker {worker_id} terminé → {local_success} succès, {local_errors} erreurs")
    return local_success, local_errors

# ============================
# 7️⃣ TRAITEMENT D'UN FICHIER
# ============================

def process_result_file(result_file):
    base_name  = os.path.splitext(os.path.basename(result_file))[0]
    output_csv = os.path.join(details_dir, f"Details_{base_name}.csv")
    stats_file = os.path.join(details_dir, f"Stats_{base_name}.txt")

    log_print(f"\n{'='*60}")
    log_print(f"📁 Traitement : {base_name}")
    log_print(f"{'='*60}")

    processed_links = load_progress(base_name)
    if processed_links:
        log_print(f"🔄 Reprise : {len(processed_links)} services déjà traités")

    if not os.path.exists(output_csv):
        with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["Titre", "Vendeur", "Acheteurs", "Notes",
                             "Date Dernier Avis", "Catégorie",
                             "Sous-Catégorie", "Mots Clés", "Lien"])

    services = []
    try:
        with open(result_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                link = row.get("Lien du Service", row.get("link", "")).strip()
                if link and link not in processed_links:
                    services.append(link)
    except Exception as e:
        log_print(f"❌ Erreur lecture {result_file}: {e}", "error")
        return 0

    total_services = len(services)
    log_print(f"🎯 {total_services} services à traiter avec {NB_WORKERS} workers")

    if total_services == 0:
        log_print(f"✅ Déjà complet !")
        return 0

    chunk_size = max(1, total_services // NB_WORKERS)
    chunks = []
    for i in range(NB_WORKERS):
        start = i * chunk_size
        end   = start + chunk_size if i < NB_WORKERS - 1 else total_services
        chunk = services[start:end]
        if chunk:
            chunks.append(chunk)

    log_print(f"📦 Division : {[len(c) for c in chunks]} services par worker")

    total_success = 0
    total_errors  = 0

    with ThreadPoolExecutor(max_workers=NB_WORKERS) as executor:
        futures = {
            executor.submit(
                worker_process,
                worker_id + 1,
                chunk,
                output_csv,
                base_name,
                processed_links
            ): worker_id
            for worker_id, chunk in enumerate(chunks)
        }

        for future in as_completed(futures):
            try:
                success, errors = future.result()
                total_success  += success
                total_errors   += errors
            except Exception as e:
                log_print(f"❌ Erreur future : {e}", "error")

    save_progress(base_name, processed_links)

    with open(stats_file, "w", encoding="utf-8") as f:
        f.write(f"RAPPORT - {base_name}\n")
        f.write("=" * 60 + "\n")
        f.write(f"Total traités : {total_services}\n")
        f.write(f"Succès        : {total_success}\n")
        f.write(f"Erreurs       : {total_errors}\n")
        f.write(f"Workers       : {NB_WORKERS}\n")

    log_print(f"\n📊 {base_name} : {total_success} succès, {total_errors} erreurs")
    return total_success

# ============================
# 8️⃣ BOUCLE PRINCIPALE
# ============================

grand_total = 0

try:
    for result_file in result_files:
        try:
            total       = process_result_file(result_file)
            grand_total += total
        except Exception as e:
            log_print(f"❌ Erreur critique sur {result_file}: {e}", "error")
            continue

except KeyboardInterrupt:
    log_print("\n🛑 Interruption utilisateur", "warning")

except Exception as e:
    log_print(f"❌ Erreur globale : {e}", "error")

finally:
    log_print("\n" + "=" * 60)
    log_print("       📊 RAPPORT FINAL")
    log_print("=" * 60)
    log_print(f"📁 Dossier détails : {details_dir}")
    log_print(f"🎯 TOTAL GÉNÉRAL   : {grand_total} services détaillés")
    log_print(f"⚡ Workers utilisés : {NB_WORKERS}")
    log_print("=" * 60)
