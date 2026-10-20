# fun IT club の Claude Code プラグイン

WG で使い回すスキルを置くマーケットプレイス。

## 入れ方

ターミナルのセッションのプロンプトで：

```
/plugin install wg-activity --marketplace funITclub/claude-plugins
```

`y` でマーケットプレイスを追加し、スコープは user（既定）のまま Enter。
user スコープで入れると、**どのリポジトリで Claude Code を起動しても使えます**。

シェルから入れる場合：

```
claude plugin install wg-activity --marketplace funITclub/claude-plugins
```

デスクトップアプリで `/plugin` が使えない場合は、プロンプト横の + → Plugins →
Add marketplace に `funITclub/claude-plugins` を入れて、Add plugin。

## 入っているもの

| プラグイン | 中身 |
|---|---|
| `wg-activity` | WG のリポジトリに活動ページ（`<WG>_activity` アプリ）を足すスキル。トップに WG の紹介・構想資料への案内・チケットの様子を並べ、構想資料（スライド）と Redmine 風のチケット管理を持つ |

`django-tracker` は `wg-activity` に置き換えた。入れていた人は外してから入れ直す：

```
claude plugin uninstall django-tracker
claude plugin install wg-activity --marketplace funITclub/claude-plugins
```

## 新しいスキルを足すとき

1. `plugins/<名前>/.claude-plugin/plugin.json` を作る
2. `plugins/<名前>/skills/<名前>/SKILL.md` にスキルを書く
3. `.claude-plugin/marketplace.json` の `plugins` に 1 行足す
4. 入れている人は `claude plugin update` → `/reload-plugins`

テンプレート（`wg-template`）と違い、**作成済みの WG リポジトリにも行き渡ります**。
各自が一度インストールすれば、更新は `claude plugin update` で追えます。
