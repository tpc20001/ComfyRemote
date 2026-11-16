"""☁ 雲端自動更新（V0.3.36，跟 SortCut／TikLive 同一套）：讀 GitHub Releases 上的 update.json，有新版只「提示」，一定要你按「更新」才下載.
沒有 Qt：畫面那邊（app.py）用 bind() 把「通知」「熱更新」「換 EXE」「現在在忙什麼」交給這裡，熱更新換新版後會再 bind 一次。

- 開程式 1 分鐘後檢查一次，之後每 6 小時（設定可以關）；全部在背景執行緒，不會卡畫面。
- 只有程式變 → 下載 CR_V….zip（背景、低優先、限速）→ 比 SHA-256 → 熱更新（程式不用關，生圖不中斷）。
- EXE 要換（update.json 的 launcher 比現在的大）→ 有生圖在跑／排隊就先列給你看、建議等做完；你堅持才繼續 →
  下載 CR_Shell_L….zip → 寫一個小 BAT：等程式關掉 → 換 ComfyRemote.exe 和 _internal → 開起來 → 新的開不起來就換回舊的；
  過程寫進 LOG\\update_log.txt。程式是「正常關掉」的，開起來排隊的生圖會自動接著做。
"""
import builtins
import hashlib
import json
import os
import ssl
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

REPO = 'tpc20001/ComfyRemote'
URLS = (f'https://github.com/{REPO}/releases/latest/download/update.json',              # Public repo：更新檔放它自己的 Releases
        f'https://github.com/{REPO}-Release/releases/latest/download/update.json')      # （以後改 Private：更新檔放這個公開 repo）
IS_WIN = os.name == 'nt'

# 熱更新會重新載入這個模組：狀態放在 builtins 裡，新舊版本共用（下載到一半、檢查結果不會不見）
_S = builtins.__dict__.setdefault('_ak_cloud_state', {'chk': None, 'dl': None, 'busy': False, 'loop': False, 'cancel': False, 'msg': '', 'checking': False, 'ctx': {}})


def bind(**kw):
    """app.py 告訴這裡：eng（引擎）、ver（程式版本）、brand、notify(訊息)、apply_zip(路徑)、swap(外殼zip)、busy()→[說明…]."""
    _S['ctx'].update(kw)


def C(k, d=None): return _S['ctx'].get(k, d)


def vkey(v):
    import re
    return tuple(int(x) for x in re.findall(r'\d+', str(v or ''))) or (0,)


def launcher():
    """現在這個 EXE 是第幾版啟動器（第 2 版起會設環境變數 AK_LAUNCHER；舊的＝1）."""
    try: return int(os.environ.get('AK_LAUNCHER') or 1)
    except ValueError: return 1


def log(msg):
    E = C('eng')
    try: E.log.w('☁ ' + msg)
    except Exception: pass
    try:
        root = Path(E.root) if E is not None else Path(sys.executable).parent
        (root / 'LOG').mkdir(exist_ok=True)
        with open(root / 'LOG' / 'update_log.txt', 'a', encoding='utf-8') as f: f.write(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] ☁ {msg}\n')
    except Exception: pass


def cfg(k, d=None):
    try:
        v = C('eng').cfg.get(k)
        return d if v is None else v
    except Exception: return d


def store(**kw):
    """Data\\cloud_upd.json：略過的版本、提示過的版本、上次檢查時間."""
    try: p = Path(C('eng').data) / 'cloud_upd.json'
    except Exception: return {}
    try: D = json.loads(p.read_text(encoding='utf-8'))
    except Exception: D = {}
    if kw:
        D.update(kw)
        try: t = p.with_suffix('.tmp'); t.write_text(json.dumps(D, ensure_ascii=False), encoding='utf-8'); os.replace(str(t), str(p))
        except Exception: pass
    return D


# ---------------------------------------------------------------- 連線
_CTX = None


def _ctx():
    """憑證：Windows 自己的憑證庫有時候還沒有 GitHub 的根憑證 → 再加上 certifi 的清單（新的 EXE 有帶）；都不行就用 PowerShell 下載."""
    global _CTX
    if _CTX is None:
        c = ssl.create_default_context()
        try:
            import certifi; c.load_verify_locations(cafile=certifi.where())
        except Exception: pass
        _CTX = c
    return _CTX


def _open(url, timeout=20):
    req = urllib.request.Request(url, headers={'User-Agent': f'ComfyRemote-Updater/{C("ver", "?")}', 'Accept': 'application/octet-stream, application/json'})
    return urllib.request.urlopen(req, timeout=timeout, context=_ctx())


