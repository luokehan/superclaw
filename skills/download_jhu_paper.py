#!/usr/bin/env python3
"""
JHU EZProxy Paper Downloader using undetected-chromedriver
用于绕过Cloudflare，通过JHU机构访问下载付费论文PDF
"""
import os
import sys
import time
import glob
import shutil
import subprocess

def load_jhu_credentials():
    creds = {}
    env_file = '/root/.openclaw/jhu-credentials.env'
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    creds[k.strip()] = v.strip().strip('"').strip("'")
    return creds.get('JHU_USERNAME', ''), creds.get('JHU_PASSWORD', '')

def download_paper(url, output_dir, timeout=120):
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    username, password = load_jhu_credentials()
    if not username or not password:
        print("ERROR: JHU credentials not found")
        return None
    
    print(f"Credentials loaded: {username}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Configure Chrome options for download
    options = uc.ChromeOptions()
    options.add_argument(f'--display={os.environ.get("DISPLAY", ":10")}')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    
    # Set download directory
    prefs = {
        'download.default_directory': output_dir,
        'download.prompt_for_download': False,
        'download.directory_upgrade': True,
        'plugins.always_open_pdf_externally': True,  # Download PDF instead of opening
        'safebrowsing.enabled': True
    }
    options.add_experimental_option('prefs', prefs)
    
    driver = None
    try:
        print("Starting undetected Chrome...")
        driver = uc.Chrome(options=options, version_main=None)
        wait = WebDriverWait(driver, 30)
        
        # Build EZProxy URL
        ezproxy_url = f"https://proxy1.library.jhu.edu/login?url={url}"
        print(f"Navigating to: {ezproxy_url}")
        driver.get(ezproxy_url)
        time.sleep(3)
        
        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")
        
        # Check if redirected to Microsoft SSO login
        current_url = driver.current_url
        
        if 'login.microsoftonline.com' in current_url or 'login.live.com' in current_url or 'microsoft' in current_url.lower():
            print("Microsoft SSO login page detected")
            
            # Fill in email
            try:
                email_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"], input[name="loginfmt"], #i0116')))
                email_field.clear()
                email_field.send_keys(username)
                time.sleep(1)
                
                # Click Next
                next_btn = driver.find_element(By.CSS_SELECTOR, 'input[type="submit"], #idSIButton9')
                next_btn.click()
                time.sleep(3)
                print("Email submitted")
            except Exception as e:
                print(f"Email field error: {e}")
            
            # Fill in password
            try:
                pwd_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"], #i0118')))
                pwd_field.clear()
                pwd_field.send_keys(password)
                time.sleep(1)
                
                # Click Sign In
                signin_btn = driver.find_element(By.CSS_SELECTOR, 'input[type="submit"], #idSIButton9')
                signin_btn.click()
                time.sleep(5)
                print("Password submitted")
            except Exception as e:
                print(f"Password field error: {e}")
            
            # Handle "Stay signed in?" prompt
            try:
                no_btn = driver.find_element(By.CSS_SELECTOR, '#idBtn_Back, input[value="No"]')
                no_btn.click()
                time.sleep(3)
                print("Dismissed stay signed in")
            except:
                pass
        
        print(f"After login URL: {driver.current_url}")
        time.sleep(3)
        
        # Now we should be on the paper page - look for PDF download link
        current_url = driver.current_url
        print(f"Current page: {driver.title}")
        
        # Try to find and click PDF download button
        pdf_downloaded = False
        
        # Common selectors for PDF download on Cell.com / ScienceDirect
        pdf_selectors = [
            'a[data-track-action="download pdf"]',
            'a.pdf-download-btn-link',
            'a[href*=".pdf"]',
            'a[title*="PDF"]',
            'a[title*="pdf"]',
            '.article-tools a[href*="pdf"]',
            '#pdfLink',
            'a.download-btn',
        ]
        
        for selector in pdf_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    href = elem.get_attribute('href') or ''
                    text = elem.text.lower()
                    if 'pdf' in href.lower() or 'pdf' in text:
                        print(f"Found PDF link: {href} (text: {elem.text})")
                        elem.click()
                        time.sleep(10)
                        pdf_downloaded = True
                        break
                if pdf_downloaded:
                    break
            except Exception as e:
                print(f"Selector {selector} error: {e}")
        
        if not pdf_downloaded:
            # Try JavaScript approach - look for all PDF links
            links = driver.execute_script("""
                var links = [];
                document.querySelectorAll('a').forEach(function(a) {
                    if (a.href && (a.href.indexOf('.pdf') > -1 || a.href.indexOf('pdf') > -1 || 
                        (a.textContent && a.textContent.toLowerCase().indexOf('pdf') > -1))) {
                        links.push({href: a.href, text: a.textContent.trim()});
                    }
                });
                return links;
            """)
            print(f"All PDF-related links found: {links[:10]}")
            
            if links:
                pdf_url = links[0]['href']
                print(f"Trying to navigate to: {pdf_url}")
                driver.get(pdf_url)
                time.sleep(10)
        
        # Wait for download to complete
        time.sleep(15)
        
        # Check if PDF was downloaded
        pdf_files = glob.glob(os.path.join(output_dir, '*.pdf'))
        
        # Also check /tmp and default download dirs
        for check_dir in [output_dir, '/root/Downloads', '/tmp']:
            for pdf in glob.glob(os.path.join(check_dir, '*.pdf')):
                if pdf not in pdf_files:
                    pdf_files.append(pdf)
        
        # Filter out small files (error pages)
        valid_pdfs = [f for f in pdf_files if os.path.getsize(f) > 100 * 1024]
        
        if valid_pdfs:
            print(f"Downloaded PDFs: {valid_pdfs}")
            # Move to output dir if not already there
            for pdf in valid_pdfs:
                if not pdf.startswith(output_dir):
                    dest = os.path.join(output_dir, os.path.basename(pdf))
                    shutil.move(pdf, dest)
                    print(f"Moved to: {dest}")
            return valid_pdfs[0]
        else:
            print("No valid PDF downloaded")
            # Save screenshot for debugging
            screenshot_path = os.path.join(output_dir, 'debug_screenshot.png')
            driver.save_screenshot(screenshot_path)
            print(f"Debug screenshot saved: {screenshot_path}")
            return None
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        if driver:
            try:
                screenshot_path = os.path.join(output_dir, 'error_screenshot.png')
                driver.save_screenshot(screenshot_path)
                print(f"Error screenshot: {screenshot_path}")
            except:
                pass
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


if __name__ == '__main__':
    url = sys.argv[1] if len(sys.argv) > 1 else 'https://www.cell.com/cancer-cell/abstract/S1535-6108(26)00112-1'
    output_dir = sys.argv[2] if len(sys.argv) > 2 else '/home/openclaw/workspace/tasks/download_cancer_cell_f78e54b2'
    
    result = download_paper(url, output_dir)
    if result:
        size = os.path.getsize(result)
        print(f"\nSUCCESS: {result} ({size/1024:.1f} KB)")
        sys.exit(0)
    else:
        print("\nFAILED: Could not download PDF")
        sys.exit(1)
