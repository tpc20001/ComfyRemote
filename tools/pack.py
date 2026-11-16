"""打包更新包：python tools/pack.py  →  out/<前綴>_V<版本>.zip
會先檢查：app.py 的 APP_VERSION＝CHANGELOG.json 最上面那筆的版本、所有 .py 都能編譯、brand.json 讀得到。
更新包內容：manifest.json（app、version、requires_launcher）＋ app/ 底下所有檔（不含 __pycache__）。"""
import sys, re, json, zipfile, py_compile, pathlib
KIT = pathlib.Path(__file__).resolve().parent.parent; APP = KIT / 'app'; OUT = KIT / 'out'
ALLOWED = ('.py', '.json', '.md', '.txt', '.css', '.js', '.html', '.png', '.ico', '.svg')


def main():
    B = json.loads((APP / 'brand.json').read_text(encoding='utf-8-sig'))
    ver = re.search(r"APP_VERSION\s*=\s*'([^']+)'", (APP / 'app.py').read_text(encoding='utf-8')).group(1)
    C = json.loads((APP / 'CHANGELOG.json').read_text(encoding='utf-8'))
    if not C or str(C[0].get('version')) != ver: sys.exit(f'✖ CHANGELOG.json 最上面那筆要是 {ver}（現在是 {C[0].get("version") if C else "空的"}）：用 tools/bump.py 加')
    if not re.fullmatch(r'\d+\.\d+\.\d\d', ver): sys.exit(f'✖ 版本格式要像 0.1.02（最後一段兩位數）：{ver}')
    for f in APP.glob('*.py'):
        try: py_compile.compile(str(f), doraise=True)
        except py_compile.PyCompileError as ex: sys.exit(f'✖ {f.name} 編譯失敗：{ex.msg}')
    files = [f for f in sorted(APP.iterdir()) if f.is_file() and f.suffix.lower() in ALLOWED]
    OUT.mkdir(exist_ok=True); z = OUT / f'{B["prefix"]}_V{ver}.zip'
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('manifest.json', json.dumps({'app': B['id'], 'version': ver, 'requires_launcher': 1}, ensure_ascii=False))
        for f in files: zf.write(f, 'app/' + f.name)
    print(f'✔ {z}（{len(files)} 個檔）'); return z


if __name__ == '__main__': main()
