import requests

# ==========================================
# CONFIGURATION
# ==========================================
TOKEN = "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"  # ← Remplace par ton token
REPO  = "gamedrivne/khamsat-scraper"  # ← Ton repo

headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# ==========================================
# SUPPRESSION DES ANCIENS RUNS
# ==========================================
print("🔍 Récupération des workflow runs...")

page = 1
total_deleted = 0

while True:
    url = f"https://api.github.com/repos/{REPO}/actions/runs?per_page=100&page={page}"
    response = requests.get(url, headers=headers)
    runs = response.json().get("workflow_runs", [])
    
    if not runs:
        break
    
    for run in runs:
        run_id = run["id"]
        run_name = run["name"]
        run_date = run["created_at"]
        
        del_url = f"https://api.github.com/repos/{REPO}/actions/runs/{run_id}"
        del_response = requests.delete(del_url, headers=headers)
        
        if del_response.status_code == 204:
            total_deleted += 1
            print(f"🗑️ Supprimé : {run_name} | {run_date}")
        else:
            print(f"❌ Erreur sur run {run_id} : {del_response.status_code}")
    
    page += 1

print(f"\n✅ TERMINÉ : {total_deleted} runs supprimés !")
