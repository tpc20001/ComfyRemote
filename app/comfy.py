"""🎨 跟本機 ComfyUI 溝通（只用標準函式庫，不准 import Qt）。

- Comfy：HTTP API（上傳照片、送工作、查進度、拿結果、中斷）。ComfyUI Desktop 預設 127.0.0.1:8000，免安裝版 127.0.0.1:8188。
- WS：最小的 websocket 用戶端，收 ComfyUI 的即時進度（第幾步／共幾步）。連不上就改成每 2 秒查 /history。
- ui_to_api：ComfyUI 一般存檔格式（有 nodes／links）→ API 格式（送工作要用這種）。也接受直接 Export (API) 的檔。
- prepare：把流程裡的「讀圖節點」換成手機上傳的照片、提示詞填進文字編碼節點、種子隨機、只留 SaveImage／PreviewImage 會用到的節點。
"""
import os, re, json, copy, time, base64, random, socket, struct, uuid, urllib.request, urllib.parse, urllib.error

CTRL_VALUES = {'fixed', 'increment', 'decrement', 'randomize', 'increment-wrap', 'decrement-wrap'}
WIDGET_TYPES = {'INT', 'FLOAT', 'STRING', 'BOOLEAN', 'COMBO'}
STD_OUTPUTS = {'SaveImage', 'PreviewImage', 'SaveAnimatedWEBP', 'SaveAnimatedPNG', 'SaveVideo', 'SaveWEBM', 'VHS_VideoCombine'}
TEXT_KEYS = ('text', 'prompt', 'text_g', 'positive', 'string', 'value')
PROMPT_HINT = ('integrated_multimodal_description', 'description', 'caption', 'prompt_text', 'instruction')
AUDIO_FIELDS = ('overall_soundscape', 'non_diegetic_music')
VIRTUAL = {'Reroute', 'Note', 'MarkdownNote', 'PrimitiveNode', 'SetNode', 'GetNode', 'Label (rgthree)', 'Fast Groups Bypasser (rgthree)',
           'Fast Groups Muter (rgthree)', 'Bookmark (rgthree)'}
DEFAULT_URLS = ('http://127.0.0.1:8000', 'http://127.0.0.1:8188')


class ComfyError(Exception):
    pass


class ComfyDown(ComfyError):
    """連不到 ComfyUI（關掉了／還沒開）：工作放回排隊，等它回來再跑，不算失敗."""


def is_link(v): return isinstance(v, list) and len(v) == 2 and isinstance(v[0], (str, int)) and isinstance(v[1], int)


# ================================================================ HTTP
class Comfy:
    def __init__(self, url, timeout=20):
        self.url = str(url or DEFAULT_URLS[0]).rstrip('/'); self.timeout = timeout

    def _req(self, path, data=None, ctype=None, method=None, timeout=None):
        h = {'User-Agent': 'ComfyRemote'}
        if ctype: h['Content-Type'] = ctype
        r = urllib.request.Request(self.url + path, data=data, headers=h, method=method or ('POST' if data is not None else 'GET'))
        try:
            with urllib.request.urlopen(r, timeout=timeout or self.timeout) as f: return f.read()
        except urllib.error.HTTPError as ex:
            body = b''
            try: body = ex.read()
            except Exception: pass
            raise ComfyError(self._err_text(ex.code, body)) from None
        except (urllib.error.URLError, OSError) as ex:
            raise ComfyDown(f'連不到 ComfyUI（{self.url}）：{getattr(ex, "reason", ex)}') from None

    @staticmethod
    def _err_text(code, body):
        try: j = json.loads(body.decode('utf-8', 'replace'))
        except Exception: return f'ComfyUI 回 {code}：{body[:300].decode("utf-8", "replace")}'
        msg = []
        e = j.get('error')
        if isinstance(e, dict): msg.append(str(e.get('message') or e.get('type') or ''))
        elif e: msg.append(str(e))
        for nid, ne in (j.get('node_errors') or {}).items():
            for x in (ne.get('errors') or [])[:3]:
                msg.append(f'節點 {nid}（{ne.get("class_type", "")}）：{x.get("message", "")} {x.get("details", "")}'.strip())
        return f'ComfyUI 拒絕（{code}）：' + '；'.join(m for m in msg if m)[:800]

    def get_json(self, path, timeout=None): return json.loads(self._req(path, timeout=timeout).decode('utf-8'))

    def post_json(self, path, obj, timeout=None):
        b = self._req(path, json.dumps(obj).encode('utf-8'), 'application/json', timeout=timeout)
        try: return json.loads(b.decode('utf-8') or '{}')
        except Exception: return {}

    def stats(self): return self.get_json('/system_stats', timeout=4)

    def userdata_put(self, rel, data, overwrite=False):
        """V0.3.34 存一個檔到 ComfyUI 的使用者資料夾（例如 workflows/xxx.json → 左邊「工作流」清單看得到）。已經有同名檔又不蓋：回 False."""
        q = urllib.parse.quote(rel, safe='')
        try: self._req(f'/api/userdata/{q}?overwrite={"true" if overwrite else "false"}&full_info=true', data, 'application/json', 'POST', timeout=30); return True
        except ComfyError as ex:
            if '409' in str(ex): return False
            raise

    def object_info(self, cls): return (self.get_json('/object_info/' + urllib.parse.quote(cls, safe=''), timeout=15) or {}).get(cls)

    def upload(self, name, data):
        bd = '----cr' + uuid.uuid4().hex
        def field(k, v): return (f'--{bd}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n').encode('utf-8')
        ext = os.path.splitext(name)[1].lower(); ct = {'.png': 'image/png', '.webp': 'image/webp'}.get(ext, 'image/jpeg')
        body = (field('overwrite', 'true') + field('type', 'input') +
                f'--{bd}\r\nContent-Disposition: form-data; name="image"; filename="{name}"\r\nContent-Type: {ct}\r\n\r\n'.encode('utf-8') + data + f'\r\n--{bd}--\r\n'.encode())
        j = json.loads(self._req('/upload/image', body, f'multipart/form-data; boundary={bd}', timeout=120).decode('utf-8'))
        return (j.get('subfolder') + '/' if j.get('subfolder') else '') + j.get('name', name)

    def queue_prompt(self, prompt, client_id):
        j = self.post_json('/prompt', {'prompt': prompt, 'client_id': client_id}, timeout=60)
        if not j.get('prompt_id'): raise ComfyError('ComfyUI 沒有收下這個工作：' + json.dumps(j, ensure_ascii=False)[:400])
        return j['prompt_id']

    def history(self, pid): return (self.get_json('/history/' + urllib.parse.quote(pid), timeout=15) or {}).get(pid)

    def queue(self): return self.get_json('/queue', timeout=8)

    def view(self, filename, subfolder='', type_='output'):
        return self._req('/view?' + urllib.parse.urlencode({'filename': filename, 'subfolder': subfolder or '', 'type': type_ or 'output'}), timeout=120)

    def free(self, unload=True):
        """叫 ComfyUI 把留在記憶體裡的模型清掉（POST /free）."""
        return self._req('/free', json.dumps({'unload_models': bool(unload), 'free_memory': True}).encode(), 'application/json', timeout=30)

    def cancel(self, pid):
        """排隊中的拿掉；正在跑的中斷."""
        try:
            q = self.queue(); running = {x[1] for x in q.get('queue_running') or [] if len(x) > 1}
        except Exception: running = set()
        if pid in running:
            try: self.post_json('/interrupt', {'prompt_id': pid})
            except ComfyError: self.post_json('/interrupt', {})
        else:
            try: self.post_json('/queue', {'delete': [pid]})
            except Exception: pass


