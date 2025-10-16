import requests
import time
import random

def fetch_with_proxy_only(url):
    """
    Simple proxy-only fetching function for maximum reliability
    """
    print(f"🌐 Fetching with proxy only: {url}")
    
    # Method 1: AllOrigins API
    try:
        print("🔄 Trying AllOrigins proxy...")
        proxy_url = f"https://api.allorigins.win/get?url={url}"
        response = requests.get(proxy_url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if 'contents' in data and data['contents']:
                print("✅ Success with AllOrigins proxy")
                return data['contents']
    except Exception as e:
        print(f"❌ AllOrigins failed: {e}")
    
    # Method 2: ThingProxy
    try:
        print("🔄 Trying ThingProxy...")
        proxy_url = f"https://thingproxy.freeboard.io/fetch/{url}"
        response = requests.get(proxy_url, timeout=30)
        if response.status_code == 200:
            print("✅ Success with ThingProxy")
            return response.text
    except Exception as e:
        print(f"❌ ThingProxy failed: {e}")
    
    # Method 3: JSONProxy
    try:
        print("🔄 Trying JSONProxy...")
        proxy_url = f"https://jsonp.afeld.me/?url={url}"
        response = requests.get(proxy_url, timeout=30)
        if response.status_code == 200:
            print("✅ Success with JSONProxy")
            return response.text
    except Exception as e:
        print(f"❌ JSONProxy failed: {e}")
    
    # Method 4: CORS Anywhere (if available)
    try:
        print("🔄 Trying CORS Anywhere...")
        proxy_url = f"https://cors-anywhere.herokuapp.com/{url}"
        headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(proxy_url, headers=headers, timeout=30)
        if response.status_code == 200:
            print("✅ Success with CORS Anywhere")
            return response.text
    except Exception as e:
        print(f"❌ CORS Anywhere failed: {e}")
    
    print("❌ All proxy methods failed")
    raise Exception("Unable to fetch content through any proxy method")

# Simple wrapper for scraper compatibility
def make_proxy_only_request(url):
    return fetch_with_proxy_only(url)