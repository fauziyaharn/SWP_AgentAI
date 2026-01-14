import json
from app import app, initialize_system


def run_test():
    # Inisialisasi sistem (memuat model, dataset fallback, dll.)
    initialize_system()

    with app.test_client() as client:
        payload = {"query": "cari catering di bandung budget 20 juta"}
        resp = client.post('/api/process', json=payload)
        print('STATUS:', resp.status_code)
        try:
            data = resp.get_json()
            print(json.dumps(data, ensure_ascii=False, indent=2))
        except Exception:
            print(resp.get_data(as_text=True))


if __name__ == '__main__':
    run_test()
