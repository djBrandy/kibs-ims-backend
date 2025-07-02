#!/usr/bin/env python3
"""Simple test to check if Flask server is running"""

import requests
import sys

def test_server():
    try:
        response = requests.get('http://localhost:5000/api/products', timeout=5)
        print(f"✅ Server is running! Status: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running or not accessible on localhost:5000")
        return False
    except requests.exceptions.Timeout:
        print("❌ Server timeout - server may be slow to respond")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Flask server connection...")
    if test_server():
        sys.exit(0)
    else:
        print("\n💡 To start the server:")
        print("   cd ims-kibs-backend")
        print("   python run.py")
        sys.exit(1)