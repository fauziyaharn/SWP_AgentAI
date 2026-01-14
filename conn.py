"""
Database Connection Module - Supabase REST Client
Modul untuk koneksi ke Supabase REST API menggunakan SUPABASE_URL + SUPABASE_ANON_KEY

Instructions:
- Set SUPABASE_URL dan SUPABASE_ANON_KEY di .env (sama seperti di BE)
- Install dependency: pip install requests (sudah di requirements.txt)
- Tidak perlu psycopg2 atau DATABASE_URL
"""

import os
import requests


class SupabaseClient:
    """Simple Supabase REST client untuk AI backend.
    
    Menggunakan SUPABASE_URL + SUPABASE_ANON_KEY dari .env
    Menyediakan method get_items_by_filter() untuk sistem rekomendasi.
    """
    
    def __init__(self, supabase_url=None, anon_key=None):
        """Inisialisasi Supabase REST client
        
        Args:
            supabase_url: Base URL Supabase (default dari env SUPABASE_URL)
            anon_key: Anon key untuk auth (default dari env SUPABASE_ANON_KEY)
        """
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        # Prefer anon key, but fall back to service role key if available (server-side)
        self.anon_key = (
            anon_key
            or os.getenv('SUPABASE_ANON_KEY')
            or os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        )
        
        # Konstruksi REST endpoint untuk tabel items
        if self.supabase_url:
            self.rest_url = f"{self.supabase_url}/rest/v1/items?select=*"
        else:
            self.rest_url = None

    def connect(self):
        """Test koneksi ke Supabase"""
        if not self.rest_url or not self.anon_key:
            print("✗ SUPABASE_URL atau SUPABASE_ANON_KEY tidak diset")
            return False
        
        try:
            headers = {
                'apikey': self.anon_key,
                'Authorization': f"Bearer {self.anon_key}"
            }
            # Test dengan limit 1
            test_url = f"{self.rest_url}&limit=1"
            r = requests.get(test_url, headers=headers, timeout=5)
            
            if r.status_code == 200:
                print("✓ Berhasil terhubung ke Supabase")
                return True
            else:
                print(f"✗ Supabase connection failed: {r.status_code}")
                return False
        except Exception as e:
            print(f"✗ Error koneksi ke Supabase: {e}")
            return False

    def get_items_by_filter(self, tema=None, lokasi=None, budget_min=None, budget_max=None, category=None, flexible=True):
        """Mengambil items dari Supabase dengan filter
        
        Args:
            tema: Tema pernikahan (optional)
            lokasi: Lokasi (optional)
            budget_min: Budget minimum (optional)
            budget_max: Budget maximum (optional)
            category: Nama kategori (optional)
            flexible: Jika True, relax filter jika tidak ada hasil (default: True)
            
        Returns:
            List of dict berisi data items
        """
        if not self.rest_url or not self.anon_key:
            return []

        filters = []
        
        # Filter tema: search nama, deskripsi, vendor dengan ilike
        if tema:
            term = tema.replace(' ', '%')
            # Supabase PostgREST syntax: or=(col1.ilike.pattern, col2.ilike.pattern)
            filters.append(f"or=(name.ilike.*{term}*,description.ilike.*{term}*,vendor.ilike.*{term}*)")

        # Filter lokasi: search vendor, deskripsi
        if lokasi:
            term = lokasi.replace(' ', '%')
            filters.append(f"or=(vendor.ilike.*{term}*,description.ilike.*{term}*)")

        # Filter kategori: match exact
        if category:
            # Try both common column names
            filters.append(f"or=(category_name.ilike.*{category}*,kategori.ilike.*{category}*)")

        # Filter budget dengan toleransi 20% jika flexible
        if budget_min is not None:
            if flexible:
                adjusted_min = int(budget_min * 0.8)
            else:
                adjusted_min = int(budget_min)
            filters.append(f"price=gte.{adjusted_min}")

        if budget_max is not None:
            if flexible:
                adjusted_max = int(budget_max * 1.2)
            else:
                adjusted_max = int(budget_max)
            filters.append(f"price=lte.{adjusted_max}")

        # Limit untuk safety
        filters.append('limit=200')

        # Konstruksi query string
        query = self.rest_url
        if filters:
            query += "&" + "&".join(filters)

        # Header dengan auth
        headers = {
            'apikey': self.anon_key,
            'Authorization': f"Bearer {self.anon_key}"
        }

        try:
            r = requests.get(query, headers=headers, timeout=10)
            if r.status_code != 200:
                print(f"✗ Supabase request failed: {r.status_code}")
                if r.text:
                    print(f"   Response: {r.text[:200]}")
                return []
            
            data = r.json()
            if not isinstance(data, list):
                return []

            # Mapping hasil dari Supabase ke format internal
            results = []
            for row in data:
                item = {
                    'id': row.get('id'),
                    'name': row.get('name') or row.get('nama') or '-',
                    'vendor': row.get('vendor') or '-',
                    'description': row.get('description') or row.get('deskripsi') or '-',
                    'price': int(row.get('price') or row.get('harga_min') or 0),
                    'image_url': row.get('image_url') or row.get('image_url_full') or '',
                    'image_url_full': row.get('image_url_full') or row.get('image_url') or '',
                    'status': row.get('status') or 'ongoing',
                    'category_name': row.get('category_name') or row.get('kategori') or '',
                    'category_id': row.get('category_id'),
                }
                results.append(item)

            # Jika tidak ada hasil dan flexible mode, coba relax filter
            if not results and flexible and (tema or lokasi or budget_min or budget_max):
                print("   🔄 Tidak ada hasil dengan filter ketat, mencoba filter yang lebih fleksibel...")
                
                if budget_min or budget_max:
                    return self.get_items_by_filter(tema, lokasi, None, None, category, flexible=False)
                elif lokasi:
                    return self.get_items_by_filter(tema, None, budget_min, budget_max, category, flexible=False)
                elif tema:
                    return self.get_items_by_filter(None, lokasi, budget_min, budget_max, category, flexible=False)

            return results

        except Exception as e:
            print(f"✗ Error saat query Supabase: {e}")
            return []

    def get_all_categories(self):
        """Mengambil semua kategori dari Supabase"""
        if not self.rest_url or not self.anon_key:
            return []
        
        # Query tabel categories
        categories_url = f"{self.supabase_url}/rest/v1/categories?select=*"
        headers = {
            'apikey': self.anon_key,
            'Authorization': f"Bearer {self.anon_key}"
        }
        
        try:
            r = requests.get(categories_url, headers=headers, timeout=10)
            if r.status_code == 200:
                return r.json()
            return []
        except Exception as e:
            print(f"✗ Error mengambil categories: {e}")
            return []


def get_db_connection():
    """Fungsi helper untuk mendapatkan koneksi database (Supabase).
    
    Returns:
        SupabaseClient object jika koneksi berhasil, atau None jika gagal.
    """
    client = SupabaseClient()
    if client.connect():
        return client
    return None