def find_url(pref=''):
    """設定的網址先試，再試 Desktop 預設 8000、免安裝版 8188。回傳 (網址, system_stats) 或 ('', 錯誤)."""
    tried = []; last = ''
    for u in ([pref] if pref else []) + list(DEFAULT_URLS):
        u = str(u or '').strip().rstrip('/')
        if not u or u in tried: continue
        if not re.match(r'https?://', u): u = 'http://' + u
        tried.append(u)
        try: return u, Comfy(u).stats()
        except Exception as ex: last = str(ex)
    return '', f'找不到 ComfyUI（試過 {"、".join(tried)}）。ComfyUI 有打開嗎？' + (f'\n{last}' if last else '')


# ================================================================ websocket（只收不送；收到 ping 回 pong）
class WS:
    def __init__(self, base_url, client_id, timeout=8):
        u = urllib.parse.urlsplit(base_url); host = u.hostname or '127.0.0.1'; port = u.port or (443 if u.scheme == 'https' else 80)
        if u.scheme == 'https': raise ComfyError('websocket 不支援 https（本機 ComfyUI 用 http）')
        self.s = socket.create_connection((host, port), timeout=timeout); key = base64.b64encode(os.urandom(16)).decode()
        req = (f'GET /ws?clientId={urllib.parse.quote(client_id)} HTTP/1.1\r\nHost: {host}:{port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n'
               f'Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\nUser-Agent: ComfyRemote\r\n\r\n')
        self.s.sendall(req.encode()); hdr = b''
        while b'\r\n\r\n' not in hdr:
            c = self.s.recv(4096)
            if not c: raise ComfyError('websocket 握手失敗')
            hdr += c
            if len(hdr) > 65536: raise ComfyError('websocket 握手太長')
        head, _, self.buf = hdr.partition(b'\r\n\r\n')
        if b' 101 ' not in head.split(b'\r\n')[0]: raise ComfyError('websocket 握手被拒：' + head.split(b'\r\n')[0].decode('latin-1'))

    def _read(self, n):
        while len(self.buf) < n:
            c = self.s.recv(max(65536, n - len(self.buf)))
            if not c: raise ConnectionError('websocket 斷了')
            self.buf += c
        d, self.buf = self.buf[:n], self.buf[n:]; return d

    def _send(self, op, payload=b''):
        mask = os.urandom(4); n = len(payload)
        h = bytes([0x80 | op]) + (bytes([0x80 | n]) if n < 126 else bytes([0x80 | 126]) + struct.pack('>H', n))
        self.s.sendall(h + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))

    def recv(self, timeout=1.0):
        """回傳 dict（文字訊息）、'' （二進位預覽，忽略）、None（逾時）。斷線丟 ConnectionError."""
        self.s.settimeout(timeout)
        try: h = self._read(2)
        except socket.timeout: return None
        self.s.settimeout(30); op = h[0] & 0x0f; n = h[1] & 0x7f; masked = h[1] & 0x80
        if n == 126: n = struct.unpack('>H', self._read(2))[0]
        elif n == 127: n = struct.unpack('>Q', self._read(8))[0]
        m = self._read(4) if masked else b''; p = self._read(n)
        if masked: p = bytes(b ^ m[i % 4] for i, b in enumerate(p))
        if op == 9: self._send(10, p); return ''
        if op == 8: raise ConnectionError('websocket 關了')
        if op == 1:
            try: return json.loads(p.decode('utf-8'))
            except Exception: return ''
        if op == 2 and len(p) > 8 and struct.unpack('>I', p[:4])[0] == 1 and p[8:11] in (b'\xff\xd8\xff', b'\x89PN'):   # V0.2.86 ComfyUI 算圖中的預覽圖（JPEG／PNG）
            return {'type': '_preview', 'data': {'img': p[8:]}}
        return ''

    def close(self):
        try: self._send(8)
        except Exception: pass
        try: self.s.close()
        except Exception: pass


# ================================================================ 流程：一般格式 → API 格式
def is_ui_format(wf): return isinstance(wf, dict) and isinstance(wf.get('nodes'), list) and 'links' in wf


def is_api_format(wf):
    return isinstance(wf, dict) and bool(wf) and all(isinstance(v, dict) and 'class_type' in v and 'inputs' in v for v in wf.values())


def load_workflow(data):
    """bytes／str／dict → dict；檢查是不是 ComfyUI 的流程."""
    wf = data
    if isinstance(data, (bytes, bytearray)): data = data.decode('utf-8-sig')
    if isinstance(data, str): wf = json.loads(data)
    if isinstance(wf, dict) and isinstance(wf.get('prompt'), dict) and is_api_format(wf['prompt']): wf = wf['prompt']
    if is_ui_format(wf):
        if (wf.get('definitions') or {}).get('subgraphs'): wf = flatten_subgraphs(wf)        # 新版官方範本多半包成子圖：展開成一般節點
        return wf
    if is_api_format(wf): return wf
    raise ComfyError('看不懂這個檔：不是 ComfyUI 的流程 JSON')


def _lnk(L):
    """連線（list 或 dict）→ [id, 起點節點, 起點槽, 終點節點, 終點槽, 型別]."""
    if isinstance(L, dict): return [L.get('id'), L.get('origin_id'), int(L.get('origin_slot') or 0), L.get('target_id'), int(L.get('target_slot') or 0), L.get('type')]
    L = list(L) + [None] * 6; return [L[0], L[1], int(L[2] or 0), L[3], int(L[4] or 0), L[5]]


