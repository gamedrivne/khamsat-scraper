import requests
import os

# ==========================================
# CONFIGURATION VIA SECRETS GITHUB
# ==========================================
TOKEN = os.environ.get("GITHUB_TOKEN")
REPO  = os.environ.get("GITHUB_REPO")

if not TOKEN:
    print("❌ ERREUR : GITHUB_TOKEN non trouvé !")
    exit(1)

if not REPO:
    print("❌ ERREUR : GITHUB_REPO non trouvé !")
    exit(1)

headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# ==========================================
# SUPPRESSION DES ANCIENS RUNS
# ==========================================
print(f"🔍 Récupération des workflow runs de {REPO}...")

page = 1
total_deleted = 0

while True:
    url = f"https://api.github.com/repos/{REPO}/actions/runs?per_page=100&page={page}"
    response = requests.get(url, headers=headers)
    runs = response.json().get("workflow_runs", [])

    if not runs:
        break

    for run in runs:
        run_id   = run["id"]
        run_name = run["name"]
        run_date = run["created_at"]

        # Ne pas supprimer le run actuel (cleanup lui-même)
        if run_name == "Cleanup Old Workflow Runs":
            print(f"⏭️ Ignoré (run actuel) : {run_name}")
            continue

        del_url      = f"https://api.github.com/repos/{REPO}/actions/runs/{run_id}"
        del_response = requests.delete(del_url, headers=headers)

        if del_response.status_code == 204:
            total_deleted += 1
            print(f"🗑️ Supprimé : [{run_id}] {run_name} | {run_date}")
        else:
            print(f"❌ Erreur {run_id} : {del_response.status_code}")

    page += 1

print(f"\n✅ TERMINÉ : {total_deleted} runs supprimés !")
