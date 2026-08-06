import os
import re
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")


def get_client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[DB] Variables SUPABASE_URL / SUPABASE_KEY manquantes — skip DB.")
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ── Job 1 ──────────────────────────────────────────────────────────────────────
def upsert_categories(categories: list[dict]):
    """categories = [{'name': '...', 'slug': '...'}]"""
    client = get_client()
    if not client:
        return
    try:
        client.table("categories").upsert(categories, on_conflict="slug").execute()
        print(f"[DB] {len(categories)} catégories upsertées.")
    except Exception as e:
        print(f"[DB] Erreur upsert categories : {e}")


# ── Job 2 ──────────────────────────────────────────────────────────────────────
def upsert_subcategories(subcategories: list[dict]):
    """subcategories = [{'category_slug': '...', 'name': '...', 'slug': '...'}]"""
    client = get_client()
    if not client:
        return
    try:
        client.table("subcategories").upsert(subcategories, on_conflict="slug").execute()
        print(f"[DB] {len(subcategories)} sous-catégories upsertées.")
    except Exception as e:
        print(f"[DB] Erreur upsert subcategories : {e}")


# ── Job 3 ──────────────────────────────────────────────────────────────────────
def upsert_services(services: list[dict]):
    """services = [{'subcategory_slug': '...', 'category_slug': '...', 'title': '...', 'seller': '...', 'url': '...'}]"""
    client = get_client()
    if not client:
        return
    try:
        client.table("services").upsert(services, on_conflict="url").execute()
        print(f"[DB] {len(services)} services upsertés.")
    except Exception as e:
        print(f"[DB] Erreur upsert services : {e}")


# ── Job 4 ──────────────────────────────────────────────────────────────────────
def upsert_service_details(details: list[dict], cycle_number: int = 1):
    """details = liste de dicts avec les colonnes de service_details"""
    client = get_client()
    if not client:
        return
    try:
        rows = []
        for d in details:
            rows.append({
                "title":            d.get("Titre", ""),
                "seller":           d.get("Vendeur", ""),
                "buyers":           int(d.get("Acheteurs", 0) or 0),
                "notes":            int(d.get("Notes", 0) or 0),
                "last_review_date": d.get("Date Dernier Avis", ""),
                "category":         d.get("Catégorie", ""),
                "subcategory":      d.get("Sous-Catégorie", ""),
                "keywords":         d.get("Mots Clés", ""),
                "url":              d.get("Lien", ""),
                "cycle_number":     cycle_number,
            })
        # Filtre les lignes sans URL
        rows = [r for r in rows if r["url"]]
        client.table("service_details").upsert(rows, on_conflict="url").execute()
        print(f"[DB] {len(rows)} détails upsertés.")
    except Exception as e:
        print(f"[DB] Erreur upsert service_details : {e}")


# ── Pipeline runs ──────────────────────────────────────────────────────────────
def log_pipeline_start(job_name: str, cycle_number: int = 1) -> int:
    """Insère un run et retourne son ID."""
    client = get_client()
    if not client:
        return -1
    try:
        res = client.table("pipeline_runs").insert({
            "job_name":     job_name,
            "cycle_number": cycle_number,
            "status":       "running",
        }).execute()
        run_id = res.data[0]["id"]
        print(f"[DB] Pipeline run #{run_id} démarré pour {job_name}.")
        return run_id
    except Exception as e:
        print(f"[DB] Erreur log_pipeline_start : {e}")
        return -1


def log_pipeline_end(run_id: int, records_processed: int, status: str = "success"):
    """Met à jour le run avec le résultat final."""
    client = get_client()
    if not client or run_id == -1:
        return
    try:
        client.table("pipeline_runs").update({
            "status":            status,
            "records_processed": records_processed,
            "finished_at":       "now()",
        }).eq("id", run_id).execute()
        print(f"[DB] Pipeline run #{run_id} terminé — {records_processed} enregistrements.")
    except Exception as e:
        print(f"[DB] Erreur log_pipeline_end : {e}")
