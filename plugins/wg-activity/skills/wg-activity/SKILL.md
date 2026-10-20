---
name: wg-activity
description: fun IT club の WG のリポジトリに、活動ページ（<WG>_activity アプリ）を足す・直す。トップに WG の紹介・構想資料（スライド）への案内・チケットの様子（件数、期日が近いもの、最近の動き、プロジェクトの進み具合）・参加のしかたを並べ、その下に構想資料と Redmine 風のチケット管理を持つ。「活動ページを作って」「活動ページを足して」「構想資料を活動ページに載せて」「チケット管理を足して」「課題管理」「Redmine のような管理画面」「WG の紹介ページ」と言われたら必ずこのスキルを使う。旧 django-tracker スキルの後継。
---

# WG に活動ページを足す

活動ページは、WG が**何をしていて、いまどこまで進んでいるか**を見せる場所。WG が作る
Web アプリとは別のアプリとして、その一段下の URL に置く。

| URL（本番） | WG のリポジトリで | 中身 |
|---|---|---|
| `/<WG>/activity/` | `/activity/` | トップ：紹介・構想資料への案内・チケットの様子・参加のしかた |
| `/<WG>/activity/slides/` | `/activity/slides/` | 構想資料（スライド。ページ送りつき） |
| `/<WG>/activity/tracker/issues/`・`…/tracker/projects/` | `/activity/tracker/…` | チケット管理 |
| `/<WG>/` | `/` | WG が作る Web アプリ（このスキルの外） |

`assets/activity/` の雛形を `scripts/install.py` でコピーして配線する。コードは書き起こさない。

## 先に確認する

1. **WG のリポジトリか。** `manage.py` と `config/settings_common.py` があること（`wg-template` から
   作ったもの）。違えば止めて利用者に伝える。
2. **WG の名前。** 英小文字と数字だけ（`welfare`、`protein`）。homepage の `wg-apps.yml` の
   URL（`/welfare/`）と同じにする。分からなければ利用者に聞く。
3. **`<WG>_activity` が空いているか。** 既にあれば上書きせず、直したいところを聞く。
4. **古い形が残っていないか。** `<WG>_tracker/`（旧 django-tracker）や、構想資料だけを出す
   アプリ（`<WG>/templates/<WG>/slides.html`）があれば、下の「古い形から移す」に進む。

## 入れる

### 1. 雛形をコピーする

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/wg-activity/scripts/install.py" <WG の名前> <manage.py のある場所>
```

雛形の `WGNAME` が WG の名前に置き換わり、アプリ名・URL の名前空間・テンプレートの置き場所・
テーブル名（`funitclub_<WG>_activity_*`）がすべて `<WG>_activity` になる。名前に WG を
入れるのは、本番では全 WG のアプリが homepage の中で一緒に動くため（同じ名前があると起動しない）。

**`apps.py` は置かない。** 本番では `wg.<WG>_activity` として読み込まれる。`name` を書いた
`apps.py` があると起動に失敗する。

### 2. WG の情報を書く

`<WG>_activity/content.py` を埋める。WG のリポジトリの README、homepage の WG 一覧の
カード、利用者の話から取る。分からないところは雛形の文のまま残し、利用者に伝える。

| 項目 | 中身 |
|---|---|
| `CODE`・`NAME` | WG 一覧のカードと同じ識別子と名前（`WG-03`） |
| `LEAD` | 何をしている WG かを 1 文で |
| `INTRO` | 紹介。空行で段落を分ける |
| `SLIDES_TITLE`・`SLIDES_SUMMARY` | 構想資料の題と一言。資料が無いうちは `None` のまま（トップに出ず、`/slides/` も 404） |
| `LINKS` | 関連リンク（WG の Web アプリなど）。`（名前, URL）` |

**個人の名前・連絡先は書かない**（メンバーは Classroom と Chat で分かる）。

### 3. 構想資料を置く（あれば）

`<WG>_activity/templates/<WG>_activity/slides.html` は見本。WG の資料に差し替える。

- 1 枚＝ `<section class="slide" id="s<番号>">`。末尾の `.controls` と `<script>`（ページ送り）は残す
- `.controls-inner` の先頭の「‹ 活動ページ」のリンク（`{% url '<WG>_activity:home' %}`）を残す
- `<title>` は `{{ wg.slides_title }} | fun IT club`
- pptx から作るときは、配色・見出し・発表者ノートを元のファイルから取る。中身を足したり削ったりしない

### 4. 設定と URL をつなぐ

`config/settings_common.py` の `INSTALLED_APPS`（自作アプリの並び）に `'<WG>_activity',` を足す。

`config/urls.py` に足す。`/` は WG が作る Web アプリのために空けておく。まだ何も無ければ、
手元で開きやすいよう活動ページへ転送しておく（本番は homepage の URL を使うので影響しない）。

```python
from django.views.generic import RedirectView

