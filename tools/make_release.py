"""雲端打包用（GitHub Actions 會叫）：做出 Release 要放的檔案（跟 SortCut／TikLive 同一套）.

python tools/make_release.py --version     → 印出程式版本（app/app.py 的 APP_VERSION，例如 0.3.36）
python tools/make_release.py --launcher    → 印出啟動器版本（build/launcher.py 的 LAUNCHER_VERSION）
python tools/make_release.py --dist work/dist/ComfyRemote --out out --repo tpc20001/ComfyRemote

產生（前綴、名稱從 app/brand.json 讀）：
  CR_V<版本>.zip               程式更新包（manifest.json＋app\\*），跟 tools/pack.py 做的一樣；程式裡「☁ 更新」下載的就是這個（熱更新）
  CR_Shell_L<啟動器>.zip       EXE 外殼（ComfyRemote.exe＋_internal），啟動器版本變大才會用到
  ComfyRemote_Full_V<版本>.zip 第一次安裝用（外殼＋程式＋空的 UPDATE／LOG／Data；FFmpeg、你的資料不在裡面）
  update.json                  給程式讀：版本、啟動器版本、下載網址、SHA-256、大小、更新說明
  notes.md                     Release 頁面上的說明
"""
import argparse, hashlib, json, re, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / 'app'
OK_EXT = ('.py', '.json', '.md', '.txt', '.css', '.js', '.html', '.png', '.ico', '.svg')   # 跟 tools/pack.py、程式裡 load_pkg 認得的一樣


def brand(): return json.loads((APP / 'brand.json').read_text(encoding='utf-8-sig'))


def app_version():
    return re.search(r"^APP_VERSION\s*=\s*['\"]([^'\"]+)['\"]", (APP / 'app.py').read_text(encoding='utf-8'), re.M).group(1)


def launcher_version():
    return int(re.search(r'^LAUNCHER_VERSION\s*=\s*(\d+)', (ROOT / 'build' / 'launcher.py').read_text(encoding='utf-8'), re.M).group(1))


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def app_files(): return sorted(f for f in APP.iterdir() if f.is_file() and f.suffix.lower() in OK_EXT)


def zip_dir(zf, src, prefix=''):
    for p in sorted(Path(src).rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and p.name not in ('selftest.json',): zf.write(p, prefix + p.relative_to(src).as_posix())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--version', action='store_true'); ap.add_argument('--launcher', action='store_true')
    ap.add_argument('--dist', default=''); ap.add_argument('--out', default='out'); ap.add_argument('--repo', default='tpc20001/ComfyRemote')
    a = ap.parse_args()
    B = brand(); ver = app_version(); L = launcher_version(); pre = B['prefix']; name = B['id']
    if a.version: print(ver); return
    if a.launcher: print(L); return
    C = json.loads((APP / 'CHANGELOG.json').read_text(encoding='utf-8'))
    if not C or str(C[0].get('version')) != ver: sys.exit(f'CHANGELOG.json 最上面那筆要是 {ver}')
    for f in app_files():                                                       # 壞掉的程式檔不發
        if f.suffix == '.py': compile(f.read_text(encoding='utf-8'), str(f), 'exec')
        elif f.suffix == '.json': json.loads(f.read_text(encoding='utf-8-sig'))
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    tag = f'v{ver}'; base = f'https://github.com/{a.repo}/releases/download/{tag}/'

    zp = out / f'{pre}_V{ver}.zip'
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('manifest.json', json.dumps({'app': B['id'], 'version': ver, 'requires_launcher': 1}, ensure_ascii=False))
        for f in app_files(): zf.write(f, 'app/' + f.name)
    files = {'zip': zp}
    if a.dist:
        d = Path(a.dist); exe = f'{name}.exe'
        if not (d / exe).exists(): sys.exit(f'找不到 {d / exe}')
        sp = out / f'{pre}_Shell_L{L}.zip'
        with zipfile.ZipFile(sp, 'w', zipfile.ZIP_DEFLATED) as zf: zip_dir(zf, d)
        fp = out / f'{name}_Full_V{ver}.zip'
        with zipfile.ZipFile(fp, 'w', zipfile.ZIP_DEFLATED) as zf:
            zip_dir(zf, d, f'{name}/')
            for f in app_files(): zf.write(f, f'{name}/app/' + f.name)
            for n in ('UPDATE', 'LOG', 'Data'): zf.writestr(f'{name}/{n}/', '')
        files.update(shell=sp, full=fp)

    cur = next((e for e in C if str(e.get('version')) == ver), None) or {}
    info = {'app': B['id'], 'version': ver, 'launcher': L, 'date': cur.get('date', ''), 'tag': tag, 'notes': list(cur.get('items') or []),
            'zip': base + files['zip'].name, 'zip_sha256': sha(files['zip']), 'zip_size': files['zip'].stat().st_size}
    if 'shell' in files:
        info.update(shell=base + files['shell'].name, shell_sha256=sha(files['shell']), shell_size=files['shell'].stat().st_size,
                    full=base + files['full'].name, full_sha256=sha(files['full']), full_size=files['full'].stat().st_size)
    (out / 'update.json').write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding='utf-8')
    md = [f'## {B["name"]} V{ver}', '']
    md += [f'- {x}' for x in info['notes']] or ['- （這版沒有寫更新說明）']
    md += ['', '### 檔案', f'- `{pre}_V{ver}.zip`：程式更新包（程式裡按「☁ 更新」會自己下載這個，熱更新不用關程式）']
    if 'shell' in files:
        md += [f'- `{pre}_Shell_L{L}.zip`：EXE 外殼，啟動器第 {L} 版', f'- `{name}_Full_V{ver}.zip`：第一次安裝用（解壓縮後執行 {name}.exe；不含 FFmpeg）']
    md += ['- `update.json`：給程式讀的版本資訊']
    (out / 'notes.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print(json.dumps({k: (str(v) if isinstance(v, Path) else v) for k, v in info.items() if k != 'notes'}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