def flatten_subgraphs(wf):
    """把子圖（definitions.subgraphs）展開成一般節點，回傳新的流程（一般格式、沒有子圖）。
    子圖的「輸入」：外面有接線 → 接到裡面；沒接線但有欄位值 → 用外面那顆子圖節點上的值蓋掉裡面的值；子圖的「輸出」→ 外面接它的線改接到裡面真正的來源。
    子圖節點被略過／停用 → 裡面的節點也一樣。子圖裡面還有子圖：一層一層展開."""
    wf = copy.deepcopy(wf); SG = {str(g.get('id')): g for g in (wf.get('definitions') or {}).get('subgraphs') or []}
    nodes = list(wf.get('nodes') or []); links = {}
    for L in wf.get('links') or []:
        x = _lnk(L); links[x[0]] = x
    ids = [int(n['id']) for n in nodes if str(n.get('id')).lstrip('-').isdigit()] + [0]
    nid = [max(ids) + 1]; lid = [max([int(k) for k in links if str(k).lstrip('-').isdigit()] + [0]) + 1]
    def new_link(o, os_, t, ts, typ):
        k = lid[0]; lid[0] += 1; links[k] = [k, o, os_, t, ts, typ]; return k
    for _round in range(20):
        inst = next((n for n in nodes if str(n.get('type')) in SG), None)
        if inst is None: break
        g = SG[str(inst['type'])]; I = inst['id']; mode = inst.get('mode', 0)
        idmap = {}; inner = []
        for n in g.get('nodes') or []:
            m = copy.deepcopy(n); idmap[n['id']] = nid[0]; m['id'] = nid[0]; nid[0] += 1
            if mode in (2, 4) and not m.get('mode'): m['mode'] = mode
            for i in m.get('inputs') or []: i['link'] = None
            for o in m.get('outputs') or []: o['links'] = []
            inner.append(m)
        byid = {m['id']: m for m in inner}
        def tin(t, ts):
            m = byid.get(idmap.get(t)); ins = (m or {}).get('inputs') or []
            return (m, ins[ts]) if ts < len(ins) else (m, None)
        out_src = {}; in_tgt = {}
        for L in g.get('links') or []:
            _k, o, os_, t, ts, typ = _lnk(L)
            if t == -20: out_src[ts] = (o, os_)
            elif o == -10: in_tgt.setdefault(os_, []).append((t, ts))
            elif o in idmap and t in idmap:
                m, inp = tin(t, ts)
                if inp is not None: inp['link'] = new_link(idmap[o], os_, idmap[t], ts, typ)
        # 子圖節點自己的輸入：照順序對到子圖的輸入（名字對得上就用名字）
        gin = g.get('inputs') or []; iins = inst.get('inputs') or []
        wvals = inst.get('widgets_values') if isinstance(inst.get('widgets_values'), list) else []
        # 外面子圖節點的 widgets_values ＝ 子圖「欄位型」輸入照子圖輸入的順序排（不是照外面節點列出來的那幾個）
        def _is_w(k):
            if str((gin[k] if k < len(gin) else {}).get('type')) in WIDGET_TYPES: return True
            return any(isinstance((tin(t, ts)[1] or {}).get('widget'), dict) for t, ts in in_tgt.get(k, []))
        wpos = {}
        for k in range(len(gin)):
            if _is_w(k): wpos[k] = len(wpos)
        def inst_input(k):
            nm = gin[k].get('name') if k < len(gin) else None
            if nm: return next((x for x in iins if x.get('name') == nm), None)       # 照名字對（外面節點只列出部分輸入，不能照位置）
            return iins[k] if k < len(iins) else None
        outer_src = {}
        for k in range(max(len(gin), len(iins))):
            x = inst_input(k); src = None
            if x is not None and x.get('link') is not None and x['link'] in links: src = (links[x['link']][1], links[x['link']][2])
            outer_src[k] = src
            lab = (x or {}).get('label') or (gin[k] if k < len(gin) else {}).get('label')
            for t, ts in in_tgt.get(k, []):
                m, inp = tin(t, ts)
                if inp is None: continue
                if src is not None: inp['link'] = new_link(src[0], src[1], m['id'], ts, inp.get('type'))
                elif k in wpos and wpos[k] < len(wvals) and isinstance(inp.get('widget'), dict):
                    m.setdefault('_wset', {})[inp['widget'].get('name') or inp.get('name')] = wvals[wpos[k]]   # 外面子圖節點上的值 → 蓋掉裡面那個欄位（照名字）
                if lab and str(m.get('type', '')).startswith('Primitive') and not m.get('title'): m['title'] = lab
        # 外面接「子圖輸出」的線 → 改從裡面真正的來源出來
        for k, L in list(links.items()):
            if L[3] == I: links.pop(k); continue
            if L[1] == I:
                o = out_src.get(L[2])
                if o is None: links.pop(k); continue
                if o[0] == -10: src = outer_src.get(o[1])
                else: src = (idmap.get(o[0]), o[1]) if o[0] in idmap else None
                if src is None or src[0] is None: links.pop(k); continue
                L[1], L[2] = src[0], src[1]
        nodes = [n for n in nodes if n is not inst] + inner
    # 重新整理每個節點 inputs／outputs 上的線編號
    for n in nodes:
        for o in n.get('outputs') or []: o['links'] = []
    by = {n['id']: n for n in nodes}
    for n in nodes:
        for i in n.get('inputs') or []:
            if i.get('link') is not None and i['link'] not in links: i['link'] = None
    for k, L in links.items():
        tn = by.get(L[3]); sn = by.get(L[1])
        if tn is None or sn is None: continue
        ins = tn.get('inputs') or []
        if L[4] < len(ins) and ins[L[4]].get('link') in (None, k): ins[L[4]]['link'] = k
        outs = sn.get('outputs') or []
        if L[2] < len(outs): outs[L[2]].setdefault('links', []).append(k)
    used = {i.get('link') for n in nodes for i in n.get('inputs') or [] if i.get('link') is not None}
    wf['nodes'] = nodes; wf['links'] = [L for k, L in links.items() if k in used and L[1] in by and L[3] in by]
    wf.pop('definitions', None); wf.setdefault('extra', {})['flattened_subgraphs'] = True
    return wf


def _info_widgets(info, prefix=''):
    """ComfyUI /object_info 的定義 → 存檔裡 widgets_values 的順序：[(名字, 型別, 動態選項)]。
    COMFY_DYNAMICCOMBO_V3（動態下拉）型別記成 DYN，選項底下的欄位等讀到值再接著排；COMFY_AUTOGROW_V3 是接線用的，不算."""
    order = info.get('input_order') or {}; I = info.get('input') or {}; out = []
    for sec in ('required', 'optional'):
        D = I.get(sec) or {}
        for k in (order.get(sec) or list(D.keys())) if not prefix else list(D.keys()):
            spec = D.get(k)
            if not isinstance(spec, (list, tuple)) or not spec: continue
            typ = spec[0]; opts = spec[1] if len(spec) > 1 and isinstance(spec[1], dict) else {}
            if opts.get('forceInput') or opts.get('rawLink'): continue
            if typ == 'COMFY_DYNAMICCOMBO_V3': out.append((prefix + k, 'DYN', opts.get('options') or []))
            elif isinstance(typ, list): out.append((prefix + k, 'COMBO', None))
            elif typ in WIDGET_TYPES: out.append((prefix + k, typ, None))
    return out


