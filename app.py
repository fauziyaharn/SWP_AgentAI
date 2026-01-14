import os
import math
import json
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from local_transformer_intent import LocalIntentPipeline
from recommendation import RecommendationEngine
from package_planner import WeddingPackagePlanner

# optional seq2seq
try:
    from seq2seq_generator import generate_reply_safe
    USE_SEQ2SEQ = True
except:
    USE_SEQ2SEQ = False

app = Flask(__name__)
CORS(app)

# =========================
# GLOBAL STATE
# =========================
ai_pipeline = None
db = None
recommendation_engine = None
package_planner = None
wedding_dataset = None

# =========================
# SAFE JSON SANITIZER
# =========================
def _sanitize_for_json(obj):
    import pandas as _pd
    import numpy as np
    try:
        isna = _pd.isna
    except:
        isna = lambda x: False

    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [_sanitize_for_json(v) for v in obj]

    if isinstance(obj, (np.floating, np.integer)):
        try:
            return obj.item()
        except:
            return float(obj)

    try:
        if isna(obj):
            return None
    except:
        pass

    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj

    return obj

# =========================
# DB FALLBACK / Supabase Support
# =========================
from dotenv import load_dotenv
from conn import SupabaseClient

# Load .env if present
load_dotenv()


def get_db_connection():
    """Delegasi ke `conn.get_db_connection()` jika tersedia.

    Ini mencoba in order:
    1) DATABASE_URL (full Postgres/Supabase)
    2) SUPABASE_PUBLIC_REST (+ optional SUPABASE_ANON_KEY)

    Jika tidak ada koneksi, kembalikan None (caller dapat fallback ke CSV).
    """
    try:
        from conn import get_db_connection as _get_db
        return _get_db()
    except Exception as e:
        print(f"⚠️ Error delegating to conn.get_db_connection: {e}")
        return None

# =========================
# INIT SYSTEM
# =========================
def initialize_system():
    global ai_pipeline, db, recommendation_engine, package_planner, wedding_dataset

    print("🚀 Initializing Wedding System...")

    wedding_dataset = pd.read_csv("dataset_pertanyaan_wedding.csv")

    if "harga_min" in wedding_dataset.columns:
        wedding_dataset["harga_min"] = wedding_dataset["harga_min"].fillna(0).astype(int)

    if "harga_max" in wedding_dataset.columns:
        wedding_dataset["harga_max"] = wedding_dataset["harga_max"].fillna(999999999).astype(int)

    print("✓ CSV Loaded")

    if ai_pipeline is None:
        ai_pipeline = LocalIntentPipeline("models/local_transformer_intent")
        print("✓ Local Intent Model Ready")

    db_conn = get_db_connection()

    if not db_conn:
        print("⚠️ DB Not Connected → Using CSV Fallback")
        db = wedding_dataset
    else:
        db = db_conn
        print("✓ Database Ready")

    recommendation_engine = RecommendationEngine(n_clusters=3)
    print("✓ Recommendation Engine Ready")

    package_planner = WeddingPackagePlanner(db)
    print("✓ Package Planner Ready")

    print("🎉 System Ready!")

# =========================
# REPLY GENERATOR
# =========================
def generate_assistant_reply(ai_result: dict, clustering_result: dict, items: list):
    intent = ai_result.get('intent_pred', '')
    slots = ai_result.get('slots', {})

    if intent == 'estimasi_budget':
        reply = "Kamu ingin estimasi budget ya."
    elif intent in ['cari_venue', 'cari_dekor', 'cari_catering', 'cari_vendor']:
        reply = "Baik, aku carikan rekomendasinya ya."
    elif intent == 'tanya_kemungkinan':
        reply = "Oke, aku cek kemungkinan opsinya dulu."
    else:
        reply = "Berikut rekomendasi terbaik untuk kamu."

    parts = [reply]

    if slots:
        slot_text = []
        if slots.get('tema'):
            slot_text.append(f"tema {slots['tema']}")
        if slots.get('lokasi'):
            slot_text.append(f"lokasi {slots['lokasi']}")
        if slots.get('budget_min') or slots.get('budget_max'):
            bmin = slots.get('budget_min')
            bmax = slots.get('budget_max')
            if bmin and bmax:
                slot_text.append(f"budget Rp {int(bmin):,} - Rp {int(bmax):,}")
            elif bmin:
                slot_text.append(f"budget minimal Rp {int(bmin):,}")
            elif bmax:
                slot_text.append(f"budget maksimal Rp {int(bmax):,}")

        if slot_text:
            parts.append("Dengan preferensi: " + ", ".join(slot_text))

    if clustering_result and clustering_result.get("recommendations"):
        parts.append(
            f"Aku temukan {len(clustering_result['recommendations'])} pilihan cocok 😊"
        )

    return " ".join(parts)

