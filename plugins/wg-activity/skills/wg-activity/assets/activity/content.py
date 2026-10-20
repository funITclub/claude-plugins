# 活動ページに出す WG の情報。WG が自分で書き換える（変えたら PR を出す）。
#
# 個人の名前・連絡先は書かない（メンバーは Classroom と Chat で分かる）。

# WG 一覧のカードと同じ識別子と名前
CODE = 'WG-00'
NAME = 'WG の名前'

# 何をしている WG かを 1 文で。ページの見出しの下に出る
LEAD = '何を作っている WG かを 1 文で書く。'

# WG の紹介。空行で段落を分ける
INTRO = '''
何を問題だと思い、何を作ろうとしているのかを書く。

いまどの段階にいるのか（調べている・試作している・使ってもらっている）も書いておくと、
初めて見た人に伝わりやすい。
'''

# 構想資料（templates/WGNAME_activity/slides.html）。まだ無いうちは None のままにする。
# 入れると、トップに案内が出て /slides/ が開く
SLIDES_TITLE = None
SLIDES_SUMMARY = ''

# トップの「関連リンク」。（名前, URL）を並べる。WG が作っている Web アプリなど
LINKS = [
    # ('Webアプリ', 'https://funitclub.org/WGNAME/'),
]

# 「参加するには」のリンク先。WG 一覧の「WG に参加」から入ってもらう
JOIN_URL = 'https://funitclub.org/wg/'


def as_dict():
    """テンプレートに渡す形。"""
    return {
        'code': CODE,
        'name': NAME,
        'lead': LEAD,
        'intro': INTRO.strip(),
        'slides_title': SLIDES_TITLE,
        'slides_summary': SLIDES_SUMMARY,
        'links': LINKS,
        'join_url': JOIN_URL,
    }
