from fastapi import FastAPI, HTTPException
import re
from scrapling import Fetcher
import uvicorn

app = FastAPI(title="Shopee Scraper API")

def get_ids(u):
    m1 = re.search(r'product/(\d+)/(\d+)', u)
    if m1: return m1.group(1), m1.group(2)
    m2 = re.search(r'-i\.(\d+)\.(\d+)', u)
    if m2: return m2.group(1), m2.group(2)
    if 's.shopee.vn' in u:
        # Sử dụng cách khởi tạo Fetcher giống file mẫu
        fetcher = Fetcher(auto_match=False)
        p = fetcher.get(u)
        # Fetcher của Scrapling trả về đối tượng có thuộc tính url sau khi redirect
        return get_ids(p.url)
    return None, None

@app.get("/scrape")
def scrape(url: str):
    try:
        sid, pid = get_ids(url)
        if not sid:
            raise HTTPException(status_code=400, detail="Không lấy được ID từ URL")

        target = f"https://shopee.vn/CKW-i.{sid}.{pid}"
        
        # Khởi tạo fetcher giống hệt file scrape.py mẫu
        fetcher = Fetcher(auto_match=False)
        page = fetcher.get(target)
        
        # Lấy content (giống cách xử lý trong scrape.py)
        html_source = page.body.decode('utf-8', errors='ignore') if hasattr(page, 'body') else page.text
        
        # Trích xuất dữ liệu
        t_match = re.search(r'"title"\s*:\s*"([^"]+)"', html_source)
        i_match = re.search(r'"image"\s*:\s*"([^"]+)"', html_source)
        
        return {
            "status": "success",
            "data": {
                "title": t_match.group(1) if t_match else "Not found",
                "image": i_match.group(1) if i_match else "Not found",
                "shop_id": sid,
                "product_id": pid,
                "target_url": target
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def home():
    return {"message": "API Scraper đang chạy!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

