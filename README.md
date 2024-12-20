# Paspenta Book Manager

蔵書管理をするアプリです。

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

## images

### index
![スクリーンショット 2024-11-10 195500](https://github.com/user-attachments/assets/d07f9d93-424f-4145-b11e-7a75bc0fb7ae)

### index(シリーズをまとめて表示)
![image](https://github.com/user-attachments/assets/bf62688c-bb29-4085-ab25-387630ce822f)
![image](https://github.com/user-attachments/assets/29c34b08-dfbf-420c-af61-365a179b58e1)

### API検索画面
![スクリーンショット 2024-11-10 195539](https://github.com/user-attachments/assets/032b01de-16d7-44ca-bc16-db8bb84e2645)

### 登録画面
![スクリーンショット 2024-11-10 195607](https://github.com/user-attachments/assets/aadebb36-bfa7-4d35-b5a1-ad6dcc981795)

### 登録書籍の編集画面
![image](https://github.com/user-attachments/assets/ff9ccb55-4c26-4f62-ac9a-83fed080b5db)

