# 📋 WORKFLOWS — KHAMSAT SCRAPER

> Guide de référence des workflows GitHub Actions

---

## ⭐ WORKFLOW PRINCIPAL

| Fichier | Nom | Déclencheur | Rôle |
|---------|-----|-------------|------|
| `scraper-pipeline.yml` | Khamsat Full Pipeline (Monthly) | Le 15 de chaque mois à 22h UTC + manuel | Lance les 4 jobs en séquence : catégories → sous-catégories → services → détails |

### Options du pipeline principal
- **`reset: oui`** → Nouveau cycle complet (efface progression job4)
- **`reset: non`** → Reprend depuis la dernière progression

---

## 📊 DASHBOARD

| Fichier | Nom | Déclencheur | Rôle |
|---------|-----|-------------|------|
| `dashboard.yml` | Dashboard Update | Automatique après chaque job + manuel | `dashboard.yml` écoute : `continue-details-scraping, update-dashboard, trigger-dashboard` |

---

## 🔧 WORKFLOWS DE DEBUG (manuels uniquement)

| Fichier | Nom | Rôle |
|---------|-----|------|
| `scraper-categories.yml` | Khamsat Categories Scraper | Debug manuel — lance uniquement `rac1.py` |
| `scraper.yml` | Khamsat Sous-Categories Scraper | Debug manuel — lance uniquement `rac2.py` |
| `scraper-services.yml` | Khamsat Services Scraper | Debug manuel — lance uniquement `rac3.py` |
| `scraper-details.yml` | Khamsat Details Scraper | Debug manuel — lance uniquement `rac4.py` |

---

## 🗑️ MAINTENANCE

| Fichier | Nom | Rôle |
|---------|-----|------|
| `cleanup-runs.yml` | Cleanup Old Workflow Runs | Nettoie les vieux runs GitHub Actions (utilise `CLEANUP_TOKEN`) |

---

## ⚠️ RÈGLES IMPORTANTES

- Ne jamais activer `continue-details-scraping` dans `scraper-details.yml` — conflit avec le pipeline principal
- Toujours utiliser `scraper-pipeline.yml` pour les runs de production
- Les workflows de debug sont pour tests ponctuels uniquement

---

## 🔑 SECRETS REQUIS

| Secret | Utilisé par | Rôle |
|--------|-------------|------|
| `SUPABASE_URL` | Tous les jobs | URL du projet Supabase |
| `SUPABASE_KEY` | Tous les jobs | Clé secrète Supabase |
| `CLEANUP_TOKEN` | `cleanup-runs.yml` | Token GitHub pour supprimer les vieux runs |
