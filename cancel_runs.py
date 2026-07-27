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
# ANNULATION DES RUNS EN COURS
# ==========================================
print(f"🔍 Recherche des runs en cours sur {REPO}...")

total_cancelled = 0

# Statuts à annuler
statuts = ["in_progress", "queued", "waiting"]

for statut in statuts:
    page = 1
    while True:
        url = f"https://api.github.com/repos/{REPO}/actions/runs?status={statut}&per_page=100&page={page}"
        response = requests.get(url, headers=headers)
        runs = response.json().get("workflow_runs", [])

        if not runs:
            break

        for run in runs:
            run_id   = run["id"]
            run_name = run["name"]

            # Ne pas annuler le cancel_runs lui-même
            if run_name == "Cancel Running Workflows":
                print(f"⏭️ Ignoré (run actuel) : {run_name}")
                continue

            cancel_url      = f"https://api.github.com/repos/{REPO}/actions/runs/{run_id}/cancel"
            cancel_response = requests.post(cancel_url, headers=headers)

            if cancel_response.status_code == 202:
                total_cancelled += 1
                print(f"✅ Annulé : [{run_id}] {run_name} | statut: {statut}")
            else:
                print(f"❌ Erreur {run_id} : {cancel_response.status_code}")

        page += 1

print(f"\n✅ TERMINÉ : {total_cancelled} runs annulés !")