def _is_cert(ex): return isinstance(ex, ssl.SSLError) or 'CERTIFICATE' in str(ex).upper()


def _ps_get(url, dest, timeout=600):
    """最後一招：用 Windows 自己的 PowerShell 下載（走 Windows 的憑證檢查，會自動補根憑證）."""
    u = url.replace("'", "''"); o = str(dest).replace("'", "''")
    cmd = f"$ProgressPreference='SilentlyContinue';[Net.ServicePointManager]::SecurityProtocol='Tls12';Invoke-WebRequest -UseBasicParsing -UserAgent 'ComfyRemote-Updater' -Uri '{u}' -OutFile '{o}'"
    r = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', cmd], capture_output=True, timeout=timeout,
                       creationflags=(0x08000000 | 0x00004000) if IS_WIN else 0)   # 沒有視窗、低優先
    if r.returncode != 0 or not Path(dest).exists(): raise IOError('PowerShell 也下載失敗：' + (r.stderr or b'').decode('utf-8', 'ignore')[-300:])
    return Path(dest)


def _low_priority():
    """這條下載執行緒降到最低優先，不跟生圖搶 CPU."""
    if not IS_WIN: return
    try:
        import ctypes
        ctypes.windll.kernel32.SetThreadPriority(ctypes.windll.kernel32.GetCurrentThread(), -2)   # THREAD_PRIORITY_LOWEST
    except Exception: pass


# ---------------------------------------------------------------- 檢查
def check(manual=False, urls=None):
    """讀 update.json → 有沒有新版、要不要換 EXE。有新版只提示（同一版只提示一次；略過的那版不提示）."""
    err = ''; R = None; cur = C('ver', '0'); app_id = (C('brand') or {}).get('id', 'ComfyRemote')
    for u in (urls or URLS):
        try:
            try:
                with _open(u) as r: info = json.loads(r.read().decode('utf-8-sig'))
            except Exception as ex0:
                if not (_is_cert(ex0) and IS_WIN): raise
                import tempfile
                tp = _ps_get(u, Path(tempfile.gettempdir()) / f'cr_upd_{os.getpid()}.json', timeout=120)
                info = json.loads(tp.read_bytes().decode('utf-8-sig'))
                try: tp.unlink()
                except Exception: pass
            if str(info.get('app') or app_id) != app_id or not info.get('version'): err = f'{u}：不是 {app_id} 的 update.json'; continue
            need_shell = bool(info.get('shell')) and int(info.get('launcher') or 1) > launcher()
            newer_code = vkey(info['version']) > vkey(cur)
            R = {'ok': True, 'info': info, 'url': u, 't': time.time(), 'need_shell': need_shell, 'newer_code': newer_code, 'newer': newer_code or need_shell, 'cur': cur, 'launcher': launcher()}
            break
        except Exception as ex: err = f'{type(ex).__name__}: {ex}'[:200]
    if R is None: R = {'ok': False, 'newer': False, 't': time.time(), 'cur': cur, 'message': '連不到 GitHub 更新：' + err}
    D = store(last_t=time.time(), last_ok=R['ok'])
    R['skipped'] = bool(R.get('newer') and D.get('skip') == (R.get('info') or {}).get('version') and not R.get('need_shell'))
    _S['chk'] = R
    if R.get('newer') and not R['skipped']:
        v = R['info']['version']; key = f"{v}/{R['info'].get('launcher')}"
        if manual or D.get('told') != key:
            store(told=key)
            msg = f"雲端有新版 V{v}（現在 V{cur}）" + ('，這次要換 EXE（程式會關掉再自動打開）' if R['need_shell'] else '，可以熱更新、不中斷生圖')
            log(msg)
            try: (C('notify') or (lambda m: None))(msg)
            except Exception: pass
    elif manual: log(R.get('message') or f"已經是最新（雲端 V{(R.get('info') or {}).get('version')}）")
    return R


def loop_start():
    """開程式 1 分鐘後檢查，之後每 6 小時（設定「cloud_on」關掉就不查）。只開一條，熱更新後也不重開."""
    if _S.get('loop'): return
    _S['loop'] = True
    def run_():
        try:
            time.sleep(60)
            while True:
                try:
                    if cfg('cloud_on', True): check()
                except Exception: pass
                t0 = time.time()
                while time.time() - t0 < 6 * 3600: time.sleep(20)
        finally: _S['loop'] = False
    threading.Thread(target=run_, name='CloudUpdCheck', daemon=True).start()


