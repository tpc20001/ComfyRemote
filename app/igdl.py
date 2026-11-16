"""V0.3.35 📸 IG 下載（從 TikLive TK_V1.0.83 原封不動搬過來）：貼 IG 貼文／Reels 網址 → 照片存 JPG、影片存 MP4 → 電腦的 IGDownloader 資料夾；
手機頁可以看、篩選、播放、存到手機；「📲 電腦下載好也自動存一份到這支手機」。
只抓「公開」貼文；不登入、不用帳號密碼。IG 擋沒登入的下載時，可以貼自己的 IG sessionid（只存在這台電腦）。"""
import os, re, json, time, shutil, subprocess, threading
from datetime import datetime
from pathlib import Path

IS_WIN = os.name == 'nt'


def _no_window_kwargs(low_priority=False):
    if not IS_WIN: return {}
    f = 0x08000000
    if low_priority: f |= 0x00004000                                            # BELOW_NORMAL_PRIORITY_CLASS
    return {'creationflags': f}


def ffmpeg_info(ff, path, timeout=60):
    """(width, height, codec, duration_sec) from FFmpeg's stream summary; missing values are 0 / ''."""
    try:
        r = subprocess.run([ff, '-hide_banner', '-nostdin', '-i', str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=timeout, **_no_window_kwargs())
        txt = r.stderr.decode('utf-8', 'ignore')
    except Exception:
        return 0, 0, '', 0.0
    w = h = 0; codec = ''; dur = 0.0
    m = re.search(r'Video:\s*(\w+)[^\n]*?\b(\d{2,5})x(\d{2,5})\b', txt)
    if m: codec = m.group(1); w = int(m.group(2)); h = int(m.group(3))
    m = re.search(r'Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)', txt)
    if m: dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    return w, h, codec, dur


class IGDL:
    IGDL_DIR = 'IGDownloader'
    _IGDL_RE = re.compile(r'https?://(?:www\.|m\.)?instagram\.com/(?:[A-Za-z0-9._]+/)?(p|reels?|tv)/([A-Za-z0-9_-]{5,})[^\s]*')
    _IG_BASE = 'https://www.instagram.com'
    _IG_APP = '936619743392459'
    _TKD_NAME = re.compile(r'^(.+?)_(\d{8})_(\d{6})(?:_\d+)*\.(?:mp4|jpe?g|webp|png)$', re.I)
    _EXT = ('.mp4', '.jpg', '.jpeg', '.webp', '.png')

    def __init__(self, engine):
        self.E = engine; self.st = {'q': [], 'run': False, 'done': [], 'lock': threading.Lock()}

    # ---- 資料夾：預設 Data\IGDownloader；設定可以改（例如跟 TikLive 共用 E:\IGDownloader）
    def _igdl_dir(self):
        p = str(self.E.cfg.get('ig_dir') or '').strip()
        return Path(p) if p else self.E.data / self.IGDL_DIR

    def set_dir(self, p):
        p = str(p or '').strip().strip('"')
        if not p: self.E.cfg.set('ig_dir', ''); return {'ok': True, 'dir': str(self._igdl_dir()), 'message': '改回預設資料夾'}
        if not os.path.isabs(p): return {'ok': False, 'message': '要寫完整路徑，例如 E:\\IGDownloader'}
        try: Path(p).mkdir(parents=True, exist_ok=True)
        except Exception as ex: return {'ok': False, 'message': f'建不了這個資料夾：{ex}'}
        self.E.cfg.set('ig_dir', p); return {'ok': True, 'dir': p, 'message': '✔ 之後下載到 ' + p}

    def _experiment_ffmpeg(self): return self.E._ffmpeg()

    def _ytdlp_paths(self):
        y = shutil.which('yt-dlp') or ''
        for c in (self.E.root / ('yt-dlp.exe' if IS_WIN else 'yt-dlp'),):
            if c.is_file(): y = str(c)
        return (Path(y) if y else None), None

    @staticmethod
    def _ig_items(media):
        """IG 的貼文資料（GraphQL 或 embed 裡的 shortcode_media）→ [(是影片, 網址)]；多張（輪播）照順序."""
        out = []
        def one_(n):
            if not isinstance(n, dict): return
            if n.get('is_video') and n.get('video_url'): out.append((True, n['video_url'])); return
            rs = n.get('display_resources') or []
            best = max(rs, key=lambda r: int(r.get('config_width') or 0)) if rs else None
            u = (best or {}).get('src') or n.get('display_url') or n.get('display_src')
            if u: out.append((False, u))
        side = ((media.get('edge_sidecar_to_children') or {}).get('edges')) or []
        if side:
            for e in side: one_((e or {}).get('node'))
        else: one_(media)
        return out

    @staticmethod
    def _ig_v1_items(it):
        """TK_V1.0.80 新版（v1 格式）貼文 → [(是影片, 網址)]：media_type 1＝照片、2＝影片、8＝輪播（carousel_media）."""
        out = []
        def one_(x):
            if not isinstance(x, dict): return
            vv = x.get('video_versions') or []
            if vv:
                b = max(vv, key=lambda v: int(v.get('width') or 0) * int(v.get('height') or 0))
                if b.get('url'): out.append((True, b['url'])); return
            cs = ((x.get('image_versions2') or {}).get('candidates')) or []
            if cs:
                b = max(cs, key=lambda v: int(v.get('width') or 0) * int(v.get('height') or 0))
                if b.get('url'): out.append((False, b['url']))
        car = it.get('carousel_media') or []
        if car:
            for x in car: one_(x)
        else: one_(it)
        return out

    def _ig_cookie_path(self): return self.E.data / 'ig_cookie.json'

    def _ig_cookie_get(self):
        try: return str(json.loads(self._ig_cookie_path().read_text(encoding='utf-8')).get('sessionid') or '').strip()
        except Exception: return ''

    def _ig_cookie_set(self, v):
        """使用者自己貼的 IG sessionid（只存在這台電腦的 _DB_SSD，不會從網頁讀回來；空白＝刪掉）."""
        v = str(v or '').strip().strip('"').strip()
        m_ = re.search(r'sessionid=([^;\s]+)', v)
        if m_: v = m_.group(1)
        p_ = self._ig_cookie_path()
        if not v:
            try: p_.unlink()
            except Exception: pass
            return {'ok': True, 'set': False, 'message': '已刪掉 IG 登入 Cookie'}
        if len(v) < 20 or not re.fullmatch(r'[A-Za-z0-9%:._\-]+', v): return {'ok': False, 'message': '這看起來不像 IG 的 sessionid（應該是一長串英數字，中間常有 %3A）'}
        p_.parent.mkdir(parents=True, exist_ok=True); t_ = p_.with_suffix('.tmp'); t_.write_text(json.dumps({'sessionid': v, 't': time.time()}), encoding='utf-8'); os.replace(str(t_), str(p_))
        return {'ok': True, 'set': True, 'message': '✔ 存好了：之後下載 IG 會用這個登入（只存在這台電腦）'}

    def _ig_cookie_info(self):
        v = self._ig_cookie_get()
        try: t_ = float(json.loads(self._ig_cookie_path().read_text(encoding='utf-8')).get('t') or 0)
        except Exception: t_ = 0
        return {'ok': True, 'set': bool(v), 't': t_}

    def _igdl_one(self, url):
        import urllib.request, urllib.parse, http.cookiejar, html as _html
        m = self._IGDL_RE.search(url or '')
        if not m: return {'ok': False, 'url': url, 'message': '✖ 看不懂這個 IG 網址'}
        code = m.group(2); base = self._IG_BASE
        UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
        sid0 = self._ig_cookie_get()
        def _get(use_ck):
            cj = http.cookiejar.CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
            H = {'User-Agent': UA, 'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8', 'X-IG-App-ID': self._IG_APP, 'Referer': f'{base}/p/{code}/'}
            media = None; why = ''; tries = []
            sid_ = sid0 if use_ck else ''                                            # TK_V1.0.80 使用者自己貼的 IG 登入 Cookie（選用，只存在這台電腦）
            if sid_:
                try:
                    from urllib.parse import urlparse as _up
                    dom = _up(base).hostname or 'www.instagram.com'; dom = '.instagram.com' if dom.endswith('instagram.com') else dom
                    cj.set_cookie(http.cookiejar.Cookie(0, 'sessionid', sid_, None, False, dom, True, dom.startswith('.'), '/', True, base.startswith('https'), None, False, None, None, {}))
                    uid_ = re.split(r'%3A|:', sid_)[0]
                    if uid_.isdigit(): cj.set_cookie(http.cookiejar.Cookie(0, 'ds_user_id', uid_, None, False, dom, True, dom.startswith('.'), '/', True, base.startswith('https'), None, False, None, None, {}))
                except Exception: pass
            home = ''
            try: home = op.open(urllib.request.Request(f'{base}/', headers={'User-Agent': UA, 'Accept': 'text/html,application/xhtml+xml', 'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Site': 'none'}), timeout=20).read(3 << 20).decode('utf-8', 'ignore')   # 拿 csrftoken＋LSD（不登入）
            except Exception: pass
            csrf = next((c.value for c in cj if c.name == 'csrftoken'), '')
            mm_ = re.search(r'\["LSD",\[\],\{"token":"([^"]+)"', home) or re.search(r'"lsd":\{"token":"([^"]+)"', home)
            lsd = mm_.group(1) if mm_ else ''
            if sid_:                                                                # 登入模式：先用 v1 媒體資訊（登入才給）
                try:
                    AL = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'; mid = 0
                    for ch_ in code[:11]: mid = mid * 64 + AL.index(ch_)
                    for host_, ua_, app_ in ((base, UA, self._IG_APP), (base.replace('://www.', '://i.'), 'Instagram 309.1.0.41.113 Android (31/12; 420dpi; 1080x2400; samsung; SM-G991B; o1s; exynos2100; zh_TW; 541635890)', '567067343352427')):
                        try:
                            h4 = {'User-Agent': ua_, 'X-IG-App-ID': app_, 'X-CSRFToken': csrf or 'missing', 'Accept': '*/*', 'Referer': f'{base}/p/{code}/', 'X-Requested-With': 'XMLHttpRequest'}
                            j = json.loads(op.open(urllib.request.Request(f'{host_}/api/v1/media/{mid}/info/', headers=h4), timeout=25).read().decode('utf-8', 'ignore'))
                            it = (j.get('items') or [None])[0]
                            fl = self._ig_v1_items(it) if it else []
                            if fl: media = {'_flat': fl, 'owner': {'username': ((it.get('user') or {}).get('username') or '')}, 'taken_at': it.get('taken_at')}; break
                            tries.append('登入 v1 沒給資料')
                        except Exception as ex: tries.append(f'登入 v1：{ex}')
                except Exception as ex: tries.append(f'登入 v1：{ex}')
            for ep, nm_ in (('/api/graphql', 'PolarisPostActionLoadPostQueryQuery'), ('/graphql/query', 'PolarisPostActionLoadPostQueryQuery')):   # ⓪ 2026 新版（IG 網頁自己用的那個查詢）
                if media: break
                try:
                    vars_ = {'shortcode': code, '__relay_internal__pv__PolarisAIGMMediaWebLabelEnabledrelayprovider': False}
                    bd = {'variables': json.dumps(vars_), 'doc_id': '27128499623469141', 'fb_api_caller_class': 'RelayModern', 'fb_api_req_friendly_name': nm_, 'server_timestamps': 'true'}
                    if lsd: bd['lsd'] = lsd
                    h3 = dict(H, **{'Accept': '*/*', 'Content-Type': 'application/x-www-form-urlencoded', 'Origin': base, 'X-ASBD-ID': '129477', 'X-IG-WWW-Claim': '0', 'X-CSRFToken': csrf or 'missing',
                                    'X-FB-Friendly-Name': nm_, 'X-Requested-With': 'XMLHttpRequest', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin'})
                    if lsd: h3['X-FB-LSD'] = lsd
                    j = json.loads(op.open(urllib.request.Request(base + ep, data=urllib.parse.urlencode(bd).encode(), headers=h3), timeout=25).read().decode('utf-8', 'ignore'))
                    it = ((((j.get('data') or {}).get('xdt_api__v1__media__shortcode__web_info')) or {}).get('items') or [None])[0]
                    if it:
                        fl = self._ig_v1_items(it)
                        if fl: media = {'_flat': fl, 'owner': {'username': ((it.get('user') or it.get('owner') or {}).get('username') or '')}, 'taken_at': it.get('taken_at')}
                    if not media: tries.append(f'{ep} 沒給資料')
                except Exception as ex: tries.append(f'{ep}：{ex}')
            if not media:
              try:                                                                    # ① 舊版公開貼文 GraphQL（不用登入）
                  body = urllib.parse.urlencode({'variables': json.dumps({'shortcode': code, 'fetch_tagged_user_count': None, 'hoisted_comment_id': None, 'hoisted_reply_id': None}),
                                                 'doc_id': '8845758582119845'}).encode()
                  h2 = dict(H, **{'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': csrf or 'missing', 'X-Requested-With': 'XMLHttpRequest'})
                  j = json.loads(op.open(urllib.request.Request(f'{base}/graphql/query', data=body, headers=h2), timeout=25).read().decode('utf-8', 'ignore'))
                  media = ((j.get('data') or {}).get('xdt_shortcode_media')) or ((j.get('data') or {}).get('shortcode_media'))
                  if not media: why = 'IG 沒給這則的資料（可能是私人帳號、已刪除，或 IG 暫時擋了）'
              except Exception as ex: why = f'讀不到 IG 資料：{ex}'
            if not media:                                                           # ② 嵌入頁（embed）
                try:
                    pg = op.open(urllib.request.Request(f'{base}/p/{code}/embed/captioned/', headers={'User-Agent': UA, 'Accept-Language': 'zh-TW,zh;q=0.9'}), timeout=25).read().decode('utf-8', 'ignore')
                    mm = re.search(r'"contextJSON"\s*:\s*("(?:\\.|[^"\\])*")', pg)
                    if mm:
                        try:
                            cj_ = json.loads(json.loads(mm.group(1)))
                            media = ((cj_.get('context') or {}).get('media')) or (((cj_.get('gql_data') or {}).get('shortcode_media')))
                        except Exception: media = None
                    if not media:
                        vids = [json.loads('"' + v + '"') for v in re.findall(r'"video_url"\s*:\s*"((?:\\.|[^"\\])*)"', pg)]
                        imgs = [_html.unescape(u) for u in re.findall(r'class="EmbeddedMediaImage"[^>]*src="([^"]+)"', pg)]
                        us = re.search(r'class="UsernameText"[^>]*>([^<]+)<', pg)
                        if vids or imgs: media = {'_flat': [(True, v) for v in vids] + [(False, i) for i in imgs], 'owner': {'username': (us.group(1).strip() if us else '')}}
                    if not media and not why: why = '嵌入頁也找不到照片／影片'
                except Exception as ex: why = why or f'讀不到 IG 嵌入頁：{ex}'
            return media, why, tries, op
        media = None; why = ''; tries = []; sid_ = ''
        for use_ck in ((False, True) if sid0 else (False,)):                   # TK_V1.0.81 先不登入試（之前不登入抓得到），不行才用你貼的 Cookie
            media, w_, t_, op = _get(use_ck)
            tries += [('〔登入〕' if use_ck else '') + x for x in t_]
            if w_: why = (('〔登入〕' if use_ck else '') + w_) if not why else why
            if media: break
            sid_ = sid0 if use_ck else ''
        if not media:
            tl = '；'.join(x[:70] for x in tries[:5])
            if tries and all('urlopen error' in x for x in tries) and 'urlopen error' in (why or 'urlopen error'):
                return {'ok': False, 'url': url, 'message': f'✖ IG {code}：連不上 IG（網路斷了或被擋），晚點再試'}
            return {'ok': False, 'url': url, 'message': f'✖ IG {code}：{why or "抓不到"}' + (f'（試過：{tl}）' if tl else '') +
                    ('（已用你貼的 IG 登入 Cookie 也抓不到：Cookie 可能過期了，重新貼一次）' if sid_ else '（沒登入抓不到：IG 最近常擋沒登入的下載。可以在「📸 IG」頁下面的「IG 登入（選用）」貼上你的 IG Cookie 再試）')}
        items = media.get('_flat') or self._ig_items(media)
        user = str(((media.get('owner') or {}).get('username')) or 'ig')
        try: ts = float(media.get('taken_at_timestamp') or media.get('taken_at') or 0) or time.time()
        except Exception: ts = time.time()
        if not items: return {'ok': False, 'url': url, 'message': f'✖ @{user} 這則沒有照片或影片'}
        d = self._igdl_dir(); d.mkdir(parents=True, exist_ok=True)
        safe = re.sub(r'[^\w.\-]+', '_', user) or 'ig'; stamp = datetime.fromtimestamp(ts).strftime('%Y%m%d_%H%M%S')
        def good(p, vid):
            try:
                with open(p, 'rb') as fh: h_ = fh.read(12)
                return (h_[4:8] == b'ftyp') if vid else (h_[:3] == b'\xff\xd8\xff' or h_[:4] == b'RIFF' or h_[:8] == b'\x89PNG\r\n\x1a\n')
            except Exception: return False
        saved = []; bad = 0; n_ = len(items)
        for i, (vid, u) in enumerate(items, 1):
            ext = '.mp4' if vid else '.jpg'
            out = d / (f'{safe}_{stamp}' + (f'_{i}' if n_ > 1 else '') + ext); k_ = 2
            while out.exists():
                out = d / (f'{safe}_{stamp}' + (f'_{i}' if n_ > 1 else '') + f'_{k_}{ext}'); k_ += 1
            tmp = out.with_suffix('.part')
            try:
                with op.open(urllib.request.Request(u, headers={'User-Agent': UA, 'Referer': base + '/'}), timeout=60) as r, open(tmp, 'wb') as f:
                    while True:
                        b = r.read(1 << 20)
                        if not b: break
                        f.write(b)
                if good(tmp, vid):
                    if not vid:                                                 # 有時給的是 webp／png：照真正格式存（還是叫 .jpg 會打不開）
                        with open(tmp, 'rb') as fh: h_ = fh.read(12)
                        if h_[:4] == b'RIFF': out = out.with_suffix('.webp')
                        elif h_[:4] == b'\x89PNG': out = out.with_suffix('.png')
                    os.replace(tmp, out)
                    try: os.utime(out, (ts, ts))                                # 檔案時間＝貼文時間
                    except Exception: pass
                    saved.append(out)
                else: bad += 1
            except Exception: bad += 1
            finally:
                try:
                    if tmp.exists(): tmp.unlink()
                except Exception: pass
        if not saved:
            y, _dn = self._ytdlp_paths()
            if y is not None and any(v for v, _ in items):                       # ③ 影片最後試 yt-dlp
                tmpl = str(d / f'{safe}_{stamp}_%(autonumber)s.%(ext)s')
                try: subprocess.run([str(y), '--no-part', '-o', tmpl, url.split('?')[0]], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600, **_no_window_kwargs(low_priority=True))
                except Exception: pass
                saved = [p for p in d.glob(f'{safe}_{stamp}_*') if p.suffix.lower() in ('.mp4', '.jpg', '.webp')]
        if not saved: return {'ok': False, 'url': url, 'message': f'✖ @{user} 這則 {n_} 個檔案都沒下載成功（IG 可能暫時擋了，晚點再試）'}
        nj = sum(1 for p in saved if p.suffix.lower() != '.mp4'); nv = len(saved) - nj; mb = sum(p.stat().st_size for p in saved) / 1e6
        return {'ok': True, 'url': url, 'file': saved[0].name, 'files': [p.name for p in saved], 'mb': round(mb, 1),
                'message': f'✔ IG @{user}：' + '、'.join(x for x in [f'{nj} 張照片' if nj else '', f'{nv} 部影片' if nv else ''] if x) + f'（{mb:.1f} MB）→ {d}' + (f'（另有 {bad} 個沒下載成功）' if bad else '')}

    # ---- 網址 → 排隊下載（跟 TikLive 一樣：一次一個，做完的留 50 筆給手機看）
    def split(self, text):
        urls = [m.group(0) for m in self._IGDL_RE.finditer(text or '')]
        out = []
        for u in urls:
            if u not in out: out.append(u)
        return out

    def add(self, text):
        urls = self.split(text)
        if not urls: return {'ok': False, 'message': '看不到 IG 貼文／Reels 網址（instagram.com/p/… 或 /reel/…）'}
        st = self.st; now = time.time()
        with st['lock']:
            for u in urls:
                if not any(x['url'] == u for x in st['q']): st['q'].append({'url': u, 't': now})
            run = st['run']; st['run'] = True
        if not run: threading.Thread(target=self._worker, name='IGDL', daemon=True).start()
        return {'ok': True, 'ttdl': True, 'n': len(urls), 'message': f'開始下載 {len(urls)} 個 IG 貼文（照片存 JPG、影片存 MP4）'}

    def info(self):
        st = self.st
        return {'ok': True, 'dir': str(self._igdl_dir()), 'run': st['run'], 'q': [x['url'] for x in st['q']], 'done': st['done'][-20:], 'prog': st.get('prog')}

    def _worker(self):
        st = self.st
        try:
            while True:
                with st['lock']:
                    if not st['q']: st['run'] = False; return
                    job = st['q'][0]
                job['msg'] = '下載中'
                try: r = self._igdl_one(job['url'])
                except Exception as ex: r = {'ok': False, 'url': job['url'], 'message': f'下載失敗：{ex}'}
                r['t'] = time.time(); r['src'] = 'ig'
                if r.get('ok') and not r.get('files') and r.get('file'): r['files'] = [r['file']]
                with st['lock']:
                    st['q'] = [x for x in st['q'] if x is not job]; st['done'] = (st['done'] + [r])[-50:]
                try: self.E.log.w('IG 下載：' + r.get('message', ''))
                except Exception: pass
        finally:
            st['run'] = False

    # ---- 資料夾清單／縮圖／檔案（手機頁用）
    def file(self, name):
        """只接受 IGDownloader 裡的檔名（不能帶路徑）."""
        n = Path(str(name or '')).name
        if not n or n != str(name) or not n.lower().endswith(self._EXT): return None
        f = self._igdl_dir() / n
        return f if f.is_file() else None

    def list(self):
        """資料夾裡的影片／照片（帳號、時間、大小、長度）；長度用 FFmpeg 讀一次就記住."""
        d = self._igdl_dir(); out = []
        mp = self.E.data / 'ig_meta.json'
        try: meta = json.loads(mp.read_text(encoding='utf-8'))
        except Exception: meta = {}
        changed = False; ff = self._experiment_ffmpeg()
        try: files = [f for f in d.iterdir() if f.is_file() and f.suffix.lower() in self._EXT] if d.is_dir() else []
        except Exception: files = []
        for f in files:
            try: st = f.stat()
            except Exception: continue
            dl_ = int(getattr(st, 'st_birthtime', 0) or st.st_ctime or st.st_mtime)   # 下載時間＝檔案建立時間（修改時間被改成發文時間了）
            m = self._TKD_NAME.match(f.name)
            try: t = datetime.strptime(m.group(2) + m.group(3), '%Y%m%d%H%M%S').timestamp() if m else st.st_mtime
            except Exception: t = st.st_mtime
            if f.suffix.lower() != '.mp4':                                      # 照片：不用 FFmpeg
                out.append({'f': f.name, 'u': (m.group(1) if m else f.stem), 't': int(t), 'mb': round(st.st_size / 1e6, 2), 'd': 0, 'w': 0, 'h': 0, 'k': 'i', 'dl': dl_}); continue
            k = f'{f.name}|{st.st_size}'; x = meta.get(k)
            if x is None and ff:
                try: w_, h_, c_, du = ffmpeg_info(ff, f, timeout=30); x = {'d': round(float(du or 0), 1), 'w': int(w_ or 0), 'h': int(h_ or 0)}
                except Exception: x = {'d': 0}
                meta[k] = x; changed = True
            out.append({'f': f.name, 'u': (m.group(1) if m else f.stem), 't': int(t), 'mb': round(st.st_size / 1e6, 1), 'd': (x or {}).get('d', 0), 'w': (x or {}).get('w', 0), 'h': (x or {}).get('h', 0), 'k': 'v', 'dl': dl_})
        if changed:
            try: mp.parent.mkdir(parents=True, exist_ok=True); mp.write_text(json.dumps(meta, ensure_ascii=False), encoding='utf-8')
            except Exception: pass
        out.sort(key=lambda o: (-o['t'], o['f']))
        return {'ok': True, 'dir': str(d), 'src': 'ig', 'items': out}

    def thumb(self, name):
        """縮圖（影片第 1 秒／照片本身，480 高；快取在 Data\\ig_thumbs）."""
        f = self.file(name)
        if f is None: return None
        try: st = f.stat()
        except Exception: return None
        img = f.suffix.lower() != '.mp4'
        th = self.E.data / 'ig_thumbs' / f'ig_{f.stem}_{f.suffix[1:].lower()}_{st.st_size}.jpg'
        if th.exists() and th.stat().st_size > 0: return th
        ff = self._experiment_ffmpeg()
        if not ff: return f if img else None
        th.parent.mkdir(parents=True, exist_ok=True); tmp = th.with_suffix('.tmp.jpg')
        try: subprocess.run([ff, '-hide_banner', '-loglevel', 'error', '-nostdin', '-y'] + ([] if img else ['-ss', '1']) + ['-i', str(f), '-frames:v', '1', '-vf', 'scale=-2:480', '-q:v', '4', str(tmp)], stdin=subprocess.DEVNULL, capture_output=True, timeout=60, **_no_window_kwargs())
        except Exception: pass
        if tmp.exists() and tmp.stat().st_size > 0: os.replace(tmp, th); return th
        try: tmp.unlink()
        except Exception: pass
        return f if img else None
