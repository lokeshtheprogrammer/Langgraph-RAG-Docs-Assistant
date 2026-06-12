import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def wait_for_server():
    print("Waiting for server to start...")
    for _ in range(30):
        try:
            res = requests.get(f"{BASE_URL}/health")
            if res.status_code == 200:
                print("Server is up!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    print("Server failed to start within 30 seconds.")
    return False

def test_endpoints():
    print("Testing /health...")
    res = requests.get(f"{BASE_URL}/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"

    print("Testing /documents (empty list expected)...")
    res = requests.get(f"{BASE_URL}/documents")
    assert res.status_code == 200, f"List documents failed: {res.text}"

    print("Smoke tests passed successfully!")

if __name__ == "__main__":
    if not wait_for_server():
        sys.exit(1)
    test_endpoints()