path('activity/', include('<WG>_activity.urls', namespace='<WG>_activity')),
path('', RedirectView.as_view(pattern_name='<WG>_activity:home')),  # Web アプリができたら差し替える
```

### 5. マイグレーションとテスト

```bash
DJANGO_SETTINGS_MODULE=config.settings_dev python manage.py makemigrations <WG>_activity
DJANGO_SETTINGS_MODULE=config.settings_dev python manage.py migrate
DJANGO_SETTINGS_MODULE=config.settings_dev python manage.py test
```

`DJANGO_SETTINGS_MODULE` は明示する（devcontainer の環境変数が別のプロジェクトを指していることがある）。
活動ページのテストは 44 件。構想資料を置いたら、題・枚数・各スライドの見出しを確かめるテストを
`<WG>_activity/test_slides.py` に足す。**通らないまま報告しない。**

### 6. homepage に載せる

WG のリポジトリでは `main` に直接 push しない。ブランチを切って PR を出す。

PR がマージされたら、homepage の `wg-apps.yml` の `take` を直す（順番を逆にすると、取り込む
フォルダーが無くてデプロイが止まる。止まっても本番は前の版のまま）。

```yaml
take:
  - {app: <WG>_activity, url: <WG>/activity}   # /<WG>/activity/ 活動ページ
```

WG 一覧のカードは、WG が homepage の編集画面（`/edit/`）で直す（掲載は WG の仕事。
ログイン情報はクラブの Classroom に掲示してある）。利用者に伝える：

- 追加リンクの名前「活動ページ」、URL `https://funitclub.org/<WG>/activity/`
- Webアプリの URL は、WG のアプリができるまで空欄（「作成中」ページに繋がる）

## 古い形から移す

旧 django-tracker（`<WG>_tracker`）と、構想資料だけのアプリ（`<WG>`）がある WG の場合。

1. **チケットのデータを移すか、利用者に確かめる。** 移さないなら作り直し（下の手順）。
   移すなら `dumpdata <WG>_tracker` → モデル名を書き換えて `loaddata` する手順を別に立てる
2. 上の「入れる」で `<WG>_activity` を作る
3. `<WG>/templates/<WG>/slides.html` を `<WG>_activity/templates/<WG>_activity/slides.html` へ移し、
   3 の決まり（戻るリンク・`<title>`）に合わせる。`<WG>/tests.py` の資料のテストは
   `<WG>_activity/test_slides.py` へ移し、URL 名を `<WG>_activity:slides` に直す
4. `<WG>_tracker/` と、資料だけだった `<WG>/` を消す。`INSTALLED_APPS` と `config/urls.py` からも外す
5. README の「このリポジトリで動いているもの」を直す
6. homepage の `wg-apps.yml` から `<WG>` と `<WG>_tracker` を外し、`<WG>_activity` を足す

本番 DB の古いテーブル（`funitclub_<WG>_tracker_*`）は残る。消すのは運営の作業なので、
利用者に伝える。

## 入っているもの

| | |
|---|---|
| トップ | 紹介、構想資料の案内、チケットの件数と完了の割合、期日が 14 日以内・過ぎた未完了のチケット、最近の動き 5 件、プロジェクトごとの進み具合、関連リンク、参加のしかた（WG 一覧の「WG に参加」へ） |
| 構想資料 | スライド 1 枚ずつのページ送り（ボタン・キー・スワイプ、`#s<番号>` で直接開ける）。JS が無ければ縦に並ぶ |
| チケット | `Project`（名称・識別子・説明）、`Issue`（トラッカー・題名・説明・ステータス・優先度・担当者・開始日・期日・進捗率）の一覧・詳細・作成・編集・削除。状態／プロジェクト／トラッカー／ステータス／優先度／担当者で絞り込み、主な列で並べ替え（優先度とステータスは選択肢の順）、25 件ごとのページング |
| 見た目 | Redmine 風。CSS は `templates/<WG>_activity/base.html` に直書き、外部依存なし。スマートフォンでは表が縦に並ぶ |

画面の文言は日本語で直書き。選択肢は `models.py` の `TextChoices`（トラッカー：バグ／機能／サポート、
ステータス：新規／進行中／解決／フィードバック／終了／却下、優先度：低め／通常／高め／急いで）。

## 必ず利用者に伝えること

- **全画面が公開で、だれでもチケットを作成・編集・削除できる。** 本番（homepage）は既定で全画面が
  ログイン必須だが、活動ページはログインなしで見て書けるよう、全ビューに
  `login_not_required` を付けて外してある（テスト `test_every_view_is_public` が付け忘れを捕まえる）。
  homepage の通行証は導線の仕掛けで、守りではない。入れた直後にこれを伝える。黙って済ませない
- **担当者は自由入力。** 本名ではなく、WG の中で通じる呼び名にしてもらう
- **プロジェクトを消すと、そのチケットも全部消える**（`on_delete=CASCADE`）。確認画面で件数と題名を先に見せる

## よく頼まれる手直し

| 頼まれごと | どこを直すか |
|---|---|
| トップに項目を足す | `views.py` の `HomeView.get_context_data` と `templates/<WG>_activity/home.html`。`HomeTests` にテストを足す |
| 期日が近いとみなす日数 | `views.py` の `DUE_SOON_DAYS` |
| 状態を増やす・減らす | `models.py` の `Issue.Status`。`OPEN_STATUSES`（未完了とみなす集合）も合わせる。`base.html` に `.s-<値>` の色を足す |
| コメント欄がほしい | `Comment` モデル（`Issue` への `ForeignKey`、本文、投稿日、`db_table` も付ける）を足し、詳細画面に一覧と投稿フォームを置く。ビューには `PageMixin` と `login_not_required` を付ける |
| 一覧の件数を変える | `views.py` の `IssueListView.paginate_by` |
| プロジェクトを畳みたい | `Project` に `is_archived` を足し、一覧とトップから隠す（削除とは別） |

ビューを足すときは、必ず `PageMixin` を継いで（全画面に WG の名前とナビが出る）、
`@method_decorator(login_not_required, name='dispatch')` を付ける。
