import requests
from bs4 import BeautifulSoup
import time
import sys
from PIL import Image
from io import BytesIO
import re
import random

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

def get_machine_names():
    """Get all machine names from the main page"""
    url = "https://vulnyx.com/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the vm-table
        vm_table = soup.find('table', id='vm-table')
        if not vm_table:
            print("Error: vm-table not found")
            return []
        
        # Find all machine names in the table
        machine_names = []
        for span in vm_table.find_all('span', class_='vm-name'):
            name = span.text.strip()
            if name:
                machine_names.append(name)
        
        return machine_names
    except Exception as e:
        print(f"Error fetching main page: {e}")
        return []

def display_captcha(session, captcha_url):
    """Download and display CAPTCHA for manual solving"""
    try:
        # Add delay before fetching CAPTCHA (randomized)
        time.sleep(random.uniform(4, 7))
        
        response = session.get(captcha_url, timeout=10)
        response.raise_for_status()
        
        # Open and display image
        img = Image.open(BytesIO(response.content))
        
        # Save temporarily
        temp_file = 'temp_captcha.png'
        img.save(temp_file)
        
        # Try to open with default image viewer
        try:
            import platform
            system = platform.system()
            if system == 'Darwin':  # macOS
                import subprocess
                subprocess.run(['open', temp_file])
            elif system == 'Linux':
                import subprocess
                subprocess.run(['xdg-open', temp_file])
            elif system == 'Windows':
                import os
                os.startfile(temp_file)
        except:
            # If can't open, just show it with PIL
            img.show()
        
        return True
    except Exception as e:
        print(f"    Error displaying CAPTCHA: {e}")
        return False

