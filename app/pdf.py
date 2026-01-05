import os
import sys
from playwright.sync_api import sync_playwright

from logger import log_message

def convert_html_to_pdf(html_in, pdf_out, pdf_size, top_margin, bottom_margin):
    max_retries = 3
    retry_delay = 10
    
    def are_all_images_loaded(page):
        return page.evaluate("""
            new Promise(resolve => {
                const images = Array.from(document.querySelectorAll('img[src*="lh3.googleusercontent.com/d/"]'));
                if (images.length === 0) {
                    resolve(true);
                    return;
                }
                let loaded = true;
                images.forEach(img => {
                    if (!(img.complete && img.naturalWidth > 0 && img.naturalHeight > 0)) {
                        loaded = false;
                    }
                });
                resolve(loaded);
            });
        """)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            page = browser.new_page()

            abs_html_path = f"file://{os.path.abspath(html_in)}"
            page.goto(abs_html_path, wait_until="load", timeout=30000)
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            page.wait_for_timeout(1000)

            for attempt in range(max_retries + 1):
                all_loaded = are_all_images_loaded(page)
                if all_loaded:
                    if attempt == 0:
                        log_message(f"✅ All Google Drive images loaded")
                    else:
                        log_message(f"✅ All Google Drive images loaded after {attempt} attempts.")
                    break
                elif attempt < max_retries:
                    log_message(f"⚠️ Not all Google Drive images loaded. Retrying in {retry_delay} seconds (Attempt {attempt + 1}/{max_retries + 1})...")
                    page.wait_for_timeout(retry_delay * 1000)
                else:
                    log_message("❌ Max retries reached. Some Google Drive images may not be loaded.")


            abs_pdf_path = os.path.abspath(pdf_out)
            page.pdf(
                path=abs_pdf_path,
                format=pdf_size,
                margin={"top": top_margin, "bottom": bottom_margin}
            )

            if os.path.exists(abs_pdf_path):
                log_message(f"✅ PDF successfully created at: {abs_pdf_path}")
            else:
                log_message("❌ PDF file was not created.")
                raise FileNotFoundError(f"PDF not created: {abs_pdf_path}")

            browser.close()

    except Exception as e:
        log_message(f"🔥 Top-level error in PDF generation: {e}")
        raise

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: python your_script_name.py <html_in> <pdf_out> <pdf_size> <top_margin> <bottom_margin>")
        sys.exit(1)
    convert_html_to_pdf(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])