def ui_to_api(ui, get_info=None):
    """ComfyUI 一般存檔（nodes／links）→ API 格式。
    widget 的名字優先用節點自己 inputs 裡的 widget 標記（新版 ComfyUI 存檔都有）；沒有才問 ComfyUI 的 /object_info（get_info(類別)）。"""
    nodes = {str(n['id']): n for n in ui.get('nodes') or []}
    links = {}
    for L in ui.get('links') or []:
        if isinstance(L, dict): links[L.get('id')] = (str(L.get('origin_id')), int(L.get('origin_slot') or 0), L.get('type'))
        elif isinstance(L, list) and len(L) >= 5: links[L[0]] = (str(L[1]), int(L[2] or 0), L[5] if len(L) > 5 else None)
    setnodes = {}
    for n in nodes.values():
        if n.get('type') == 'SetNode' and n.get('widgets_values'): setnodes[str(n['widgets_values'][0])] = n

    def resolve(link_id, depth=0):
        """沿著 Reroute／略過的節點／Set-Get 找到真正的來源 (節點, 輸出槽)；PrimitiveNode → None（用目標節點自己的值）."""
        if link_id is None or link_id not in links or depth > 40: return None
        src, slot, typ = links[link_id]; n = nodes.get(src)
        if n is None: return None
        t = n.get('type'); mode = n.get('mode', 0)
        if t == 'PrimitiveNode': return None
        if t == 'Reroute':
            ins = n.get('inputs') or []
            return resolve(ins[0].get('link') if ins else None, depth + 1)
        if t == 'GetNode':
            sn = setnodes.get(str((n.get('widgets_values') or [''])[0]))
            ins = (sn or {}).get('inputs') or []
            return resolve(ins[0].get('link') if ins else None, depth + 1)
        if t == 'SetNode':
            ins = n.get('inputs') or []
            return resolve(ins[0].get('link') if ins else None, depth + 1)
        if mode == 4:                                                       # 略過（bypass）：找同型別的輸入接過去
            outs = n.get('outputs') or []; ot = outs[slot].get('type') if slot < len(outs) else typ
            for i in n.get('inputs') or []:
                if i.get('link') is not None and (i.get('type') == ot or ot in (None, '*')): return resolve(i['link'], depth + 1)
            return None
        if mode == 2: return None                                           # 停用（mute）
        return (src, slot)

    api = {}
    for nid, n in nodes.items():
        t = n.get('type')
        if t in VIRTUAL or n.get('mode', 0) in (2, 4): continue
        wv = n.get('widgets_values'); inputs = {}; missing = False
        winputs = [i for i in n.get('inputs') or [] if isinstance(i.get('widget'), dict)]
        if isinstance(wv, dict):
            inputs.update({k: v for k, v in wv.items() if not isinstance(v, dict)})
        elif isinstance(wv, list) and wv:
            names = [(i['widget'].get('name') or i['name'], i.get('type'), None) for i in winputs]
            info_names = None
            if get_info is not None:
                info = get_info(t)
                if info is None: missing = not winputs
                else: info_names = _info_widgets(info)
            # 新版存檔只幫「拉出去／子圖露出來」的欄位做標記：標記不齊（比值少）就照 ComfyUI 的定義排
            if info_names is not None and (not names or len(names) < len(info_names) or any(x[1] == 'DYN' for x in info_names)): names = info_names
            q = list(names); i = 0
            while q and i < len(wv):
                k, typ, extra = q.pop(0)
                inputs[k] = wv[i]; i += 1
                if typ == 'DYN':                                            # 動態下拉（例如「縮放方式」選了之後才有的欄位）：接著排選到的那個選項底下的欄位
                    opt = next((o for o in extra or [] if isinstance(o, dict) and o.get('key') == inputs[k]), None)
                    if opt: q = _info_widgets({'input': opt.get('inputs') or {}}, prefix=k + '.') + q
                if typ in ('INT', 'COMBO') and i < len(wv) and isinstance(wv[i], str) and wv[i] in CTRL_VALUES and (typ == 'INT' or k in ('seed', 'noise_seed')): i += 1
        if isinstance(n.get('_wset'), dict):                               # 子圖外面那顆節點上的值（展開時記下來的）
            for k, v in n['_wset'].items(): inputs[k] = v
        for inp in n.get('inputs') or []:
            if inp.get('link') is None: continue
            r = resolve(inp['link'])
            nm = (inp.get('widget') or {}).get('name') or inp.get('name')
            if r is None: continue
            inputs[nm] = [r[0], r[1]]
        api[nid] = {'class_type': t, 'inputs': inputs, '_meta': {'title': n.get('title') or t}}
        if missing: api[nid]['_missing'] = True
    for v in api.values():                                                  # 指到被丟掉節點的線拿掉
        for k in [k for k, x in v['inputs'].items() if is_link(x) and str(x[0]) not in api]: v['inputs'].pop(k)
    return api


# ================================================================ 分析＋準備送出
def _nid_key(k):
    try: return (0, int(k))
    except Exception: return (1, str(k))


VIDEO_LOADERS = {'LoadVideo': 'file', 'VHS_LoadVideo': 'video', 'VHS_LoadVideoFFmpeg': 'video'}   # 讀影片節點 → 放檔名的欄位


def _is_image_loader(cls):
    c = str(cls).lower().replace(' ', '').replace('_', '')
    return ('loadimage' in c) and 'mask' not in c and 'model' not in c


def _media_kind(cls):
    if cls in VIDEO_LOADERS: return 'video'
    return 'image' if _is_image_loader(cls) else None


def _upstream_text(api, link, avoid=None, depth=6, prefer='positive'):
    """從 KSampler／SamplerCustom 的 positive／negative 往上找，第一個有文字欄位的節點 → (節點, 欄位名)。
    中間經過的節點有 positive 和 negative 兩個入口時（例如 WanAnimate2ToVideo），只走同一邊（prefer）."""
    other = 'negative' if prefer == 'positive' else 'positive'
    seen = set(); q = [(str(link[0]), 0)]
    while q:
        nid, d = q.pop(0)
        if nid in seen or nid not in api or d > depth: continue
        seen.add(nid); n = api[nid]; ins = n.get('inputs') or {}
        if 'zeroout' in n.get('class_type', '').lower(): return None
        for k in TEXT_KEYS:
            if k in ins and (isinstance(ins[k], str) or is_link(ins[k]) and k not in ('positive', 'negative')) and 'Loader' not in n['class_type']:   # positive 接線＝條件，不是文字
                if nid != avoid: return (nid, k)
                return None
        ks = sorted([k for k in ins.keys() if k != other and not k.startswith(other + '_')],
                    key=lambda k: (0 if k == prefer else 1 if 'cond' in k else 2 if prefer in k else 3, k))
        if prefer in ins or other in ins: ks = [k for k in ks if k == prefer or 'cond' in k]   # 有正負兩邊的節點：只沿著同一邊往上
        for k in ks:
            if is_link(ins[k]): q.append((str(ins[k][0]), d + 1))
    return None


def analyze(api):
    """找出：讀圖節點、提示詞欄位（正／負）、種子、輸出節點."""
    keys = sorted(api.keys(), key=_nid_key)
    imgs = [k for k in keys if _media_kind(api[k].get('class_type'))]               # 讀圖、讀影片節點（照編號：圖一、圖二…）
    pos = neg = None
    for k in keys:
        ins = api[k].get('inputs') or {}
        if is_link(ins.get('positive')):
            pos = pos or _upstream_text(api, ins['positive'])
            if is_link(ins.get('negative')) and not neg: neg = _upstream_text(api, ins['negative'], avoid=pos[0] if pos else None, prefer='negative')
    if pos is None:                                                        # 沒有 KSampler：第一個有文字欄位的編碼節點
        for k in keys:
            c = api[k].get('class_type', ''); ins = api[k].get('inputs') or {}
            if 'Encode' in c or 'Text' in c:
                for t in TEXT_KEYS:
                    if t in ins and (isinstance(ins[t], str) or is_link(ins[t]) and t not in ('positive', 'negative')): pos = (k, t); break
            if pos: break
    if pos is None:                                                        # 還是找不到（新模型自己的提示詞節點、欄位名不一樣）：挑最長的一段「文字描述」
        best = 0
        for k in keys:
            c = str(api[k].get('class_type', '')); ins = api[k].get('inputs') or {}
            if c in STD_OUTPUTS or 'load' in c.lower() or 'save' in c.lower(): continue
            for t, v in ins.items():
                if t in AUDIO_FIELDS or t in ('expression', 'filename_prefix') or not isinstance(v, str) or v.lower().endswith(MODEL_EXT) or '/' in v[:30] and ' ' not in v[:30]: continue
                if t.endswith(('_type', '_method', 'method', 'mode', 'format', 'codec')) or (v.isascii() and len(v.split()) < 4 and t not in PROMPT_HINT and t not in TEXT_KEYS): continue   # 下拉選項（例如「scale by multiplier」）不是提示詞
                sc = len(v) + (500 if t in PROMPT_HINT else 300 if t in TEXT_KEYS else 0)
                if (' ' in v.strip() or '\n' in v or t in PROMPT_HINT or t in TEXT_KEYS) and sc > best: best = sc; pos = (k, t)
    seeds = [(k, s) for k in keys for s in ('seed', 'noise_seed') if isinstance((api[k].get('inputs') or {}).get(s), int)]
    outs = [k for k in keys if api[k].get('class_type') in STD_OUTPUTS]
    if any(api[k].get('class_type') != 'PreviewImage' for k in outs): outs = [k for k in outs if api[k].get('class_type') != 'PreviewImage']   # 有存檔節點：預覽（例如骨架圖）不算結果
    return {'image': imgs, 'kinds': [_media_kind(api[k].get('class_type')) for k in imgs], 'pos': pos, 'neg': neg, 'seeds': seeds, 'outputs': outs}


