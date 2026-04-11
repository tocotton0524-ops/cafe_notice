import requests
from bs4 import BeautifulSoup
import json

def fetch_cafe_articles(club_id, menu_id=None):
    url = f"https://m.cafe.naver.com/ArticleList.nhn?search.clubid={club_id}"
    if menu_id:
        url += f"&search.menuid={menu_id}"
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': f'https://m.cafe.naver.com/ca-fe/web/cafes/{club_id}'
    }
    
    print(f"Fetching: {url}")
    res = requests.get(url, headers=headers)
    print(f"Status: {res.status_code}")
    
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # m.cafe.naver.com の新UIはSPA化されていて、HTMLには #app 要素しかなく
    # JSでレンダリングしている場合がある。
    # 昔ながらのサーバーサイドレンダリングか確認する。
    items = soup.select('ul.list_area li')
    print(f"Found classic li items: {len(items)}")
    
    if len(items) == 0:
        # JS内から window.__INITIAL_STATE__ 的なものを抜けるか？
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string and 'window.__INITIAL_STATE__' in script.string:
                print("Found __INITIAL_STATE__ data")
                return
    
    for item in items[:3]:
        title_el = item.select_one('.tit')
        writer_el = item.select_one('.txt_block .name')
        if title_el and writer_el:
            print(f"- {title_el.text.strip()} by {writer_el.text.strip()}")

if __name__ == "__main__":
    fetch_cafe_articles('30984349')
    print("---")
    fetch_cafe_articles('29424353', '382')
