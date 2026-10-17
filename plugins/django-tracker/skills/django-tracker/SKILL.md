---
name: django-tracker
description: Django のプロジェクトに、Redmine 風のチケット管理画面（プロジェクトと課題の一覧・詳細・作成・編集・削除、絞り込み、並べ替え）を tracker アプリとして足す。「チケット管理を足して」「課題管理」「Redmine のような管理画面」「issue tracker」「タスク管理の画面」と言われたとき、または Django のアプリに CRUD の管理画面が要るときに使う。
---

# Django にチケット管理画面を足す

`assets/tracker/` の雛形をコピーして配線する。コードは書き起こさない。

## 先に確認する

1. **Django のプロジェクトか。** `manage.py` と `settings.py`（または `config/settings*.py`）があること。無ければ、ここで止めて利用者に伝える。
2. **`tracker` が空いているか。** 同名のアプリやディレクトリが既にあれば、上書きせず利用者に聞く。
3. **設定ファイルの構成。** `settings.py` 1 枚か、`settings_common.py` + `settings_dev.py` のように分かれているか。`INSTALLED_APPS` が書かれている方を直す。

## 入れる

### 1. アプリをコピーする

`${CLAUDE_PLUGIN_ROOT}/skills/django-tracker/assets/tracker` を、`manage.py` と同じ階層に `tracker` としてコピーする。

```bash
cp -r "${CLAUDE_PLUGIN_ROOT}/skills/django-tracker/assets/tracker" <manage.py のある場所>/tracker
```

**`apps.py` は意図的に置いていない。** 既定の `AppConfig` に任せることで、`tracker` としても
`wg.tracker` のような別のパスの下でも、そのまま読み込める。`name = 'tracker'` と書いた
`apps.py` を置くと、別のパスで読み込むプロジェクト（fun IT club の WG アプリなど）で
起動に失敗する。足さないこと。

### 2. INSTALLED_APPS に足す

`INSTALLED_APPS` の末尾（自作アプリの並び）に `'tracker',` を足す。

### 3. URL をつなぐ

プロジェクトの `urls.py`（`ROOT_URLCONF` が指すもの）に足す。既存の `path('', ...)` と衝突しないよう、**前置きを付けるのが既定**。

```python
path('manage/', include('tracker.urls', namespace='tracker')),
```

これで `/manage/issues/` と `/manage/projects/` になる。利用者が前置きを指定したらそれに従う。ルート直下に置きたいと言われた場合だけ `path('', include(...))` にする。

### 4. テーブル名の決まりがあるか確かめる

共有DBを使うプロジェクトでは、テーブル名を `db_table` で固定する決まりがあることが多い。
**`makemigrations` の前に**確かめる（あとから変えると移行作業になる）。既存の `models.py` に
`db_table` を書いているアプリがあれば、それに倣う。

fun IT club の WG アプリなら、`models.py` の各 `Meta` に次を足す。

```python
class Meta:
    db_table = 'funitclub_tracker_project'   # Project
    db_table = 'funitclub_tracker_issue'     # Issue
```

### 5. マイグレーション

```bash
python manage.py makemigrations tracker
python manage.py migrate
```

`DJANGO_SETTINGS_MODULE` が要るプロジェクトでは付ける（例：`DJANGO_SETTINGS_MODULE=config.settings_dev`）。
devcontainer などで環境変数に既定値が入っていると `manage.py` の `setdefault` を上書きしてしまうので、
別のプロジェクトを触るときは明示する。

### 6. テストを通す

```bash
python manage.py test tracker
```

26 件ある。通らなければ、配線のどこかが抜けている。**通らないまま報告しない。**

## 入っているもの

| | |
|---|---|
| モデル | `Project`（名称・識別子・説明）、`Issue`（プロジェクト・トラッカー・題名・説明・ステータス・優先度・担当者・開始日・期日・進捗率） |
| 画面 | チケットとプロジェクトの一覧・詳細・作成・編集・削除 |
| 一覧 | 状態／プロジェクト／トラッカー／ステータス／優先度／担当者で絞り込み、主な列で並べ替え、25 件ごとのページング |
| 見た目 | Redmine 風（紺のヘッダ、細い罫線の表、ステータスの色バッジ、進捗バー）。CSS は `templates/tracker/base.html` に直書き、外部依存なし |

画面の文言は日本語で直書きしてある。ただし **Django が出すフォームのエラー文言は
`LANGUAGE_CODE` に従う**ので、日本語で揃えたいプロジェクトでは `LANGUAGE_CODE = 'ja'` にする。

選択肢は `TextChoices` で定義してある（トラッカー：バグ／機能／サポート、ステータス：新規／進行中／解決／フィードバック／終了／却下、優先度：低め／通常／高め／急いで）。日本語。変えたいと言われたら `models.py` のそこを直し、`makemigrations` し直す。

## 必ず利用者に伝えること

- **認証がない。** 誰でも作成・編集・削除できる。公開する場所に置くなら、`LoginRequiredMixin` と Django の認証を足す必要がある。入れた直後にこれを伝える。黙って済ませない
- **本番が既定でログイン必須のプロジェクト**（fun IT club の WG アプリなど）では、逆にこのままだとログインした人しか触れない。公開したいと言われたら各ビューに付ける：

  ```python
  from django.contrib.auth.decorators import login_not_required
  from django.utils.decorators import method_decorator

  @method_decorator(login_not_required, name='dispatch')
  class IssueListView(generic.ListView):
      ...
  ```

  公開すれば誰でも消せる、ということを伝えてから付ける
- **プロジェクトを消すと、そのチケットも全部消える**（`on_delete=CASCADE`）。確認画面で件数と題名を先に見せるようにはしてある

## よく頼まれる手直し

| 頼まれごと | どこを直すか |
|---|---|
| ログイン必須にする | `views.py` の各ビューに `LoginRequiredMixin` を足し、`settings.py` に `LOGIN_URL` を置く |
| 担当者を選択式にする | `models.py` の `assignee`（いまは必須の自由入力の `CharField`）を `ForeignKey` にする。`User` か、新しく作る `Member` モデルへ |
| 状態を増やす・減らす | `models.py` の `Issue.Status`。`OPEN_STATUSES`（未完了とみなす集合）も合わせる。`base.html` に `.s-<値>` の色を足す |
| コメント欄がほしい | `Comment` モデル（`Issue` への `ForeignKey`、本文、投稿日）を足し、詳細画面に一覧と投稿フォームを置く |
| 一覧の件数を変える | `views.py` の `IssueListView.paginate_by` |
| プロジェクトを畳みたい | `Project` に `is_archived` を足し、一覧から隠す（Redmine のアーカイブ相当。削除とは別） |