def prune(api, outs):
    """只留輸出節點用得到的節點（像寫到別的資料夾的存檔、顯示數字的節點、批次用的計數器都拿掉）."""
    if not outs: return api
    keep = set(); st = list(outs)
    while st:
        k = str(st.pop())
        if k in keep or k not in api: continue
        keep.add(k)
        for v in (api[k].get('inputs') or {}).values():
            if is_link(v): st.append(str(v[0]))
    return {k: v for k, v in api.items() if k in keep}


def img_slots(api, A=None):
    """每個讀圖節點的名字（給畫面當「圖一：場景」「圖二：人物」這種標題）."""
    A = A or analyze(api); out = []
    for i, k in enumerate(A['image']):
        t = str(((api.get(k) or {}).get('_meta') or {}).get('title') or '')
        out.append(t if t and t not in ('LoadImage', 'Load Image', 'Load Image Batch') and not t.startswith('📱') else f'圖{"一二三四五六"[i] if i < 6 else i + 1}')
    return out


def summary(api):
    A = analyze(api); cls = lambda k: api.get(k, {}).get('class_type', '?')
    return {'need_img': bool(A['image']), 'n_img': len(A['image']), 'slots': img_slots(api, A), 'kinds': A['kinds'], 'video_out': any(v.get('class_type') in ('SaveVideo', 'VHS_VideoCombine', 'SaveWEBM') for v in api.values()),
            'segmented': any(v.get('class_type') == 'WanAnimate2ToVideo' for v in api.values()), 'img_node': (f'{A["image"][0]} {cls(A["image"][0])}' if A['image'] else ''),
            'pos': (f'{A["pos"][0]} {cls(A["pos"][0])}.{A["pos"][1]}' if A['pos'] else ''), 'neg': (f'{A["neg"][0]} {cls(A["neg"][0])}.{A["neg"][1]}' if A['neg'] else ''),
            'seeds': len(A['seeds']), 'outputs': [f'{k} {cls(k)}' for k in A['outputs']], 'nodes': len(api)}


def _build(wf, image_name='', prompt='', negative='', get_info=None, need_image=True):
    """一般格式→API、換讀圖節點、填提示詞、只留輸出用得到的節點。回傳 (api, analyze 結果, 說明)。
    image_name：一張（字串）或好幾張（清單）。好幾個讀圖節點時照節點編號由小到大：第 1 張給第一個（圖一）、第 2 張給第二個（圖二）…"""
    api = ui_to_api(wf, get_info) if is_ui_format(wf) else json.loads(json.dumps(wf))
    A = analyze(api); notes = []
    imgs = [x for x in (image_name if isinstance(image_name, (list, tuple)) else [image_name]) if x]
    if A['image']:
        if need_image and len(imgs) < len(A['image']):
            raise ComfyError('這個流程需要一張照片' if len(A['image']) == 1 else f'這個流程需要 {len(A["image"])} 張照片（' + '、'.join(img_slots(api, A)) + '）')
        for i, k in enumerate(A['image']):
            n = api[k]; nm = imgs[i] if i < len(imgs) else ''
            vf = VIDEO_LOADERS.get(n.get('class_type'))
            if vf:                                                          # 讀影片：只換檔名
                if nm: n['inputs'][vf] = nm
                continue
            if n.get('class_type') != 'LoadImage':
                notes.append(f'讀圖節點 {k}（{n.get("class_type")}）換成你的照片')
                api[k] = {'class_type': 'LoadImage', 'inputs': {'image': nm or 'x.png'}, '_meta': {'title': (n.get('_meta') or {}).get('title') or '📱 照片'}}
            else: n['inputs']['image'] = nm or n['inputs'].get('image')
    elif imgs: notes.append('這個流程沒有讀圖節點，照片沒用到')
    if A['pos']:
        P = api[A['pos'][0]]['inputs']; main = prompt
        if any(f in P for f in AUDIO_FIELDS) and prompt.strip():               # H3 這種分欄位的提示詞：「overall_soundscape: …」「non_diegetic_music: …」放到自己的欄位，沒寫就清空（不要留範本的聲音描述）
            got = {}; keep = []
            for ln in prompt.splitlines():
                m = re.match(r'\s*(overall_soundscape|non_diegetic_music)\s*[:：]\s*(.*)$', ln, re.I)
                if m: got[m.group(1).lower()] = m.group(2).strip()
                else: keep.append(ln)
            main = '\n'.join(keep).strip()
            for f in AUDIO_FIELDS:
                if f in P and not is_link(P[f]): P[f] = got.get(f, '')
        P[A['pos'][1]] = main if (prompt.strip() or not need_image) else P[A['pos'][1]]
    elif prompt.strip(): notes.append('找不到提示詞節點，提示詞沒用到')
    if A['neg'] and (negative.strip() or not need_image): api[A['neg'][0]]['inputs'][A['neg'][1]] = negative
    api = prune(api, A['outputs'])
    return api, A, notes


def apply_params(api, params):
    """params＝{'節點.欄位': 值}：只改流程裡本來就是「值」的欄位（接線的不動）."""
    n = 0
    for key, v in (params or {}).items():
        nid, _, name = str(key).partition('.')
        ins = (api.get(nid) or {}).get('inputs')
        if ins is None or name not in ins or is_link(ins[name]): continue
        ins[name] = v; n += 1
    return n


def prepare(wf, image_name='', prompt='', negative='', seed=-1, get_info=None, params=None):
    """回傳 (要送的 API 流程, 說明)。wf＝一般格式或 API 格式（不會改到原本的）."""
    api, A, notes = _build(wf, image_name, prompt, negative, get_info)
    if params: apply_params(api, params)
    sd = int(seed) if seed is not None and int(seed) >= 0 else random.randint(1, 2 ** 50)
    for k, s in A['seeds']:
        if s in (api.get(k, {}).get('inputs') or {}) and not is_link(api[k]['inputs'][s]): api[k]['inputs'][s] = sd
    miss = sorted({v['class_type'] for v in api.values() if v.get('_missing')})
    if miss: raise ComfyError('ComfyUI 沒有這些節點（缺自訂節點？）：' + '、'.join(miss))
    for v in api.values(): v.pop('_meta', None); v.pop('_missing', None)
    return api, {'seed': sd, 'notes': notes}