# ---------------------------------------------------------------- 下載
def download(url, dest, sha='', size=0, label=''):
    """背景、低優先、限速（設定 cloud_kbps，預設 2048 KB/s）、先寫 .part、比 SHA-256；可以取消."""
    _low_priority()
    dest = Path(dest); dest.parent.mkdir(parents=True, exist_ok=True); tmp = dest.with_name(dest.name + '.part')
    lim = max(64.0, float(cfg('cloud_kbps', 2048) or 2048)) * 1024; h = hashlib.sha256(); got = 0; t0 = time.time()
    _S['dl'] = {'label': label, 'got': 0, 'size': int(size or 0), 't0': t0, 'spd': 0.0}
    try:
        try:
            with _open(url, timeout=60) as r, open(tmp, 'wb') as f:
                tot = int(r.headers.get('Content-Length') or size or 0); _S['dl']['size'] = tot
                while True:
                    if _S.get('cancel'): raise InterruptedError('取消了')
                    b = r.read(256 * 1024)
                    if not b: break
                    f.write(b); h.update(b); got += len(b)
                    el = time.time() - t0; need = got / lim
                    if need > el: time.sleep(need - el)
                    _S['dl'].update(got=got, spd=got / max(0.001, time.time() - t0))
        except InterruptedError: raise
        except Exception as ex0:
            if not (_is_cert(ex0) and IS_WIN): raise
            _ps_get(url, tmp); h = hashlib.sha256()                              # 憑證不過：改用 Windows 自己下載
            with open(tmp, 'rb') as f:
                for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
        if sha and h.hexdigest().lower() != str(sha).lower(): raise IOError('下載的檔案不完整（SHA-256 對不上），請再按一次更新')
        os.replace(str(tmp), str(dest)); return dest
    except BaseException:
        try: tmp.unlink()
        except Exception: pass
        raise
    finally: _S['dl'] = None


# ---------------------------------------------------------------- 更新
def busy():
    try: return list((C('busy') or (lambda: []))())
    except Exception: return []


def update(force=False):
    """按「更新」：沒有要換 EXE → 下載後熱更新；要換 EXE → 有工作在做就先回清單（force＝我堅持）→ 下載 → 換 EXE、重開."""
    R = _S.get('chk'); E = C('eng'); prefix = (C('brand') or {}).get('prefix', 'CR')
    if _S.get('busy'): return {'ok': False, 'message': '已經在更新了，請稍候'}
    if not R or not R.get('ok') or not R.get('newer'): return {'ok': False, 'message': '沒有新版（先按「檢查更新」）'}
    info = R['info']
    if R['need_shell']:
        if not getattr(sys, 'frozen', False): return {'ok': False, 'message': '這不是 EXE 執行的（原始碼模式），不能換 EXE'}
        B = busy()
        if B and not force:
            return {'ok': False, 'need_confirm': True, 'busy': B,
                    'message': f"這次要換 EXE，程式會關掉再自動打開（約 1 分鐘）。現在還有：" + '、'.join(B) + '。建議等做完再更新；堅持現在更新的話，正在做的那張會中斷，打開後排隊的會自動接著做（中斷的那張重新做）。'}
    _S['busy'] = True; _S['cancel'] = False; _S['msg'] = '下載中…'
    root = Path(E.root)
    def run_():
        try:
            if R['need_shell']:
                if R['newer_code']:                                              # 程式也有新的：放進 UPDATE，新 EXE 開起來時由啟動器套用
                    download(info['zip'], root / 'UPDATE' / f"{prefix}_V{info['version']}.zip", info.get('zip_sha256'), info.get('zip_size'), f"程式 V{info['version']}")
                sz = download(info['shell'], root / 'UPDATE' / f"{prefix}_Shell_L{info.get('launcher')}.zip", info.get('shell_sha256'), info.get('shell_size'), f"EXE 第 {info.get('launcher')} 版")
                _S['msg'] = '下載好了，準備換 EXE（程式會關掉再自動打開）'; log(f"EXE 第 {info.get('launcher')} 版下載好了（SHA-256 對過），準備換 EXE")
                C('swap')(str(sz))
            else:
                zp = download(info['zip'], Path(E.data) / 'cloud' / f"{prefix}_V{info['version']}.zip", info.get('zip_sha256'), info.get('zip_size'), f"程式 V{info['version']}")
                _S['msg'] = f"下載好了（SHA-256 對過），熱更新到 V{info['version']}…"; log(f"V{C('ver')} → V{info['version']}（熱更新，生圖不中斷）")
                C('apply_zip')(str(zp)); _S['busy'] = False
        except Exception as ex:
            _S['busy'] = False; _S['msg'] = f'更新失敗：{ex}'; log(f'更新失敗：{ex}')
    threading.Thread(target=run_, name='CloudUpdDl', daemon=True).start()
    return {'ok': True, 'message': '開始下載（背景、限速），好了會自動更新' + ('；要換 EXE，程式會關掉再自動打開' if R['need_shell'] else '，不中斷生圖')}