def get_download_link(session, machine_name):
    """Get the Proton Drive download link for a machine"""
    machine_url = f"https://vulnyx.com/vm/{machine_name}/"
    
    try:
        # Add initial delay before any request (randomized to appear more human)
        time.sleep(random.uniform(8, 12))
        
        # First, get the page to find the CAPTCHA image
        response = session.get(machine_url, timeout=10)
        response.raise_for_status()
        
        # Add delay after getting page
        time.sleep(random.uniform(6, 10))
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the CAPTCHA image - try multiple methods
        captcha_img = None
        
        # Method 1: Look for img with alt containing captcha
        captcha_img = soup.find('img', {'alt': lambda x: x and 'captcha' in x.lower()}) if not captcha_img else captcha_img
        
        # Method 2: Look for img with src containing captcha
        if not captcha_img:
            captcha_img = soup.find('img', src=lambda x: x and 'captcha' in x.lower())
        
        # Method 3: Look for img in form
        if not captcha_img:
            form = soup.find('form')
            if form:
                captcha_img = form.find('img')
        
        # Method 4: Look for any img tag (last resort)
        if not captcha_img:
            all_imgs = soup.find_all('img')
            for img in all_imgs:
                src = img.get('src', '')
                if src and not any(x in src.lower() for x in ['logo', 'icon', 'banner']):
                    captcha_img = img
                    break
        
        if not captcha_img:
            print(f"    ✗ No CAPTCHA image found")
            return None
        
        captcha_src = captcha_img.get('src')
        
        # Fix relative URLs properly
        if captcha_src.startswith('../../'):
            captcha_src = f"https://vulnyx.com/{captcha_src.replace('../../', '')}"
        elif captcha_src.startswith('../'):
            captcha_src = f"https://vulnyx.com/{captcha_src.replace('../', '')}"
        elif captcha_src.startswith('//'):
            captcha_src = f"https:{captcha_src}"
        elif captcha_src.startswith('/'):
            captcha_src = f"https://vulnyx.com{captcha_src}"
        elif not captcha_src.startswith('http'):
            captcha_src = f"https://vulnyx.com/{captcha_src}"
        
        # Add delay before requesting CAPTCHA
        time.sleep(random.uniform(6, 10))
        
        # Display CAPTCHA for manual solving
        print(f"    Opening CAPTCHA image...")
        display_captcha(session, captcha_src)
        
        # Add delay after fetching CAPTCHA
        time.sleep(random.uniform(4, 7))
        
        # Ask user to solve it
        print(f"    Please solve the CAPTCHA (5 characters, uppercase + numbers):")
        captcha_solution = input("    Enter CAPTCHA: ").strip().upper()
        
        # Validate input
        captcha_solution = re.sub(r'[^A-Z0-9]', '', captcha_solution)
        if len(captcha_solution) != 5:
            print(f"    ✗ Invalid input (must be 5 characters)")
            return None
        
        print(f"    Using CAPTCHA: {captcha_solution}")
        
        # Add delay before submitting
        time.sleep(random.uniform(6, 10))
        
        # Submit the CAPTCHA
        post_data = {
            'captcha': captcha_solution
        }
        
        response = session.post(
            machine_url,
            data=post_data,
            headers={
                'Referer': machine_url,
                'Origin': 'https://vulnyx.com',
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            allow_redirects=False,  # Don't auto-follow, we need the Location header
            timeout=10
        )
        
        # Check for redirect with Proton Drive link
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            if 'proton.me' in location or 'drive.proton' in location:
                return location
            else:
                print(f"    ✗ Unexpected redirect to: {location}")
                return None
        
        # If not a redirect, parse the response page
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for Proton Drive links
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'proton.me' in href or 'drive.proton' in href:
                return href
        
        # If not found in links, search in text
        if 'proton.me' in response.text or 'drive.proton' in response.text:
            # Extract URL from text using regex
            match = re.search(r'https://drive\.proton\.me/urls/[A-Z0-9]+#[A-Za-z0-9]+', response.text)
            if match:
                return match.group(0)
        
        print(f"    ✗ No Proton Drive link found (wrong CAPTCHA?)")
        return None
        
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return None

def main():
    # Set up logging
    logger = Logger('nyx_logs.txt')
    sys.stdout = logger
    
    print("Vulnyx Download Links Crawler (Manual CAPTCHA Mode)")
    print("=" * 50)
    print("NOTE: You will need to manually solve each CAPTCHA")
    print("=" * 50)
    
    # Create session
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    })
    
    # Get machine names
    print("\nFetching machine list...")
    machine_names = get_machine_names()
    
    if not machine_names:
        print("No machines found. Exiting.")
        logger.close()
        return
    
    print(f"Found {len(machine_names)} machines")
    print("\nStarting crawl. Press Ctrl+C to stop and save progress.\n")
    
    download_links = []
    
    try:
        for i, machine_name in enumerate(machine_names, 1):
            print(f"\n[{i}/{len(machine_names)}] Processing: {machine_name}")
            
            # Check if this is the Memory machine - stop here
            if machine_name.lower() == 'memory':
                print(f"  Found 'Memory' machine - this is the last one. Stopping after this.")
            
            download_link = get_download_link(session, machine_name)
            
            if download_link:
                print(f"  ✓ {download_link}")
                download_links.append(download_link)
            else:
                print(f"  ✗ Failed")
            
            # Save progress after each machine
            with open('nyx_output.txt', 'w') as f:
                for link in download_links:
                    f.write(link + '\n')
            
            # If this was Memory, stop now
            if machine_name.lower() == 'memory':
                print(f"\nStopping at Memory machine as requested.")
                break
            
            # Be respectful to the server - 90-120 seconds per machine to avoid 429
            if i < len(machine_names):  # Don't wait after last machine
                wait_time = random.randint(90, 120)
                print(f"  Waiting {wait_time} seconds before next machine...")
                time.sleep(wait_time)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Saving progress...")
    
    # Write final output
    print(f"\n{'=' * 50}")
    print(f"Total download links found: {len(download_links)}")
    
    with open('nyx_output.txt', 'w') as f:
        for link in download_links:
            f.write(link + '\n')
    
    print(f"Download links saved to nyx_output.txt")
    print("Log saved to nyx_logs.txt")
    
    # Close logger
    logger.close()
    sys.stdout = logger.terminal

if __name__ == "__main__":
    main()