"""活動ページの雛形（assets/activity）を、WG の名前を入れて Django のプロジェクトにコピーする。

    python install.py <WG の名前> <manage.py のある場所>
    python install.py --issue-templates <manage.py のある場所>   issue フォームだけ置く

例: python install.py welfare .  →  ./welfare_activity/ と ./.github/ISSUE_TEMPLATE/ ができる

雛形の中の WGNAME（ファイルの中身とパス）を WG の名前に置き換える。アプリ名・URL の
名前空間・テンプレートの置き場所がすべて <WG の名前>_activity になり、homepage の中で
ほかの WG とぶつからない。アプリが既にあるときは上書きせずに止まる。

issue フォーム（assets/ISSUE_TEMPLATE。題名と本文が一般公開されるという注意書きつき）は
.github/ISSUE_TEMPLATE/ に置く。同じ名前のファイルがあれば、そのファイルだけ飛ばす。
"""

import re
import sys
from pathlib import Path

PLACEHOLDER = 'WGNAME'
ASSETS = Path(__file__).resolve().parent.parent / 'assets'


def copy_issue_templates(dest):
    out_dir = dest / '.github' / 'ISSUE_TEMPLATE'
    out_dir.mkdir(parents=True, exist_ok=True)
    for src in sorted((ASSETS / 'ISSUE_TEMPLATE').glob('*.yml')):
        out = out_dir / src.name
        if out.exists():
            print(f'{out} は既にある。飛ばした（注意書きが入っているか確かめる）。')
            continue
        out.write_text(src.read_text(encoding='utf-8'), encoding='utf-8')
        print(f'{out} を置いた。')


def main(argv):
    if len(argv) == 3 and argv[1] == '--issue-templates':
        copy_issue_templates(Path(argv[2]))
        return
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
    for src in sorted((ASSETS / 'activity').rglob('*')):
        if src.is_dir() or '__pycache__' in src.parts:
            continue
        rel = str(src.relative_to(ASSETS / 'activity')).replace(PLACEHOLDER, name)
        out = app / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(src.read_text(encoding='utf-8').replace(PLACEHOLDER, name), encoding='utf-8')
        count += 1
    print(f'{app} に {count} ファイルを置いた（アプリ名 {name}_activity）。')
    copy_issue_templates(dest)


if __name__ == '__main__':
    main(sys.argv)
