# Backend
## アクセス
アプリurl: https://brave-plant-06292c600.azurestaticapps.net <br>
バックエンド(API)url: https://journey-list.azurewebsites.net

## 使用技術
言語: Python3.8 <br>
フレームワーク: Flask <br>
データベース: ElasticSearch <br>
サーバー: Azure App Service

## 機能
/api/country_states: 国名を元に、その国の都市名一覧を返す。 <br>
/api/login_process: ElasticSearchを参照し、ログインを行う。<br>
/api/register_process: ElasticSearchを参照し、ユーザー登録を行う。パスワードはフロント側からハッシュで送られ、ユーザー名は一意である必要がある。 <br>
/api/country_currency: 国名を元に、その国の通貨を返す。 <br>
/api/insert_visit_data: 滞在データをElasticSearchに保存。<br>
/api/search_personal_data: ユーザーのデータを検索して返す。