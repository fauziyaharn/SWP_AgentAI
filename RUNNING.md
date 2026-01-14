# Menjalankan Backend (transformers_swp/app.py)

Panduan singkat untuk menjalankan backend Flask lokal dan menguji endpoint `/api/process`.

Persyaratan:

- Python (direkomendasikan 3.10+)
- Dependensi: lihat `transformers_swp/requirements.txt`

Catatan penting (PyTorch):

- PyTorch releases are platform- and Python-version-specific. If `pip install -r requirements.txt` fails with errors like "No matching distribution found for torch==...", please follow the official PyTorch install selector at https://pytorch.org/get-started/locally/ and run the generated install command (choose CPU or the matching CUDA version).
- Example CPU-only install command (Windows PowerShell):

```powershell
py -3 -m pip install torch --index-url https://download.pytorch.org/whl/cpu
```

Langkah cepat (PowerShell):

```powershell

# Install dependensi
python -m pip install -r transformers_swp/requirements.txt

# (opsional) install flask-cors jika belum terpasang
python -m pip install flask-cors

# Jalankan server (di terminal baru):
cd D:\Nurul\Prokon\transformers_swp
python app.py

# Cek endpoint (PowerShell):
Invoke-RestMethod -Uri http://127.0.0.1:5000/api/process -Method Post -ContentType 'application/json' -Body '{"query":"cari catering di bandung budget 20 juta"}'
```

Catatan:

- Aplikasi mencoba terhubung ke database via `DATABASE_URL` (Supabase/Postgres) jika tersedia; jika tidak tersedia atau koneksi gagal, aplikasi otomatis menggunakan fallback CSV.

  Alternatif: jika Anda ingin backend hanya menggunakan Supabase REST (tanpa menyimpan DATABASE_URL), Anda dapat set `SUPABASE_PUBLIC_REST` dan (opsional) `SUPABASE_ANON_KEY` di `.env`. Contoh:

  SUPABASE_PUBLIC_REST=https://<project>.supabase.co/rest/v1/items?select=\*
  SUPABASE_ANON_KEY=<your_anon_key>

  Cara connect ke Supabase (full DB via DATABASE_URL):

  1. Di Supabase dashboard → Settings → Database → Connection string, salin connection string (Postgres URL).
  2. Di PowerShell sementara: ` $env:DATABASE_URL = "postgresql://<user>:<password>@<host>:5432/<db>?sslmode=require"`
  3. Atau tambahkan ke `.env`: `DATABASE_URL=postgresql://...` lalu restart aplikasi.

  Tes koneksi cepat (PowerShell):

  ```powershell
  py -c "from conn import DatabaseConnection; db = DatabaseConnection(database_url=\"$env:DATABASE_URL\"); print('connected' if db.connect() else 'failed')"
  ```

- Frontend (Vite) harus diarahkan ke `VITE_API_URL` yang sesuai, mis. `http://localhost:5000` saat testing lokal.
- Jika ingin mengaktifkan seq2seq (Hugging Face) untuk reply generator, set environment variable `ENABLE_SEQ2SEQ=1` sebelum menjalankan `app.py`. Perlu menginstal paket `transformers` dan `sentencepiece` (sudah ditambahkan ke `requirements.txt`).