def info():
    R = dict(_S.get('chk') or {}); D = store(); I = R.get('info') or {}
    return {'ok': True, 'cur': C('ver'), 'launcher': launcher(), 'on': bool(cfg('cloud_on', True)), 'kbps': int(cfg('cloud_kbps', 2048) or 2048),
            'chk': {k: R.get(k) for k in ('ok', 'newer', 'need_shell', 'newer_code', 'skipped', 't', 'message', 'url')} if R else None,
            'ver': I.get('version'), 'new_launcher': I.get('launcher'), 'notes': list(I.get('notes') or [])[:30], 'date': I.get('date'),
            'zip_size': I.get('zip_size'), 'shell_size': I.get('shell_size'), 'skip': D.get('skip'), 'last_t': D.get('last_t'),
            'busy': bool(_S.get('busy')), 'checking': bool(_S.get('checking')), 'msg': _S.get('msg') or '', 'dl': dict(_S.get('dl') or {}) or None,
            'work': busy(), 'frozen': bool(getattr(sys, 'frozen', False))}


def op(d):
    o = str((d or {}).get('op') or '')
    if o == 'check':
        if _S.get('checking'): return {'ok': True, 'message': '檢查中…'}
        _S['checking'] = True
        def run_():
            try: check(manual=True)
            finally: _S['checking'] = False
        threading.Thread(target=run_, name='CloudUpdCheckNow', daemon=True).start()
        return {'ok': True, 'message': '檢查中…（幾秒）'}
    if o == 'update': return update(force=bool(d.get('force')))
    if o == 'skip':
        v = str(((_S.get('chk') or {}).get('info') or {}).get('version') or '')
        if not v: return {'ok': False, 'message': '沒有可以略過的版本'}
        if (_S.get('chk') or {}).get('need_shell'): return {'ok': False, 'message': '這版要換 EXE，不能略過'}
        store(skip=v); _S['chk']['skipped'] = True; log(f'略過雲端版本 V{v}')
        return {'ok': True, 'message': f'這版（V{v}）不再提示；有更新的版本才會再提示'}
    if o == 'unskip': store(skip=''); return {'ok': True, 'message': '取消略過'}
    if o == 'cancel': _S['cancel'] = True; return {'ok': True, 'message': '取消下載'}
    if o == 'on':
        try: C('eng').cfg.set('cloud_on', bool(d.get('v'))); return {'ok': True, 'message': '自動檢查更新：' + ('開' if d.get('v') else '關')}
        except Exception as ex: return {'ok': False, 'message': str(ex)}
    return {'ok': False, 'message': '不認得'}


