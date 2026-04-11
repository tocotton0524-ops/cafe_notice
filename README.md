# Naver Cafe Update Notifier

このフォルダに入っているファイルを使って、Naver Cafeの新しい投稿をDiscordに自動で通知する仕組みをGitHubで作ります。💻

## 🚀 準備・設定のステップ

### 1. このフォルダをGitHubにアップロードする
1. [GitHub](https://github.com/) にログインし、画面右上の「+」から「**New repository**」を選択します。
2. リポジトリのなまえ（例: `cafe_notice`）を入力します。
   - `Public`でも`Private`でも構いませんが、「**Private**」を選択しておくのが安全です。
   - すべて空のまま「Create repository」をクリックします。
3. 作成された画面に「uploading an existing file」というリンクがあるのでそこをクリックします。
4. このフォルダ（`cafe_notice`）の**中身すべて**（`main.py`、`requirements.txt`、`.gitignore`、`.github`フォルダなど）をドラッグ＆ドロップしてアップロードし、Commitします。

### 2. Discord Webhook URLを登録する
1. 先ほど作ったGitHubの画面上部にある「**Settings**」タブを開きます。
2. 左メニューの下の方にある「**Secrets and variables**」から「**Actions**」をクリックします。
3. 「**New repository secret**」という緑のボタンを押します。
4. 以下の通りに入力して保存（Add secret）します：
   - Name: `DISCORD_WEBHOOK_URL`
   - Secret: *（取得したDiscordのWebhook URLを貼り付けます）*

### 3. 一度テスト実行してみる！
1. GitHubの画面上部「**Actions**」タブを開きます。
2. 左側の「**Naver Cafe Notification**」を選択し、右側に出る「**Run workflow**」ボタンを押します。
3. スクリプトが動き出し、**数分後にDiscordへ初回の通知が届きます！**
   *(※初回は、最新の記事が通知されます。)*
4. 以降は**15分ごと**に自動でチェックし、増えていれば通知が来るようになります。

---
💡 **設定を変えたい場合**
`main.py`の中にある `TARGETS` という部分を編集することで、特定のメンバー名での絞り込みや、違うカフェIDを増やすことも可能です。
