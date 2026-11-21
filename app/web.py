"""📱 手機網頁：用手機（或別台電腦的瀏覽器）透過 Tailscale 遙控這個程式。

和你的其他程式錯開、不會互相蓋掉（重要規則，換程式也照這樣）：
  - 本機只聽 127.0.0.1:<本機埠>（brand.json 的 web_port，每個程式要不一樣）。
  - Tailscale 用「自己的」HTTPS 埠＝本機埠 + 1000：tailscale serve --bg --https=<本機埠+1000> http://127.0.0.1:<本機埠>
  - 只設定／關掉自己這個埠：從來不碰 443（TikLive 用的根目錄）、從來不跑 tailscale serve reset（會清掉別的程式的設定）。
  - 手機上每個程式是不同的埠＋不同的 manifest id（brand.json 的 phone_id）→ 可以各自安裝成 App、同時開。
伺服器是自己寫的小型 HTTP（只用 socket／threading，啟動器 EXE 裡一定有），每個連線一條背景執行緒；
碰到畫面的動作一律交給畫面執行緒（ui）。新功能的 API：寫一個 api_<名字>(self, req) 方法就好（登入檢查已經做好）。
"""
import os, re, json, time, socket, threading, hashlib, struct, zlib, subprocess, shutil, traceback, urllib.parse
from pathlib import Path

MAX_BODY = 640 * 1024 * 1024                 # 影片（手機錄的 mp4）可能幾百 MB
NO_WINDOW = 0x08000000 if os.name == 'nt' else 0
HERE = Path(__file__).resolve().parent


def https_port(local_port):
    """規則：Tailscale HTTPS 埠＝本機埠 + 1000."""
    return int(local_port) + 1000


def pin_hash(pin, salt): return hashlib.sha256((salt + '|' + str(pin)).encode('utf-8')).hexdigest()


def pin_ok_format(pin): return bool(re.fullmatch(r'[^\s]{4,20}', str(pin or '')))


def rand_hex(n=16): return os.urandom(n).hex()


def same(a, b):
    a = str(a).encode(); b = str(b).encode()
    if len(a) != len(b): return False
    r = 0
    for x, y in zip(a, b): r |= x ^ y
    return r == 0


