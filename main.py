import os
import json
import requests
import re
from datetime import datetime

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
    # モバイル版のWebページにスマホのフリをしてアクセス
    url = f"https://m.cafe.naver.com/ca-fe/web/cafes/{club_id}/articles"
    if menu_id:
        url = f"https://m.cafe.naver.com/ca-fe/web/cafes/{club_id}/menus/{menu_id}"
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
        'Referer': f'https://m.cafe.naver.com/ca-fe/web/cafes/{club_id}'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        # HTML内から記事データを抽出する
        match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});</script>', response.text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                if menu_id:
                    return data.get("menu", {}).get("articleList", [])
                else:
                    return data.get("articleList", {}).get("articleList", [])
            except:
                pass
    print(f"Error fetching {club_id}: {response.status_code} (HTML Parsing Failed)")
    return []

def send_discord_notification(article, cafe_name, club_id):
    if not WEBHOOK_URL:
        print("Webhook URLが設定されていません。")
        return

    article_id = article.get("articleId")
    title = article.get("subject")
    author = article.get("writerNickname")
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
        print("新しい記事はありませんでした。")

if __name__ == "__main__":
    main()