# =========================
# API
# =========================
@app.route("/")
def home():
    """Homepage untuk test apakah server berjalan"""
    return jsonify({
        "status": "running",
        "message": "Wedding AI API is running",
        "endpoints": {
            "chat_ui": "/chat (Web Interface)",
            "chat_api": "/api/process (POST)",
            "test_db": "/api/test-db (GET)",
            "health": "/api/health (GET)"
        }
    })

@app.route("/chat")
def chat_interface():
    """Serve chat UI"""
    return send_from_directory('static', 'chat.html')

@app.route("/api/health")
def health_check():
    """Health check endpoint"""
    status = {
        "status": "healthy",
        "ai_pipeline": ai_pipeline is not None,
        "database": db is not None,
        "recommendation_engine": recommendation_engine is not None,
        "package_planner": package_planner is not None
    }
    return jsonify(status)

@app.route("/api/test-db")
def test_database():
    """Test koneksi database dan ambil sample data"""
    if not db:
        return jsonify({
            "error": "Database not connected",
            "db_status": "disconnected"
        }), 500
    
    try:
        # Ambil 5 items pertama dari database
        items = db.get_items_by_filter(flexible=True)
        
        # Ambil hanya 5 pertama
        sample_items = items[:5] if items else []
        
        result = {
            "status": "connected",
            "total_items": len(items) if items else 0,
            "sample_items": [
                {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "category": item.get("category"),
                    "location": item.get("location"),
                    "min_price": item.get("min_price"),
                    "max_price": item.get("max_price")
                }
                for item in sample_items
            ]
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "error": str(e),
            "db_status": "error"
        }), 500

@app.route("/api/process", methods=["POST"])
def chat_api():
    global ai_pipeline, recommendation_engine, package_planner, wedding_dataset

    data = request.get_json(force=True)
    text = data.get("text", "")

    if not text:
        return jsonify({"error": "text kosong"}), 400

    # AI Process
    ai_result = ai_pipeline.predict(text)
    
    # Get items from database
    if db and hasattr(db, 'get_items_by_filter'):
        # Get from Supabase
        items = db.get_items_by_filter(
            tema=ai_result.get("slots", {}).get("tema"),
            lokasi=ai_result.get("slots", {}).get("lokasi"),
            budget_min=ai_result.get("slots", {}).get("budget_min"),
            budget_max=ai_result.get("slots", {}).get("budget_max"),
            flexible=True
        )
    else:
        # Fallback to CSV
        items = []
    
    # Clustering recommendation
    clustering_result = recommendation_engine.cluster_items(
        items=items if items else [],
        slots=ai_result.get("slots", {})
    )

    # Package planning (optional, skip for now to keep it simple)
    package = None

    try:
        if USE_SEQ2SEQ:
            assistant_reply = generate_reply_safe(text)
        else:
            assistant_reply = generate_assistant_reply(ai_result, clustering_result, [])
    except:
        assistant_reply = generate_assistant_reply(ai_result, clustering_result, [])

    response = {
        "user_text": text,
        "intent": ai_result.get("intent_pred"),
        "slots": ai_result.get("slots"),
        "probabilities": ai_result.get("probs"),
        "recommendations": clustering_result,
        "wedding_package": package,
        "assistant_reply": assistant_reply
    }

    return jsonify(_sanitize_for_json(response))

# =========================
# RUN
# =========================
initialize_system()

if __name__ == "__main__":
    # Use FLASK_DEBUG env var to control debug mode (default: False in this repo)
    debug_env = os.getenv('FLASK_DEBUG', 'False').lower()
    debug = debug_env in ('1', 'true', 'yes')
    app.run(host="0.0.0.0", port=int(os.getenv('PORT', 5000)), debug=debug)

def get_csv_recommendations(intent, slots):
    df = wedding_dataset.copy()

    # intent2 yang dianggap rekomendasi
    if intent not in [
        "cari_rekomendasi_paket",
        "cari_vendor",
        "cari_venue",
        "cari_catering"
    ]:
        return []

    # filter lokasi
    if slots.get("lokasi"):
        df = df[df["lokasi"].str.contains(slots["lokasi"], case=False, na=False)]

    # filter budget
    if slots.get("budget_min"):
        budget = slots["budget_min"]
        df = df[
            (df["harga_min"] <= budget) &
            (df["harga_max"] >= budget)
        ]

    if len(df) == 0:
        return []

    # ambil top 5
    results = df.head(5)

    rekom = []
    for _, row in results.iterrows():
        rekom.append({
            "nama": row.get("nama", "-"),
            "lokasi": row.get("lokasi", "-"),
            "harga": f"{row.get('harga_min',0)} - {row.get('harga_max',0)}",
            "kategori": row.get("kategori","-")
        })

    return rekom
