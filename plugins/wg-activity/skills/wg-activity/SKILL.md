---
name: wg-activity
description: fun IT club の WG のリポジトリに、活動ページ（<WG>_activity アプリ）を足す・直す。トップに WG の紹介・構想資料（スライド）への案内・チケットの様子（件数、期日が近いもの、最近の動き、プロジェクトの進み具合）・参加のしかたを並べ、その下に構想資料と、GitHub の Issue／Projects を読んで見せる Redmine 風のチケット一覧を持つ。「活動ページを作って」「活動ページを足して」「構想資料を活動ページに載せて」「チケット管理を足して」「課題管理」「Redmine のような管理画面」「WG の紹介ページ」「Projects を活動ページに出して」と言われたら必ずこのスキルを使う。旧 django-tracker スキルの後継。
---

# WG に活動ページを足す

活動ページは、WG が**何をしていて、いまどこまで進んでいるか**を見せる場所。WG が作る
Web アプリとは別のアプリとして、その一段下の URL に置く。

| URL（本番） | WG のリポジトリで | 中身 |
|---|---|---|
| `/<WG>/activity/` | `/activity/` | トップ：紹介・構想資料への案内・チケットの様子・参加のしかた |
| `/<WG>/activity/slides/` | `/activity/slides/` | 構想資料（スライド。ページ送りつき） |
| `/<WG>/activity/tracker/issues/`・`…/tracker/projects/` | `/activity/tracker/…` | チケットの一覧・詳細（読むだけ） |
| `/<WG>/activity/tracker/wbs/`・`…/tracker/gantt/` | `/activity/tracker/…` | WBS・ガントチャート（Project を使う WG だけ） |
| `/<WG>/` | `/` | WG が作る Web アプリ（このスキルの外） |

**チケットは GitHub に書く。** 会員が WG のリポジトリの Issue と、org の Project（ステータス・
優先度・期日など）で直接管理し、活動ページはそれを読んで見せるだけ。活動ページから書き込む
画面は無い（書けるのは GitHub のチームの人だけ、という守りを GitHub に任せる）。

`assets/` の雛形を `scripts/install.py` でコピーして配線する。コードは書き起こさない。

## 先に確認する

1. **WG のリポジトリか。** `manage.py` と `config/settings_common.py` があること（`wg-template` から
   作ったもの）。違えば止めて利用者に伝える。
2. **WG の名前。** 英小文字と数字だけ（`welfare`、`protein`）。homepage の `wg-apps.yml` の
   URL（`/welfare/`）と同じにする。リポジトリは `wg-<名前>`。分からなければ利用者に聞く。
3. **`<WG>_activity` が空いているか。** 既にあれば上書きせず、直したいところを聞く。
   `models.py` があれば自前の DB でチケットを持っていた旧版なので、下の「旧版から移す」に進む。
4. **もっと古い形が残っていないか。** `<WG>_tracker/`（旧 django-tracker）や、構想資料だけを出す
   アプリ（`<WG>/templates/<WG>/slides.html`）があれば、下の「古い形から移す」に進む。

## 入れる

### 1. 雛形をコピーする

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/wg-activity/scripts/install.py" <WG の名前> <manage.py のある場所>
```

雛形の `WGNAME` が WG の名前に置き換わり、アプリ名・URL の名前空間・テンプレートの置き場所が
すべて `<WG>_activity` になる。名前に WG を入れるのは、本番では全 WG のアプリが homepage の中で
一緒に動くため（同じ名前があると起動しない）。

あわせて `.github/ISSUE_TEMPLATE/` に issue フォーム（バグ・機能・サポート）と `config.yml`
（白紙の issue を閉じる）を置く。フォームの先頭に「**題名と本文は活動ページで一般公開される。
個人の名前・連絡先・パスワードや API キーは書かない**」とあるので、消さない。同じ名前のファイルが
既にあれば飛ばすので、そのときは注意書きが入っているか確かめる。

**`apps.py` は置かない。** 本番では `wg.<WG>_activity` として読み込まれる。`name` を書いた
`apps.py` があると起動に失敗する。**モデルも無い**（チケットは GitHub にあるので、マイグレーションも要らない）。

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
| `GITHUB_REPO` | チケットを読むリポジトリ（`wg-<名前>`。雛形のままでよいことが多い） |
| `GITHUB_PROJECT` | org の Project の番号。使わないうちは `None`（下の 5） |

**個人の名前・連絡先は書かない**（メンバーは Classroom と Chat で分かる）。

### 3. 構想資料を置く（あれば）

`<WG>_activity/templates/<WG>_activity/slides.html` は見本。WG の資料に差し替える。

- 1 枚＝ `<section class="slide" id="s<番号>">`。末尾の `.controls` と `<script>`（ページ送り）は残す
- `.controls-inner` の先頭の「× 閉じる」（`id="close-tab"`、`href` は `{% url '<WG>_activity:home' %}`）を残す。
  スライドはトップとナビから別タブで開くので、閉じれば活動ページに戻る。閉じられないときは `href` の活動ページへ移る
- `<title>` は `{{ wg.slides_title }} | fun IT club`
- pptx から作るときは、配色・見出し・発表者ノートを元のファイルから取る。中身を足したり削ったりしない

### 4. 設定・URL・パッケージをつなぐ

`config/settings_common.py` の `INSTALLED_APPS`（自作アプリの並び）に `'<WG>_activity',` を足す。

`config/urls.py` に足す。`/` は WG が作る Web アプリのために空けておく。まだ何も無ければ、
手元で開きやすいよう活動ページへ転送しておく（本番は homepage の URL を使うので影響しない）。

```python
from django.views.generic import RedirectView