# ================================================================ 可調參數（流程裡所有「值」的欄位：下拉選單、數字、開關…）
LABEL = {'scale_to_length': '輸出邊長（像素）', 'megapixels': '輸出百萬像素', 'width': '寬', 'height': '高', 'steps': '步數', 'cfg': 'CFG', 'denoise': '重繪強度',
         'sampler_name': '取樣器', 'scheduler': '排程', 'unet_name': '主模型', 'ckpt_name': '模型', 'clip_name': '文字模型', 'clip_name1': '文字模型 1', 'clip_name2': '文字模型 2',
         'vae_name': 'VAE', 'lora_name': 'LoRA', 'strength_model': 'LoRA 強度', 'strength_clip': 'LoRA 文字強度', 'weight_dtype': '精度', 'batch_size': '一次幾張',
         'scale_to_side': '以哪一邊為準', 'aspect_ratio': '比例', 'fit': '裁切方式', 'method': '縮放方法', 'upscale_method': '縮放方法', 'filename_prefix': '檔名開頭'}
HIDE_INPUTS = {('WanAnimate2ToVideo', 'video_frame_offset'), ('WanAnimate2ToVideo', 'batch_size')}   # 程式自己管的（分段接續），不給改
MAIN_EXTRA = {('WanAnimate2ToVideo', 'length'): '每段幾格（81≈3.4 秒）', ('WanAnimate2ToVideo', 'pose_strength'): '動作跟隨強度',
              ('WanAnimate2ToVideo', 'reference_image_strength'): '像主角照片的強度', ('Video Slice', 'duration'): '只用影片前幾秒（0＝整支）',
              ('Video Slice', 'start_time'): '從影片第幾秒開始'}
MAIN_TITLE = {'duration': '影片長度（秒，最長 15）', 'float (duration)': '影片長度（秒，最長 15）', 'turbo_mode': 'Turbo 加速（少很多步，要 turbo LoRA）',
              'boolean (enable lightning lora)': 'Turbo 加速（少很多步，要 turbo LoRA）', 'turbo_steps': 'Turbo 步數', 'int (lightning lora)': 'Turbo 步數',
              'int (full)': '一般步數（沒開 Turbo 時）', 'turbo_model_strength': 'Turbo LoRA 強度', 'enable lightning lora?': 'Lightning 加速（少很多步）'}     # 子圖露出來的 Primitive 節點（照標題）
MAIN_EXTRA.update({('ResolutionSelector', 'aspect_ratio'): '畫面比例', ('MiniMaxH3FunControlNetApply', 'strength'): '跟原影片動作的強度',
                   ('MiniMaxH3ReferenceToVideo', 'ref_image_size'): '參考圖精細度（match 快／max 像）',
                   ('TextEncodeQwenImage21', 'resolution'): '照片縮到約幾×幾（越小越快，0＝原尺寸）', ('ReferenceMultiLatent', 'resolution.megapixels'): '照片縮到幾百萬像素（越小越快）',
                   ('ResizeImageMaskNode', 'resize_type.megapixels'): '照片縮到幾百萬像素（越小越快）'})
RES_KEYS = {'scale_to_length', 'megapixels', 'width', 'height', 'longer_edge', 'shorter_edge', 'resolution', 'size', 'max_size', 'target_size'}
SAMPLER_KEYS = ('steps', 'cfg', 'denoise', 'sampler_name', 'scheduler')
MODEL_KEYS = {'ckpt_name', 'unet_name', 'clip_name', 'clip_name1', 'clip_name2', 'clip_name3', 'vae_name', 'lora_name', 'weight_dtype', 'strength_model', 'strength_clip',
              'model_name', 'control_net_name', 'upscale_model', 'style_model_name', 'clip_vision'}
FLOAT_NAMES = {'cfg', 'denoise', 'megapixels', 'guidance', 'shift', 'reserved', 'strength', 'weight', 'scale_by', 'eta', 's_noise'}
RES_PRESETS = [512, 640, 768, 896, 960, 1024, 1152, 1280, 1408, 1536, 1792, 2048]
SAMPLERS = ['euler', 'euler_ancestral', 'heun', 'dpm_2', 'dpm_2_ancestral', 'lms', 'dpmpp_2s_ancestral', 'dpmpp_sde', 'dpmpp_2m', 'dpmpp_2m_sde', 'dpmpp_3m_sde', 'ddim', 'uni_pc', 'res_multistep', 'lcm']
SCHEDULERS = ['normal', 'karras', 'exponential', 'sgm_uniform', 'simple', 'ddim_uniform', 'beta', 'linear_quadratic', 'kl_optimal']


def _spec(info, name):
    """object_info 裡這個欄位的 (型別或選項清單, 選項)."""
    I = (info or {}).get('input') or {}
    for sec in ('required', 'optional'):
        sp = (I.get(sec) or {}).get(name)
        if isinstance(sp, (list, tuple)) and sp:
            return sp[0], (sp[1] if len(sp) > 1 and isinstance(sp[1], dict) else {})
    return None, {}