# ---------------------------------------------------------------- 換 EXE
def write_bat(root, shell_zip, pid, exe):
    """等程式（pid）關掉 → 解開新 EXE → 換 exe、_internal → 打開、等它回報（UPDATE\\shell_ok.flag）→ 刪舊的；
    換不成或新的開不起來 → 換回舊的照常打開。過程寫進 LOG\\update_log.txt."""
    root = Path(root); okf = root / 'UPDATE' / 'shell_ok.flag'; bat = root / 'UPDATE' / 'shell_update.bat'; tmp = root / 'UPDATE' / 'shell_new'; logf = root / 'LOG' / 'update_log.txt'
    q = lambda p: str(p).replace('%', '%%')
    s = f"""@echo off
chcp 65001 >nul
title ComfyRemote 換 EXE
set "LOGF={q(logf)}"
echo 等 ComfyRemote 關掉...
set /a N=0
:wait
set /a N+=1
if %N% GTR 180 goto go
tasklist /FI "PID eq {int(pid)}" /NH 2>nul | find "{int(pid)}" >nul && (timeout /t 1 /nobreak >nul & goto wait)
:go
timeout /t 3 /nobreak >nul
echo [%date% %time%] [換 EXE] 開始（{q(shell_zip)}） >> "%LOGF%"
if exist "{q(tmp)}" rmdir /s /q "{q(tmp)}"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '{q(shell_zip)}' -DestinationPath '{q(tmp)}' -Force"
if not exist "{q(tmp)}\\{exe}" goto fail
if exist "{q(root)}\\_internal_old" rmdir /s /q "{q(root)}\\_internal_old"
if exist "{q(root)}\\{exe}.old" del /f /q "{q(root)}\\{exe}.old"
if exist "{q(root)}\\_internal" move "{q(root)}\\_internal" "{q(root)}\\_internal_old" >nul
move "{q(root)}\\{exe}" "{q(root)}\\{exe}.old" >nul
if exist "{q(root)}\\{exe}" goto restore
robocopy "{q(tmp)}" "{q(root)}" /E /R:3 /W:2 /NFL /NDL /NJH /NJS /NP >nul
if not exist "{q(root)}\\{exe}" goto restore
if not exist "{q(root)}\\_internal" goto restore
echo [%date% %time%] [換 EXE] 檔案換好了，打開新的 EXE、等它開起來（最多 3 分鐘） >> "%LOGF%"
rmdir /s /q "{q(tmp)}"
if exist "{q(okf)}" del /f /q "{q(okf)}"
start "" /D "{q(root)}" "{q(root)}\\{exe}"
set /a K=0
:chk
timeout /t 3 /nobreak >nul
if exist "{q(okf)}" goto good
set /a K+=1
if %K% GTR 60 goto slow
tasklist /FI "IMAGENAME eq {exe}" /NH 2>nul | find /I "{exe}" >nul && goto chk
echo [%date% %time%] [換 EXE] 新的 EXE 開不起來（自己關掉了），換回舊的 >> "%LOGF%"
goto restore
:good
echo [%date% %time%] [換 EXE] 新的 EXE 開起來了，刪掉舊的 >> "%LOGF%"
del /f /q "{q(okf)}"
if exist "{q(root)}\\_internal_old" rmdir /s /q "{q(root)}\\_internal_old"
if exist "{q(root)}\\{exe}.old" del /f /q "{q(root)}\\{exe}.old"
exit /b 0
:slow
echo [%date% %time%] [換 EXE] 新的 EXE 還在跑但 3 分鐘沒回報，先留著舊的備份（_internal_old） >> "%LOGF%"
exit /b 0
:restore
echo [%date% %time%] [換 EXE] 失敗，換回舊的 >> "%LOGF%"
if exist "{q(root)}\\_internal_old" (if exist "{q(root)}\\_internal" rmdir /s /q "{q(root)}\\_internal")
if exist "{q(root)}\\_internal_old" move "{q(root)}\\_internal_old" "{q(root)}\\_internal" >nul
if exist "{q(root)}\\{exe}.old" (if exist "{q(root)}\\{exe}" del /f /q "{q(root)}\\{exe}")
if exist "{q(root)}\\{exe}.old" move "{q(root)}\\{exe}.old" "{q(root)}\\{exe}" >nul
:fail
echo [%date% %time%] [換 EXE] 沒有換成（解壓縮或搬檔失敗），用原本的 EXE 打開 >> "%LOGF%"
if exist "{q(tmp)}" rmdir /s /q "{q(tmp)}"
tasklist /FI "IMAGENAME eq {exe}" /NH 2>nul | find /I "{exe}" >nul && exit /b 1
start "" /D "{q(root)}" "{q(root)}\\{exe}"
exit /b 1
"""
    bat.parent.mkdir(parents=True, exist_ok=True); logf.parent.mkdir(parents=True, exist_ok=True)
    bat.write_bytes(s.replace('\n', '\r\n').encode('utf-8')); return bat


def run_bat(bat):
    """開一個不擋住程式的 BAT（程式關掉它還繼續跑）."""
    if IS_WIN: subprocess.Popen(['cmd', '/c', str(bat)], creationflags=0x00000008 | 0x00000200 | 0x08000000, close_fds=True)   # DETACHED | NEW_GROUP | NO_WINDOW


def shell_ok_later(root, exe, delay=20):
    """換 EXE 後開起來了 → 20 秒後告訴 BAT（它才刪舊的；沒回報又關掉就換回舊的）."""
    root = Path(root)
    if not ((root / '_internal_old').exists() or (root / f'{exe}.old').exists()): return
    def go():
        time.sleep(delay)
        try: (root / 'UPDATE').mkdir(exist_ok=True); (root / 'UPDATE' / 'shell_ok.flag').write_text(str(time.time()), encoding='utf-8'); log(f'換 EXE 成功：啟動器第 {launcher()} 版、V{C("ver")}')
        except Exception: pass
    threading.Thread(target=go, name='CloudShellOk', daemon=True).start()
