from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import re
from scrapling import Fetcher
import uvicorn

app = FastAPI(title="Shopee Scraper API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "https://ck-affiliate.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_ids(u):
    # Clean params trước
    clean_url = u.split('?')[0]
    path = clean_url.replace('https://shopee.vn', '').replace('http://shopee.vn', '')
    
    # Pattern item: /product/shopid/itemid
    m1 = re.search(r'product/(\d+)/(\d+)', u)
    if m1: return m1.group(1), m1.group(2)
    
    # Pattern item: /-i.shopid.itemid
    m2 = re.search(r'-i\.(\d+)\.(\d+)', u)
    if m2: return m2.group(1), m2.group(2)
    
    # Pattern item: /username/shopid/itemid hoặc /opaanlp/shopid/itemid
    m3 = re.search(r'shopee\.vn/[^/]+/(\d+)/(\d+)', u)
    if m3: return m3.group(1), m3.group(2)
    
    # Pattern redirect: s.shopee.vn hoặc vn.shp.ee
    if 's.shopee.vn' in u or 'vn.shp.ee' in u:
        fetcher = Fetcher()
        p = fetcher.get(u)
        final_url = p.url
        return get_ids(final_url)
    
    # Pattern shop: /shopname (1 segment) - có thể có params
    segments = [s for s in path.strip('/').split('/') if s]
    if len(segments) == 1 and segments[0]:
        return "SHOP", clean_url
        
    return None, None

import asyncio

def process_scraping(url):
    sid, pid = get_ids(url)
    
    # Trường hợp shop
    if sid == "SHOP":
        detected_url = pid  # pid chứa clean URL
        return {
            "status": "success",
            "data": {
                "type": "shop",
                "target_url": detected_url
            }
        }
    
    if not sid:
        raise ValueError("Không lấy được ID từ URL")

    target = f"https://shopee.vn/product/{sid}/{pid}"
    
    # Khởi tạo fetcher
    fetcher = Fetcher()
    page = fetcher.get(target)
    
    # Lấy content (giống cách xử lý trong scrape.py)
    html_source = page.body.decode('utf-8', errors='ignore') if hasattr(page, 'body') else page.text
    
    # Trích xuất dữ liệu
    t_match = re.search(r'"title"\s*:\s*"([^"]+)"', html_source)
    i_match = re.search(r'"image"\s*:\s*"([^"]+)"', html_source)
    
    if not t_match or not i_match:
        raise ValueError("Không tìm thấy thông tin title hoặc image")
        
    return {
        "status": "success",
        "data": {
            "type": "item",
            "title": t_match.group(1),
            "image": i_match.group(1),
            "shop_id": sid,
            "item_id": pid,
            "target_url": target
        }
    }

@app.get("/scrape")
async def scrape(url: str):
    try:
        # Chạy logic trích xuất ở thread khác và cài đặt timeout 3 giây
        data = await asyncio.wait_for(asyncio.to_thread(process_scraping, url), timeout=5.0)
        return data
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Thời gian trích xuất dữ liệu vượt quá 5 giây")
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def process_scrape_full(url):
    sid, pid = get_ids(url)
    
    if not sid:
        raise ValueError("Không lấy được ID từ URL")
    
    if sid == "SHOP":
        target = url.split('?')[0]
    else:
        target = f"https://shopee.vn/product/{sid}/{pid}"
    
    fetcher = Fetcher()
    page = fetcher.get(target)
    
    html_source = page.body.decode('utf-8', errors='ignore') if hasattr(page, 'body') else page.text
        
    return {
        "status": "success",
        "data": {
            "html": html_source
        }
    }

@app.get("/scrape-full")
async def scrape_full(url: str):
    try:
        data = await asyncio.wait_for(asyncio.to_thread(process_scrape_full, url), timeout=10.0)
        return data
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Thời gian trích xuất dữ liệu vượt quá 10 giây")
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def home():
    return {"message": "API Scraper đang chạy!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)