def tunables(wf, get_info=None):
    """流程裡可以調的東西 → [{'g': 分組名, 'open': 預設打開?, 'items': [{'id','label','type','value','choices','min','max','step'}]}]。
    常用（解析度、步數、CFG、取樣器…）打開；模型／LoRA、其他節點的設定收合。照片、提示詞、種子另外處理."""
    api, A, _n = _build(wf, '', '', '', get_info, need_image=False)
    skip = set(A['image']); hide = set(((wf.get('extra') or {}).get('cr') or {}).get('hide') or []) if isinstance(wf, dict) else set()
    skipf = {A['pos'], A['neg']} - {None}
    n_samp = sum(1 for v in api.values() if isinstance((v.get('inputs') or {}).get('steps'), int))
    main, models, groups = [], [], []
    for k in sorted(api.keys(), key=_nid_key):
        if k in skip: continue
        n = api[k]; cls = n.get('class_type', ''); title = (n.get('_meta') or {}).get('title') or cls
        info = None
        if get_info is not None:
            try: info = get_info(cls)
            except Exception: info = None
        tag = title if title == cls else f'{title}（{cls}）'
        items = []; is_samp = isinstance((n.get('inputs') or {}).get('steps'), int)
        for name, v in (n.get('inputs') or {}).items():
            if name in hide or is_link(v) or (k, name) in skipf or name in ('seed', 'noise_seed') or isinstance(v, (dict, list)) or v is None or (cls, name) in HIDE_INPUTS: continue
            typ, opts = _spec(info, name)
            it = {'id': f'{k}.{name}', 'label': LABEL.get(name, name), 'value': v, 'node': tag}
            ch = list(typ) if isinstance(typ, list) else (list(opts.get('options') or []) if typ == 'COMBO' else None)
            if ch is not None or typ == 'COMBO':
                it['type'] = 'choice'; it['choices'] = ch or [v]
            elif typ is None and name in ('sampler_name', 'scheduler') and isinstance(v, str):
                it['type'] = 'choice'; it['choices'] = list(dict.fromkeys([v] + (SAMPLERS if name == 'sampler_name' else SCHEDULERS)))
            elif isinstance(v, bool) or typ == 'BOOLEAN': it['type'] = 'bool'
            elif typ is None and isinstance(v, (int, float)) and (name in FLOAT_NAMES or name.startswith('strength') or name.endswith('_strength') or name.endswith('_percent')): it['type'] = 'float'
            elif typ is None and isinstance(v, str) and 'textencode' in cls.lower() and name in TEXT_KEYS: it['type'] = 'text'
            elif (isinstance(v, int) and typ in (None, 'INT')) or typ == 'INT': it['type'] = 'int'
            elif isinstance(v, (int, float)) or typ == 'FLOAT': it['type'] = 'float'
            else:
                if len(str(v)) > 300 or opts.get('multiline'):
                    if 'textencode' not in cls.lower(): continue
                    it['type'] = 'text'                                     # 其他的文字框（例如「動作描述」）：可以改，給大一點的框
                else: it['type'] = 'str'
            if cls == 'ResolutionSelector' and name == 'aspect_ratio' and it['type'] == 'choice' and any(x == 'image' for x in A['kinds']):
                it['choices'] = [MATCH_ASPECT] + [c for c in it['choices'] if c != MATCH_ASPECT]       # 有放照片的流程：可以選「跟原圖一樣」
            if it['type'] == 'choice' and v not in it['choices']: it['choices'] = [v] + it['choices']
            for o in ('min', 'max', 'step'):
                if isinstance(opts.get(o), (int, float)): it[o] = opts[o]
            low = cls.lower()
            if cls.startswith('Primitive') and title.lower() in MAIN_TITLE:
                it['label'] = MAIN_TITLE[title.lower()]; main.append(it)
            elif (cls, name) in MAIN_EXTRA:
                it['label'] = MAIN_EXTRA[(cls, name)]; main.append(it)
            elif name in RES_KEYS and it['type'] in ('int', 'float') and (name in ('scale_to_length', 'megapixels') or any(w in low for w in ('latent', 'scale', 'resize', 'size', 'tovideo'))):
                if it['type'] == 'int' and isinstance(v, int) and 64 <= v <= 8192: it['presets'] = sorted(set(RES_PRESETS + [v]))
                if name == 'scale_to_length' and n['inputs'].get('scale_to_side'): it['label'] = f'輸出邊長（{ {"longest": "長邊", "shortest": "短邊", "width": "寬", "height": "高"}.get(n["inputs"]["scale_to_side"], n["inputs"]["scale_to_side"]) }，像素）'
                if title != cls: it['label'] = f'{title} · ' + re.sub(r'（[^）]*）', '', it['label'])
                it['res'] = True; main.append(it)
            elif is_samp and name in SAMPLER_KEYS:
                if it['type'] == 'choice' and len(it['choices']) <= 1: it['choices'] = list(dict.fromkeys([v] + (SAMPLERS if name == 'sampler_name' else SCHEDULERS)))
                if name == 'denoise': it.setdefault('min', 0.0); it.setdefault('max', 1.0); it.setdefault('step', 0.05)
                if n_samp > 1: it['label'] = f'{it["label"]}（{title}）'
                main.append(it)
            elif name in MODEL_KEYS or 'loader' in low or 'lora' in low:
                if title != cls: it['label'] = f'{title} · {it["label"]}'
                models.append(it)
            else: items.append(it)
        if items: groups.append({'g': tag, 'open': False, 'items': items})
    main.append({'id': '_seed', 'label': '種子（空白＝每次隨機）', 'type': 'seed', 'value': None})
    out = [{'g': '常用', 'open': True, 'items': main}]
    if models: out.append({'g': '模型／LoRA', 'open': False, 'items': models})
    return out + groups


def cast_params(defs, given):
    """手機／電腦送來的參數 → 照型別轉好、不在選項裡的丟掉。回傳 (全部參數（含流程預設）, 種子)."""
    eff = {}; seed = -1; given = dict(given or {})
    for g in defs:
        for it in g['items']:
            if it['type'] == 'seed':
                v = given.get('_seed')
                try: seed = int(v) if v not in (None, '', -1, '-1') else -1
                except Exception: seed = -1
                continue
            v = given.get(it['id'], it['value'])
            try:
                if it['type'] == 'int': v = int(float(v))
                elif it['type'] == 'float': v = float(v)
                elif it['type'] == 'bool': v = v if isinstance(v, bool) else str(v).lower() in ('1', 'true', 'yes', 'on')
                elif it['type'] == 'choice' and v not in it['choices']: v = it['value']
                else: v = str(v) if it['type'] in ('str', 'text') else v
                if it['type'] in ('int', 'float'):
                    if 'min' in it: v = max(it['min'], v)
                    if 'max' in it: v = min(it['max'], v)
            except Exception: v = it['value']
            eff[it['id']] = v
    return eff, seed


MODEL_INPUTS = {'UNETLoader': ('unet_name', 'diffusion_models'), 'CheckpointLoaderSimple': ('ckpt_name', 'checkpoints'), 'VAELoader': ('vae_name', 'vae'),
                'CLIPLoader': ('clip_name', 'text_encoders'), 'CLIPVisionLoader': ('clip_name', 'clip_vision'), 'LoraLoaderModelOnly': ('lora_name', 'loras'),
                'LoraLoader': ('lora_name', 'loras'), 'DualCLIPLoader': ('clip_name1', 'text_encoders')}


MODEL_EXT = ('.safetensors', '.gguf', '.ckpt', '.pt', '.pth', '.bin', '.sft')


def _guess_folder(cls, inp):
    c = (str(cls) + ' ' + str(inp)).lower()
    for keys, f in ((('lora',), 'loras'), (('unet', 'diffusion', 'transformer'), 'diffusion_models'), (('clip_vision', 'clipvision'), 'clip_vision'),
                    (('text_encoder', 'clip', 'te_name', 'encoder'), 'text_encoders'), (('vae',), 'vae'), (('ckpt', 'checkpoint'), 'checkpoints'),
                    (('upscale',), 'upscale_models'), (('embedding',), 'embeddings')):
        if any(k in c for k in keys): return f
    return 'diffusion_models'


def required_models(wf, get_info=None):
    """流程用到的模型檔：[(節點類別, 欄位, 檔名, 資料夾)]（只算真的會跑到的節點）。認得的讀模型節點照表；
    不認得的（新模型的專用讀取節點）：類別名有 Load、欄位值是模型檔（.safetensors 等）就算."""
    api, _A, _n = _build(wf, '', '', '', get_info, need_image=False); out = []
    for v in api.values():
        cls = v.get('class_type'); ins = v.get('inputs') or {}; m = MODEL_INPUTS.get(cls)
        if m:
            f = ins.get(m[0])
            if isinstance(f, str) and f: out.append((cls, m[0], f, m[1]))
            continue
        if 'load' not in str(cls).lower(): continue
        for k, f in ins.items():
            if isinstance(f, str) and f.lower().endswith(MODEL_EXT): out.append((cls, k, f, _guess_folder(cls, k)))
    return out


def _exif_orient(b):
    """JPEG 的 EXIF 方向（1～8），沒有回 1."""
    try:
        i = 2
        while i < len(b) - 4:
            if b[i] != 0xff: return 1
            m = b[i + 1]; L = struct.unpack('>H', b[i + 2:i + 4])[0]
            if m == 0xe1 and b[i + 4:i + 10] == b'Exif\x00\x00':
                t = i + 10; e = '<' if b[t:t + 2] == b'II' else '>'
                off = struct.unpack(e + 'I', b[t + 4:t + 8])[0]; n = struct.unpack(e + 'H', b[t + off:t + off + 2])[0]
                for k in range(n):
                    q = t + off + 2 + 12 * k
                    if struct.unpack(e + 'H', b[q:q + 2])[0] == 0x0112: return struct.unpack(e + 'H', b[q + 8:q + 10])[0]
                return 1
            if m == 0xda: return 1
            i += 2 + L
    except Exception: pass
    return 1