path('activity/', include('<WG>_activity.urls', namespace='<WG>_activity')),
path('', RedirectView.as_view(pattern_name='<WG>_activity:home')),  # Web アプリができたら差し替える
```

`requirements.txt` の「WG で使うもの」に `nh3==0.3.7` を足す（本文の HTML を削る。本番では homepage の分に合流する）。

### 5. Project をつなぐ（任意。ステータス・優先度・期日を使うなら）

`GITHUB_PROJECT = None` のままでも動く。そのときは Issue の Open/Closed とラベルだけで、
優先度・期日・プロジェクトの列と、トップの「期日が近い」「プロジェクトの進み具合」は出ない。
使うなら、org の Project のテンプレート「活動ページのテンプレート」
（https://github.com/orgs/funITclub/projects/1 。2026-10-23 に運営が作ったもの）を複製する。
**WG のリーダーと相談してから**流す（org に Project が 1 つ増える）。先に
`gh project list --owner funITclub` で「<WG の名前> の活動」が既に無いか見る（あれば複製せずその番号を使う）。

複製すると、項目と選択肢に加えて Workflows も引き継がれる（追加したら「新規」、Issue を閉じたら
「終了」、開き直したら「進行中」、ボードで「終了」にしたら Issue を閉じる）。表示も引き継がれる：
「WBS」（表。親の Issue＝Parent issue ごとにまとめ、子の進み具合 Sub-issues progress を出す）と
「ガントチャート」（Roadmap。開始日〜期日の横棒）。WBS の階層は、Issue の画面の「Create sub-issue」で作る。複製はテンプレートではなく、
非公開の普通の Project になる。

```bash
gh auth refresh -h github.com -s project   # Project を作る権限（初回だけ。ブラウザで許可する）
T=$(gh project list --owner funITclub --limit 100 --format json \
      --jq '.projects[] | select(.title=="活動ページのテンプレート") | .number')
N=$(gh project copy "$T" --source-owner funITclub --target-owner funITclub \
      --title "<WG の名前> の活動" --format json --jq .number)
gh project link "$N" --owner funITclub --repo funITclub/wg-<名前>

# WG のチームに Project の書き込みを付ける（メンバーがボードを動かせるように）
P=$(gh project view "$N" --owner funITclub --format json --jq .id)
TEAM=$(gh api orgs/funITclub/teams/wg-<名前> --jq .node_id)
gh api graphql -f p="$P" -f t="$TEAM" -f query='mutation($p: ID!, $t: ID!) {
  updateProjectV2Collaborators(input: {projectId: $p, collaborators: [{teamId: $t, role: WRITER}]}) {
    clientMutationId } }'
