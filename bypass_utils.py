# Advanced bypass utilities for SSC website restrictions
import requests
import time
import random
from urllib.parse import urljoin, urlparse
import base64

class SSCBypassManager:
    """
    Advanced request manager to bypass SSC website restrictions.
    Implements techniques similar to what websites like RankItra use.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.setup_session()
    
    def setup_session(self):
        """Setup session with realistic browser headers"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-User': '?1',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Cache-Control': 'max-age=0'
        }
        self.session.headers.update(headers)
    
    def get_referer_from_url(self, url):
        """Extract potential referer from URL structure"""
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Common SSC referer patterns
        potential_referers = [
            f"{base_url}/",
            f"{base_url}/per/",
            "https://ssc.nic.in/",
            "https://ssc.digialm.com/",
            "https://www.digialm.com/"
        ]
        return random.choice(potential_referers)
    
    def simulate_browser_navigation(self, url):
        """
        Simulate realistic browser navigation pattern
        This mimics how a real user would access the page
        """
        try:
            # Step 1: Visit the base domain first
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            print(f"Step 1: Visiting base domain {base_url}")
            self.session.get(base_url, timeout=10)
            time.sleep(random.uniform(0.5, 1.5))
            
            # Step 2: Set referer and visit target URL
            referer = self.get_referer_from_url(url)
            self.session.headers['Referer'] = referer
            
            print(f"Step 2: Accessing target URL with referer: {referer}")
            response = self.session.get(url, timeout=30)
            
            return response
            
        except Exception as e:
            print(f"Browser navigation simulation failed: {e}")
            return None
    
    def try_proxy_methods(self, url):
        """
        Try alternative methods to access the content
        """
        methods = [
            self.try_allorigins_proxy,
            self.try_cors_anywhere_proxy,
            self.try_thingproxy,
            self.try_archive_org,
            self.try_google_cache
        ]
        
        for method in methods:
            try:
                print(f"🔄 Trying {method.__name__}...")
                result = method(url)
                if result and result.status_code == 200:
                    print(f"✅ Success with {method.__name__}")
                    return result
                else:
                    print(f"❌ Failed with {method.__name__}")
            except Exception as e:
                print(f"❌ {method.__name__} error: {e}")
                continue
        
        return None
    
    def try_allorigins_proxy(self, url):
        """Try accessing through allorigins proxy"""
        proxy_url = f"https://api.allorigins.win/get?url={url}"
        try:
            response = self.session.get(proxy_url, timeout=20)
            if response.status_code == 200:
                # AllOrigins returns JSON with contents field
                import json
                data = response.json()
                if 'contents' in data:
                    # Create a mock response object
                    class MockResponse:
                        def __init__(self, content):
                            self.text = content
                            self.status_code = 200
                    return MockResponse(data['contents'])
            return None
        except:
            return None
    
    def try_cors_anywhere_proxy(self, url):
        """Try accessing through CORS anywhere proxy"""
        proxy_url = f"https://cors-anywhere.herokuapp.com/{url}"
        try:
            headers = self.session.headers.copy()
            headers['X-Requested-With'] = 'XMLHttpRequest'
            response = self.session.get(proxy_url, headers=headers, timeout=15)
            return response if response.status_code == 200 else None
        except:
            return None
    
    def try_thingproxy(self, url):
        """Try accessing through thingproxy"""
        proxy_url = f"https://thingproxy.freeboard.io/fetch/{url}"
        try:
            response = self.session.get(proxy_url, timeout=15)
            return response if response.status_code == 200 else None
        except:
            return None
    
    def try_archive_org(self, url):
        """Try getting from Internet Archive"""
        archive_url = f"https://web.archive.org/web/{url}"
        try:
            return self.session.get(archive_url, timeout=15)
        except:
            return None
    
    def try_google_cache(self, url):
        """Try accessing Google's cached version"""
        cache_url = f"https://webcache.googleusercontent.com/search?q=cache:{url}"
        try:
            return self.session.get(cache_url, timeout=15)
        except:
            return None
    
    def fetch_with_all_methods(self, url, max_retries=3):
        """
        Comprehensive fetching with proxy methods prioritized
        """
        print(f"🔄 Attempting to fetch: {url}")
        
        # Method 1: Try proxy methods first (most reliable for SSC)
        print("🌐 Trying proxy methods first...")
        proxy_response = self.try_proxy_methods(url)
        if proxy_response and proxy_response.status_code == 200:
            print("✅ Success: Proxy method")
            return proxy_response.text
        
        # Method 2: Direct access with browser simulation
        try:
            print("🚀 Trying direct browser simulation...")
            response = self.simulate_browser_navigation(url)
            if response and response.status_code == 200:
                print("✅ Success: Direct browser simulation")
                return response.text
        except Exception as e:
            print(f"❌ Direct access failed: {e}")
        
        # Method 3: Multiple user agents with delays
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36'
        ]
        
        for attempt in range(max_retries):
            try:
                # Rotate user agent
                self.session.headers['User-Agent'] = random.choice(user_agents)
                
                # Add random delay
                delay = random.uniform(1, 3)
                print(f"⏱️  Waiting {delay:.1f}s before retry {attempt + 1}")
                time.sleep(delay)
                
                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    print(f"✅ Success: Retry {attempt + 1} with user agent rotation")
                    return response.text
                elif response.status_code == 403:
                    print(f"🚫 403 Forbidden on attempt {attempt + 1}")
                else:
                    print(f"⚠️  HTTP {response.status_code} on attempt {attempt + 1}")
                    
            except Exception as e:
                print(f"❌ Attempt {attempt + 1} failed: {e}")
        
        # If all methods fail
        print("❌ All methods exhausted")
        raise Exception(f"Unable to fetch {url} after trying all bypass methods")

def make_advanced_request(url, max_retries=5):
    """
    Main function to use advanced bypass techniques
    """
    bypass_manager = SSCBypassManager()
    return bypass_manager.fetch_with_all_methods(url, max_retries)