def img_size_shown(data):
    """照片「看起來」的寬高（手機直拍的 JPEG 會用 EXIF 轉向，ComfyUI 讀的時候也會轉）."""
    w, h = img_size(data)
    b = bytes(data[:300000])
    if b[:2] == b'\xff\xd8' and _exif_orient(b) in (5, 6, 7, 8): w, h = h, w
    return w, h


MATCH_ASPECT = '📷 跟原圖一樣'


def match_aspect(api, w, h, only_marked=False):
    """「影片比例跟照片一樣」：接在「Resolution Selector」寬／高的線拿掉，改成照照片比例算的寬高（總像素照它的百萬像素、對齊 multiple）。回傳 (寬, 高) 或 None."""
    if not (w and h): return None
    got = None
    for k, v in list(api.items()):
        if v.get('class_type') != 'ResolutionSelector': continue
        ins = v.get('inputs') or {}
        if only_marked and ins.get('aspect_ratio') != MATCH_ASPECT: continue
        mp = float(ins.get('megapixels') or 0.4) if not is_link(ins.get('megapixels')) else 0.4
        mul = int(ins.get('multiple') or 32) if not is_link(ins.get('multiple')) else 32
        ar = w / h; W = max(mul, round((mp * 1e6 * ar) ** 0.5 / mul) * mul); H = max(mul, round((mp * 1e6 / ar) ** 0.5 / mul) * mul)
        for v2 in api.values():
            for nm, x in list((v2.get('inputs') or {}).items()):
                if is_link(x) and str(x[0]) == str(k): v2['inputs'][nm] = W if int(x[1]) == 0 else H
        got = (W, H)
    return got


def apply_mask(api, orig, mask, blur=10, cue=''):
    """V0.1.90 🖌 局部修改：每個 SaveImage 前面接「原圖＋模型結果＋遮罩」合成（全部是 ComfyUI 內建節點）.
    原圖當底（原本的解析度），模型結果縮放成原圖大小，只貼遮罩白色的地方；遮罩先模糊一點，邊緣比較自然。回傳改了幾個輸出."""
    outs = [k for k, v in api.items() if v.get('class_type') in ('SaveImage', 'PreviewImage') and isinstance((v.get('inputs') or {}).get('images'), list)]
    if not outs: return 0
    api['crm1'] = {'class_type': 'LoadImage', 'inputs': {'image': orig}}
    api['crm2'] = {'class_type': 'LoadImage', 'inputs': {'image': mask}}
    api['crm3'] = {'class_type': 'ImageBlur', 'inputs': {'image': ['crm2', 0], 'blur_radius': int(blur), 'sigma': max(1.0, blur / 2)}}
    api['crm4'] = {'class_type': 'ImageToMask', 'inputs': {'image': ['crm3', 0], 'channel': 'red'}}
    if cue in ('gray', 'red'):                                               # V0.2.64 讓模型「看得到」塗的位置：送進模型的照片先把那塊塗成灰色（要補背景）或紅色（要放東西）
        first = next((k for k, v in api.items() if v.get('class_type') == 'LoadImage' and (v.get('inputs') or {}).get('image') == orig and not str(k).startswith('crm')), None)
        if first:
            api['crm6'] = {'class_type': 'ImageToMask', 'inputs': {'image': ['crm2', 0], 'channel': 'red'}}
            api['crm7'] = {'class_type': 'EmptyImage', 'inputs': {'width': 64, 'height': 64, 'batch_size': 1, 'color': 0x808080 if cue == 'gray' else 0xFF0000}}
            api['crm8'] = {'class_type': 'ImageCompositeMasked', 'inputs': {'destination': [first, 0], 'source': ['crm7', 0], 'x': 0, 'y': 0, 'resize_source': True, 'mask': ['crm6', 0]}}
            for k, v in api.items():
                if str(k).startswith('crm'): continue
                for name, val in list((v.get('inputs') or {}).items()):
                    if isinstance(val, list) and len(val) == 2 and str(val[0]) == str(first) and val[1] == 0: v['inputs'][name] = ['crm8', 0]
    for i, k in enumerate(outs):
        n = f'crm5_{i}'
        api[n] = {'class_type': 'ImageCompositeMasked', 'inputs': {'destination': ['crm1', 0], 'source': api[k]['inputs']['images'], 'x': 0, 'y': 0, 'resize_source': True, 'mask': ['crm4', 0]}}
        api[k]['inputs']['images'] = [n, 0]
    return len(outs)


def img_size(data):
    """PNG／JPEG／WEBP 的寬高（只看檔頭，不用 PIL）。不認得回 (0, 0)."""
    try:
        b = bytes(data[:300000])
        if b[:8] == b'\x89PNG\r\n\x1a\n': return struct.unpack('>II', b[16:24])
        if b[:4] == b'RIFF' and b[8:12] == b'WEBP':
            c = b[12:16]
            if c == b'VP8X': return 1 + int.from_bytes(b[24:27], 'little'), 1 + int.from_bytes(b[27:30], 'little')
            if c == b'VP8 ': w, h = struct.unpack('<HH', b[26:30]); return w & 0x3fff, h & 0x3fff
            if c == b'VP8L': x = int.from_bytes(b[21:25], 'little'); return (x & 0x3fff) + 1, ((x >> 14) & 0x3fff) + 1
        if b[:2] == b'\xff\xd8':
            i = 2
            while i < len(b) - 9:
                if b[i] != 0xff: i += 1; continue
                m = b[i + 1]
                if m in (0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf):
                    h, w = struct.unpack('>HH', b[i + 5:i + 9]); return w, h
                if m in (0xd8, 0x01) or 0xd0 <= m <= 0xd7: i += 2; continue
                i += 2 + struct.unpack('>H', b[i + 2:i + 4])[0]
    except Exception: pass
    return 0, 0


def mem_hint(msg):
    """ComfyUI 記憶體不夠的錯誤 → 後面加上白話的處理方法."""
    m = str(msg or ''); low = m.lower()
    if 'defaultcpuallocator' in low or ('not enough memory' in low and 'cuda' not in low) or 'unable to allocate' in low or 'paging file' in low or '頁面檔' in m:
        return m + '　👉 電腦記憶體（RAM）不夠：Windows 加大「虛擬記憶體」（分頁檔，建議設 64GB 以上，放在 SSD），或把影片長度／解析度調小；跑之前把其他吃記憶體的程式關掉'
    if 'out of memory' in low or 'outofmemory' in low or 'allocation on device' in low:
        return m + '　👉 顯示卡記憶體不夠：把解析度（百萬像素）或影片長度調小，或 ComfyUI 加啟動參數 --lowvram（新版要再加 --disable-dynamic-vram）'
    return m


def output_files(hist):
    """history 裡的輸出檔：[(filename, subfolder, type)]，output 優先，沒有才拿 temp（預覽）."""
    F = []
    for _nid, o in (hist.get('outputs') or {}).items():
        for key in ('images', 'gifs', 'videos', 'animated'):
            for x in o.get(key) or []:
                if isinstance(x, dict) and x.get('filename'): F.append((x['filename'], x.get('subfolder', ''), x.get('type', 'output')))
    out = [f for f in F if f[2] == 'output']
    seen = set(); R = []
    for f in (out or F):
        if f not in seen: seen.add(f); R.append(f)
    return R