```

- テンプレートが見つからない（`T` が空）・作れないと言われたときは、止めて利用者に伝える（運営の作業。
  テンプレートの作り方は homepage の deploy.txt の「WG の活動ページのチケット」）
- `content.py` の `GITHUB_PROJECT` に `$N` を書く
- 3 つの issue フォーム（`bug.yml`・`feature.yml`・`support.yml`）の `labels:` の下に
  `projects: ["funITclub/<N>"]` を足す（新しいチケットが自動でボードに入る）
- 複製したら、ボードの項目「プロジェクト」の選択肢を WG の作るものに直してもらう（選択肢の説明が
  活動ページのプロジェクトの説明になる）
- Project は非公開のままでよい（活動ページは鍵で読む）

項目の名前は変えない（活動ページは名前で読む）：ステータス（組み込みの Status）・優先度・開始日・
期日・進捗率・プロジェクト。ステータスが解決・終了・却下か、Issue が Closed なら完了とみなす。

### 6. 手元で動かす・テスト

```bash
DJANGO_SETTINGS_MODULE=config.settings_dev python manage.py test
GITHUB_TOKEN=$(gh auth token) DJANGO_SETTINGS_MODULE=config.settings_dev python manage.py runserver
```

`DJANGO_SETTINGS_MODULE` は明示する（devcontainer の環境変数が別のプロジェクトを指していることがある）。
`GITHUB_TOKEN` を付けないと「GitHub に繋がっていません」と出てチケットは 0 件になる（テストは
GitHub に繋がないので、付けなくても通る）。Project を読むには `gh auth refresh -s read:project` が要る。

活動ページのテストは 83 件。構想資料を置いたら、題・枚数・各スライドの見出しを確かめるテストを
`<WG>_activity/test_slides.py` に足す。**通らないまま報告しない。**

### 7. homepage に載せる

WG のリポジトリでは `main` に直接 push しない。ブランチを切って PR を出す。

PR がマージされたら、homepage の `wg-apps.yml` の `take` を直す（順番を逆にすると、取り込む
フォルダーが無くてデプロイが止まる。止まっても本番は前の版のまま）。

```yaml
take:
  - {app: <WG>_activity, url: <WG>/activity}   # /<WG>/activity/ 活動ページ
```

本番は homepage の GitHub App（funitclub-wg-join。Issues と Projects の読み取り）で読む。
WG ごとの設定は要らない。

WG 一覧のカードは、WG が homepage の編集画面（`/edit/`）で直す（掲載は WG の仕事。
ログイン情報はクラブの Classroom に掲示してある）。利用者に伝える：

- 追加リンクの名前「活動ページ」、URL `https://funitclub.org/<WG>/activity/`
- Webアプリの URL は、WG のアプリができるまで空欄（「作成中」ページに繋がる）

## 新しい版に上げる（0.3 以降の活動ページ）

`<WG>_activity/` に `tickets.py` があれば 0.3 以降。雛形の新しい版の中身に差し替える。
WG が書き換えるもの（`content.py`・`templates/<WG>_activity/slides.html`・`test_slides.py`・
`migrations/`）は残す。それ以外を WG が直していないか、先に旧版の雛形と比べる
（直していれば、その直しを新しい版にも入れる）。

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/wg-activity/scripts/install.py" <WG の名前> /tmp/<WG>-new  # manage.py だけ置いた空のフォルダーに入れる
# /tmp/<WG>-new/<WG>_activity/ のうち、上の 4 つ以外を <WG>_activity/ に上書きする
```

テストを流し（上の「入れる」の 6）、PR を出す。マイグレーションは要らない（モデルが無いため）。

## 旧版（自前の DB のチケット）から移す

0.2 までの活動ページは、チケットを自前のモデル（`Project`・`Issue`）で持ち、だれでも書き換えられた。

1. **チケットのデータを GitHub に移すか、利用者に確かめる。** 移すなら Issue に手で書き写す
   （件数が少なければ）。移さないなら作り直し
2. `content.py`・`templates/<WG>_activity/slides.html`・`test_slides.py`・`migrations/` を
   脇によけて、`<WG>_activity/` を消す。上の「入れる」の 1 で入れ直す
3. よけておいたものを戻す。`content.py` は新しい雛形のほうに、`CODE`〜`LINKS` の値を書き写す
   （`GITHUB_REPO`・`GITHUB_PROJECT` が足されているため）
4. 自前のテーブルを消すマイグレーションを作る。モデルが無くなったので、削除だけが出る

   ```bash
   DJANGO_SETTINGS_MODULE=config.settings_dev python manage.py makemigrations <WG>_activity
   ```

   本番では、起動時の migrate で `funitclub_<WG>_activity_*` が消える。**中のチケットも消える**ので、1 を先に済ませる
5. 上の 4（`nh3`）と 6 を行い、README の「このリポジトリで動いているもの」のチケットの説明を直す

## 古い形から移す

旧 django-tracker（`<WG>_tracker`）と、構想資料だけのアプリ（`<WG>`）がある WG の場合。

1. **チケットのデータを移すか、利用者に確かめる。** 移すなら GitHub の Issue に書き写す
2. 上の「入れる」で `<WG>_activity` を作る
3. `<WG>/templates/<WG>/slides.html` を `<WG>_activity/templates/<WG>_activity/slides.html` へ移し、
   3 の決まり（閉じるリンク・`<title>`）に合わせる。`<WG>/tests.py` の資料のテストは
   `<WG>_activity/test_slides.py` へ移し、URL 名を `<WG>_activity:slides` に直す
4. `<WG>_tracker/` と、資料だけだった `<WG>/` を消す。`INSTALLED_APPS` と `config/urls.py` からも外す
5. README の「このリポジトリで動いているもの」を直す
6. homepage の `wg-apps.yml` から `<WG>` と `<WG>_tracker` を外し、`<WG>_activity` を足す

本番 DB の古いテーブル（`funitclub_<WG>_tracker_*`）は残る。消すのは運営の作業なので、
利用者に伝える。

## 入っているもの

| | |
|---|---|
| トップ | 紹介、構想資料の案内、チケットの件数と完了の割合、期日が 14 日以内・過ぎた未完了のチケット、最近の動き 5 件、プロジェクトごとの進み具合、関連リンク、参加のしかた（WG 一覧の「WG に参加」へ）、「GitHub で新しいチケット」 |
| 構想資料 | トップの「スライドを見る」とナビの「構想資料」から別タブで開き、「閉じる」で戻る。スライド 1 枚ずつのページ送り（ボタン・キー・スワイプ、`#s<番号>` で直接開ける）。JS が無ければ縦に並ぶ |
| チケット | GitHub の Issue（PR は除く。500 件まで）の一覧・詳細。状態／プロジェクト／トラッカー／ステータス／優先度で絞り込み、主な列で並べ替え（優先度とステータスは Project の選択肢の順）、25 件ごとのページング。各チケットに「GitHub で開く」、一覧に「GitHub で新しいチケット」「GitHub のボード」（別タブ） |
| WBS | GitHub の sub-issue の親子で、親の下に子を字下げして並べ、親に「子の完了 n / m」を出す。親がほかのリポジトリの Issue なら一番上の段に置く。Project が無くても出る |
| ガントチャート | 開始日〜期日のあるチケットを横棒で並べる（開始日だけ・期日だけなら 1 日）。今日の線、未完了・期日を過ぎた未完了・完了の色分け、進捗率の濃い帯。表は月曜〜日曜の区切りで、長いときは横に送る。Project を使っていない WG ではナビに出ず 404 |
| 読み方 | `github.py`（鍵の選び方と GraphQL）、`tickets.py`（チケットの形・5 分のキャッシュ・失敗したら最後に読めた分）、`body.py`（本文の HTML を許可リストで削る） |
| 見た目 | Redmine 風。CSS は `templates/<WG>_activity/base.html` に直書き、外部依存なし。スマートフォンでは表が縦に並ぶ |

