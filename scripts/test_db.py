"""Quick DB test helper

Usage:
  py scripts/test_db.py

This script tries to obtain a DB client via `get_db_connection()` from `conn.py`.
It prints connection type, sample item count and a few sample names.
"""
import os
import sys
import pathlib

# Ensure project root is on sys.path so `import conn` works when running from scripts/
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from conn import get_db_connection
except Exception as e:
    print("✗ Gagal import module conn:", e)
    sys.exit(1)
    
# Load .env from project root if present
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=ROOT / '.env')
except Exception:
    # python-dotenv optional; ignore if not installed
    pass

# Also try to load BE .env (sepasangwp) if present to mirror backend keys
try:
    be_env = ROOT.parent / 'GitHub' / 'sepasangwp' / '.env'
    if be_env.exists():
        try:
            load_dotenv(dotenv_path=be_env)
            print(f"Loaded BE .env from: {be_env}")
        except Exception:
            pass
except Exception:
    pass


def main():
    print("== DB Connection Test ==")
    conn = get_db_connection()
    if not conn:
        print("✗ No database connection available (None)")
        print("  - Pastikan SUPABASE_URL + SUPABASE_ANON_KEY ada di .env, atau DATABASE_URL jika menggunakan Postgres.")
        sys.exit(1)

    print(f"✓ Connected via: {conn.__class__.__name__}")

    try:
        items = conn.get_items_by_filter()
        if items is None:
            print("✗ get_items_by_filter returned None")
            sys.exit(1)

        print(f"Sample items returned: {len(items)} items")
        for it in (items[:5] if items else []):
            print(' -', it.get('name') or it.get('nama') or it.get('id'))

    except Exception as e:
        print('✗ Error querying items:', e)
        sys.exit(1)

    print('OK')
    sys.exit(0)


if __name__ == '__main__':
    main()
