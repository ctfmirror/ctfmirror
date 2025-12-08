import requests
from bs4 import BeautifulSoup
import time
import sys

class Logger:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, 'w', encoding='utf-8')
    
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
    
    def flush(self):
        self.terminal.flush()
        self.log.flush()
    
    def close(self):
        self.log.close()

def login(session, username, password):
    """Login to HackMyVM"""
    login_url = "https://hackmyvm.eu/login/auth.php"
    
    try:
        # Prepare login data with correct field names
        login_data = {
            'admin': username,
            'password_usuario': password
        }
        
        # Post login credentials
        response = session.post(login_url, data=login_data, timeout=10, allow_redirects=True)
        
        # Check if we were redirected to dashboard (successful login)
        if 'dashboard' in response.url or ('Sign in' not in response.text and response.status_code == 200):
            print("✓ Login successful")
            return True
        else:
            print("✗ Login failed")
            return False
    except Exception as e:
        print(f"✗ Login error: {e}")
        return False

def get_machine_links(session, page_num):
    """Get all machine links from a machines list page"""
    url = f"https://hackmyvm.eu/machines/?p={page_num}"
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all machine links
        machine_links = []
        for h4 in soup.find_all('h4', class_='vmname'):
            a_tag = h4.find('a')
            if a_tag and 'href' in a_tag.attrs:
                href = a_tag['href']
                # Convert relative URL to absolute
                if href.startswith('/'):
                    full_url = f"https://hackmyvm.eu{href}"
                else:
                    full_url = href
                machine_links.append(full_url)
        
        return machine_links
    except Exception as e:
        print(f"Error fetching page {page_num}: {e}")
        return []

def get_download_link(session, machine_url):
    """Get the download link from a machine page"""
    try:
        response = session.get(machine_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find download link
        download_div = soup.find('div', class_='d-flex mt-4')
        if download_div:
            a_tag = download_div.find('a', class_='download')
            if a_tag and 'href' in a_tag.attrs:
                return a_tag['href']
        
        return None
    except Exception as e:
        print(f"Error fetching machine page: {e}")
        return None

def follow_redirect(session, download_url):
    """Follow the download URL redirect to get the actual mega.nz link"""
    try:
        response = session.get(download_url, allow_redirects=True, timeout=10)
        # The final URL after redirect should be the mega.nz link
        final_url = response.url
        
        if 'mega.nz' in final_url:
            return final_url
        else:
            return None
    except Exception as e:
        print(f"Error following redirect: {e}")
        return None

def main():
    # Set up logging
    logger = Logger('hmv_logs.txt')
    sys.stdout = logger
    
    print("HackMyVM Download Links Crawler")
    print("=" * 50)
    
    # Create session
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    # Login
    username = "<redacted>"
    password = "<redacted>"
    
    if not login(session, username, password):
        print("Failed to login. Exiting.")
        logger.close()
        return
    
    mega_links = []
    max_pages = 5  # Only check first 5 pages
    found_realsaga = False
    
    for page in range(1, max_pages + 1):
        if found_realsaga:
            print("Found 'RealSaga' machine. Stopping crawl.")
            break
            
        print(f"\nCrawling page {page}...")
        machine_links = get_machine_links(session, page)
        
        if not machine_links:
            print(f"No machines found on page {page}.")
            continue
        
        print(f"Found {len(machine_links)} machines on page {page}")
        
        for machine_url in machine_links:
            # Extract machine name from URL
            machine_name = machine_url.split('vm=')[-1] if 'vm=' in machine_url else 'unknown'
            
            # Check if this is the RealSaga machine
            if machine_name.lower() == 'realsaga':
                print(f"  {machine_name} ✓ (STOPPING - Found RealSaga)")
                found_realsaga = True
                break
            
            download_url = get_download_link(session, machine_url)
            
            if download_url:
                # Follow redirect to get mega.nz link
                mega_link = follow_redirect(session, download_url)
                
                if mega_link:
                    print(f"  {machine_name} ✓")
                    mega_links.append(mega_link)
                else:
                    print(f"  {machine_name} ✗ (no mega.nz link)")
            else:
                print(f"  {machine_name} ✗ (no download link)")
            
            # Be respectful to the server
            time.sleep(0.5)
        
        time.sleep(1)  # Pause between pages
    
    # Write to output file
    print(f"\n{'=' * 50}")
    print(f"Total mega.nz links found: {len(mega_links)}")
    
    with open('hmv_links.txt', 'w') as f:
        for link in mega_links:
            f.write(link + '\n')
    
    print(f"Download links saved to hmv_links.txt")
    print("Log saved to hmv_logs.txt")
    
    # Close logger
    logger.close()
    sys.stdout = logger.terminal

if __name__ == "__main__":
    main()