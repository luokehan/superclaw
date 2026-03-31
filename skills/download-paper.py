#!/usr/bin/env python3
"""
论文下载工具 — 使用 undetected-chromedriver 绕过 Cloudflare，自动登录 JHU SSO 下载付费论文。
用法: python3 download-paper.py <论文URL> <保存目录>
"""
import sys
import os
import time
import glob

def load_jhu_credentials():
    env_file = "/root/.openclaw/jhu-credentials.env"
    creds = {}
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    creds[k] = v
    return creds.get("JHU_USERNAME", ""), creds.get("JHU_PASSWORD", "")


def download_paper(url, save_dir):
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    os.makedirs(save_dir, exist_ok=True)
    username, password = load_jhu_credentials()
    if not username or not password:
        print("ERROR: JHU credentials not found")
        sys.exit(1)

    print(f"[1/6] 启动浏览器 (undetected-chromedriver)...")
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    prefs = {
        "download.default_directory": os.path.abspath(save_dir),
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True,
    }
    options.add_experimental_option("prefs", prefs)

    driver = uc.Chrome(options=options, use_subprocess=True)
    driver.set_window_size(1280, 900)
    wait = WebDriverWait(driver, 30)

    try:
        print(f"[2/6] 访问论文页面: {url}")
        driver.get(url)
        time.sleep(8)

        print(f"[2/6] 当前页面: {driver.title}")
        page_text = driver.page_source

        # Check if we need institution login
        pdf_downloaded = False

        # Try to find PDF link directly
        if "pdf" in page_text.lower() or "download" in page_text.lower():
            try:
                # Try direct PDF link (Cell.com pattern)
                pdf_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="pdf"], a[href*="PDF"]')
                for link in pdf_links:
                    href = link.get_attribute("href")
                    if href and "pdf" in href.lower():
                        print(f"[3/6] 找到 PDF 链接: {href}")
                        driver.get(href)
                        time.sleep(5)
                        break
            except Exception:
                pass

        # Check if redirected to login
        current_url = driver.current_url
        print(f"[3/6] 当前 URL: {current_url}")

        if "login.microsoftonline.com" in current_url or "idp" in current_url.lower() or "sso" in current_url.lower():
            print("[4/6] 检测到 SSO 登录页，开始登录...")
            _do_jhu_login(driver, wait, username, password)
            time.sleep(5)
            print(f"[4/6] 登录后 URL: {driver.current_url}")

        # If we're on the abstract/article page, try to get PDF
        if not pdf_downloaded:
            # Try "Access through your institution" button
            try:
                inst_links = driver.find_elements(By.PARTIAL_LINK_TEXT, "Access")
                for link in inst_links:
                    txt = link.text.lower()
                    if "institution" in txt or "access" in txt:
                        print(f"[4/6] 点击机构访问: {link.text}")
                        link.click()
                        time.sleep(8)
                        break
            except Exception:
                pass

            # Handle SSO if redirected
            if "login.microsoftonline.com" in driver.current_url:
                print("[5/6] SSO 登录...")
                _do_jhu_login(driver, wait, username, password)
                time.sleep(5)

            # Now try PDF download
            print(f"[5/6] 尝试下载 PDF... 当前: {driver.current_url}")
            try:
                pdf_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="pdf"], a[href*="PDF"], a[class*="pdf"], button[class*="pdf"]')
                for link in pdf_links:
                    href = link.get_attribute("href") or ""
                    text = link.text
                    if "pdf" in href.lower() or "pdf" in text.lower():
                        print(f"  点击: {text} -> {href[:80]}")
                        link.click()
                        time.sleep(10)
                        pdf_downloaded = True
                        break
            except Exception as e:
                print(f"  PDF 链接点击失败: {e}")

            # Try direct PDF URL pattern for Cell.com
            if not pdf_downloaded:
                pii = None
                if "S1535" in url:
                    pii = url.split("/")[-1]
                if pii:
                    pdf_url = f"https://www.cell.com/cancer-cell/pdfExtended/{pii}"
                    print(f"[5/6] 尝试直接 PDF URL: {pdf_url}")
                    driver.get(pdf_url)
                    time.sleep(10)

        # Wait for download
        print("[6/6] 等待下载完成...")
        for i in range(30):
            files = glob.glob(os.path.join(save_dir, "*.pdf"))
            crdownloads = glob.glob(os.path.join(save_dir, "*.crdownload"))
            if files:
                for f in files:
                    size = os.path.getsize(f)
                    if size > 100 * 1024:
                        print(f"SUCCESS: PDF 下载完成: {f} ({size/1024:.0f} KB)")
                        return f
            if crdownloads:
                print(f"  下载中... ({i+1}s)")
            time.sleep(1)

        # Check if page itself is a PDF (save as PDF)
        print("[6/6] 尝试保存页面为 PDF...")
        import subprocess
        pdf_path = os.path.join(save_dir, "paper.pdf")
        result = subprocess.run(
            ["google-chrome", "--no-sandbox", "--headless=new", "--disable-gpu",
             f"--print-to-pdf={pdf_path}", driver.current_url],
            capture_output=True, timeout=30
        )
        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 100 * 1024:
            print(f"SUCCESS: 页面保存为 PDF: {pdf_path} ({os.path.getsize(pdf_path)/1024:.0f} KB)")
            return pdf_path

        # List what we got
        all_files = os.listdir(save_dir)
        print(f"FAILED: 目录中的文件: {all_files}")
        print(f"最终 URL: {driver.current_url}")
        print(f"页面标题: {driver.title}")
        return None

    finally:
        driver.quit()


def _do_jhu_login(driver, wait, username, password):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC

    try:
        # Email field
        try:
            email_field = wait.until(EC.presence_of_element_located((By.NAME, "loginfmt")))
            email_field.clear()
            email_field.send_keys(username)
            next_btn = driver.find_element(By.ID, "idSIButton9")
            next_btn.click()
            time.sleep(3)
        except Exception:
            pass

        # Password field
        try:
            pwd_field = wait.until(EC.presence_of_element_located((By.NAME, "passwd")))
            pwd_field.clear()
            pwd_field.send_keys(password)
            sign_in = driver.find_element(By.ID, "idSIButton9")
            sign_in.click()
            time.sleep(5)
        except Exception:
            pass

        # "Stay signed in?" prompt
        try:
            stay_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "idSIButton9"))
            )
            stay_btn.click()
            time.sleep(3)
        except Exception:
            pass

    except Exception as e:
        print(f"  SSO 登录异常: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"用法: python3 {sys.argv[0]} <论文URL> <保存目录>")
        sys.exit(1)

    url = sys.argv[1]
    save_dir = sys.argv[2]
    result = download_paper(url, save_dir)
    if result:
        print(f"\nOK: {result}")
        sys.exit(0)
    else:
        print("\nFAILED: 下载失败")
        sys.exit(1)
