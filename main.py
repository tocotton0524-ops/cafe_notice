import os
import json
import requests
from datetime import datetime

# 設定: 監視するカフェの情報
# ユーザーの希望URLに基づく設定
TARGETS = [
    {
        "name": "아카캉 카페 (全体)",
        "club_id": "30984349",
        "menu_id": None,  # 全体の新着を見る場合は None
        "target_author": None # 特定のメンバーだけ通知したい場合はここに名前を入力 (例: "아카캉")
    },
    {
        "name": "스텔라이브 카페 (게시판 382)",
        "club_id": "29424353",
        "menu_id": "382", # URLにあった menuid=382 に限定
        "target_author": None
    }
]

HISTORY_FILE = "history.json"
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def get_articles(club_id, menu_id=None):
    """Naver Cafe APIから記事一覧を取得する"""
    url = f"https://apis.naver.com/cafe-web/cafe2/ArticleList.json?search.clubid={club_id}&search.queryType=lastArticle&search.page=1&search.perPage=20"
    if menu_id:
        url += f"&search.menuid={menu_id}"
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': f'https://m.cafe.naver.com/ca-fe/web/cafes/{club_id}'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        articles = data.get("message", {}).get("result", {}).get("articleList", [])
        return articles
    else:
        print(f"Error fetching {club_id}: {response.status_code}")
        return []

def send_discord_notification(article, cafe_name, club_id):
    """DiscordにWebhookで通知を送信する"""
    if not WEBHOOK_URL:
        print("Webhook URLが設定されていません。")
        return

    article_id = article.get("articleId")
    title = article.get("subject")
    author = article.get("writerNickname")
    
    # 記事のURL
    article_url = f"https://cafe.naver.com/ArticleRead.nhn?clubid={club_id}&articleid={article_id}"
    
    payload = {
        "content": f"🚨 **新しい通知があります！**\n\n**カフェ:** {cafe_name}\n**投稿者:** {author}\n**タイトル:** {title}\n**URL:** {article_url}"
    }
    
    requests.post(WEBHOOK_URL, json=payload)
    print(f"通知を送信しました: {title}")

def main():
    # 履歴の読み込み
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
    else:
        history = {}

    changed = False

    for target in TARGETS:
        club_id = target["club_id"]
        menu_id = target["menu_id"]
        cafe_name = target["name"]
        author_filter = target.get("target_author")
        
        # 履歴キー (カフェごとに最新の記事IDを保持)
        history_key = f"{club_id}_{menu_id if menu_id else 'all'}"
        last_article_id = history.get(history_key, 0)
        
        print(f"Checking: {cafe_name} (Last ID: {last_article_id})")
        
        articles = get_articles(club_id, menu_id)
        if not articles:
            continue
            
        # 一番新しい記事からチェック（通常、APIの最初の要素が最新）
        # ただし、設定より新しいものだけをチェックしたいので逆順に処理して通知する
        new_articles = [a for a in articles if a.get("articleId", 0) > last_article_id]
        
        # 逆順 (古い順) から通知して時系列を保つ
        for article in reversed(new_articles):
            author = article.get("writerNickname", "")
            
            # フィルター指定があれば、その作成者の記事だけ通知する
            if author_filter and author_filter != author:
                continue
                
            send_discord_notification(article, cafe_name, club_id)
            
        # 履歴の更新
        if new_articles:
            history[history_key] = max([a.get("articleId", 0) for a in new_articles])
            changed = True

    # 履歴に更新があれば保存して終了する
    if changed:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f)
        print("履歴を更新しました。")
    else:
        print("新しい記事はありませんでした。")

if __name__ == "__main__":
    main()