def make_icon_png(size, accent=(229, 30, 99)):
    """沒有圖檔時自己畫一個 PNG 圖示（不用 PIL）：深色圓角方塊＋彩色圓點。Android 安裝 App 需要 192／512 的 PNG."""
    S = int(size); rad = S * 0.22; rows = []
    for y in range(S):
        row = bytearray(b'\x00')
        for x in range(S):
            dx = max(rad - x, 0, x - (S - 1 - rad)); dy = max(rad - y, 0, y - (S - 1 - rad))
            if dx * dx + dy * dy > rad * rad: row += b'\x0b\x0f\x14\xff'; continue
            cx, cy = x - S / 2, y - S / 2; d2 = cx * cx + cy * cy
            if d2 <= (S * 0.2) ** 2: row += bytes((*accent, 255))
            elif d2 <= (S * 0.3) ** 2 and d2 >= (S * 0.26) ** 2: row += b'\xe8\xec\xf2\xff'
            else: t = (x + y) / (2 * S); row += bytes((int(16 + 20 * t), int(22 + 30 * t), int(34 + 50 * t), 255))
        rows.append(bytes(row))
    raw = zlib.compress(b''.join(rows), 9)
    def chunk(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', S, S, 8, 6, 0, 0, 0)) + chunk(b'IDAT', raw) + chunk(b'IEND', b'')


# ------------------------------------------------------------------ Tailscale（只動自己的埠）
def tailscale_exe():
    exe = shutil.which('tailscale') or ''
    for c in (os.path.expandvars(r'%ProgramFiles%\Tailscale\tailscale.exe'), r'C:\Program Files\Tailscale\tailscale.exe', r'C:\Program Files (x86)\Tailscale\tailscale.exe'):
        if not exe and c and os.path.isfile(c): exe = c
    return exe


def tailscale_run(args, timeout=10):
    exe = tailscale_exe()
    if not exe: return -1, '找不到 tailscale（這台電腦還沒裝 Tailscale？）'
    if args and args[0] == 'serve' and 'reset' in args: return -1, '不准 tailscale serve reset（會清掉別的程式的設定）'
    try:
        p = subprocess.run([exe] + list(args), capture_output=True, timeout=timeout, creationflags=NO_WINDOW, stdin=subprocess.DEVNULL)
        return p.returncode, (p.stdout + p.stderr).decode('utf-8', 'replace')
    except subprocess.TimeoutExpired: return -9, '逾時（Tailscale 沒回應；如果要登入，請看電腦右下角的 Tailscale）'
    except Exception as ex: return -1, f'{type(ex).__name__}: {ex}'


def tailscale_info(local_port):
    """{'installed', 'dns'（電腦名稱.xxx.ts.net）, 'ip', 'serving'（自己的 HTTPS 埠有沒有設好）, 'url', 'others'（別的程式用的埠，只顯示）}."""
    out = {'installed': bool(tailscale_exe()), 'dns': '', 'ip': '', 'serving': False, 'url': '', 'others': []}
    if not out['installed']: return out
    rc, s = tailscale_run(['status', '--json'], 6)
    if rc == 0 and '{' in s:
        try:
            j = json.loads(s[s.index('{'):]); me = j.get('Self') or {}
            out['dns'] = str(me.get('DNSName') or '').rstrip('.'); ips = me.get('TailscaleIPs') or []; out['ip'] = next((i for i in ips if '.' in i), ips[0] if ips else '')
        except Exception: pass
    hp = https_port(local_port)
    rc, s = tailscale_run(['serve', 'status', '--json'], 6)
    if rc == 0 and '{' in s:
        try:
            j = json.loads(s[s.index('{'):]); tcp = j.get('TCP') or {}
            out['serving'] = str(hp) in {str(k) for k in tcp.keys()}; out['others'] = sorted(str(k) for k in tcp.keys() if str(k) != str(hp))
        except Exception: pass
    if out['dns']: out['url'] = f'https://{out["dns"]}:{hp}/'
    return out


def tailscale_serve_on(local_port):
    return tailscale_run(['serve', '--bg', f'--https={https_port(local_port)}', f'http://127.0.0.1:{int(local_port)}'], 40)


def tailscale_serve_off(local_port):
    return tailscale_run(['serve', f'--https={https_port(local_port)}', 'off'], 20)


# ------------------------------------------------------------------ HTTP
MEDIA_K = ('/api/img', '/api/zip', '/api/igfile', '/api/igthumb')   # 只有看圖、下載這兩個能用網址裡的 k 登入（<img>/<video>/下載連結帶不了標頭）

class Req:
    def __init__(self, method, path, query, headers, body, peer):
        self.method = method; self.path = path; self.query = query; self.headers = headers; self.body = body; self.peer = peer

    def q(self, k, d=''):
        v = self.query.get(k); return v[0] if v else d

    def json(self):
        try: return json.loads(self.body.decode('utf-8') or '{}')
        except Exception: return {}

    def cookie(self, k):
        for part in (self.headers.get('cookie') or '').split(';'):
            a, _, b = part.strip().partition('=')
            if a == k: return urllib.parse.unquote(b)
        return ''

    def client(self):
        if self.peer in ('127.0.0.1', '::1'): return (self.headers.get('x-forwarded-for') or self.peer or '').split(',')[0].strip()
        return self.peer or ''


class Resp:
    def __init__(self, code=200, body=b'', ctype='application/json; charset=utf-8', headers=None):
        self.code = code; self.body = body; self.ctype = ctype; self.headers = headers or {}


def jresp(obj, code=200, headers=None):
    return Resp(code, json.dumps(obj, ensure_ascii=False, default=str).encode('utf-8'), headers=headers)


REASON = {200: 'OK', 206: 'Partial Content', 416: 'Range Not Satisfiable', 400: 'Bad Request', 401: 'Unauthorized', 403: 'Forbidden', 404: 'Not Found', 413: 'Payload Too Large', 429: 'Too Many Requests', 500: 'Internal Server Error'}


class WebServer:
    """get_eng()／get_win()：目前的引擎和主視窗（熱更新後自動是新的）；ui(fn)：交給畫面執行緒；app_mod()：目前的 app 模組."""

    def __init__(self, get_eng, get_win, ui, app_mod, version, brand):
        self.E = get_eng; self.W = get_win; self.ui = ui; self.app_mod = app_mod; self.version = version; self.brand = dict(brand)
        self.sock = None; self.th = None; self.stop = False; self.port = 0; self.bind = ''; self.err = ''; self.fails = {}; self.n_conn = 0; self.lock = threading.Lock(); self._icons = {}

    def start(self, port, lan=False):
        self.close(); self.port = int(port); self.bind = '0.0.0.0' if lan else '127.0.0.1'; self.err = ''
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if os.name == 'nt' and hasattr(socket, 'SO_EXCLUSIVEADDRUSE'): s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            else: s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.bind, self.port)); s.listen(32); s.settimeout(1.0)
        except OSError as ex:
            self.err = f'埠 {self.port} 不能用（{ex.strerror or ex}）：可能被別的程式佔用了，請在設定換一個（例如 {self.port + 10}）'
            self._log('⚠ 手機網頁開不起來：' + self.err); return False
        self.sock = s; self.stop = False
        self.th = threading.Thread(target=self._loop, name='Web', daemon=True); self.th.start()
        self._log(f'手機網頁開了：{self.bind}:{self.port}（Tailscale HTTPS 用 {https_port(self.port)}）'); return True

    def close(self):
        self.stop = True; s = self.sock; self.sock = None
        if s is not None:
            try: s.close()
            except Exception: pass
            self._log(f'手機網頁關了（埠 {self.port}）')
        if self.th is not None and self.th is not threading.current_thread():
            try: self.th.join(2.5)
            except Exception: pass
        self.th = None

    @property
    def running(self): return self.sock is not None and not self.stop

    def _log(self, m):
        try: self.E().log.w(m)
        except Exception: pass

    def _loop(self):
        s = self.sock
        while not self.stop and s is not None:
            try: c, addr = s.accept()
            except socket.timeout: continue
            except OSError: break
            if self.n_conn > 48: c.close(); continue
            threading.Thread(target=self._conn, args=(c, addr), name='WebConn', daemon=True).start()

    def _conn(self, c, addr):
        with self.lock: self.n_conn += 1
        try:
            c.settimeout(30); f = c.makefile('rb')
            line = f.readline(65536).decode('latin-1').strip()
            if not line: return
            parts = line.split(' ')
            if len(parts) < 2: return
            method, target = parts[0].upper(), parts[1]; H = {}; t_dead = time.time() + 20; nh = 0
            while True:
                h = f.readline(65536); nh += 1
                if nh > 100 or time.time() > t_dead: return
                if not h or h in (b'\r\n', b'\n'): break
                k, _, v = h.decode('latin-1').partition(':'); H[k.strip().lower()] = v.strip()
            try: n = int(H.get('content-length') or 0)
            except ValueError: n = -1
            if n < 0: self._send(c, Resp(400, b'bad length', 'text/plain')); return
            if n > MAX_BODY: self._send(c, Resp(413, b'too big', 'text/plain')); return
            if n > (1 << 20):                                                   # 還沒登入的不收大的內容
                tk = H.get('x-app-token') or ''
                if not tk:
                    for part in (H.get('cookie') or '').split(';'):
                        a_, _, b_ = part.strip().partition('=')
                        if a_ == 'app_t': tk = urllib.parse.unquote(b_)
                if not (tk and any(same(tk, x) for x in (self.E().cfg.get('web_tokens') or []))): self._send(c, Resp(413, b'too big', 'text/plain')); return
            body = f.read(n) if n else b''
            u = urllib.parse.urlsplit(target); req = Req(method, urllib.parse.unquote(u.path), urllib.parse.parse_qs(u.query), H, body, addr[0] if addr else '')
            try: r = self.route(req)
            except Exception as ex:
                self._log(f'手機網頁錯誤：{method} {req.path}\n{traceback.format_exc()}'); r = jresp({'ok': False, 'message': f'{type(ex).__name__}: {ex}'}, 500)
            self._send(c, r, method == 'HEAD')
        except Exception: pass
        finally:
            try: c.close()
            except Exception: pass
            with self.lock: self.n_conn -= 1

    def _send(self, c, r, head=False):
        H = {'Content-Type': r.ctype, 'Connection': 'close', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer', 'Cache-Control': 'no-store'}
        H.update(r.headers); H['Content-Length'] = str(len(r.body))
        c.sendall((f'HTTP/1.1 {r.code} {REASON.get(r.code, "OK")}\r\n' + ''.join(f'{k}: {v}\r\n' for k, v in H.items()) + '\r\n').encode('latin-1', 'replace'))
        if not head: c.sendall(r.body)

    # ---- 登入（PIN：錯 5 次鎖 5 分鐘；登入後給 token，存在 cookie）
    def authed(self, req):
        toks = self.E().cfg.get('web_tokens') or []
        c = [req.headers.get('x-app-token'), req.cookie('app_t')]                 # V0.3.33 每一個都試：瀏覽器留著「舊的、失效的」cookie 時，不會擋掉有效的登入碼
        if req.method in ('GET', 'HEAD') and req.path in MEDIA_K: c.append(req.q('k'))   # V0.3.31 圖片網址帶 k＝登入碼
        return any(t and any(same(t, x) for x in toks) for t in c)

    def login(self, req):
        E = self.E(); d = req.json(); cl = req.client(); n, t0 = self.fails.get(cl, (0, 0))
        if n >= 5 and time.time() - t0 < 300: return jresp({'ok': False, 'message': '錯太多次，請 5 分鐘後再試'}, 429)
        h = E.cfg.get('web_pin_hash'); salt = E.cfg.get('web_pin_salt') or ''
        if not h: return jresp({'ok': False, 'message': '電腦上還沒設定 PIN：到 設定 → 📱 手機網頁 設一個'}, 403)
        if not same(pin_hash(str(d.get('pin', '')), salt), h):
            self.fails[cl] = (n + 1, time.time()); self._log(f'手機網頁：PIN 錯誤（{cl}，第 {n + 1} 次）')
            return jresp({'ok': False, 'message': 'PIN 不對' + (f'（再錯 {4 - n} 次會鎖 5 分鐘）' if n >= 1 else '')}, 401)
        self.fails.pop(cl, None); tok = rand_hex(24); E.cfg.set('web_tokens', list(E.cfg.get('web_tokens') or [])[-19:] + [tok])
        self._log(f'手機網頁：登入成功（{cl}）')
        return jresp({'ok': True, 'token': tok}, headers={'Set-Cookie': f'app_t={tok}; Path=/; Max-Age=31536000; HttpOnly; SameSite=Strict'})

    # ---- 靜態（頁面、PWA）
    def icon(self, size):
        try:
            mt = (self.E().data / 'icon_512.png').stat().st_mtime
            if mt != getattr(self, '_icon_mt', None): self._icon_mt = mt; self._icons = {}
        except Exception: pass
        if size not in self._icons:
            fn = {512: 'icon_512.png', 192: 'icon_192.png', 'mask': 'icon_512.png'}.get(size)
            try: self._icons[size] = next((d / fn).read_bytes() for d in (self.E().data, HERE) if (d / fn).is_file())   # 設定裡換的圖示（Data）優先
            except Exception:
                a = self.brand.get('accent', '#e51e63').lstrip('#'); rgb = tuple(int(a[i:i + 2], 16) for i in (0, 2, 4)) if len(a) == 6 else (229, 30, 99)
                self._icons[size] = make_icon_png(size if isinstance(size, int) else 512, rgb)
        return Resp(200, self._icons[size], 'image/png', {'Cache-Control': 'public, max-age=86400'})

    def manifest(self):
        B = self.brand
        m = {'name': B.get('title'), 'short_name': B.get('name'), 'start_url': './', 'scope': './', 'display': 'standalone', 'orientation': 'any',
             'background_color': '#0b0f14', 'theme_color': '#0b0f14', 'id': B.get('phone_id') or (B.get('id', 'app').lower() + '-phone'), 'lang': 'zh-TW',
             'icons': [{'src': 'icon-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'}, {'src': 'icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any'},
                       {'src': 'icon-mask.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'}]}
        return Resp(200, json.dumps(m, ensure_ascii=False).encode('utf-8'), 'application/manifest+json; charset=utf-8')

    def sw(self):
        js = ("const V='%s-%s';self.addEventListener('install',e=>self.skipWaiting());"
              "self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(K=>Promise.all(K.filter(k=>k!==V).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));"
              "self.addEventListener('fetch',e=>{const u=new URL(e.request.url);if(e.request.method!=='GET'||u.pathname.startsWith('/api/'))return;"
              "e.respondWith(fetch(e.request).then(r=>{if(r.ok&&(u.pathname==='/'||u.pathname.endsWith('.png'))){const c=r.clone();caches.open(V).then(x=>x.put(e.request,c));}return r;})"
              ".catch(()=>caches.match(e.request).then(r=>r||new Response('<h3 style=\"font-family:sans-serif;color:#ccc;background:#0b0f14\">連不到電腦（Tailscale 有開嗎？電腦開著嗎？）</h3>',{headers:{'Content-Type':'text/html; charset=utf-8'}}))));});"
              ) % (self.brand.get('id', 'app'), self.version)
        return Resp(200, js.encode('utf-8'), 'application/javascript; charset=utf-8', {'Service-Worker-Allowed': '/'})

    def page(self):
        import webpage
        html = webpage.PAGE.replace('__VER__', str(self.version)).replace('__NAME__', str(self.brand.get('name'))).replace('__TITLE__', str(self.brand.get('title'))).replace('__ACCENT__', str(self.brand.get('accent', '#e51e63'))).replace('__PREFIX__', str(self.brand.get('prefix', 'CR')))
        return Resp(200, html.encode('utf-8'), 'text/html; charset=utf-8')

    def route(self, req):
        p = req.path
        if p in ('/', '/index.html'):
            r = self.page()
            if 'gzip' in (req.headers.get('accept-encoding') or ''):        # V0.2.99 頁面壓縮：300KB → 約 70KB，手機用 Tailscale 打開快很多
                import gzip as _gz
                k = (len(r.body), hash(r.body)); c = getattr(self, '_gzc', None)
                if not c or c[0] != k: c = (k, _gz.compress(r.body, 6)); self._gzc = c
                r = Resp(200, c[1], r.ctype, {'Content-Encoding': 'gzip', 'Vary': 'Accept-Encoding'})
            return r
        if p == '/manifest.webmanifest': return self.manifest()
        if p == '/sw.js': return self.sw()
        if p in ('/icon-192.png', '/icon-512.png', '/favicon.ico'): return self.icon(512 if '512' in p else 192)
        if p in ('/icon-mask.png', '/apple-touch-icon.png'): return self.icon('mask')
        if p == '/api/hello':
            a = self.authed(req); h = req.headers.get('x-app-token') or ''; hd = {}
            if a and h and req.cookie('app_t') != h and any(same(h, x) for x in (self.E().cfg.get('web_tokens') or [])):   # V0.3.33 舊 cookie 換成現在有效的登入碼
                hd = {'Set-Cookie': f'app_t={h}; Path=/; Max-Age=31536000; HttpOnly; SameSite=Strict'}
            return jresp({'ok': True, 'ver': self.version, 'name': self.brand.get('name'), 'authed': a, 'pin_set': bool(self.E().cfg.get('web_pin_hash'))}, headers=hd)
        if p == '/api/login' and req.method == 'POST': return self.login(req)
        if not p.startswith('/api/'): return Resp(404, b'not found', 'text/plain')
        if not self.authed(req): return jresp({'ok': False, 'message': '要先輸入 PIN', 'login': True}, 401)
        name = p[5:].split('/')[0]; fn = getattr(self, 'api_' + name.replace('-', '_'), None)
        if fn is None: return jresp({'ok': False, 'message': f'沒有這個功能：{name}'}, 404)
        return fn(req)

    def _ui(self, fn):
        try: self.ui(fn)
        except Exception: pass

    # ================================================================ API（新功能照這樣加：def api_xxx(self, req): ... return jresp({...})）
    def api_state(self, req):
        E = self.E(); I = E.info()
        return jresp({'ok': True, 'ver': self.version, 'time': time.strftime('%H:%M:%S'), 'info': I, 'ctl': E.bg_view(),
                      'tasks': [{k: t.get(k) for k in ('title', 'state', 'pct', 'msg', 't0')} for t in E.tasks_list()[-15:]][::-1]})

    def api_perf(self, req):
        return jresp(dict(self.E().perf.view(), ok=True, time=time.strftime('%H:%M:%S')))

    def api_bgctl(self, req):
        """後台總控制：a＝pause／resume／stop／up／down／all_pause／all_resume／guard（on、cpu_max、ramp_sec）／demo（排示範工作）."""
        E = self.E(); d = req.json() if req.method == 'POST' else {}; a = d.get('a'); k = d.get('k')
        if a in ('pause', 'resume', 'stop', 'up', 'down') and k not in {x[0] for x in E.BG_KINDS}: return jresp({'ok': False, 'message': '不認得的項目'}, 400)
        if a: E.log.w(f'📱 手機：後台 {a} {k or ""}')
        if a == 'guard':
            if 'on' in d: E.cfg.set('cpu_guard', bool(d['on']))
            if d.get('cpu_max'): E.cfg.set('cpu_max', max(50, min(100, int(d['cpu_max']))))
            if d.get('ramp_sec') is not None: E.cfg.set('bg_ramp_sec', max(0, min(300, int(d['ramp_sec']))))
        elif a == 'pause': E.bg_set_pause(k, True, '手機')
        elif a == 'resume': E.bg_set_pause(k, False, '手機')
        elif a == 'stop': E.bg_stop_now(k)
        elif a in ('up', 'down'): E.bg_move(k, -1 if a == 'up' else 1)
        elif a == 'all_pause': E.bg_all(True)
        elif a == 'all_resume': E.bg_all(False)
        elif a == 'demo': E.demo_add(int(d.get('n') or 5), float(d.get('sec') or 8))
        self._ui(lambda: getattr(self.W(), 'bgp', None) and self.W().bgp.refresh())
        return jresp({'ok': True, 'ctl': E.bg_view()})

    SETTABLE = {'ui_theme': str, 'cpu_guard': bool, 'cpu_max': int, 'bg_ramp_sec': int, 'demo_n': int, 'close_to_tray': bool, 'auto_restart': bool,
                'comfy_url': str, 'gen_mp': float, 'gen_timeout_min': int, 'keep_awake': bool, 'hf_token': str, 'gen_free_idle': bool, 'gen_auto_retry': bool}   # 手機可以改的設定（新功能的設定加在這裡）

    def api_settings(self, req):
        E = self.E()
        if req.method == 'POST':
            d = req.json(); ch = []
            for k, v in d.items():
                tp = self.SETTABLE.get(k)
                if tp is None: continue
                try: E.cfg.set(k, tp(v)); ch.append(k)
                except Exception: pass
            self._ui(lambda: getattr(self.W(), 'setp', None) and self.W().setp.load())
            return jresp({'ok': True, 'changed': ch})
        cfg = {k: E.cfg.get(k) for k in self.SETTABLE}
        if cfg.get('hf_token'): cfg['hf_token'] = '••••' + str(cfg['hf_token'])[-4:]          # 金鑰不整個傳回手機
        return jresp({'ok': True, 'cfg': cfg, 'lab': dict(E.cfg.get('lab') or {}), 'labs': getattr(self.app_mod(), 'LAB_LIST', [])})

    def api_lab(self, req):
        E = self.E(); d = req.json(); k = str(d.get('k') or '')
        if k not in {x[0] for x in getattr(self.app_mod(), 'LAB_LIST', [])}: return jresp({'ok': False, 'message': '不認得的實驗功能'}, 400)
        L = dict(E.cfg.get('lab') or {}); L[k] = bool(d.get('on')); E.cfg.set('lab', L)
        self._ui(lambda: getattr(self.W(), 'lab', None) and self.W().lab.load()); return jresp({'ok': True, 'lab': L})

    def api_log(self, req):
        E = self.E(); f = req.q('f', 'app_log.txt')
        if f not in ('app_log.txt', 'error_log.txt', 'ui_freeze_log.txt', 'update_log.txt'): f = 'app_log.txt'
        try:
            p = E.log.d / f; sz = p.stat().st_size
            with open(p, 'rb') as fh: fh.seek(max(0, sz - 60000)); txt = fh.read().decode('utf-8', 'replace')
        except Exception: txt = ''
        return jresp({'ok': True, 'f': f, 'text': txt[-60000:]})

    def api_update(self, req):
        """手機上傳更新包（<前綴>_V….zip）→ 放進 UPDATE → 在電腦上熱更新（程式不用關）."""
        E = self.E(); W = self.W(); M = self.app_mod()
        if req.method != 'POST' or not req.body: return jresp({'ok': False, 'message': '沒有收到檔案'})
        nm = re.sub(r'[^\w.\-]', '_', req.q('name') or 'update.zip')
        if not nm.lower().endswith('.zip'): nm += '.zip'
        d = E.root / 'UPDATE'; d.mkdir(exist_ok=True); p = d / nm; p.write_bytes(req.body)
        try: pkg = M.load_pkg(p)
        except Exception as ex:
            try: p.unlink()
            except Exception: pass
            return jresp({'ok': False, 'message': f'這個更新包不能用：{ex}'})
        E.log.w(f'📱 手機：上傳更新包 {nm}（V{pkg["version"]}）')
        if not pkg.get('hot_ok'): return jresp({'ok': True, 'message': f'已放進 UPDATE（V{pkg["version"]}），這版要重開程式才會套用'})
        def go():
            try: W.upd.pkg = pkg; M.hot_update(W, pkg)
            except Exception: E.log.err('手機熱更新')
        self._ui(lambda: M.QTimer.singleShot(400, go))
        return jresp({'ok': True, 'message': f'V{pkg["version"]} 熱更新中…（大約 5～10 秒，之後手機會自動重新整理）', 'ver': pkg['version']})

    # ---- 📦 更新包（TK 一樣的流程）：選檔 → 上傳 → 先看這版改了什麼 → 按「確定更新」才更新；⏪ 退回前面的版本
    def _pending(self): d = self.E().root / 'UPDATE' / '_pending'; d.mkdir(parents=True, exist_ok=True); return d

    def api_update_check(self, req):
        E = self.E(); M = self.app_mod()
        if req.method != 'POST' or not req.body: return jresp({'ok': False, 'message': '沒有收到檔案'})
        nm = re.sub(r'[^\w.\-]', '_', req.q('name') or 'update.zip')
        if not nm.lower().endswith('.zip'): nm += '.zip'
        for o in self._pending().glob('*.zip'):
            try: o.unlink()
            except Exception: pass
        p = self._pending() / nm; p.write_bytes(req.body)
        try: pkg = M.load_pkg(p)
        except Exception as ex:
            try: p.unlink()
            except Exception: pass
            return jresp({'ok': False, 'message': f'這個更新包不能用：{ex}'})
        cur = getattr(M, 'APP_VERSION', self.version); d, c = M.vkey(pkg['version']), M.vkey(cur)
        E.log.w(f'📱 手機：上傳更新包 {nm}（V{pkg["version"]}），等確認')
        return jresp({'ok': True, 'name': nm, 'version': pkg['version'], 'current': cur, 'notes': pkg['notes'], 'hot_ok': pkg['hot_ok'],
                      'way': 'newer' if d > c else ('same' if d == c else 'older')})

    def _hot(self, pkg, what):
        E = self.E(); W = self.W(); M = self.app_mod()
        def go():
            try: W.upd.pkg = pkg; M.hot_update(W, pkg)
            except Exception: E.log.err('手機：' + what)
        self._ui(lambda: M.QTimer.singleShot(400, go))

    def api_update_apply(self, req):
        E = self.E(); M = self.app_mod(); nm = re.sub(r'[^\w.\-]', '_', str(req.json().get('name') or ''))
        p = self._pending() / nm
        if not nm or not p.is_file(): return jresp({'ok': False, 'message': '找不到剛剛上傳的更新包，請重新選一次'})
        try: pkg = M.load_pkg(p)
        except Exception as ex: return jresp({'ok': False, 'message': f'這個更新包不能用：{ex}'})
        if not pkg.get('hot_ok'):
            try: os.replace(str(p), str(E.root / 'UPDATE' / nm))
            except Exception: pass
            return jresp({'ok': True, 'message': f'V{pkg["version"]} 放進 UPDATE 了，這版要重開程式才會套用', 'restart': True})
        E.log.w(f'📱 手機：確定更新到 V{pkg["version"]}'); self._hot(pkg, '熱更新')
        return jresp({'ok': True, 'message': f'V{pkg["version"]} 更新中…（大約 5～10 秒，之後這頁會自動重新整理）', 'ver': pkg['version']})

    def api_update_rollback(self, req):
        E = self.E(); M = self.app_mod()
        L = M.list_backups() if hasattr(M, 'list_backups') else []
        if req.method != 'POST': return jresp({'ok': True, 'current': getattr(M, 'APP_VERSION', self.version), 'items': [{k: x[k] for k in ('version', 'time', 'notes', 'older')} for x in L]})
        try: x = L[int(req.json().get('i'))]
        except Exception: return jresp({'ok': False, 'message': '清單變了，請重新整理'})
        try: pkg = M.backup_pkg(x['path'])
        except Exception as ex: return jresp({'ok': False, 'message': f'這個備份不能用：{ex}'})
        E.log.w(f'📱 手機：退回 V{pkg["version"]}'); self._hot(pkg, '退回版本')
        return jresp({'ok': True, 'message': f'退回 V{pkg["version"]} 中…（大約 5～10 秒，之後這頁會自動重新整理）', 'ver': pkg['version']})

    def api_changelog(self, req):
        try: C = json.loads((HERE / 'CHANGELOG.json').read_text(encoding='utf-8'))[:20]
        except Exception: C = []
        return jresp({'ok': True, 'log': C})

    def api_logout(self, req):
        E = self.E(); t = req.headers.get('x-app-token') or req.cookie('app_t')
        E.cfg.set('web_tokens', [x for x in (E.cfg.get('web_tokens') or []) if not same(x, t)])
        return jresp({'ok': True}, headers={'Set-Cookie': 'app_t=; Path=/; Max-Age=0'})

    # ================================================================ 🎨 生圖
    def _gen_refresh(self):
        self._ui(lambda: getattr(self.W(), 'gen', None) and self.W().gen.refresh(True))

    def _gen_err(self, ex):
        import comfy
        if isinstance(ex, comfy.ComfyError): return jresp({'ok': False, 'message': str(ex)})
        self.E().log.err('手機：生圖'); return jresp({'ok': False, 'message': f'{type(ex).__name__}: {ex}'})

    def api_gen(self, req):
        """狀態：ComfyUI 連線、工作清單；full=1 再加流程清單和設定."""
        E = self.E(); out = {'ok': True, 'comfy': E.comfy_status(), 'jobs': E.gen_jobs(int(req.q('n', '20') or 20)), 'info': E.info(), 'paused': E.bg_hold('gen'),
                             'now': time.time(), 'wait': getattr(E, 'gen_wait', ''), 'qsum': E.gen_qsum()}
        if req.q('full'): out.update(wfs=E.gen_workflows(), wf=E.cfg.get('gen_wf'), mp=E.cfg.get('gen_mp'), spd={k: round(v[0]) for k, v in E._wf_speed().items()}, stars={r[0]: [round(r[1], 1), r[2]] for r in E.db.q('SELECT wf, AVG(vote), COUNT(*) FROM gen_jobs WHERE vote>0 AND deleted=0 GROUP BY wf')}, lineup={n: {'steps': st, 'lic': lic, 'note': note} for n, _t, st, lic, note in E.LINEUP})
        return jresp(out)

    def api_gen_upload(self, req):
        if req.method != 'POST' or not req.body: return jresp({'ok': False, 'message': '沒有收到照片'})
        try: return jresp({'ok': True, 'img': self.E().gen_save_input(req.body, '手機' + (f'，影片第 {req.q("tag")[1:].lstrip("0") or 0} 格' if req.q('tag') else ''), req.q('tag') or '')})
        except Exception as ex: return self._gen_err(ex)

    def api_gen_run(self, req):
        E = self.E(); d = req.json()
        try:
            import itertools
            P = d.get('params') if isinstance(d.get('params'), dict) else None; ids = []
            slots = [[str(x) for x in (sl or []) if x] for sl in (d.get('slots') or []) if isinstance(sl, list)]
            if slots and all(slots):                                            # 好幾格照片（圖一、圖二…）：每格可以多張 → 每種組合各排一次
                combos = list(itertools.product(*slots))[:200]
                MK = d.get('masks') if isinstance(d.get('masks'), dict) else {}            # V0.2.47 合併也可以只改圖一的某一塊（例如只換衣服那塊，臉和背景一個像素都不動）
                for c in combos: ids += E.gen_add(d.get('wf'), d.get('prompt', ''), c[0], d.get('neg', ''), int(d.get('n') or 1), '手機', params=P, imgs=list(c), mask=str(MK.get(c[0]) or ''))
                imgs = combos
            else:
                imgs = [str(x) for x in d.get('imgs') or [] if x][:200] or [d.get('img', '')]       # 批量：每張照片各排一次，提示詞一樣
                MK = d.get('masks') if isinstance(d.get('masks'), dict) else {}            # V0.1.90 🖌 每張照片自己的遮罩
                for im in imgs: ids += E.gen_add(d.get('wf'), d.get('prompt', ''), im, d.get('neg', ''), int(d.get('n') or 1), '手機', params=P, mask=str(MK.get(im) or ''), cue=str(d.get('cue') or ''), ref=str(d.get('ref') or ''), chain=d.get('chain') if isinstance(d.get('chain'), dict) else None)
            try: jn = int(d.get('join') or 0)
            except (TypeError, ValueError): jn = 0
            E.gen_set_batch(ids + ([jn] if jn > 0 else []))                    # V0.1.92 「🔁 兩個都跑」：兩個流程的工作收成同一批（歷史紀錄放在一起）
            if len(imgs) > 1: E.log.w(f'📱 手機：批量 {len(imgs)} 組照片 → {len(ids)} 個工作')
            self._gen_refresh(); return jresp({'ok': True, 'ids': ids, 'message': f'排好了 {len(ids)} 張' + (f'（{len(imgs)} 張照片）' if len(imgs) > 1 else '')})
        except Exception as ex: return self._gen_err(ex)

    def api_cmp(self, req):
        """🧪 比較。GET ?a=rows（每個流程）／runs（以前的比較）／run&id=。POST {a:'start', imgs, prompt, wfs, n, same_seed, params}／{a:'dl', wfs}／{a:'vote', id, v}."""
        E = self.E()
        try:
            if req.method == 'POST':
                d = req.json(); a = d.get('a')
                if a == 'start':
                    rid, ids, skip = E.cmp_start(d.get('imgs'), d.get('prompt', ''), d.get('wfs'), int(d.get('n') or 1), d.get('same_seed', True) is not False, d.get('params'), d.get('neg', ''), d.get('cols'))
                    self._gen_refresh(); return jresp({'ok': True, 'id': rid, 'ids': ids, 'skip': skip, 'message': f'🧪 比較 {rid}：排好 {len(ids)} 張' + (f'（跳過 {len(skip)} 個）' if skip else '')})
                if a == 'dl': n = E.cmp_dl([str(x) for x in d.get('wfs') or []]); return jresp({'ok': True, 'n': n, 'message': f'開始下載 {n} 個模型（一個一個下載，進度在每一列和「🖥 背景」）' if n else '勾的流程模型都有了'})
                if a == 'vote': return jresp({'ok': True, 'v': E.cmp_vote(d.get('id'), d.get('v'))})
                if a == 'stop': n = E.cmp_stop(int(d.get('id') or 0)); self._gen_refresh(); return jresp({'ok': True, 'message': f'停掉了 {n} 個（做好的都留著）'})
                if a == 'del': n = E.cmp_del(int(d.get('id') or 0)); self._gen_refresh(); return jresp({'ok': True, 'message': f'刪掉了（{n} 筆放進回收桶，30 天內可以還原）'})
                if a == 'retry':
                    ids, err = E.cmp_retry(int(d.get('id') or 0)); self._gen_refresh()
                    return jresp({'ok': bool(ids) or not err, 'message': (f'重跑 {len(ids)} 張' if ids else '沒有失敗的') + (f'（{len(err)} 個排不進去：{err[0]}）' if err else '')})
                return jresp({'ok': False, 'message': '不認得的動作'}, 400)
            a = req.q('a', 'rows')
            if a == 'runs': return jresp({'ok': True, 'runs': E.cmp_runs()})
            if a == 'recent':                                                    # 最近用過的照片（電腦上已經有，不用再上傳）
                L = []
                for r in E.db.q("SELECT img, imgs, ref FROM gen_jobs WHERE img<>'' AND deleted=0 ORDER BY id DESC LIMIT 400"):   # V0.2.50 也算圖二、參考圖
                    try: X = [r[0]] + [x for x in json.loads(r[1] or '[]') if x] + ([r[2]] if r[2] else [])
                    except Exception: X = [r[0]]
                    for im in X:
                        if im and im not in L and not E.is_video_name(im) and (E.data / 'inputs' / im).is_file(): L.append(im)
                    if len(L) >= 30: break
                return jresp({'ok': True, 'imgs': L})
            if a == 'run': return jresp(dict(E.cmp_run(int(req.q('id', '0') or 0)), ok=True))
            return jresp({'ok': True, 'rows': E.cmp_rows(), 'disk': E.disk_free()})
        except Exception as ex: return self._gen_err(ex)

    def api_mdl(self, req):
        """🧩 模型檔：GET 清單；POST {a:'del', path}."""
        E = self.E()
        try:
            if req.method == 'POST':
                d = req.json()
                if d.get('a') == 'slim_plan': return jresp(dict(E.slim_plan(d.get('extra') or []), ok=True))
                if d.get('a') == 'slim':
                    n, fr, err = E.slim_do(d.get('extra') or []); return jresp({'ok': not err, 'message': f'收掉 {n} 個流程、省下 {fr / 1e9:.1f} GB' + (f'（{len(err)} 個沒刪成功：{err[0]}）' if err else '')})
                if d.get('a') == 'del': sz = E.mdl_del(d.get('path')); return jresp({'ok': True, 'freed': sz, 'message': f'刪掉了，省下 {sz / 1e9:.1f} GB'})
                return jresp({'ok': False, 'message': '不認得的動作'}, 400)
            return jresp(dict(E.mdl_list(), ok=True))
        except Exception as ex: return self._gen_err(ex)

    def api_prompts(self, req):
        """常用提示詞。POST {a:'save'|'del', p}."""
        E = self.E()
        if req.method == 'POST':
            d = req.json()
            if d.get('a') in ('rsave', 'rdel'): E.recipe_save(d.get('r') or {}, d.get('a') == 'rsave')
            else: E.prompt_save(str(d.get('p') or ''), d.get('a') != 'del')
        return jresp(dict(E.prompts(), recipes=E.recipes(), ok=True))

    def api_diag(self, req):
        try: return jresp({'ok': True, 'items': self.E().diag()})
        except Exception as ex: return self._gen_err(ex)

    def api_gen_act(self, req):
        """a＝cancel／rerun／reuse（拿結果當新照片）／hide（從清單移除，檔案留著）."""
        E = self.E(); d = req.json(); a = d.get('a'); jid = d.get('id')
        try:
            if a == 'cancel': r = {'ok': E.gen_cancel(jid)}
            elif a == 'restart':                                               # V0.3.42 卡住：中斷、清記憶體、放回排隊
                J = E.gen_active.get(jid)
                if J: J['restart'] = True
                r = {'ok': bool(J), 'message': '中斷、清記憶體後重新排（幾秒）' if J else '這個沒有在跑'}
            elif a == 'cancel_many': r = E.gen_cancel_many(d.get('batch') or 0, bool(d.get('run')))   # V0.3.39 批量取消
            elif a == 'rerun':
                ids = E.gen_rerun(jid, '手機', n=d.get('n') or 1); E.gen_set_batch(ids); r = {'ok': True, 'ids': ids, 'message': f'再排了 {len(ids)} 張（不同的隨機種子）'}
            elif a == 'other':
                wf = str(d.get('wf') or ''); r = {'ok': True, 'ids': E.gen_rerun(jid, '手機', wf=wf, params=d.get('params') or {}), 'message': f'用「{wf}」排好了，做好在下面／歷史紀錄'}
            elif a == 'reuse':
                r = {'ok': True, 'img': E.gen_reuse(jid, d.get('idx') or 0)}
                mr = E.db.one('SELECT mask FROM gen_jobs WHERE id=?', (int(jid),)); r['mask'] = (mr[0] if mr else '') or ''   # V0.2.04 局部改的結果再改：帶著同一個遮罩
            elif a == 'hide': r = {'ok': E.gen_hide(jid)}
            elif a == 'top': r = {'ok': E.gen_top(jid), 'message': '⏫ 下一個就做它'}
            elif a == 'gif': r = {'ok': True, 'file': E.gen_gif(str(d.get('f') or ''), int(d.get('w') or 480))}
            elif a in ('upscale', 'interp'): ids, m = E.gen_post(jid, d.get('idx') or 0, a, '手機'); r = {'ok': True, 'ids': ids, 'message': m + '，做好在歷史紀錄'}
            else: return jresp({'ok': False, 'message': '不認得的動作'}, 400)
            E.log.w(f'📱 手機：生圖 {a} #{jid}'); self._gen_refresh(); return jresp(r)
        except Exception as ex: return self._gen_err(ex)

    def api_gen_wf(self, req):
        """上傳流程 JSON（ComfyUI 一般存檔或 Export (API) 都可以）."""
        if req.method != 'POST' or not req.body: return jresp({'ok': False, 'message': '沒有收到檔案'})
        try: nm = self.E().gen_wf_save(req.q('name') or 'workflow', req.body); self._gen_refresh(); return jresp({'ok': True, 'name': nm, 'message': f'已匯入流程「{nm}」'})
        except Exception as ex: return self._gen_err(ex)

    def api_gen_tpl(self, req):
        """從 ComfyUI 內建的官方範本做流程：?tpl=範本名稱&name=流程名字&force=1（同名換掉）."""
        try:
            E = self.E(); nm = E.gen_from_template(req.q('tpl'), req.q('name') or None, force=bool(req.q('force')))
            self._gen_refresh(); return jresp({'ok': True, 'name': nm, 'message': f'✔ 做好流程「{nm}」'})
        except Exception as ex: return self._gen_err(ex)

    def api_bench(self, req):
        """🔬 拿某一筆紀錄的原圖＋提示詞排一組測速：?id=紀錄編號."""
        try:
            E = self.E(); r = E.db.one('SELECT img, prompt FROM gen_jobs WHERE id=?', (int(req.q('id') or 0),))
            if not r: return jresp({'ok': False, 'message': '找不到這筆'})
            ids, note = E.gen_benchmark(r[0], r[1]); self._gen_refresh()
            return jresp({'ok': True, 'message': f'🔬 排了 {len(ids)} 個測速工作{note}，做完在歷史紀錄同一組看秒數'})
        except Exception as ex: return self._gen_err(ex)

    def api_people(self, req):
        """👤 人物庫：GET 列表；POST ?a=new&name= ／ a=add&code=（body＝照片）／ a=name&code=&name= ／ a=del&code=[&f=照片]."""
        E = self.E(); a = req.q('a')
        try:
            if a == 'new': c = E.people_new(req.q('name')); return jresp({'ok': True, 'code': c, 'message': f'✔ 建好 {c}'})
            if a == 'add':
                if req.method != 'POST' or not req.body: return jresp({'ok': False, 'message': '沒有收到照片'})
                return jresp({'ok': True, 'f': E.people_add_photo(req.q('code'), req.body)})
            if a == 'name': E.people_save(req.q('code'), req.q('name')); return jresp({'ok': True})
            if a == 'cover':
                P = E.people_get(req.q('code')) or {}; f = req.q('f'); o = [f] + [x for x in P.get('photos') or [] if x != f]
                E.people_save(req.q('code'), order=o); return jresp({'ok': True})
            if a == 'del': E.people_del(req.q('code'), req.q('f') or None); return jresp({'ok': True, 'message': '已刪除（搬到 people\\_old）'})
            return jresp({'ok': True, 'people': E.people_list()})
        except Exception as ex: return self._gen_err(ex)

    def api_gen_params(self, req):
        """這個流程可以調的參數（分組：常用打開、其他收合）."""
        try: return jresp({'ok': True, 'groups': self.E().gen_params(req.q('wf'))})
        except Exception as ex: return self._gen_err(ex)

    def api_models(self, req):
        """GET ?wf=：這個流程要的模型、ComfyUI 有沒有、下載進度。POST {a:'dl', files:[…]}／{a:'cancel', file}."""
        E = self.E()
        if req.method == 'POST':
            d = req.json()
            if d.get('a') == 'dl': n = E.dl_add([str(x) for x in d.get('files') or []]); return jresp({'ok': True, 'n': n, 'message': f'開始下載 {n} 個模型' if n else '沒有要下載的'})
            if d.get('a') == 'cancel': return jresp({'ok': E.dl_cancel(str(d.get('file') or ''))})
            return jresp({'ok': False, 'message': '不認得的動作'}, 400)
        try: return jresp({'ok': True, 'items': E.gen_models(req.q('wf'))})
        except Exception as ex: return self._gen_err(ex)

    def api_gen_hist(self, req):
        E = self.E()
        try: return jresp(dict(E.gen_history(req.q('q'), req.q('state'), req.q('wf'), int(req.q('offset', '0') or 0), int(req.q('limit', '30') or 30), req.q('view')), ok=True, now=time.time()))
        except Exception as ex: return self._gen_err(ex)

    def api_hist_act(self, req):
        """歷史紀錄：{a: hide|unhide|del|restore|purge, ids: [...]}."""
        E = self.E(); d = req.json(); a = d.get('a')
        if a not in ('hide', 'unhide', 'del', 'restore', 'purge'): return jresp({'ok': False, 'message': '不認得的動作'}, 400)
        n = E.gen_hist_act(d.get('ids') or [], a); E.log.w(f'📱 手機：歷史紀錄 {a} {n} 筆')
        self._ui(lambda: getattr(self.W(), 'hist', None) and self.W().hist.isVisible() and self.W().hist.load(self.W().hist.off))
        return jresp({'ok': True, 'n': n})

    def api_gen_stats(self, req):
        return jresp({'ok': True, 'stats': self.E().gen_stats()})

    def api_zip(self, req):
        """V0.3.12 好幾筆結果打包成一個 zip 下載：?ids=1,2,3."""
        import io, zipfile as _zf
        E = self.E(); ids = [int(x) for x in re.findall(r'\d+', req.q('ids') or '')][:300]
        if not ids: return jresp({'ok': False, 'message': '沒有選'}, 400)
        buf = io.BytesIO(); n = 0
        with _zf.ZipFile(buf, 'w', _zf.ZIP_STORED) as z:
            for r in E.db.q(f'SELECT id, outs FROM gen_jobs WHERE id IN ({",".join("?" * len(ids))})', ids):
                for o in json.loads(r['outs'] or '[]'):
                    p = E.gen_file(o)
                    if p: z.write(str(p), f'{r["id"]}_{p.name}'); n += 1
        if not n: return jresp({'ok': False, 'message': '這些紀錄沒有結果檔'}, 404)
        return Resp(200, buf.getvalue(), 'application/zip', {'Content-Disposition': "attachment; filename*=UTF-8''" + urllib.parse.quote(f'ComfyRemote_{n}張_{time.strftime("%m%d_%H%M")}.zip')})

    def api_gen_prev(self, req):
        try: b = self.E().gen_preview(int(req.q('id') or 0))
        except ValueError: b = None
        if not b: return Resp(204, b'', 'text/plain')
        return Resp(200, b, 'image/png' if b[:4] == b'\x89PNG' else 'image/jpeg', {'Cache-Control': 'no-store'})

    # ---- V0.3.41 🏷 提示詞積木＋📚 整篇範本：存在電腦的 Data\prompt_kit.json（每支手機都看得到同一份）
    def api_pkit(self, req):
        f = Path(self.E().data) / 'prompt_kit.json'
        if req.method != 'POST':
            try: return jresp({'ok': True, **json.loads(f.read_text(encoding='utf-8'))})
            except Exception: return jresp({'ok': True, 'cats': [], 'docs': [], 't': 0})
        d = req.json() or {}
        cats = d.get('cats'); docs = d.get('docs')
        if not isinstance(cats, list) or not isinstance(docs, list): return jresp({'ok': False, 'message': '格式不對'}, 400)
        K = {'cats': [{'id': str(c.get('id') or ''), 'name': str(c.get('name') or '')[:40], 'multi': bool(c.get('multi')),
                       'opts': [{'id': str(o.get('id') or ''), 't': str(o.get('t') or '')[:2000]} for o in (c.get('opts') or [])[:300] if str(o.get('t') or '').strip()]}
                      for c in cats[:100] if str(c.get('name') or '').strip()],
             'docs': [{'id': str(x.get('id') or ''), 'title': str(x.get('title') or '')[:80], 'text': str(x.get('text') or '')[:60000], 't': float(x.get('t') or 0)}
                      for x in docs[:300] if str(x.get('text') or '').strip()], 't': time.time()}
        tmp = f.with_suffix('.tmp')
        try:
            if f.exists(): shutil.copy2(f, f.with_suffix('.bak.json'))                 # 存之前留一份上一版
            tmp.write_text(json.dumps(K, ensure_ascii=False), encoding='utf-8'); os.replace(tmp, f)
        except Exception as ex: return jresp({'ok': False, 'message': f'存不進去：{ex}'}, 500)
        return jresp({'ok': True, **K})

    # ---- V0.3.40 🤝 握手（SortCut／FusionStitch）：右上角 Lv 畫面
    def api_hs(self, req):
        import hslink
        if hslink._S.get('hs') is None: hslink.bind(eng=self.E(), ver=self.version, port=0)   # 沒有桌面視窗（測試）時
        if req.method != 'POST': return jresp(hslink.info())
        return jresp(hslink.set_(req.json() or {}))

    # ---- V0.3.36 ☁ 雲端更新（GitHub Releases）：看狀態／檢查／更新／略過／取消
    def api_cloud(self, req):
        import cloudupd
        if not cloudupd.C('ver'): cloudupd.bind(ver=self.version, eng=self.E(), brand=self.brand)   # 沒有桌面視窗（測試）時
        if req.method != 'POST': return jresp(cloudupd.info())
        d = req.json() or {}
        try: self.E().log.w(f"📱 手機：雲端更新 {d.get('op')}" + ('（堅持現在更新）' if d.get('force') else ''))
        except Exception: pass
        return jresp(cloudupd.op(d))

    # ---- V0.3.35 📸 IG 下載（跟 TikLive 一樣）
    def api_igadd(self, req):
        if req.method != 'POST': return jresp({'ok': False, 'message': '要用 POST'}, 400)
        return jresp(self.E().igdl().add(req.body.decode('utf-8', 'ignore')))

    def api_iginfo(self, req): return jresp(self.E().igdl().info())

    def api_iglist(self, req): return jresp(self.E().igdl().list())

    def api_igdir(self, req):
        if req.method != 'POST': return jresp({'ok': True, 'dir': str(self.E().igdl()._igdl_dir())})
        return jresp(self.E().igdl().set_dir((req.json() or {}).get('dir', '')))

    def api_igck(self, req):
        g = self.E().igdl()
        if req.method != 'POST': return jresp(g._ig_cookie_info())               # 只回「有沒有存」，不回內容
        return jresp(g._ig_cookie_set((req.json() or {}).get('v', '')))

    def api_igthumb(self, req):
        t = self.E().igdl().thumb(req.q('f'))
        if t is None: return Resp(404, b'not found', 'text/plain')
        ct = {'.png': 'image/png', '.webp': 'image/webp'}.get(t.suffix.lower(), 'image/jpeg')
        return Resp(200, t.read_bytes(), ct, {'Cache-Control': 'private, max-age=2592000'})

    def api_igfile(self, req):
        p = self.E().igdl().file(req.q('f'))
        if p is None: return Resp(404, b'not found', 'text/plain')
        return self._send_file(req, p)

    def _send_file(self, req, p):
        ct = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.gif': 'image/gif', '.mp4': 'video/mp4'}.get(p.suffix.lower(), 'application/octet-stream')
        H = {'Cache-Control': 'private, max-age=31536000, immutable', 'Accept-Ranges': 'bytes'}
        if req.q('dl'): H['Content-Disposition'] = "attachment; filename*=UTF-8''" + urllib.parse.quote(p.name)
        size = p.stat().st_size; rg = re.match(r'bytes=(\d*)-(\d*)', req.headers.get('range') or '')
        if rg and (rg.group(1) or rg.group(2)):
            a = int(rg.group(1)) if rg.group(1) else max(0, size - int(rg.group(2))); b = int(rg.group(2)) if rg.group(1) and rg.group(2) else size - 1
            b = min(b, size - 1, a + 8 * 1024 * 1024 - 1)
            if a >= size: return Resp(416, b'', ct, {'Content-Range': f'bytes */{size}'})
            with open(p, 'rb') as f: f.seek(a); data = f.read(b - a + 1)
            H['Content-Range'] = f'bytes {a}-{a + len(data) - 1}/{size}'; return Resp(206, data, ct, H)
        return Resp(200, p.read_bytes(), ct, H)

    def api_img(self, req):
        p = self.E().gen_file(req.q('f'))
        if p is None: return Resp(404, b'not found', 'text/plain')
        if req.q('w') and not req.q('dl'):                                       # V0.1.96 清單用縮圖（省流量、手機滑起來順）
            try: t = self.E().gen_thumb(p, int(req.q('w')))
            except ValueError: t = None
            if t: return Resp(200, t.read_bytes(), 'image/jpeg', {'Cache-Control': 'private, max-age=31536000, immutable'})
        ct = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.gif': 'image/gif', '.mp4': 'video/mp4', '.webm': 'video/webm', '.mov': 'video/quicktime', '.mkv': 'video/x-matroska'}.get(p.suffix.lower(), 'application/octet-stream')
        H = {'Cache-Control': 'private, max-age=31536000, immutable', 'Accept-Ranges': 'bytes'}
        if req.q('dl'): H['Content-Disposition'] = "attachment; filename*=UTF-8''" + urllib.parse.quote(p.name)
        size = p.stat().st_size; rg = re.match(r'bytes=(\d*)-(\d*)', req.headers.get('range') or '')
        if rg and (rg.group(1) or rg.group(2)):                                # 手機播影片會一段一段要（iPhone 一定要這樣才播得了）
            a = int(rg.group(1)) if rg.group(1) else max(0, size - int(rg.group(2))); b = int(rg.group(2)) if rg.group(1) and rg.group(2) else size - 1
            b = min(b, size - 1, a + 8 * 1024 * 1024 - 1)
            if a >= size: return Resp(416, b'', ct, {'Content-Range': f'bytes */{size}'})
            with open(p, 'rb') as f: f.seek(a); data = f.read(b - a + 1)
            H['Content-Range'] = f'bytes {a}-{a + len(data) - 1}/{size}'; return Resp(206, data, ct, H)
        return Resp(200, p.read_bytes(), ct, H)
