import os
import json
import requests
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

TARGETS = [
    {
        "name": "아카캉 카페 (全体)",
        "club_id": "30984349",
        "menu_id": None,
        "target_author": None
    },
    {
        "name": "스텔라이브 카페 (게시판 382)",
        "club_id": "29424353",
        "menu_id": "382",
        "target_author": None
    }
]

HISTORY_FILE = "history.json"
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def get_articles(club_id, menu_id=None):
    url = f"https://m.cafe.naver.com/ca-fe/web/cafes/{club_id}/articles"
    if menu_id:
        url = f"https://m.cafe.naver.com/ca-fe/web/cafes/{club_id}/menus/{menu_id}"
        
    articles = []
    
    # 隠しブラウザ(Chrome)を立ち上げて人間のようにアクセス
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            viewport={"width": 375, "height": 812}
        )
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            
            # 記事リストの表示を少し待つ
            page.wait_for_selector("a.article", timeout=15000)
            
            # ページ内の記事一覧を取得
            items = page.query_selector_all("a.article")
            
            for item in items[:20]:  # 最新20件
                try:
                    subject = ""
                    tit_el = item.query_selector("strong.tit")
                    if tit_el:
                        subject = tit_el.inner_text().strip()
                        
                    writer = ""
                    # Naverモバイル版は作者名が同じaタグ内やすぐ近くにある
                    author_el = item.query_selector(".nick_area .name, .name")
                    if author_el:
                        writer = author_el.inner_text().strip()
                        
                    href = item.get_attribute("href")
                    if not href:
                        continue
                        
                    # URLから記事IDを抜き出す
                    article_id_match = re.search(r'/articles/(\d+)', href)
                    if article_id_match:
                        article_id = int(article_id_match.group(1))
                        articles.append({
                            "articleId": article_id,
                            "subject": subject,
                            "writerNickname": writer
                        })
                except Exception as e:
                    continue
        except Exception as e:
            print(f"Error fetching {club_id}: ページの読み込みに失敗しました ({e})")
        finally:
            browser.close()
            
    return articles

def send_discord_notification(article, cafe_name, club_id):
    if not WEBHOOK_URL:
        print("Webhook URLが設定されていません。")
        return

    article_id = article.get("articleId")
    title = article.get("subject")
    author = article.get("writerNickname", "不明")
    article_url = f"https://cafe.naver.com/ArticleRead.nhn?clubid={club_id}&articleid={article_id}"
    
    payload = {
        "content": f"🚨 **新しい通知があります！**\n\n**カフェ:** {cafe_name}\n**投稿者:** {author}\n**タイトル:** {title}\n**URL:** {article_url}"
    }
    
    requests.post(WEBHOOK_URL, json=payload)
    print(f"通知を送信しました: {title}")

def main():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            try:
                history = json.load(f)
            except:
                history = {}
    else:
        history = {}

    changed = False

    for target in TARGETS:
        club_id = target["club_id"]
        menu_id = target["menu_id"]
        cafe_name = target["name"]
        author_filter = target.get("target_author")
        
        history_key = f"{club_id}_{menu_id if menu_id else 'all'}"
        last_article_id = history.get(history_key, 0)
        
        print(f"Checking: {cafe_name} (Last ID: {last_article_id})")
        
        articles = get_articles(club_id, menu_id)
        if not articles:
            print(f"{cafe_name} から記事が1つも取得できませんでした。")
            continue
            
        new_articles = [a for a in articles if a.get("articleId", 0) > last_article_id]
        
        for article in reversed(new_articles):
            author = article.get("writerNickname", "")
            if author_filter and author_filter != author:
                continue
                
            send_discord_notification(article, cafe_name, club_id)
            
        if new_articles:
            history[history_key] = max([a.get("articleId", 0) for a in new_articles])
            changed = True

    if changed:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f)
        print("履歴を更新しました。")
    else:
        print("新しい記事はありませんでした。（取得は成功しています）")

if __name__ == "__main__":
    main()
