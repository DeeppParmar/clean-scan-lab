import os
import requests
import re
import uuid
import time

def download_bing_images(query, max_results, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    url = f"https://www.bing.com/images/search?q={query.replace(' ', '+')}&form=HDRSC3"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}
    
    print(f"Searching Bing for: '{query}'")
    resp = requests.get(url, headers=headers)
    
    murls = re.findall(r'murl&quot;:&quot;(.*?)&quot;', resp.text)
    print(f"  Found {len(murls)} image URLs. Downloading up to {max_results}...")
    
    count = 0
    for img_url in murls:
        if count >= max_results:
            break
        try:
            img_resp = requests.get(img_url, timeout=4, headers=headers)
            if img_resp.status_code == 200:
                ext = img_url.split('.')[-1].lower()
                ext = re.sub(r'[^a-z]', '', ext)
                if ext not in ['jpg', 'jpeg', 'png', 'webp']:
                    ext = 'jpg'
                filename = f"aug_bing_{uuid.uuid4().hex[:8]}.{ext}"
                with open(os.path.join(output_dir, filename), 'wb') as f:
                    f.write(img_resp.content)
                count += 1
                if count % 5 == 0:
                    print(f"    Downloaded {count}/{max_results}")
        except Exception:
            pass

    print(f"Successfully downloaded {count} images for '{query}'\n")

if __name__ == '__main__':
    trash_dir = r"C:\Users\Abhi\Downloads\archive (1)\garbage_classification\trash"
    
    queries = [
        "black garbage bag isolated",
        "black trash bags on street",
        "pile of full black garbage bags"
    ]
    
    for q in queries:
        download_bing_images(q, 20, trash_dir)
        time.sleep(1)
