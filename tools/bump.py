"""升一版：python tools/bump.py "改了什麼 1" "改了什麼 2" …
APP_VERSION 照規則加一（0.1.01 → 0.1.02 … 0.1.99 → 0.2.01），CHANGELOG.json 最上面加一筆（今天日期＋你寫的項目）。
要指定版本：python tools/bump.py --to 0.3.01 "…" """
import sys, re, json, time, pathlib
KIT = pathlib.Path(__file__).resolve().parent.parent; APP = KIT / 'app'
sys.path.insert(0, str(APP)); import core  # noqa: E402


def main(argv):
    to = None
    if argv[:1] == ['--to']: to, argv = argv[1], argv[2:]
    if not argv: sys.exit('用法：python tools/bump.py "這一版改了什麼" ["…"]')
    p = APP / 'app.py'; s = p.read_text(encoding='utf-8'); cur = re.search(r"APP_VERSION = '([^']+)'", s).group(1)
    new = to or core.next_version(cur)
    p.write_text(s.replace(f"APP_VERSION = '{cur}'", f"APP_VERSION = '{new}'", 1), encoding='utf-8')
    c = APP / 'CHANGELOG.json'; C = json.loads(c.read_text(encoding='utf-8'))
    C.insert(0, {'version': new, 'date': time.strftime('%Y-%m-%d'), 'items': list(argv)})
    c.write_text(json.dumps(C, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'✔ V{cur} → V{new}')


if __name__ == '__main__': main(sys.argv[1:])
