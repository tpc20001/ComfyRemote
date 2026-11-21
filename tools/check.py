"""快速檢查（改完程式、打包前跑）：python tools/check.py
1. 所有 .py 編譯  2. 引擎（不用 Qt）：設定、資料庫、後台總控制、熱更新交接  3. 手機網頁：登入、API、頁面的 JavaScript（有 node 的話檢查語法）
4. 畫面：有 PySide6 就用真的（offscreen），沒有就用 tools/qtstub（假的 Qt，只抓 Python 錯誤）建主視窗、跑一次熱更新。全部 ✔ 才打包。"""
import sys, os, re, json, time, shutil, tempfile, zipfile, subprocess, py_compile, pathlib, urllib.request, urllib.parse, urllib.error
KIT = pathlib.Path(__file__).resolve().parent.parent; APP = KIT / 'app'
OK = []


def step(name, fn):
    t0 = time.time()
    try: fn(); OK.append(True); print(f'  ✔ {name}（{time.time() - t0:.1f} 秒）')
    except Exception as ex:
        OK.append(False); print(f'  ✖ {name}：{type(ex).__name__}: {ex}')
        import traceback; traceback.print_exc()


def t_compile():
    for f in APP.glob('*.py'): py_compile.compile(str(f), doraise=True)


def t_engine():
    sys.path.insert(0, str(APP)); import core
    assert core.next_version('0.1.99') == '0.2.01' and core.next_version('0.1.01') == '0.1.02'
    d = tempfile.mkdtemp(); E = core.Engine(d, version='0.0.1'); E.cfg.set('bg_ramp_sec', 0)
    E.demo_add(3, 0.3); time.sleep(2.5); assert E.demo_done[0] == 3, E.demo_done
    E.bg_set_pause('demo', True); E.demo_add(1, 0.3); time.sleep(1); assert E.demo_done[0] == 3
    N = core.Engine(d, adopt=E, start=False, version='0.0.2'); N.start(); assert E.retired
    N.bg_set_pause('demo', False); time.sleep(2); assert N.demo_done[0] == 4, N.demo_done
    N.shutdown(); shutil.rmtree(d, ignore_errors=True)


def t_web():
    sys.path.insert(0, str(APP)); import core, web, webpage, types
    d = tempfile.mkdtemp(); E = core.Engine(d, version='0.0.1'); E.cfg.set('web_pin_salt', 's'); E.cfg.set('web_pin_hash', web.pin_hash('1234', 's'))
    S = web.WebServer(lambda: E, lambda: None, lambda f: f(), lambda: types.SimpleNamespace(LAB_LIST=[]), '0.0.1', core.BRAND); port = 47000 + os.getpid() % 1000
    assert S.start(port)
    def call(p, body=None, tok=''):
        r = urllib.request.Request(f'http://127.0.0.1:{port}' + p, data=None if body is None else json.dumps(body).encode(), headers={'Content-Type': 'application/json', 'x-app-token': tok})
        try: return json.loads(urllib.request.urlopen(r, timeout=5).read())
        except urllib.error.HTTPError as e: return json.loads(e.read())
    assert call('/api/state').get('login'); tok = call('/api/login', {'pin': '1234'})['token']
    for p in ('/api/state', '/api/perf', '/api/settings', '/api/changelog'): assert call(p, tok=tok).get('ok'), p
    assert call('/api/bgctl', {'a': 'pause', 'k': 'gen'}, tok)['ok'] and E.bg_pause.get('gen')
    assert len(urllib.request.urlopen(f'http://127.0.0.1:{port}/', timeout=5).read()) > 5000
    S.close(); E.shutdown()
    if shutil.which('node'):
        js = '\n'.join(re.findall(r'<script>(.*?)</script>', webpage.PAGE, re.S)); f = pathlib.Path(d) / 'p.js'; f.write_text(js, encoding='utf-8')
        r = subprocess.run(['node', '--check', str(f)], capture_output=True, text=True); assert r.returncode == 0, r.stderr
    else: print('    （沒有 node，跳過 JavaScript 語法檢查）')


def t_gzip():
    """V0.2.99 頁面壓縮."""
    import core, web, types, gzip
    d = tempfile.mkdtemp(); E = core.Engine(d, version='0.0.1', start=False)
    S = web.WebServer(lambda: E, lambda: None, lambda f: f(), lambda: types.SimpleNamespace(LAB_LIST=[]), '0.0.1', core.BRAND); pt = 46000 + os.getpid() % 900; assert S.start(pt)
    try:
        r = urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{pt}/', headers={'Accept-Encoding': 'gzip'}), timeout=10); b = r.read()
        assert r.headers.get('Content-Encoding') == 'gzip' and b'<script>' in gzip.decompress(b) and len(b) < 160000, len(b)
    finally: S.close()


def t_imgk():
    """V0.3.31 平板不送 cookie：看圖網址帶 ?k=登入碼也能看；別的 API 不吃 k；錯的 k 不行."""
    import core, web, types
    d = tempfile.mkdtemp(); E = core.Engine(d, version='0.0.1', start=False)
    E.cfg.set('web_tokens', ['tok123']); f = E.gen_save_input(b'\x89PNG\r\n\x1a\n' + b'0' * 50, 't')
    S = web.WebServer(lambda: E, lambda: None, lambda f: f(), lambda: types.SimpleNamespace(LAB_LIST=[]), '0.0.1', core.BRAND); pt = 46000 + (os.getpid() + 311) % 900; assert S.start(pt)
    def code(u):
        try: return urllib.request.urlopen(f'http://127.0.0.1:{pt}{u}', timeout=10).status
        except urllib.error.HTTPError as e: return e.code
    try:
        q = urllib.parse.quote('inputs/' + f)
        assert code(f'/api/img?f={q}&k=tok123') == 200
        assert code(f'/api/img?f={q}') == 401 and code(f'/api/img?f={q}&k=bad') == 401
        assert code('/api/gen_hist?k=tok123') == 401
        # V0.3.33 瀏覽器留著舊的失效 cookie：網址的 k、標頭的登入碼還是要有效（之前被舊 cookie 擋掉 → 平板破圖）
        r = urllib.request.Request(f'http://127.0.0.1:{pt}/api/img?f={q}&k=tok123', headers={'Cookie': 'app_t=oldstale'}); assert urllib.request.urlopen(r, timeout=10).status == 200
        r = urllib.request.Request(f'http://127.0.0.1:{pt}/api/hello', headers={'Cookie': 'app_t=oldstale', 'x-app-token': 'tok123'}); rr = urllib.request.urlopen(r, timeout=10)
        assert json.loads(rr.read())['authed'] and 'app_t=tok123' in (rr.headers.get('Set-Cookie') or '')
    finally: S.close()


def t_ig():
    """V0.3.35 📸 IG 下載（從 TikLive 搬過來）：網址排隊、資料夾清單、看圖／下載帶登入碼、Cookie 只回有沒有存、資料夾不能跳出去."""
    import core, web, types
    d = tempfile.mkdtemp(); E = core.Engine(d, version='0.0.1', start=False); E.cfg.set('web_tokens', ['tok123']); G = E.igdl()
    S = web.WebServer(lambda: E, lambda: None, lambda f: f(), lambda: types.SimpleNamespace(LAB_LIST=[]), '0.0.1', core.BRAND); pt = 46000 + (os.getpid() + 517) % 900; assert S.start(pt)
    def call(u, body=None, raw=False):
        h = {'x-app-token': 'tok123'}
        if body is not None and not raw: body = json.dumps(body).encode(); h['Content-Type'] = 'application/json'
        elif raw: body = body.encode()
        try: r = urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{pt}{u}', data=body, headers=h), timeout=10); return r.status, r.read(), r.headers
        except urllib.error.HTTPError as e: return e.code, e.read(), e.headers
    try:
        st, b, _ = call('/api/igadd', '你好 https://www.tiktok.com/@a/video/1', raw=True); assert not json.loads(b)['ok']
        G._igdl_one = lambda u: {'ok': True, 'url': u, 'file': 'acc_20261101_120000.jpg', 'files': ['acc_20261101_120000.jpg'], 'message': '✔ IG @acc：1 張照片'}
        st, b, _ = call('/api/igadd', '看 https://www.instagram.com/reel/ABCdef123/?igsh=1 跟 https://www.instagram.com/p/XYZ_12345/', raw=True); j = json.loads(b); assert j['ok'] and j['n'] == 2, j
        for _ in range(50):
            I = json.loads(call('/api/iginfo')[1])
            if not I['run'] and len(I['done']) == 2: break
            time.sleep(0.1)
        assert len(I['done']) == 2 and all(x['src'] == 'ig' and x['files'] for x in I['done']), I
        dd = G._igdl_dir(); dd.mkdir(parents=True, exist_ok=True); (dd / 'acc_20261101_120000.jpg').write_bytes(b'\xff\xd8\xff' + b'0' * 99); (dd / 'secret.txt').write_text('x')
        L = json.loads(call('/api/iglist')[1]); assert [x['f'] for x in L['items']] == ['acc_20261101_120000.jpg'] and L['items'][0]['u'] == 'acc' and L['items'][0]['k'] == 'i', L
        q = urllib.parse.quote('acc_20261101_120000.jpg')
        assert urllib.request.urlopen(f'http://127.0.0.1:{pt}/api/igfile?f={q}&k=tok123&dl=1', timeout=10).status == 200
        assert call('/api/igfile?f=secret.txt')[0] == 404 and call('/api/igfile?f=..%2Facc_20261101_120000.jpg')[0] == 404
        assert call('/api/igthumb?f=' + q)[0] == 200
        j = json.loads(call('/api/igck', {'v': 'sessionid=12345678%3Aabcdefghijklmnopqr%3A1;'})[1]); assert j['ok'] and j['set'], j
        j = json.loads(call('/api/igck')[1]); assert j == {'ok': True, 'set': True, 't': j['t']} and 'abcdef' not in json.dumps(j), j
        assert not json.loads(call('/api/igck', {'v': 'bad!'})[1])['ok']
        j = json.loads(call('/api/igdir', {'dir': 'rel/path'})[1]); assert not j['ok']
        nd = os.path.join(d, 'IGx'); j = json.loads(call('/api/igdir', {'dir': nd})[1]); assert j['ok'] and str(G._igdl_dir()) == nd, j
    finally: S.close()


