import os
import csv
import json
import glob
from datetime import datetime

# ============================
# CONFIGURATION
# ============================
base_dir      = os.path.join(os.getcwd(), "categories")
sous_cat_dir  = os.path.join(base_dir, "sous_categories")
resultats_dir = os.path.join(base_dir, "resultats")
details_dir   = os.path.join(base_dir, "details_services")
progress_dir  = os.path.join(base_dir, "progress_details")
input_file    = os.path.join(base_dir, "categories_khamsat.csv")
output_file   = os.path.join(os.getcwd(), "DASHBOARD.md")

now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

# ============================
# COLLECTE DES DONNÉES
# ============================

# JOB1 — Catégories principales
nb_categories = 0
try:
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        nb_categories = sum(1 for row in csv.reader(f)) - 1
except:
    nb_categories = 0

# JOB2 — Sous-catégories
sous_cat_files = glob.glob(os.path.join(sous_cat_dir, "*.csv"))
nb_sous_cats   = 0
for f in sous_cat_files:
    try:
        with open(f, 'r', encoding='utf-8-sig') as fp:
            nb_sous_cats += sum(1 for row in csv.reader(fp)) - 1
    except:
        pass

# JOB3 — Services
resultats_files = glob.glob(os.path.join(resultats_dir, "Resultats_*.csv"))
nb_services     = 0
services_detail = {}
for f in resultats_files:
    try:
        with open(f, 'r', encoding='utf-8-sig') as fp:
            count = sum(1 for row in csv.reader(fp)) - 1
            nb_services += count
            name = os.path.splitext(os.path.basename(f))[0].replace("Resultats_", "")
            services_detail[name] = count
    except:
        pass

# JOB4 — Détails + Progression
total_processed  = 0
total_services   = nb_services
progress_detail  = {}

for f in resultats_files:
    filename      = os.path.splitext(os.path.basename(f))[0]
    cat_name      = filename.replace("Resultats_", "")
    progress_file = os.path.join(progress_dir, f"progress_{filename}.json")

    total_in_cat = services_detail.get(cat_name, 0)
    done_in_cat  = 0

    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r', encoding='utf-8') as fp:
                done_in_cat = len(json.load(fp))
        except:
            done_in_cat = 0

    total_processed += done_in_cat
    progress_detail[cat_name] = {
        "total": total_in_cat,
        "done":  done_in_cat
    }

# Pourcentage global
pct_global = (total_processed / total_services * 100) if total_services > 0 else 0

# Estimation temps restant
restants       = total_services - total_processed
temps_restant  = restants * 2  # ~2 sec par service
heures         = temps_restant // 3600
minutes        = (temps_restant % 3600) // 60

# Statut Job4
if total_processed == 0:
    job4_status = "⏳ En attente"
elif total_processed >= total_services:
    job4_status = "✅ COMPLET"
else:
    job4_status = "🔄 EN COURS"

# ============================
# GÉNÉRATION DU DASHBOARD
# ============================
lines = []
lines.append("# 📊 DASHBOARD — KHAMSAT SCRAPER")
lines.append(f"\n> 🕐 Dernière mise à jour : **{now}**")
lines.append("\n---\n")

# STATUS GÉNÉRAL
lines.append("## 🚦 STATUS DU CYCLE")
lines.append("\n| Job | Tâche | Résultat | Status |")
lines.append("|-----|-------|----------|--------|")

# Job1
s1 = "✅" if nb_categories > 0 else "⏳"
lines.append(f"| Job1 | Catégories principales | **{nb_categories}** catégories | {s1} |")

# Job2
s2 = "✅" if nb_sous_cats > 0 else "⏳"
lines.append(f"| Job2 | Sous-catégories | **{nb_sous_cats}** sous-catégories | {s2} |")

# Job3
s3 = "✅" if nb_services > 0 else "⏳"
lines.append(f"| Job3 | Services | **{nb_services}** services | {s3} |")

# Job4
lines.append(f"| Job4 | Détails services | **{total_processed}/{total_services}** ({pct_global:.1f}%) | {job4_status} |")

lines.append("\n---\n")

# BARRE DE PROGRESSION JOB4
lines.append("## 📈 PROGRESSION JOB4 — Détails services\n")
filled  = int(pct_global / 5)
empty   = 20 - filled
bar     = "█" * filled + "░" * empty
lines.append(f"```")
lines.append(f"[{bar}] {pct_global:.1f}%")
lines.append(f"Traités  : {total_processed} services")
lines.append(f"Restants : {restants} services")
if total_processed < total_services:
    lines.append(f"Temps est: ~{heures}h {minutes:02d}min")
else:
    lines.append(f"Temps est: ✅ TERMINÉ !")
lines.append(f"```")

lines.append("\n---\n")

# DÉTAIL PAR CATÉGORIE
lines.append("## 📂 DÉTAIL PAR CATÉGORIE\n")
lines.append("| Catégorie | Services | Traités | Progression | Status |")
lines.append("|-----------|----------|---------|-------------|--------|")

for cat, data in sorted(progress_detail.items()):
    total_c = data["total"]
    done_c  = data["done"]
    pct_c   = (done_c / total_c * 100) if total_c > 0 else 0
    filled_c = int(pct_c / 10)
    bar_c    = "█" * filled_c + "░" * (10 - filled_c)

    if done_c == 0:
        status_c = "⏳"
    elif done_c >= total_c:
        status_c = "✅"
    else:
        status_c = "🔄"

    lines.append(f"| {cat} | {total_c} | {done_c} | `{bar_c}` {pct_c:.0f}% | {status_c} |")

lines.append("\n---\n")

# STATISTIQUES FINALES
lines.append("## 📊 STATISTIQUES FINALES\n")
details_files = glob.glob(os.path.join(details_dir, "Details_*.csv"))
total_details = 0
for f in details_files:
    try:
        with open(f, 'r', encoding='utf-8-sig') as fp:
            total_details += sum(1 for row in csv.reader(fp)) - 1
    except:
        pass

lines.append(f"- 📁 Fichiers de détails générés : **{len(details_files)}**")
lines.append(f"- 📝 Total lignes extraites       : **{total_details}**")
lines.append(f"- 🗂️ Catégories traitées          : **{nb_categories}**")
lines.append(f"- 📋 Sous-catégories              : **{nb_sous_cats}**")
lines.append(f"- 🔗 Services totaux              : **{nb_services}**")

lines.append("\n---")
lines.append("\n*Dashboard généré automatiquement toutes les 30 minutes*")

# ÉCRITURE DU FICHIER
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("\n".join(lines))

print(f"✅ DASHBOARD.md généré avec succès !")
print(f"📊 {total_processed}/{total_services} services traités ({pct_global:.1f}%)")
