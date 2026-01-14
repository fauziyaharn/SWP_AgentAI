"""
Simple Test Script untuk Wedding AI API
Test koneksi database dan chat endpoint
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_home():
    """Test homepage"""
    print("\n1. Testing Homepage (/)...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

def test_health():
    """Test health check"""
    print("\n2. Testing Health Check (/api/health)...")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   AI Pipeline: {'✓' if data['ai_pipeline'] else '✗'}")
        print(f"   Database: {'✓' if data['database'] else '✗'}")
        print(f"   Recommendation Engine: {'✓' if data['recommendation_engine'] else '✗'}")
        print(f"   Package Planner: {'✓' if data['package_planner'] else '✗'}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

def test_database():
    """Test database connection dan ambil sample data"""
    print("\n3. Testing Database Connection (/api/test-db)...")
    try:
        response = requests.get(f"{BASE_URL}/api/test-db")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Database Status: {data['status']}")
            print(f"   ✓ Total Items in DB: {data['total_items']}")
            print(f"\n   Sample Data (5 items):")
            for i, item in enumerate(data['sample_items'], 1):
                print(f"   {i}. {item['name']}")
                print(f"      Category: {item['category']}")
                print(f"      Location: {item['location']}")
                print(f"      Price: Rp {item['min_price']:,} - Rp {item['max_price']:,}")
            return True
        else:
            print(f"   ✗ Database connection failed")
            print(f"   Response: {response.json()}")
            return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

def test_chat_api():
    """Test chat API dengan query sederhana"""
    print("\n4. Testing Chat API (/api/process)...")
    try:
        test_query = "Saya butuh venue di Jakarta budget 50 juta"
        print(f"   Query: '{test_query}'")
        
        response = requests.post(
            f"{BASE_URL}/api/process",
            json={"text": test_query}
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Intent: {data['intent']}")
            print(f"   ✓ Slots: {data['slots']}")
            print(f"   ✓ Reply: {data['assistant_reply'][:100]}...")
            
            if data.get('recommendations') and data['recommendations'].get('recommendations'):
                recs = data['recommendations']['recommendations']
                print(f"   ✓ Recommendations: {len(recs)} items found")
            
            return True
        else:
            print(f"   ✗ Chat API failed")
            return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

def main():
    print("="*60)
    print("Wedding AI API - Test Suite")
    print("="*60)
    
    results = {
        "Homepage": test_home(),
        "Health Check": test_health(),
        "Database": test_database(),
        "Chat API": test_chat_api()
    }
    
    print("\n" + "="*60)
    print("Test Results Summary:")
    print("="*60)
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:20s}: {status}")
    
    all_passed = all(results.values())
    print("\n" + ("="*60))
    if all_passed:
        print("🎉 All tests passed! AI sudah terhubung dengan Supabase!")
    else:
        print("⚠️ Some tests failed. Check errors above.")
    print("="*60)

if __name__ == "__main__":
    main()