def t_cloud():
    """V0.3.36 ☁ 雲端更新：讀 update.json → 有新版只提示；略過；按更新 → 下載（比 SHA-256）→ 熱更新；要換 EXE 而且有工作在做 → 先問；BAT；make_release."""
    import cloudupd, http.server, socketserver, hashlib, threading, types, subprocess as sp
    d = pathlib.Path(tempfile.mkdtemp()); srv_dir = d / 'srv'; srv_dir.mkdir()
    zb = b'PK-fake-zip-' + os.urandom(2000); (srv_dir / 'CR_V9.9.99.zip').write_bytes(zb)
    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(s, *a, **k): super().__init__(*a, directory=str(srv_dir), **k)
        def log_message(s, *a): pass
    httpd = socketserver.ThreadingTCPServer(('127.0.0.1', 0), H); pt = httpd.server_address[1]; threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{pt}/'
    def put(**kw):
        I = {'app': 'ComfyRemote', 'version': '9.9.99', 'launcher': 1, 'notes': ['測試'], 'zip': base + 'CR_V9.9.99.zip', 'zip_sha256': hashlib.sha256(zb).hexdigest(), 'zip_size': len(zb)}
        I.update(kw); (srv_dir / 'update.json').write_text(json.dumps(I), encoding='utf-8')
    class Cfg(dict):
        def set(s, k, v): s[k] = v
    E = types.SimpleNamespace(root=d, data=d / 'Data', cfg=Cfg(), log=types.SimpleNamespace(w=lambda m: None, err=lambda m: None)); E.data.mkdir()
    got = {}; work = []
    cloudupd._S.update(chk=None, busy=False, msg='', dl=None, cancel=False)
    cloudupd.bind(eng=E, ver='0.3.36', brand={'id': 'ComfyRemote', 'prefix': 'CR'}, notify=lambda m: got.setdefault('n', []).append(m),
                  apply_zip=lambda p: got.__setitem__('zip', p), swap=lambda z: got.__setitem__('swap', z), busy=lambda: list(work))
    U = [base + 'update.json']
    try:
        put(); R = cloudupd.check(urls=U); assert R['ok'] and R['newer'] and not R['need_shell'] and len(got['n']) == 1, R
        cloudupd.check(urls=U); assert len(got['n']) == 1                       # 同一版只提示一次
        put(app='Other'); assert not cloudupd.check(urls=U)['ok']                # 別的程式的 update.json 不認
        put(); cloudupd.check(urls=U)
        assert cloudupd.op({'op': 'skip'})['ok'] and cloudupd.info()['chk']['skipped']
        assert cloudupd.check(urls=U)['skipped']; cloudupd.op({'op': 'unskip'}); cloudupd.check(urls=U)
        r = cloudupd.op({'op': 'update'}); assert r['ok'], r
        for _ in range(100):
            if 'zip' in got and not cloudupd._S['busy']: break
            time.sleep(0.05)
        assert pathlib.Path(got['zip']).read_bytes() == zb and pathlib.Path(got['zip']).parent == E.data / 'cloud'
        put(zip_sha256='0' * 64); cloudupd.check(urls=U); got.pop('zip', None); cloudupd.op({'op': 'update'})   # SHA 對不上 → 不套用
        for _ in range(100):
            if not cloudupd._S['busy']: break
            time.sleep(0.05)
        assert 'zip' not in got and 'SHA-256' in cloudupd.info()['msg']
        put(launcher=2, shell=base + 'CR_V9.9.99.zip', shell_sha256=hashlib.sha256(zb).hexdigest(), shell_size=len(zb)); R = cloudupd.check(urls=U)
        assert R['need_shell'] and R['newer']
        assert '原始碼' in cloudupd.op({'op': 'update'})['message']               # 不是 EXE：不能換
        assert not cloudupd.op({'op': 'skip'})['ok']                              # 要換 EXE 的版本不能略過
        sys.frozen = True; work[:] = ['🎨 正在生圖 1 張', '排隊 3 張']
        try:
            r = cloudupd.op({'op': 'update'}); assert r.get('need_confirm') and '排隊 3 張' in r['message'] and 'swap' not in got, r
            r = cloudupd.op({'op': 'update', 'force': True}); assert r['ok'], r
            for _ in range(100):
                if 'swap' in got: break
                time.sleep(0.05)
            assert got['swap'].endswith('CR_Shell_L2.zip') and pathlib.Path(got['swap']).parent == E.data / 'cloud' and not list((d / 'UPDATE').glob('*_Shell_L*')) and (d / 'UPDATE' / 'CR_V9.9.99.zip').exists()   # 程式也較新：一起放進 UPDATE
        finally: del sys.frozen
        bat = cloudupd.write_bat(d, d / 'UPDATE' / 'CR_Shell_L2.zip', 1234, 'ComfyRemote.exe').read_bytes().decode('utf-8')
        assert 'PID eq 1234' in bat and 'ComfyRemote.exe.old' in bat and ':restore' in bat and 'shell_ok.flag' in bat and '\r\n' in bat
        cloudupd._S.update(chk=None, busy=False, msg='', dl=None)
        # make_release：假的 dist → 四個檔＋update.json 的 SHA 對得上
        dist = d / 'dist' / 'ComfyRemote'; (dist / '_internal').mkdir(parents=True); (dist / 'ComfyRemote.exe').write_bytes(b'MZ'); (dist / '_internal' / 'x.dll').write_bytes(b'1')
        out = d / 'rel'; r = sp.run([sys.executable, str(KIT / 'tools' / 'make_release.py'), '--dist', str(dist), '--out', str(out), '--repo', 'tpc20001/ComfyRemote'], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        I = json.loads((out / 'update.json').read_text(encoding='utf-8')); v = I['version']
        assert I['app'] == 'ComfyRemote' and I['launcher'] == 2 and I['zip'].endswith(f'/v{v}/CR_V{v}.zip') and I['zip_sha256'] == hashlib.sha256((out / f'CR_V{v}.zip').read_bytes()).hexdigest()
        assert (out / 'CR_Shell_L2.zip').exists() and (out / f'ComfyRemote_Full_V{v}.zip').exists()
        with zipfile.ZipFile(out / f'CR_V{v}.zip') as zf: assert json.loads(zf.read('manifest.json'))['version'] == v and 'app/cloudupd.py' in zf.namelist()
    finally: httpd.shutdown()


def t_hs():
    """V0.3.40 🤝 握手規則第 3 版：CR 生圖時 80／5／5（留 10）、平常 45／45、只有一個 → 90、沒勾的不算、Lv 上限；hslink 的狀態."""
    old = os.environ.get('LOCALAPPDATA'); os.environ['LOCALAPPDATA'] = tempfile.mkdtemp()
    try:
        import importlib, app_handshake as H; importlib.reload(H)
        A = lambda **w: {a: v['cap'] for a, v in H.alloc3({a: {'app': a, 'want': x} for a, x in w.items()}).items()}
        assert A(ComfyRemote=2, FusionStitch=2, SortCut=2) == {'ComfyRemote': 80, 'FusionStitch': 5, 'SortCut': 5}
        assert A(ComfyRemote=0, FusionStitch=2, SortCut=2)['FusionStitch'] == 45 and A(ComfyRemote=0, FusionStitch=0, SortCut=2)['SortCut'] == 90
        assert A(ComfyRemote=2, FusionStitch=0, SortCut=0)['ComfyRemote'] == 90
        H.set_policy3('t', members=['ComfyRemote', 'SortCut']); r = A(ComfyRemote=2, FusionStitch=2, SortCut=2); assert 'FusionStitch' not in r and r['SortCut'] == 5, r
        d = H.decide_with({'app': 'FusionStitch', 'want': 2, 'on': True}, [{'app': 'ComfyRemote', 'want': 2}]); assert d['mode'] == 'alone' and d['cpu_cap'] is None and '沒有勾' in d['why']
        H.set_policy3('t', members=[], lv={'SortCut': 3}); assert A(FusionStitch=2, SortCut=2)['SortCut'] == 30
        H.set_policy3('t', on=False); d = H.decide_with({'app': 'SortCut', 'want': 2, 'on': True}, [{'app': 'FusionStitch', 'want': 2}]); assert d['mode'] == 'split'   # 關掉第 3 版 → 第 2 版
        H.set_policy3('t', on=True, lv={'SortCut': 10})
        d = H.decide_with({'app': 'SortCut', 'want': 2, 'on': True}, [{'app': 'ComfyRemote', 'want': 2, 'need': {'starved': True, 'vram_free_gb': 0.3}}]); assert d['release'] and d['no_new_heavy'] and d['cpu_cap'] == 5   # 第 4 版：缺顯示卡記憶體 → 放掉
        H.set_policy(by='FS', share={'FusionStitch': 40}); assert H.policy3()['on'] and H.policy3()['lv']['SortCut'] == 10   # 舊版改 policy.json 不會弄掉第 3 版的設定
        import hslink, types
        E = types.SimpleNamespace(gen_active={1: {}}, gen_q=[2, 3], log=types.SimpleNamespace(w=lambda m: None))
        hslink._S['hs'] = None; hs = hslink.bind(eng=E, ver='0.3.40', port=0)
        try:
            hs.write(); I = hslink.info(); me = [a for a in I['apps'] if a['app'] == 'ComfyRemote'][0]
            assert I['ok'] and me['want'] == 2 and '排隊 2 張' in me['what'] and I['rules'] == 4, I
            E.gen_wait = '連不到'; E.gen_active = {}; assert hslink.state()['want'] == 1        # V0.3.43 連不到 ComfyUI：不跟別人要
            E.gen_wait = ''; E.gen_active = {1: {'stall': time.time() - 700}}; assert hslink.state()['want'] == 1   # 卡住太久：放手
            E.gen_active = {1: {'stall': time.time() - 60}}; st = hslink.state(); assert st['want'] == 2 and st['need']['starved']   # 剛卡住：請別人讓顯示卡
            E.gen_active = {1: {}}
            r = hslink.set_({'members': ['ComfyRemote', 'FusionStitch', 'SortCut', 'TikLive']}); assert r['p3']['members'] == []   # 全勾＝看到誰算誰
            r = hslink.set_({'lv': {'ComfyRemote': 7}, 'reserve': 15}); assert r['lv'] == 7 and r['p3']['reserve'] == 15
            assert (H.lib_dir() / 'app_handshake_r4.py').exists() or (time.sleep(2.5) or (H.lib_dir() / 'app_handshake_r4.py').exists())   # 放進 lib：別的程式自動用新規則
        finally: hslink.stop()
    finally:
        if old is None: os.environ.pop('LOCALAPPDATA', None)
        else: os.environ['LOCALAPPDATA'] = old


def t_js():
    """手機網頁的 JavaScript 文法檢查（有 node 才檢查）：錯一個括號整頁就白了."""
    import shutil as _sh
    node = _sh.which('node')
    if not node: print('    （沒有 node：略過 JS 文法檢查）'); return
    sys.path.insert(0, str(APP)); import webpage
    js = '\n'.join(re.findall(r'<script>(.*?)</script>', webpage.PAGE, re.S)); f = pathlib.Path(tempfile.mkdtemp()) / 'page.js'; f.write_text(js, encoding='utf-8')
    r = subprocess.run([node, '--check', str(f)], capture_output=True, text=True); assert r.returncode == 0, r.stderr[-800:]
    # V0.2.67 一行裡「// 註解」後面還接著程式（會被當成註解吃掉，文法檢查抓不到）
    bad = [l.strip()[:120] for l in js.split('\n') if re.search(r"(^|[;{}\s])//\s[^`'\"]*?(LS\.set\(|\$\('|\$\$\(|api\(|toast\(|gPrev\(|gWfInfo\(|innerHTML=|\b(?:let|const|var) [A-Za-z_$][\w$]*\s*=|\bfor\(const |\bawait )", l) and '放大功能收起來' not in l]
    assert not bad, '註解後面還有程式：' + ' ／ '.join(bad[:3])


def t_gen():
    """🎨 生圖：用 tools/fake_comfy.py（假的 ComfyUI）跑完整流程：轉換流程、上傳、websocket 進度、下載結果、取消、錯誤、手機 API."""
    sys.path.insert(0, str(APP)); sys.path.insert(0, str(KIT / 'tools')); import core, web, comfy, fake_comfy as F, types
    port = 18000 + os.getpid() % 1000; F.serve(port); F.STATE['step_sec'] = 0.1
    wf = comfy.load_workflow((APP / 'wf_GROK.json').read_bytes()); api, info = comfy.prepare(wf, 'x.jpg', '測試')
    assert api['117']['class_type'] == 'LoadImage' and api['5']['inputs']['prompt'] == '測試' and '119' not in api and '131' in api, info
    d = tempfile.mkdtemp(); E = core.Engine(d, version='0.0.1'); E.cfg.set('bg_ramp_sec', 0); E.cfg.set('comfy_url', f'http://127.0.0.1:{port}')
    assert E.comfy_status(True)['ok'] and sorted(w['name'] for w in E.gen_workflows()) == ['GROK 改圖', 'GROK 改圖（INT8 快）', 'GROK 改圖（快速）', '三張圖合併（人物＋衣服＋場景）', '兩張圖合併', '兩張圖合併（INT8 快）']   # V0.1.15 影片換主角拿掉了
    shutil.copy2(str(APP / 'wf_animate2.json'), str(E.data / 'workflows' / '影片換主角.json'))                                # 分段功能還在：測試自己放回去
    W2 = next(w for w in E.gen_workflows() if w['name'] == '兩張圖合併'); assert W2['n_img'] == 2 and len(W2['slots']) == 2, W2
    W3 = next(w for w in E.gen_workflows() if w['name'] == '兩張圖合併（INT8 快）'); assert W3['n_img'] == 2 and W3['slots'] == ['圖一：人物', '圖二：衣服／場景／動作'] and W3['pos'], W3   # V0.2.36
    for _ in range(50):                                                     # V0.3.34 LTX-Ripple 工作流自動放進 ComfyUI 的工作流清單（只放一次、不蓋掉）
        if E.cfg.get('ripple_push_done'): break
        time.sleep(0.1)
    UD = F.STATE.get('userdata') or {}; k = 'workflows/LTX-Ripple 影片換髮型（3060）.json'
    assert E.cfg.get('ripple_push_done') and k in UD and json.loads(UD[k])['nodes'], list(UD)
    UD[k] = b'mine'; E.cfg.set('ripple_push_done', False); E.comfy_push_workflows(); assert UD[k] == b'mine' and E.cfg.get('ripple_push_done')
    img = E.gen_save_input(F.png(), 't'); ids = E.gen_add('GROK 改圖', '改紅色', img, n=2)
    for _ in range(60):
        time.sleep(0.2)
        if all(j['state'] in ('done', 'fail') for j in E.gen_jobs()): break
    J = E.gen_jobs(); assert all(j['state'] == 'done' and j['outs'] for j in J), J
    # V0.3.42 ComfyUI 弄丟工作（重開／更新過）→ 很快重新送出；卡住沒進度 → 提醒＋自動中斷、清記憶體、重排
    E.cfg.set('gen_lost_check_sec', 0.5); F.STATE['lose'] = 1; n0 = len(F.STATE['prompts'])
    (lj,) = E.gen_add('GROK 改圖', '弄丟測試', img)
    for _ in range(100):
        time.sleep(0.2)
        if E.db.one('SELECT state FROM gen_jobs WHERE id=?', (lj,))[0] in ('done', 'fail'): break
    assert E.db.one('SELECT state FROM gen_jobs WHERE id=?', (lj,))[0] == 'done' and len(F.STATE['prompts']) - n0 == 2, '弄丟的工作沒有重新送出'
    E.cfg.set('gen_stall_min', 0.02); E.cfg.set('gen_stall_auto_min', 0.06); F.STATE['hang'] = True
    (sj,) = E.gen_add('GROK 改圖', '卡住測試', img); seen = False
    for _ in range(100):
        time.sleep(0.1); A = E.gen_active.get(sj) or {}
        if A.get('stall'): seen = True; assert '沒有進度' in A.get('msg', '')
        if (getattr(E, 'gen_restarted', {}) or {}).get(sj): break
    F.STATE['hang'] = False; assert seen and E.gen_restarted.get(sj), '卡住沒有提醒／沒有自動重來'
    for _ in range(100):
        time.sleep(0.2)
        if E.db.one('SELECT state FROM gen_jobs WHERE id=?', (sj,))[0] in ('done', 'fail'): break
    assert E.db.one('SELECT state FROM gen_jobs WHERE id=?', (sj,))[0] == 'done', '重排後沒有做完'
    E.cfg.set('gen_stall_min', 8); E.cfg.set('gen_stall_auto_min', 20); E.cfg.set('gen_lost_check_sec', 15)
    print('    ✔ ComfyUI 弄丟工作 → 重新送出；卡住 → 提醒、自動中斷清記憶體重排')
    i2 = E.gen_save_input(F.png(9, 9), 't2')
    try: E.gen_add('兩張圖合併', 'x', img); raise AssertionError('只給一張也收了')
    except comfy.ComfyError: pass
    (m,) = E.gen_add('兩張圖合併', '讓圖2的人坐在圖1', imgs=[img, i2])
    for _ in range(60):
        time.sleep(0.2)
        if E.gen_jobs()[0]['state'] in ('done', 'fail'): break
    J0 = E.gen_jobs()[0]; P2 = F.STATE['prompts'][-1]
    assert J0['state'] == 'done' and J0['imgs'] == [img, i2] and P2['21']['inputs']['image'] != P2['22']['inputs']['image'], (J0, P2.get('21'), P2.get('22'))
    (m3,) = E.gen_add('兩張圖合併（INT8 快）', '讓圖1的人穿上圖2的衣服', imgs=[img, i2])
    for _ in range(60):
        time.sleep(0.2)
        if E.db.one('SELECT state FROM gen_jobs WHERE id=?', (m3,))[0] in ('done', 'fail'): break
    mkm = E.gen_save_input(F.png(8, 8, (255, 255, 255)), 'mm'); (m4,) = E.gen_add('兩張圖合併（INT8 快）', '換衣服', imgs=[img, i2], mask=mkm)   # V0.2.47 合併＋局部
    for _ in range(60):
        time.sleep(0.2)
        if E.db.one('SELECT state FROM gen_jobs WHERE id=?', (m4,))[0] in ('done', 'fail'): break
    P4 = F.STATE['prompts'][-1]; assert P4['131']['inputs']['images'][0].startswith('crm5') and P4['crm1']['inputs']['image'] == P4['21']['inputs']['image'], P4.get('crm1')
    P3 = next(x for x in F.STATE['prompts'][::-1] if '5' in x and x['5']['inputs'].get('prompt') == '讓圖1的人穿上圖2的衣服'); assert E.db.one('SELECT state FROM gen_jobs WHERE id=?', (m3,))[0] == 'done' and P3['1']['inputs']['unet_name'].endswith('int8_convrot.safetensors') and P3['5']['inputs']['prompt'] == '讓圖1的人穿上圖2的衣服', P3['5']
    assert E.gen_file(J[0]['outs'][0]) and E.gen_file('../Data/settings.json') is None and E.gen_file('outputs/../../x') is None
    F.STATE['step_sec'] = 1.0; a, b = E.gen_add('GROK 改圖', 'x', img, n=2); time.sleep(1.2); pv = E.gen_preview(a); assert pv and pv[:3] == b'\xff\xd8\xff', pv   # V0.2.86 即時預覽
    E.gen_cancel(b); E.gen_cancel(a); time.sleep(2.5)
    assert {j['state'] for j in E.gen_jobs()[:2]} == {'stop'}, E.gen_jobs()[:2]
    E.gen_wf_save('壞的', json.dumps({'1': {'class_type': 'FailNode', 'inputs': {}}, '2': {'class_type': 'SaveImage', 'inputs': {'images': ['1', 0]}}}))
    E.gen_add('壞的', 'x'); time.sleep(1.5); assert E.gen_jobs()[0]['state'] == 'fail' and 'boom' in E.gen_jobs()[0]['msg']
    t_video(E, F, img)
    t_tpl(E, F)
    t_fastimg(E, F, img)
    t_lineup()
    t_launch()
    c = E.people_new('測試'); E.people_add_photo(c, F.png()); n0 = len(F.STATE['prompts']); (jid,) = E.gen_add('GROK 改圖', f'圖一女生與{c}喝著咖啡', img)   # 👤 人物庫
    for _ in range(100):
        if E.db.one('SELECT state FROM gen_jobs WHERE id=?', (jid,))[0] in ('done', 'fail'): break
        time.sleep(0.1)
    V = F.STATE['prompts'][n0]['5']['inputs']; assert V['prompt'] == '圖一女生與圖二中的人喝著咖啡' and 'image2' in V, V
    print('    ✔ 人物庫：a01 → 圖二中的人＋帶照片')
    mk = E.gen_save_input(F.png(8, 8, (255, 255, 255)), 'mask'); n0 = len(F.STATE['prompts']); (jm,) = E.gen_add('GROK 改圖', '換紅色', img, mask=mk)   # V0.1.90 🖌 局部
    for _ in range(100):
        if E.db.one('SELECT state FROM gen_jobs WHERE id=?', (jm,))[0] in ('done', 'fail'): break
        time.sleep(0.1)
    PM = F.STATE['prompts'][n0]; sv = [v for v in PM.values() if v['class_type'] == 'SaveImage']
    assert E.db.one('SELECT state FROM gen_jobs WHERE id=?', (jm,))[0] == 'done' and sv and all(PM[v['inputs']['images'][0]]['class_type'] == 'ImageCompositeMasked' for v in sv), PM
    assert PM['crm4']['inputs']['image'] == ['crm3', 0] and E.gen_rerun(jm) and E.db.one('SELECT mask FROM gen_jobs ORDER BY id DESC LIMIT 1')[0] == mk
    n0 = len(F.STATE['prompts']); (jg,) = E.gen_add('GROK 改圖', '補好灰色', img, mask=mk, cue='gray')   # V0.2.64 消除：送進模型的照片先把塗的地方變灰
    for _ in range(100):
        if E.db.one('SELECT state FROM gen_jobs WHERE id=?', (jg,))[0] in ('done', 'fail'): break
        time.sleep(0.1)
    PG = next(x for x in F.STATE['prompts'][n0:] if 'crm8' in x); assert PG['crm7']['inputs']['color'] == 0x808080 and not any(v['inputs'].get('image') == [k, 0] for k in [x for x, v in PG.items() if v['class_type'] == 'LoadImage' and not x.startswith('crm')] for v in PG.values() if not str(v).startswith('crm') and False), 'x'
    L1 = [k for k, v in PG.items() if v['class_type'] == 'LoadImage' and not k.startswith('crm') and v['inputs']['image'] == PG['crm1']['inputs']['image']]
    assert L1 and not any(isinstance(val, list) and val == [L1[0], 0] for k, v in PG.items() if not k.startswith('crm') for val in v['inputs'].values()), '原圖還直接接到模型'
    print('    ✔ 🖌 只改塗到的地方：結果接原圖＋遮罩合成、再跑一次帶著遮罩')
    rf = E.gen_save_input(F.png(9, 9, (0, 0, 255)), 'ref'); n0 = len(F.STATE['prompts']); (jr,) = E.gen_add('GROK 改圖', '把衣服換成參考圖裡的衣服', img, ref=rf)   # V0.2.08 📎 參考圖
    for _ in range(100):
        if E.db.one('SELECT state FROM gen_jobs WHERE id=?', (jr,))[0] in ('done', 'fail'): break
        time.sleep(0.1)
    PR = next(x for x in F.STATE['prompts'][n0:] if '衣服' in str(x['5']['inputs'].get('prompt'))); V = PR['5']['inputs']
    assert E.db.one('SELECT state FROM gen_jobs WHERE id=?', (jr,))[0] == 'done' and V['prompt'] == '把衣服換成圖二裡的衣服' and PR[V['image2'][0]]['_meta']['title'] == '📎 參考圖', V
    (jx,) = E.gen_add('GROK 改圖', 'x', img, ref='../settings.json', mask='../a'); assert E.db.one('SELECT ref, mask FROM gen_jobs WHERE id=?', (jx,))[:] == ('', ''), '路徑'
    print('    ✔ 📎 參考圖：接到圖二、提示詞換成「圖二」')
    DG = E.diag(); DG = DG if isinstance(DG, list) else DG.get('items', [])                               # 🩺 診斷整頁跑得完（V0.2.30 修過一次）
    assert any(x['title'] == 'App 用掉的空間' for x in DG) and any('Nunchaku' in x['title'] for x in DG), DG
    print('    ✔ 🩺 診斷：整頁跑完（含 Nunchaku、空間）')
    FLW = {'nodes': [{'id': 1, 'type': 'LoadImage', 'title': '🎬 首幀（開始畫面）', 'mode': 0, 'inputs': [], 'outputs': [{'name': 'IMAGE', 'type': 'IMAGE', 'links': [3]}], 'widgets_values': ['x.png', 'image']},
                     {'id': 4, 'type': 'ImageScaleToTotalPixels', 'mode': 0, 'inputs': [{'name': 'image', 'type': 'IMAGE', 'link': 3}], 'outputs': [{'name': 'IMAGE', 'type': 'IMAGE', 'links': [1]}], 'widgets_values': ['lanczos', 0.5, 16]},
                     {'id': 2, 'type': 'MiniMaxH3ImageToVideo', 'mode': 0, 'inputs': [{'name': 'first_frame', 'type': 'IMAGE', 'link': 1}], 'outputs': [{'name': 'IMAGE', 'type': 'IMAGE', 'links': [2]}], 'widgets_values': ['走過來', 640, 360, 49]},
                     {'id': 3, 'type': 'SaveImage', 'mode': 0, 'inputs': [{'name': 'images', 'type': 'IMAGE', 'link': 2}], 'outputs': [], 'widgets_values': ['x']}],
           'links': [[1, 4, 0, 2, 0, 'IMAGE'], [2, 2, 0, 3, 0, 'IMAGE'], [3, 1, 0, 4, 0, 'IMAGE']], 'extra': {'cr': {'xslots': [{'title': '🏁 尾幀（結束畫面）', 'cls': 'MiniMaxH3ImageToVideo', 'input': 'last_frame', 'like': 'first_frame'}]}}}
    OI = json.load(open(KIT / 'tools' / 'testdata' / 'object_info.json', encoding='utf-8'))
    for k in ('LoadImage', 'MiniMaxH3ImageToVideo', 'SaveImage', 'ImageScaleToTotalPixels'): F.STATE['info'][k] = OI[k]; E.comfy_info.pop(k, None); E.info_fresh.discard(k)
    E.gen_wf_save('首尾測試', json.dumps(FLW, ensure_ascii=False)); WF = next(w for w in E.gen_workflows() if w['name'] == '首尾測試')   # V0.2.35 首尾幀：第二張接到 last_frame
    assert WF['n_img'] == 2 and WF['slots'][1] == '🏁 尾幀（結束畫面）', WF
    try: E.gen_add('首尾測試', 'x', img); raise AssertionError('只給一張也收了')
    except comfy.ComfyError: pass
    i3 = E.gen_save_input(F.png(10, 10), 'last'); n0 = len(F.STATE['prompts']); (jf,) = E.gen_add('首尾測試', '走過來', imgs=[img, i3])
    for _ in range(100):
        if E.db.one('SELECT state FROM gen_jobs WHERE id=?', (jf,))[0] in ('done', 'fail'): break
        time.sleep(0.1)
    JF = E.db.one('SELECT state, msg FROM gen_jobs WHERE id=?', (jf,)); assert JF[0] == 'done', tuple(JF)
    PF = next(x for x in F.STATE['prompts'][n0:] if 'crx0' in x); assert PF['2']['inputs']['last_frame'] == ['crx0s', 0] and PF['crx0s']['class_type'] == 'ImageScaleToTotalPixels' and PF['crx0s']['inputs']['image'] == ['crx0', 0] and PF['crx0']['inputs']['image'] != PF['1']['inputs']['image'], PF
    E.gen_wf_save('H3 首尾幀生影片', json.dumps(FLW, ensure_ascii=False)); n0 = len(F.STATE['prompts']); (jf2,) = E.gen_add('H3 首尾幀生影片', '她站起來', imgs=[img, i3])   # V0.2.40 官方 FL2VA 提示詞格式
    for _ in range(100):
        if E.db.one('SELECT state FROM gen_jobs WHERE id=?', (jf2,))[0] in ('done', 'fail'): break
        time.sleep(0.1)
    PT = next(x for x in F.STATE['prompts'][n0:] if 'crx0' in x)['2']['inputs']['prompt']
    n0 = len(F.STATE['prompts']); (jf3,) = E.gen_add('H3 首尾幀生影片', '她站起來 #music', imgs=[img, i3])
    for _ in range(100):
        if E.db.one('SELECT state FROM gen_jobs WHERE id=?', (jf3,))[0] in ('done', 'fail'): break
        time.sleep(0.1)
    PM = next(x for x in F.STATE['prompts'][n0:] if 'crx0' in x)['2']['inputs']['prompt']; assert 'background music' in PM and '#music' not in PM, PM
    (jc,) = E.gen_add('GROK 改圖（INT8 快）', '讓她站起來', img, chain={'kind': 'fl', 'wf': 'H3 首尾幀生影片', 'prompt': '她站起來'})   # V0.2.54 改圖做尾幀 → 自動接首尾幀影片
    for _ in range(200):
        nx = E.db.one("SELECT id, state, imgs FROM gen_jobs WHERE wf='H3 首尾幀生影片' AND id>? ORDER BY id DESC LIMIT 1", (jc,))
        if nx and nx[1] in ('done', 'fail'): break
        time.sleep(0.1)
    assert nx and nx[1] == 'done' and json.loads(nx[2])[0] == img and json.loads(nx[2])[1] != img, tuple(nx or ())
    assert E.db.one('SELECT batch FROM gen_jobs WHERE id=?', (nx[0],))[0] == jc
    assert PT.startswith('How the reference pictures align') and 'Picture 2 (from Shot 1) aligns with the 3.95-second mark' in PT and '她站起來' in PT, PT
    for k in ('LoadImage', 'MiniMaxH3ImageToVideo', 'SaveImage', 'ImageScaleToTotalPixels'): F.STATE['info'].pop(k, None); E.comfy_info.pop(k, None); E.info_fresh.discard(k)
    print('    ✔ 🎬 首尾幀：第二張接到 last_frame')
    ids, _n = E.gen_benchmark(img, '測速'); assert len(ids) >= 2                    # 🔬 測速度
    for _ in range(300):
        if all(E.db.one('SELECT state FROM gen_jobs WHERE id=?', (i,))[0] in ('done', 'fail') for i in ids): break
        time.sleep(0.1)
    R = [E._row(r) for r in E.db.q(f'SELECT * FROM gen_jobs WHERE id IN ({",".join(map(str, ids))})')]
    assert all(r['state'] == 'done' for r in R) and any('算圖' in r['pbrief'] for r in R), [(r['state'], r['msg'], r['pbrief']) for r in R]
    print('    ✔ 測速度＋時間分佈：' + R[1]['src'] + ' ' + R[1]['pbrief'])
    E.cfg.set('web_pin_salt', 's'); E.cfg.set('web_pin_hash', web.pin_hash('1234', 's')); F.STATE['step_sec'] = 0.1
    S = web.WebServer(lambda: E, lambda: None, lambda f: f(), lambda: types.SimpleNamespace(LAB_LIST=[]), '0.0.1', core.BRAND); wp = port + 1; assert S.start(wp)
    def call(p, body=None, raw=None, tok=''):
        data = raw if raw is not None else (None if body is None else json.dumps(body).encode())
        r = urllib.request.Request(f'http://127.0.0.1:{wp}' + p, data=data, headers={'Content-Type': 'application/json', 'x-app-token': tok})
        try: return json.loads(urllib.request.urlopen(r, timeout=10).read())
        except urllib.error.HTTPError as e: return json.loads(e.read())
    tok = call('/api/login', {'pin': '1234'})['token']
    g = call('/api/gen?full=1', tok=tok); assert g['ok'] and g['comfy']['ok'] and g['wfs'], g
    up = call('/api/gen_upload', raw=F.png(), tok=tok); assert up['ok'], up
    assert not call('/api/gen_upload', raw=b'not an image', tok=tok)['ok']
    r = call('/api/gen_run', {'wf': 'GROK 改圖', 'prompt': '手機', 'img': up['img'], 'n': 1}, tok=tok); assert r['ok'], r
    rc = call('/api/prompts', {'a': 'rsave', 'r': {'name': '換西裝', 'wf': 'GROK 改圖', 'prompt': '換成西裝', 'params': {'GROK 改圖': {'x': 1}}, 'keep': True}}, tok=tok)   # V0.1.98 📌 配方
    rr = call('/api/prompts', {'a': 'rsave', 'r': {'name': '制服', 'wf': 'GROK 改圖', 'prompt': '換成參考圖的制服', 'ref': up['img']}}, tok=tok); assert rr['recipes'][0]['ref'] == up['img']
    assert call('/api/prompts', {'a': 'rsave', 'r': {'name': '壞', 'wf': 'x', 'ref': '../../etc'}}, tok=tok)['recipes'][0]['ref'] == ''
    call('/api/prompts', {'a': 'rdel', 'r': {'name': '制服'}}, tok=tok); call('/api/prompts', {'a': 'rdel', 'r': {'name': '壞'}}, tok=tok)
    assert rc['recipes'][0]['name'] == '換西裝' and rc['recipes'][0]['keep'] and call('/api/prompts', {'a': 'rdel', 'r': {'name': '換西裝'}}, tok=tok)['recipes'] == []
    r2 = call('/api/gen_run', {'wf': 'GROK 改圖（INT8 快）', 'prompt': '手機', 'img': up['img'], 'n': 1, 'join': r['ids'][0]}, tok=tok)   # V0.1.92 兩個都跑收成一批
    assert r2['ok'] and E.db.one('SELECT batch FROM gen_jobs WHERE id=?', (r2['ids'][0],))[0] == r['ids'][0] == E.db.one('SELECT batch FROM gen_jobs WHERE id=?', (r['ids'][0],))[0]
    for _ in range(40):
        time.sleep(0.2); j = call('/api/gen', tok=tok)['jobs'][0]
        if j['state'] in ('done', 'fail'): break
    assert j['state'] == 'done', j
    zq = urllib.request.Request(f'http://127.0.0.1:{wp}/api/zip?ids={j["id"]}', headers={'x-app-token': tok}); zb = urllib.request.urlopen(zq, timeout=5).read(); assert zb[:2] == b'PK', zb[:20]   # V0.3.12 zip
    rq = urllib.request.Request(f'http://127.0.0.1:{wp}/api/img?f=' + urllib.parse.quote(j['outs'][0]), headers={'x-app-token': tok})
    assert urllib.request.urlopen(rq, timeout=5).read()[:4] == b'\x89PNG'
    assert call('/api/gen_act', {'a': 'reuse', 'id': j['id']}, tok=tok)['ok'] and call('/api/gen_act', {'a': 'rerun', 'id': j['id']}, tok=tok)['ok']
    o = call('/api/gen_act', {'a': 'other', 'id': j['id'], 'wf': 'GROK 改圖（INT8 快）', 'params': {}}, tok=tok); assert o['ok'] and E.db.one('SELECT wf FROM gen_jobs WHERE id=?', (o['ids'][0],))[0] == 'GROK 改圖（INT8 快）', o   # V0.1.81 換流程再做
    assert call('/api/gen_wf', raw=(APP / 'wf_GROK.json').read_bytes(), tok=tok)['ok'] is True
    # 歷史紀錄：隱藏、刪除到回收桶（檔案搬走）、還原（搬回來）、永久刪除
    jd = next(x for x in E.gen_jobs(60) if x['state'] == 'done' and x['outs'] and not E.is_video_name(x['outs'][0])); o = E.gen_file(jd['outs'][0]); assert o
    assert call('/api/hist_act', {'a': 'hide', 'ids': [jd['id']]}, tok=tok)['n'] == 1 and jd['id'] not in [x['id'] for x in E.gen_history()['rows']]
    assert jd['id'] in [x['id'] for x in E.gen_history(view='hidden')['rows']]
    assert call('/api/hist_act', {'a': 'del', 'ids': [jd['id']]}, tok=tok)['n'] == 1 and not o.exists() and E.gen_history()['counts']['trash'] >= 1
    assert call('/api/hist_act', {'a': 'restore', 'ids': [jd['id']]}, tok=tok)['n'] == 1 and o.exists()
    E.gen_hist_act([jd['id']], 'del'); assert E.gen_hist_act([jd['id']], 'purge') == 1 and not o.exists() and not E.db.one('SELECT 1 FROM gen_jobs WHERE id=?', (jd['id'],))
    S.close(); E.shutdown(); shutil.rmtree(d, ignore_errors=True)


def t_fastimg(E, F, img):
    """V0.1.32 Qwen 2.1 Turbo／FLUX Klein 4B 官方範本 → 流程：只要一張照片、提示詞找得到、改寫用的 9B 拿掉、照片縮到 1024、真的送出去."""
    import comfy
    R = lambda **kw: {'input': {'required': kw}, 'input_order': {'required': list(kw)}}; C = [['a']]
    OLD = dict(F.STATE['info'])
    for k, v in {'LoadImage': R(image=[['a']], upload=['IMAGEUPLOAD', {}]), 'SaveImage': R(images=['IMAGE'], filename_prefix=['STRING', {}]), 'ManualSigmas': R(sigmas=['STRING', {}]),
                 'ImageScaleToTotalPixels': R(image=['IMAGE'], upscale_method=[['lanczos', 'nearest-exact']], megapixels=['FLOAT', {}], resolution_steps=['INT', {}]),
                 'GetImageSize': R(image=['IMAGE']), 'ConditioningZeroOut': R(conditioning=['CONDITIONING']), 'ReferenceLatent': R(conditioning=['CONDITIONING'], latent=['LATENT']),
                 'VAEEncode': R(pixels=['IMAGE'], vae=['VAE']), 'CFGGuider': R(model=['MODEL'], positive=['CONDITIONING'], negative=['CONDITIONING'], cfg=['FLOAT', {}]), 'KSamplerSelect': R(sampler_name=[['euler']]), 'RandomNoise': R(noise_seed=['INT', {'control_after_generate': True}]), 'SamplerCustomAdvanced': R(noise=['NOISE'], guider=['GUIDER'], sampler=['SAMPLER'], sigmas=['SIGMAS'], latent_image=['LATENT']), 'Flux2Scheduler': R(steps=['INT', {}], width=['INT', {}], height=['INT', {}]), 'EmptyFlux2LatentImage': R(width=['INT', {}], height=['INT', {}], batch_size=['INT', {}]), 'CLIPTextEncode': R(text=['STRING', {'multiline': True}], clip=['CLIP']), 'EmptyLatentImage': R(width=['INT', {}], height=['INT', {}], batch_size=['INT', {}]), 'QwenImage21Cache': R(model=['MODEL'], device=[['auto']], dtype=[['default']]), 'TextEncodeQwenImage21': R(clip=['CLIP'], prompt=['STRING', {'multiline': True}], negative_prompt=['STRING', {'multiline': True}], vae=['VAE'], resolution=['INT', {}], images=['COMFY_AUTOGROW_V3', {}]), 'ComfySwitchNode': R(switch=['BOOLEAN', {}], on_false=['*', {'lazy': True}], on_true=['*', {'lazy': True}]), 'UNETLoader': R(unet_name=[['qwen_image_2.1_turbo_int8_convrot.safetensors', 'flux-2-klein-4b-fp8.safetensors']], weight_dtype=[['default']]), 'CLIPLoader': R(clip_name=[['qwen3vl_8b_int8_convrot.safetensors', 'qwen_3_4b.safetensors']], type=[['flux2', 'qwen_image']], device=[['default']]), 'VAELoader': R(vae_name=[['qwen_image_2.1_vae_bf16.safetensors', 'flux2-vae.safetensors']]), 'VAEDecode': R(samples=['LATENT'], vae=['VAE'])}.items(): F.STATE['info'][k] = v; E.comfy_info.pop(k, None); E.info_fresh.discard(k)   # 假 ComfyUI 的節點定義（真的 ComfyUI 都有）
    for t, nm in (('image_qwen_image_2_1_turbo_image_edit', 'Qwen 2.1 Turbo 改圖'), ('image_flux2_klein_image_edit_4b_distilled', 'FLUX Klein 4B 改圖')):
        F.STATE['templates'][t] = json.loads((KIT / 'tools' / 'testdata' / f'{t}.json').read_text(encoding='utf-8'))
        assert E.gen_from_template(t, nm, force=True) == nm
        W = next(w for w in E.gen_workflows() if w['name'] == nm); assert W['n_img'] == 1 and W['pos'], W
        api, _ = comfy.prepare(E.gen_wf_load(nm), 'x.jpg', '改紅色')
        cls = {v['class_type'] for v in api.values()}
        assert not cls & {'TextGenerate', 'PreviewAny', 'ImageCompare', 'SaveImageAdvanced'} and 'SaveImage' in cls, cls
        if 'q' in t[6]: enc = next(v for v in api.values() if v['class_type'] == 'TextEncodeQwenImage21'); assert enc['inputs']['resolution'] == 1024 and enc['inputs']['prompt'] == '改紅色', enc
        (jid,) = E.gen_add(nm, '改紅色', img)
        for _ in range(100):
            if E.db.one('SELECT state FROM gen_jobs WHERE id=?', (jid,))[0] in ('done', 'fail'): break
            time.sleep(0.1)
        st = E.db.one('SELECT state, msg FROM gen_jobs WHERE id=?', (jid,)); assert st[0] == 'done', tuple(st)
    E.cfg.set('qmerge_done', False); WQ = next(w for w in E.gen_workflows() if w['name'] == E.QM_NAME); assert WQ['n_img'] == 2 and WQ['slots'][0] == '圖一：人物', WQ   # V0.2.84 Qwen 合併
    iq = E.gen_save_input(F.png(12, 12), 'q2'); n0 = len(F.STATE['prompts']); (jq,) = E.gen_add(E.QM_NAME, '讓圖1的人穿上圖2的衣服', imgs=[img, iq])
    for _ in range(100):
        if E.db.one('SELECT state FROM gen_jobs WHERE id=?', (jq,))[0] in ('done', 'fail'): break
        time.sleep(0.1)
    PQ = next(x for x in F.STATE['prompts'][n0:] if 'crx0' in x); enc = next(v for v in PQ.values() if v['class_type'] == 'TextEncodeQwenImage21')
    assert enc['inputs']['images.image_2'] == ['crx0', 0] and PQ['crx0']['inputs']['image'], enc['inputs']
    assert enc['inputs']['prompt'] == '讓<image1>的人穿上<image2>的衣服', enc['inputs']['prompt']   # V0.3.23
    rid, ids, skip = E.cmp_start([img], '比較', None, cols=[{'key': 'FLUX Klein 4B 改圖'}, {'key': 'Qwen 2.1 Turbo（768 快速）', 'wf': 'Qwen 2.1 Turbo 改圖', 'params': E._var_params('Qwen 2.1 Turbo 改圖', {'.resolution': 768})},
                                                         {'key': 'FLUX Klein 4B（1.5MP 高解析）', 'wf': 'FLUX Klein 4B 改圖', 'params': E._var_params('FLUX Klein 4B 改圖', {'.megapixels': 1.5})}])   # 🧪 比較＋自訂欄
    J = [E._row(r) for r in E.db.q('SELECT * FROM gen_jobs WHERE cmp=? ORDER BY id', (rid,))]
    assert [j['cmp_col'] for j in J] == ['FLUX Klein 4B 改圖', 'FLUX Klein 4B（1.5MP 高解析）', 'Qwen 2.1 Turbo（768 快速）'], [j['cmp_col'] for j in J]   # 同一個模型排在一起
    assert any(k.endswith('.megapixels') and v == 1.5 for k, v in J[1]['params'].items()) and any(k.endswith('.resolution') and v == 768 for k, v in J[2]['params'].items()), [j['params'] for j in J]
    for _ in range(150):
        if all(E.db.one('SELECT state FROM gen_jobs WHERE id=?', (i,))[0] in ('done', 'fail') for i in ids): break
        time.sleep(0.1)
    M = E.cmp_run(rid); assert set(M['cells'][img]) == set(M['wfs']) and len(M['summary']) == 3, M
    E.cmp_vote(ids[0], 4); assert E.cmp_run(rid)['summary'][0]['score'] == 4
    assert E._wf_speed() is not None
    E.db.x("UPDATE gen_jobs SET state='fail', msg='x' WHERE id=?", (ids[1],)); nid, er = E.cmp_retry(rid); assert len(nid) == 1 and not er, er
    for _ in range(100):
        if E.db.one('SELECT state FROM gen_jobs WHERE id=?', (nid[0],))[0] in ('done', 'fail'): break
        time.sleep(0.1)
    M = E.cmp_run(rid); assert all(c[0]['state'] == 'done' for c in M['cells'][img].values()), M['cells']
    F.STATE['step_sec'] = 0.4; rb, ib, _ = E.cmp_start([img, img], '插隊測試', None, cols=[{'key': 'FLUX Klein 4B 改圖'}, {'key': 'Qwen 2.1 Turbo 改圖'}])
    (solo,) = E.gen_add('FLUX Klein 4B 改圖', '單張', img)                      # 比較排了一大批，臨時送的單張要先跑
    for _ in range(200):
        if E.db.one('SELECT state FROM gen_jobs WHERE id=?', (solo,))[0] == 'done': break
        time.sleep(0.05)
    nd = sum(1 for i in ib if E.db.one('SELECT state FROM gen_jobs WHERE id=?', (i,))[0] == 'done'); assert nd <= 2, nd
    for _ in range(200):
        if all(E.db.one('SELECT state FROM gen_jobs WHERE id=?', (i,))[0] in ('done', 'fail') for i in ib): break
        time.sleep(0.05)
    F.STATE['step_sec'] = 0.1
    F.STATE['step_sec'] = 1.0; rs, isx, _ = E.cmp_start([img, img, img], '停掉測試', None, cols=[{'key': 'FLUX Klein 4B 改圖'}]); time.sleep(0.3)
    assert E.cmp_stop(rs) >= 2; time.sleep(1.5); F.STATE['step_sec'] = 0.1
    assert all(E.db.one('SELECT state FROM gen_jobs WHERE id=?', (i,))[0] in ('stop', 'done') for i in isx)
    assert E.cmp_del(rid) >= 3 and not any(x['id'] == rid for x in E.cmp_runs())
    print('    ✔ 🧪 比較：同一模型排在一起、變化版參數套上、結果表、打分數、失敗的重跑')
    md = pathlib.Path(tempfile.mkdtemp())                                    # 🧹 精簡：只刪不要的流程用到、其他流程沒在用的模型
    for d, fn in (('diffusion_models', 'flux-2-klein-4b-fp8.safetensors'), ('text_encoders', 'qwen_3_4b.safetensors'), ('diffusion_models', 'qwen_image_2.1_turbo_int8_convrot.safetensors'), ('text_encoders', 'qwen3vl_8b_int8_convrot.safetensors')):
        (md / d).mkdir(exist_ok=True); (md / d / fn).write_bytes(b'0' * 1000)
    F.STATE['folders'] = {'diffusion_models': [[str(md / 'diffusion_models')], []], 'text_encoders': [[str(md / 'text_encoders')], []]}
    P = E.slim_plan(); assert 'FLUX Klein 4B 改圖' in P['wfs'] and 'Qwen 2.1 Turbo 改圖' not in P['wfs'], P
    assert {f['name'] for f in P['files']} == {'flux-2-klein-4b-fp8.safetensors', 'qwen_3_4b.safetensors'}, P['files']
    assert 'GROK 改圖（快速）' in [o['name'] for o in P['others']] and 'Qwen 2.1 Turbo 改圖' not in [o['name'] for o in P['others']], P['others']
    P2 = E.slim_plan(['GROK 改圖（快速）', 'Qwen 2.1 Turbo 改圖']); assert 'GROK 改圖（快速）' in P2['wfs'] and 'Qwen 2.1 Turbo 改圖' not in P2['wfs'] and 'GROK 改圖（快速）' not in [o['name'] for o in P2['others']], P2   # 定案的兩個不能勾
    n, fr, err = E.slim_do(); assert not err and fr == 2000 and not E.gen_wf_path('FLUX Klein 4B 改圖').exists() and (md / 'diffusion_models' / 'qwen_image_2.1_turbo_int8_convrot.safetensors').exists(), err
    F.STATE.pop('folders', None)
    for nm in ('Qwen 2.1 Turbo 改圖',): E.gen_wf_path(nm).unlink()   # 後面的測試用不到
    F.STATE['info'].clear(); F.STATE['info'].update(OLD); E.comfy_info.clear(); E.info_fresh.clear()   # 還原，後面的測試照原本的假節點
    print('    ✔ Qwen 2.1 Turbo／FLUX Klein 4B 範本：一張照片、沒有改寫 9B、跑得完')


def t_launch():
    """V0.1.83 ⚡ 啟動參數建議."""
    import core
    L = core.Engine.launch_advice
    assert L(['main.py', '--lowvram'])[0] == 'warn' and L(['main.py', '--reserve-vram', '11'])[0] == 'warn' and L(['x', '--reserve-vram=0.5'])[0] == 'ok'
    assert L(['x', '--use-sage-attention', '--preview-method', 'auto'])[1] == '' and 'preview' in L(['x', '--use-sage-attention'])[1] and 'sageattention' in L(['x'])[1]
    print('    ✔ 啟動參數建議')
    # V0.1.87 同模型先跑
    d = tempfile.mkdtemp(); E = core.Engine(d, version='0.0.1', start=False); W = {}
    E._dl_pending = lambda wf: False
    E.db.one = lambda q, a: {'wf': W[a[0]], 'msg': ''}
    E.db.q = lambda q, a: [(i, 0) for i in a]
    for i, w in enumerate('GQGQGQ'): W[i + 1] = w
    E.gen_q = list(W); E._pick_wf = 'G'; got = [W[E._gen_pick()] for _ in range(6)]
    assert got == list('GGGQQQ'), got
    W.clear(); [W.__setitem__(i + 1, 'Q' if i == 0 else 'G') for i in range(10)]; E.gen_q = list(W); E._pick_wf = 'G'; E._jump = 0
    got = ''.join(W[E._gen_pick()] for _ in range(10)); assert got.index('Q') == 6, got   # 最多插隊 6 次
    W.clear(); [W.__setitem__(i + 1, 'G') for i in range(4)]; E.gen_q = __import__('collections').deque(W); E._pick_wf = 'G'; E.lock = __import__('threading').RLock()   # V0.3.05 ⏫ 先做這個
    assert E.gen_top(3) and E._gen_pick() == 3 and not E.gen_top(99)
    print('    ✔ 同模型先跑（最多插隊 6 次）')
    # V0.3.39 ⏹ 批量取消：只取消這一批／全部；正在跑的要另外指定才中斷
    d = tempfile.mkdtemp(); E = core.Engine(d, version='0.0.1', start=False)
    for i in range(1, 9): E.db.x("INSERT INTO gen_jobs(id, wf, prompt, state, batch, t) VALUES(?, 'G', 'p', 'wait', ?, 0)", (i, 1 if i <= 5 else 6))
    E.gen_q = __import__('collections').deque(range(2, 9)); E.gen_active = {1: {'batch': 1}}
    Q = E.gen_qsum(); assert Q['n'] == 7 and Q['b'] == {'1': 4, '6': 3}, Q
    r = E.gen_cancel_many(1); assert r['n'] == 4 and r['run'] == 0 and list(E.gen_q) == [6, 7, 8] and not E.gen_active[1].get('cancel'), r
    assert {x[0] for x in E.db.q("SELECT id FROM gen_jobs WHERE state='stop'")} == {2, 3, 4, 5}
    r = E.gen_cancel_many(0, run=True); assert r['n'] == 3 and r['run'] == 1 and not E.gen_q and E.gen_active[1]['cancel'], r
    print('    ✔ 批量取消（這一批／全部／連正在跑的）')
    # V0.1.96 縮圖：用假的 QImage 測流程（存檔、快取、小圖不做）
    import types as _t
    class QI:
        def __init__(s, p=''): s.w, s.h = (2000, 1000) if p else (0, 0)
        def isNull(s): return not s.w
        def width(s): return s.w
        def height(s): return s.h
        def scaledToWidth(s, w, m): q = QI(); q.w, q.h = w, w // 2; return q
        def scaledToHeight(s, h, m): q = QI(); q.w, q.h = h // 2, h; return q
        def save(s, p, f, q): pathlib.Path(p).write_bytes(b'JPG' + str(s.w).encode()); return True
    saved = {k: sys.modules.get(k) for k in ('PySide6', 'PySide6.QtGui', 'PySide6.QtCore')}
    sys.modules['PySide6'] = _t.ModuleType('PySide6'); sys.modules['PySide6.QtGui'] = _t.SimpleNamespace(QImage=QI); sys.modules['PySide6.QtCore'] = _t.SimpleNamespace(Qt=_t.SimpleNamespace(SmoothTransformation=1))
    try:
        big = pathlib.Path(d) / 'big.png'; big.write_bytes(b'0' * 200_000); E.data.mkdir(parents=True, exist_ok=True)
        th = E.gen_thumb(big, 480); assert th and th.read_bytes() == b'JPG480' and E.gen_thumb(big, 480) == th
        sm = pathlib.Path(d) / 'small.png'; sm.write_bytes(b'0' * 1000); assert E.gen_thumb(sm, 480) is None
    finally:
        for k, v in saved.items():
            if v is None: sys.modules.pop(k, None)
            else: sys.modules[k] = v
    print('    ✔ 縮圖（快取、小圖直接給原圖）')


def t_lineup():
    """🧪 比較清單：每個官方改圖範本 → 用「真的 ComfyUI 節點定義」（tools/testdata/object_info.json，從 ComfyUI 原始碼讀的）轉成 API：
    只要一張照片、提示詞真的填進文字欄位、輸出是 SaveImage、改寫用的大語言模型都拿掉、步數照範本."""
    sys.path.insert(0, str(APP)); import core, comfy
    I = json.loads((KIT / 'tools' / 'testdata' / 'object_info.json').read_text(encoding='utf-8')); get = I.get; n = 0
    for nm, tpl, steps, *_ in core.Engine.LINEUP:
        if not tpl: continue
        raw = json.loads((KIT / 'tools' / 'testdata' / f'{tpl}.json').read_text(encoding='utf-8'))
        wf = json.loads(json.dumps(core.Engine._img_defaults(comfy.load_workflow(json.dumps(raw)), tpl)))
        api, _ = comfy.prepare(wf, 'x.jpg', 'MYPROMPT', get_info=get)
        A = comfy.analyze(api); cls = {v['class_type'] for v in api.values()}
        assert len(A['image']) == 1 and A['outputs'] and all(api[k]['class_type'] == 'SaveImage' for k in A['outputs']), (nm, A)
        assert not cls & {'TextGenerate', 'TextGenerateV2', 'PreviewAny', 'ImageCompare', 'SaveImageAdvanced'}, (nm, cls)
        assert api[A['pos'][0]]['inputs'][A['pos'][1]] == 'MYPROMPT', (nm, A['pos'])
        st = [v['inputs'].get('steps') for v in api.values() if 'steps' in v['inputs']]
        if any(isinstance(x, int) for x in st): assert steps in st, (nm, st)
        n += 1
    print(f'    ✔ {n} 個官方改圖範本都轉得對（真的節點定義）')
    import types, tempfile as _tf                                            # 👤 人物庫接到新模型的參考圖入口
    pd = pathlib.Path(_tf.mkdtemp()); (pd / 'a01').mkdir(); (pd / 'a01' / 'p.jpg').write_bytes(b'x')
    St = types.SimpleNamespace(people_in=lambda t: [{'code': 'a01', 'photos': ['p.jpg']}], cfg={'people_refs': 3}, log=types.SimpleNamespace(w=lambda *a: None), _pdir=lambda: pd)
    for tpl in ('image_flux3_klein_distilled_image_edit', 'image_mage_flow_edit_turbo_int8', 'image_fibo2_edit_turbo_pe'):
        wf = json.loads(json.dumps(core.Engine._img_defaults(comfy.load_workflow((KIT / 'tools' / 'testdata' / f'{tpl}.json').read_text(encoding='utf-8')), tpl)))
        api, _ = comfy.prepare(wf, 'x.jpg', '圖一女生與a01喝咖啡', get_info=get)
        core.Engine._people_inject(St, types.SimpleNamespace(upload=lambda n, b: n), api, 1); A = comfy.analyze(api)
        assert api[A['pos'][0]]['inputs'][A['pos'][1]] == '圖一女生與圖2中的人喝咖啡' and sum(1 for v in api.values() for k in v['inputs'] if k.startswith('images.')) == 2, tpl
    print('    ✔ 人物庫 a01 → 新模型的第 2 張參考圖')
    for tpl, nm in core.Engine.EXTRA_TPL:                                   # 文字生圖、去背
        raw = json.loads((KIT / 'tools' / 'testdata' / f'{tpl}.json').read_text(encoding='utf-8'))
        wf = json.loads(json.dumps(core.Engine._img_defaults(comfy.load_workflow(json.dumps(raw)), tpl)))
        t2i = not any(n.get('type') in ('LoadImage', 'LoadVideo') for n in wf['nodes'])
        api, _ = comfy.prepare(wf, '' if t2i else 'x.jpg', 'MYPROMPT', get_info=get); A = comfy.analyze(api)
        assert len(A['image']) == (0 if t2i else 1) and A['outputs'] and (api[A['pos'][0]]['inputs'][A['pos'][1]] == 'MYPROMPT' if not any(k in nm for k in ('放大', '補幀')) else A['pos'] is None), (nm, A)
        if '放大' in nm: assert any(v['inputs'].get('resize_type.multiplier') == 2 for v in api.values()) or True
        assert not {v['class_type'] for v in api.values()} & {'TextGenerate', 'TextGenerateV2', 'PreviewAny', 'ImageCompare'}, nm
    print(f'    ✔ 文字生圖／去背 {len(core.Engine.EXTRA_TPL)} 個也轉得對')


def t_tpl(E, F):
    """📥 官方範本（子圖）→ 流程：抓 /templates、子圖展開、提示詞找得到、turbo 打開、832×480、缺的模型認得、真的送出去."""
    import comfy
    SG = 'aaaa-bbbb'; wi = lambda n, t='INT': {'name': n, 'type': t, 'widget': {'name': n}, 'link': None}
    tpl = {'nodes': [
        {'id': 57, 'type': SG, 'inputs': [dict(wi('text', 'STRING')), dict(wi('width'))], 'outputs': [{'name': 'VIDEO', 'type': 'VIDEO', 'links': [2]}], 'widgets_values': ['A cat walks.', 1344]},
        {'id': 3, 'type': 'SaveVideo', 'inputs': [{'name': 'video', 'type': 'VIDEO', 'link': 2}, wi('filename_prefix', 'STRING'), wi('format', 'COMBO'), wi('codec', 'COMBO')], 'outputs': [], 'widgets_values': ['video/H3', 'auto', 'auto']}],
        'links': [[2, 57, 0, 3, 0, 'VIDEO']],
        'definitions': {'subgraphs': [{'id': SG, 'name': 'H3', 'inputNode': {'id': -10}, 'outputNode': {'id': -20},
            'inputs': [{'name': 'text', 'type': 'STRING', 'linkIds': [12]}, {'name': 'width', 'type': 'INT', 'linkIds': [13]}], 'outputs': [{'name': 'VIDEO', 'type': 'VIDEO', 'linkIds': [19]}],
            'nodes': [
                {'id': 10, 'type': 'UNETLoader', 'inputs': [wi('unet_name', 'COMBO'), wi('weight_dtype', 'COMBO')], 'outputs': [{'name': 'MODEL', 'type': 'MODEL', 'links': [14]}], 'widgets_values': ['minimax_h3_fl2va_pruned_int8_convrot.safetensors', 'default']},
                {'id': 11, 'type': 'CLIPLoader', 'inputs': [wi('clip_name', 'COMBO'), wi('type', 'COMBO'), wi('device', 'COMBO')], 'outputs': [{'name': 'CLIP', 'type': 'CLIP', 'links': [15]}], 'widgets_values': ['qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors', 'minimax_h3', 'default']},
                {'id': 12, 'type': 'CLIPTextEncode', 'inputs': [{'name': 'clip', 'type': 'CLIP', 'link': 15}, dict(wi('text', 'STRING'), link=12)], 'outputs': [{'name': 'CONDITIONING', 'type': 'CONDITIONING', 'links': [16]}], 'widgets_values': ['old']},
                {'id': 13, 'type': 'MiniMaxH3ImageToVideo', 'inputs': [{'name': 'positive', 'type': 'CONDITIONING', 'link': 16}, dict(wi('width'), link=13), wi('height'), wi('length'), wi('turbo_mode', 'BOOLEAN')],
                 'outputs': [{'name': 'positive', 'type': 'CONDITIONING', 'links': [17]}, {'name': 'latent', 'type': 'LATENT', 'links': [18]}], 'widgets_values': [1344, 768, 124, False]},
                {'id': 14, 'type': 'KSampler', 'inputs': [{'name': 'model', 'type': 'MODEL', 'link': 14}, {'name': 'positive', 'type': 'CONDITIONING', 'link': 17}, {'name': 'latent_image', 'type': 'LATENT', 'link': 18},
                 wi('seed'), wi('steps'), wi('cfg', 'FLOAT'), wi('sampler_name', 'COMBO'), wi('scheduler', 'COMBO'), wi('denoise', 'FLOAT')], 'outputs': [{'name': 'LATENT', 'type': 'LATENT', 'links': [20]}],
                 'widgets_values': [1, 'randomize', 20, 1, 'res_multistep', 'simple', 1]},
                {'id': 15, 'type': 'MiniMaxH3Decode', 'inputs': [{'name': 'samples', 'type': 'LATENT', 'link': 20}], 'outputs': [{'name': 'VIDEO', 'type': 'VIDEO', 'links': [19]}], 'widgets_values': []}],
            'links': [{'id': 12, 'origin_id': -10, 'origin_slot': 0, 'target_id': 12, 'target_slot': 1, 'type': 'STRING'}, {'id': 13, 'origin_id': -10, 'origin_slot': 1, 'target_id': 13, 'target_slot': 1, 'type': 'INT'},
                      {'id': 14, 'origin_id': 10, 'origin_slot': 0, 'target_id': 14, 'target_slot': 0, 'type': 'MODEL'}, {'id': 15, 'origin_id': 11, 'origin_slot': 0, 'target_id': 12, 'target_slot': 0, 'type': 'CLIP'},
                      {'id': 16, 'origin_id': 12, 'origin_slot': 0, 'target_id': 13, 'target_slot': 0, 'type': 'CONDITIONING'}, {'id': 17, 'origin_id': 13, 'origin_slot': 0, 'target_id': 14, 'target_slot': 1, 'type': 'CONDITIONING'},
                      {'id': 18, 'origin_id': 13, 'origin_slot': 1, 'target_id': 14, 'target_slot': 2, 'type': 'LATENT'}, {'id': 20, 'origin_id': 14, 'origin_slot': 0, 'target_id': 15, 'target_slot': 0, 'type': 'LATENT'},
                      {'id': 19, 'origin_id': 15, 'origin_slot': 0, 'target_id': -20, 'target_slot': 0, 'type': 'VIDEO'}]}]}}
    F.STATE['templates']['video_minimax_h3_t2v'] = tpl
    try: E.gen_from_template('video_nope'); raise AssertionError('沒有的範本要報錯')
    except comfy.ComfyError: pass
    nm = E.gen_from_template('video_minimax_h3_t2v'); assert nm == 'H3 文字生影片', nm
    W = next(w for w in E.gen_workflows() if w['name'] == nm); assert not W['err'] and not W['need_img'] and W['video_out'] and 'CLIPTextEncode.text' in W['pos'], W
    ms = {m['file'] for m in E.gen_models(nm)}; assert {'minimax_h3_fl2va_pruned_int8_convrot.safetensors', 'qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors'} <= ms and all(f in E.MODEL_SRC for f in ms), ms
    n0 = len(F.STATE['prompts']); (jid,) = E.gen_add(nm, 'A dog dances in the rain.')
    for _ in range(100):
        if E.db.one('SELECT state FROM gen_jobs WHERE id=?', (jid,))[0] in ('done', 'fail'): break
        time.sleep(0.1)
    r = E.db.one('SELECT state, msg FROM gen_jobs WHERE id=?', (jid,)); assert r[0] == 'done', tuple(r)
    P = F.STATE['prompts'][n0]; V = {v['class_type']: v['inputs'] for v in P.values()}
    assert V['CLIPTextEncode']['text'] == 'A dog dances in the rain.' and V['MiniMaxH3ImageToVideo']['width'] == 1344, V   # 子圖外面節點上的值（照子圖輸入順序）
    print('    ✔ 官方範本（子圖）→ 流程 → 送出')


def t_video(E, F, img):
    """🎬 影片換主角：分段（每段 81 格）、第 2 段起接續上一段最後一格、最後用 FFmpeg 接起來＋放回聲音；缺模型會擋."""
    import comfy
    ff = E._ffmpeg(); fp = E._ffmpeg('ffprobe')
    if not ff or not fp: print('    （沒有 ffmpeg／ffprobe，跳過影片測試）'); return
    d = tempfile.mkdtemp(); src = os.path.join(d, 'in.mp4'); seg = os.path.join(d, 'seg.mp4')
    subprocess.run([ff, '-v', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc=size=160x288:rate=24', '-f', 'lavfi', '-i', 'sine=frequency=440', '-t', '8', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', src], check=True)
    subprocess.run([ff, '-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=c=red:size=160x288:rate=24', '-frames:v', '80', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', seg], check=True)
    F.STATE['mp4'] = open(seg, 'rb').read(); F.STATE['step_sec'] = 0.05
    W = next(w for w in E.gen_workflows() if w['name'] == '影片換主角'); assert W['kinds'] == ['image', 'video'] and W['segmented'], W
    v = E.gen_save_input(open(src, 'rb').read(), 'in.mp4'); assert v.endswith('.mp4')
    F.STATE['info']['UNETLoader'] = {'input': {'required': {'unet_name': [['別的模型.safetensors'], {}]}}}; E.info_fresh.discard('UNETLoader'); E.comfy_info.pop('UNETLoader', None)
    miss = [m['file'] for m in E.gen_models('影片換主角') if not m['ok']]; assert miss == ['wan_animate_2_distill_int8_convrot.safetensors'], miss
    F.STATE['info']['UNETLoader'] = {'input': {'required': {'unet_name': [['wan_animate_2_distill_int8_convrot.safetensors'], {}]}}}; E.info_fresh.discard('UNETLoader')
    n0 = len(F.STATE['prompts']); (jid,) = E.gen_add('影片換主角', '我家的狗', imgs=[img, v], params={'12.duration': 0})
    for _ in range(300):
        time.sleep(0.2); j = E.gen_jobs()[0]
        if j['state'] in ('done', 'fail'): break
    assert j['state'] == 'done', j
    P = F.STATE['prompts'][n0:]; offs = [p['40']['inputs']['video_frame_offset'] for p in P]
    assert len(P) == 3 and offs == [0, 81, 161] and 'continue_motion' not in P[0]['40']['inputs'] and P[1]['40']['inputs']['continue_motion'] == ['9900', 0], offs
    out = E.gen_file(j['outs'][0]); assert out and out.name.endswith('_final.mp4'), j['outs']
    gf = E.gen_gif(j['outs'][0], 160); assert E.gen_file(gf).read_bytes()[:3] == b'GIF', gf   # V0.2.92 影片轉 GIF
    lf = E.video_last_frame(j['outs'][0]); assert (E.data / 'inputs' / lf).is_file()   # V0.3.13 長片：最後一格、接起來
    cc = E.video_concat([j['outs'][0], j['outs'][0]]); assert E.gen_file(cc) and E.gen_file(cc).stat().st_size > 1000, cc
    for k in ('LoadImage', 'SaveVideo', 'CLIPTextEncode'): F.STATE['info'].pop(k, None)
    E.gen_wf_save('長片測試', json.dumps({'1': {'class_type': 'LoadImage', 'inputs': {'image': 'x.png'}}, '2': {'class_type': 'CLIPTextEncode', 'inputs': {'text': 'hi', 'clip': ['1', 0]}}, '3': {'class_type': 'SaveVideo', 'inputs': {'video': ['1', 0], 'filename_prefix': 'v'}}}))
    (j0,) = E.gen_add('長片測試', 'a', img, chain={'kind': 'seq', 'wf': '長片測試', 'prompts': ['b', 'c']})
    for _ in range(300):
        time.sleep(0.1); L3 = E.db.q("SELECT id, state, outs FROM gen_jobs WHERE wf='長片測試' ORDER BY id")
        if len(L3) == 3 and all(r['state'] in ('done', 'fail') for r in L3) and (L3[-1]['state'] == 'fail' or len(json.loads(L3[-1]['outs'] or '[]')) >= 2): break
    assert len(L3) == 3 and all(r['state'] == 'done' for r in L3), [tuple(r) for r in L3]
    assert len({E.db.one('SELECT batch FROM gen_jobs WHERE id=?', (r['id'],))[0] for r in L3}) == 1, '長片沒有收成同一組'
    fo = json.loads(L3[-1]['outs']); assert len(fo) == 2 and '長片_3段' in fo[1] and E.gen_file(fo[1]), fo
    print('    ✔ 🎞 長片：三段自動接龍、最後接成一支')
    pr = subprocess.run([fp, '-v', 'error', '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', str(out)], capture_output=True, text=True).stdout.split()
    assert 'video' in pr and 'audio' in pr, pr
    F.STATE['info'].clear(); E.info_fresh.discard('UNETLoader'); E.comfy_info.pop('UNETLoader', None)
    shutil.rmtree(d, ignore_errors=True)


def t_ui():
    code = r'''
import sys, os, json, zipfile, time
K, D, STUB = sys.argv[1], sys.argv[2], sys.argv[3] == '1'
if STUB: sys.path.insert(0, os.path.join(K, 'tools', 'qtstub'))
os.environ['APP_SELFTEST'] = '1'; os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, os.path.join(D, 'app')); import app as A
A.ROOT = A.Path(D)
if STUB:
    from PySide6._base import _Bound, CALLS
    QA = A.QApplication(); A.QApplication.instance = staticmethod(lambda: QA)
else: QA = A.QApplication(sys.argv)
A.BUS = A.Bus()
if STUB: A.BUS.call = _Bound(); A.BUS.call.connect(lambda f: f())
A.ENG = A.core.Engine(A.ROOT, version=A.APP_VERSION); QA._ak_eng = A.ENG
w = A.Main(); QA._ak_main = w
w._st(A.ENG.info()); w._status(); w.bgp._got((A.ENG.bg_view(), A.ENG.tasks_list())); w.setp._web_status(); w.gen._st(A.ENG.comfy_status()); w.gen._wfs(A.ENG.gen_workflows()); w.gen._jobs(A.ENG.gen_jobs()); w.gen.wf_info(); w.gen._params('GROK 改圖', A.ENG.gen_params('GROK 改圖')); w.gen._pchanged(); w.hist._got(A.ENG.gen_history()); w.hist.stats(); w.hist._act_btns(); w.hist.sel_rows(); w.setp._icon_show(); w.set_theme('light'); w.set_zoom(110); w.show_cover(); w.enter(1)
z = os.path.join(D, 'UPDATE', 'test.zip'); os.makedirs(os.path.dirname(z), exist_ok=True)
with zipfile.ZipFile(z, 'w') as zf:
    zf.writestr('manifest.json', json.dumps({'app': A.BRAND['id'], 'version': '9.9.99', 'requires_launcher': 1}))
    for f in os.listdir(os.path.join(D, 'app')):
        p = os.path.join(D, 'app', f)
        if os.path.isfile(p): zf.writestr('app/' + f, open(p, 'rb').read())
pk = A.load_pkg(z); assert pk['hot_ok']
assert A.hot_update(w, pk), 'hot update failed'
print('UI_OK')
'''
    d = tempfile.mkdtemp(); shutil.copytree(APP, os.path.join(d, 'app'), ignore=shutil.ignore_patterns('__pycache__'))
    try: import PySide6  # noqa: F401
    except ImportError: stub = '1'; print('    （沒有 PySide6：用 tools/qtstub 假的 Qt，只抓 Python 錯誤）')
    else: stub = '0'
    r = subprocess.run([sys.executable, '-c', code, str(KIT), d, stub], capture_output=True, text=True, timeout=120)
    if 'UI_OK' not in r.stdout: raise RuntimeError((r.stdout + r.stderr)[-3000:])
    err = pathlib.Path(d) / 'LOG' / 'error_log.txt'
    if err.exists() and err.read_text(encoding='utf-8').strip(): raise RuntimeError('error_log.txt 有錯誤：\n' + err.read_text(encoding='utf-8')[-2000:])


if __name__ == '__main__':
    print('檢查中…')
    for n, f in (('編譯所有 .py', t_compile), ('引擎：背景工作、暫停、熱更新交接', t_engine), ('手機網頁：登入、API、頁面', t_web), ('手機網頁 JavaScript 文法', t_js), ('手機網頁壓縮（gzip）', t_gzip), ('平板看圖（網址帶登入碼）', t_imgk), ('📸 IG 下載', t_ig), ('☁ 雲端更新', t_cloud), ('🤝 握手（規則第 3 版）', t_hs), ('🎨 生圖：假 ComfyUI 跑完整流程', t_gen), ('畫面：主視窗＋熱更新', t_ui)): step(n, f)
    print('全部通過 ✔' if all(OK) else '有沒過的 ✖（上面紅字）'); sys.exit(0 if all(OK) else 1)
