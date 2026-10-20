"""活動ページの雛形（assets/activity）を、WG の名前を入れて Django のプロジェクトにコピーする。

    python install.py <WG の名前> <manage.py のある場所>

例: python install.py welfare .  →  ./welfare_activity/ ができる

雛形の中の WGNAME（ファイルの中身とパス）を WG の名前に置き換える。アプリ名・URL の
名前空間・テンプレートの置き場所・テーブル名がすべて <WG の名前>_activity になり、
homepage の中でほかの WG とぶつからない。既にあるときは上書きせずに止まる。
"""

import re
import sys
from pathlib import Path

PLACEHOLDER = 'WGNAME'
ASSETS = Path(__file__).resolve().parent.parent / 'assets' / 'activity'


def main(argv):
    if len(argv) != 3:
        sys.exit(__doc__)
    name, dest = argv[1], Path(argv[2])
    if not re.fullmatch(r'[a-z][a-z0-9]*', name):
        sys.exit(f'WG の名前は英小文字と数字だけにする（{name!r}）。Django のアプリ名と URL に使うため。')
    if not (dest / 'manage.py').exists():
        sys.exit(f'{dest} に manage.py が無い。Django のプロジェクトの一番上を渡す。')
    app = dest / f'{name}_activity'
    if app.exists():
        sys.exit(f'{app} は既にある。上書きしない。')

    count = 0
    for src in sorted(ASSETS.rglob('*')):
        if src.is_dir() or '__pycache__' in src.parts:
            continue
        rel = str(src.relative_to(ASSETS)).replace(PLACEHOLDER, name)
        out = app / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(src.read_text(encoding='utf-8').replace(PLACEHOLDER, name), encoding='utf-8')
        count += 1
    print(f'{app} に {count} ファイルを置いた（アプリ名 {name}_activity）。')


if __name__ == '__main__':
    main(sys.argv)