トラッカーはラベルから読む（`bug` → バグ、`enhancement` → 機能、`question` → サポート。日本語の
ラベル名でもよい。どれも無ければ機能）。GitHub のリポジトリには最初から 3 つともある。

## 必ず利用者に伝えること

- **題名と本文は一般公開される。** 活動の様子を外に見せるため。issue フォームの注意書きを消さない
- **出さないもの**：担当者・書いた人・コメントの本文（GitHub のユーザー名を公開のページに出さない）。
  本文の @メンション は「@メンバー」になる。**画像も出ない**（非公開リポジトリの画像の URL は鍵入りのため）
- **全画面が公開で、書き込む画面は無い。** 本番（homepage）は既定で全画面がログイン必須なので、
  全ビューに `login_not_required` を付けて外してある（テスト `test_every_view_is_public` が付け忘れを捕まえる）
- **GitHub で直しても、活動ページに出るまで最大 5 分かかる**（キャッシュ）
- Project を複製したら、メンバーにボードの場所（`https://github.com/orgs/funITclub/projects/<番号>`）を伝える

## よく頼まれる手直し

| 頼まれごと | どこを直すか |
|---|---|
| トップに項目を足す | `views.py` の `HomeView.get_context_data` と `templates/<WG>_activity/home.html`。`HomeTests` にテストを足す |
| 期日が近いとみなす日数 | `views.py` の `DUE_SOON_DAYS` |
| 読み直す間隔 | `tickets.py` の `CACHE_SECONDS` |
| ステータスを増やす・減らす | Project のステータスの選択肢を直す（並び順もそのまま使う）。完了とみなすものは `tickets.py` の `DONE_STATUSES`、色は `STATUS_CSS` と `base.html` の `.s-<値>` |
| トラッカーを増やす | `tickets.py` の `TRACKERS`（値・表示・読むラベル）と issue フォーム |
| 一覧の件数を変える | `views.py` の `IssueListView.paginate_by` |
| ガントチャートの 1 日の幅 | `views.py` の `GanttView.DAY_PX`（下限。期間が長いと横に送る） |
| 本文に出すタグを増やす | `body.py` の `TAGS`・`ATTRIBUTES`。`img` と `style` は足さない |

ビューを足すときは、必ず `PageMixin`（チケットを使うなら `BoardMixin`）を継いで（全画面に WG の
名前とナビが出る）、`@method_decorator(login_not_required, name='dispatch')` を付ける。
活動ページから GitHub に書き込む機能は足さない（書くのは GitHub で直接）。
