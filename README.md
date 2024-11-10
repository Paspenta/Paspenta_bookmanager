# Paspenta Book Manager

蔵書管理をするWEBアプリです。

## Getting Started

このプロジェクトをローカル環境でセットアップするための手順を説明します。

### 前提条件

以下のソフトウェアがインストールされていることを確認してください：

- Python 3.x
- pip

### インストール

1. リポジトリをクローンします：

2. 仮想環境を作成し、アクティベートします：

    ```sh
    python -m venv venv
    venv/script/activate
    ```

3. 依存関係をインストールします：

    ```sh
    pip install -e .
    ```

### データベースのセットアップ

データベースを初期化します：

```bash
flask --app bookmanager init-db
```

## 機能

- アカウントで書籍情報を分ける
- アカウントの登録・ログイン・編集・削除
- 登録した書籍情報の一覧表示・検索
- 登録した書籍をシリーズごとにまとめる
- 登録した書籍の情報を編集・削除する
- 手動で入力して書籍を登録する
- Google Books APIから書籍データを取得し、自動入力する。
- シリーズをもとに書籍を追加登録する。

## 使用

- flask
- sqlite3
- jinja2
- Bootstrap5
- requests(Google Books APIからデータを取得するため)
