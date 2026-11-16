"""假的 ComfyUI（只給 check.py 測試用，不會打包）：/system_stats、/upload/image、/prompt、/history、/view、/queue、/interrupt、/ws（真的 websocket）。
python tools/fake_comfy.py 18188  → 開在 127.0.0.1:18188。流程裡有 class_type 'FailNode' 的會回執行錯誤；step_sec 控制每一步多久。"""
import sys, json, time, uuid, base64, hashlib, struct, zlib, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlsplit, parse_qs

STATE = {'ws': {}, 'hist': {}, 'uploads': {}, 'prompts': [], 'step_sec': 0.15, 'interrupt': set(), 'running': None, 'lock': threading.Lock(),
         'mp4': b'', 'info': {}, 'templates': {}}   # mp4＝SaveVideo 回傳的影片；info＝/object_info 要回的（測缺模型）


def png(w=8, h=8, rgb=(200, 50, 90)):
    raw = b''.join(b'\x00' + bytes(rgb) * w for _ in range(h))
    def ch(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw)) + ch(b'IEND', b'')


def ws_send(cid, obj):
    s = STATE['ws'].get(cid)
    if not s: return
    p = json.dumps(obj).encode(); n = len(p)
    h = bytes([0x81]) + (bytes([n]) if n < 126 else bytes([126]) + struct.pack('>H', n))
    try: s.sendall(h + p)
    except OSError: STATE['ws'].pop(cid, None)
    # 也送一個二進位的「預覽」看用戶端會不會忽略
    pv = b'\x00\x00\x00\x01\x00\x00\x00\x01\xff\xd8\xff\xe0fakejpeg'
    try: s.sendall(bytes([0x82, 4]) + b'\x00\x00\x00\x01' + bytes([0x82, len(pv)]) + pv)
    except OSError: pass


def run_prompt(pid, prompt, cid):
    with STATE['lock']:
        STATE['running'] = pid
        ws_send(cid, {'type': 'execution_start', 'data': {'prompt_id': pid}})
        try:
            if any(v.get('class_type') == 'FailNode' for v in prompt.values()):
                ws_send(cid, {'type': 'execution_error', 'data': {'prompt_id': pid, 'node_type': 'FailNode', 'exception_message': 'boom'}})
                STATE['hist'][pid] = {'outputs': {}, 'status': {'status_str': 'error', 'completed': False, 'messages': [['execution_error', {'node_type': 'FailNode', 'exception_message': 'boom'}]]}}; return
            for nid in sorted(prompt, key=lambda k: 'Sampler' in str(prompt[k].get('class_type'))):   # 取樣節點最後（後面的步數時間算它的）
                ws_send(cid, {'type': 'executing', 'data': {'node': nid, 'prompt_id': pid}})
            for i in range(1, 5):
                if pid in STATE['interrupt']:
                    ws_send(cid, {'type': 'execution_interrupted', 'data': {'prompt_id': pid}})
                    STATE['hist'][pid] = {'outputs': {}, 'status': {'status_str': 'error', 'completed': False, 'messages': [['execution_interrupted', {}]]}}; return
                time.sleep(STATE['step_sec']); ws_send(cid, {'type': 'progress', 'data': {'value': i, 'max': 4, 'prompt_id': pid, 'node': '10'}})
            outs = {k: {'images': [{'filename': f'ComfyUI_{pid[:6]}_.png', 'subfolder': '', 'type': 'output'}]} for k, v in prompt.items() if v.get('class_type') in ('SaveImage', 'PreviewImage')}
            outs.update({k: {'images': [{'filename': f'anim_{pid[:6]}.mp4', 'subfolder': 'ComfyRemote', 'type': 'output'}], 'animated': [True]} for k, v in prompt.items() if v.get('class_type') == 'SaveVideo'})
            STATE['hist'][pid] = {'outputs': outs, 'status': {'status_str': 'success', 'completed': True, 'messages': []}}
            ws_send(cid, {'type': 'executing', 'data': {'node': None, 'prompt_id': pid}}); ws_send(cid, {'type': 'execution_success', 'data': {'prompt_id': pid}})
        finally: STATE['running'] = None


class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _j(self, obj, code=200):
        b = json.dumps(obj).encode(); self.send_response(code); self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        u = urlsplit(self.path); q = parse_qs(u.query)
        if u.path == '/ws':
            key = self.headers.get('Sec-WebSocket-Key', ''); acc = base64.b64encode(hashlib.sha1((key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest()).decode()
            self.wfile.write(f'HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: {acc}\r\n\r\n'.encode()); self.wfile.flush()
            cid = q.get('clientId', [''])[0]; STATE['ws'][cid] = self.connection
            ws_send(cid, {'type': 'status', 'data': {'status': {'exec_info': {'queue_remaining': 0}}, 'sid': cid}})
            try:
                while True:
                    d = self.connection.recv(1024)
                    if not d: break
            except OSError: pass
            STATE['ws'].pop(cid, None); self.close_connection = True; return
        if u.path.startswith('/templates/'):
            t = STATE['templates'].get(u.path[len('/templates/'):].replace('.json', ''))
            if t is None: self.send_response(404); self.end_headers(); return
            b = json.dumps(t).encode(); self.send_response(200); self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b); return
        if u.path == '/internal/folder_paths': return self._j(STATE.get('folders') or {})
        if u.path == '/system_stats': return self._j({'system': {'comfyui_version': '0.9.9-fake'}, 'devices': [{'name': 'Fake GPU', 'vram_total': 24e9, 'vram_free': 20e9}]})
        if u.path.startswith('/object_info/'):
            c = u.path.split('/')[-1]; return self._j({c: STATE['info'][c]} if c in STATE['info'] else {})
        if u.path.startswith('/history/'):
            pid = u.path.split('/')[-1]; h = STATE['hist'].get(pid); return self._j({pid: h} if h else {})
        if u.path == '/queue': return self._j({'queue_running': [[0, STATE['running'], {}, {}, []]] if STATE['running'] else [], 'queue_pending': []})
        if u.path == '/view' and q.get('filename', [''])[0].endswith('.mp4'):
            b = STATE['mp4']; self.send_response(200); self.send_header('Content-Type', 'video/mp4'); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b); return
        if u.path == '/view':
            b = png(); self.send_response(200); self.send_header('Content-Type', 'image/png'); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b); return
        self._j({'error': 'nf'}, 404)

    def do_POST(self):
        n = int(self.headers.get('Content-Length') or 0); body = self.rfile.read(n); u = urlsplit(self.path)
        if u.path == '/upload/image':
            i = body.find(b'filename="'); nm = body[i + 10:body.find(b'"', i + 10)].decode() if i >= 0 else 'x.png'; STATE['uploads'][nm] = len(body); return self._j({'name': nm, 'subfolder': '', 'type': 'input'})
        if u.path.startswith('/api/userdata/'):                              # V0.3.34 存工作流到使用者資料夾
            from urllib.parse import unquote, parse_qs
            nm = unquote(u.path[len('/api/userdata/'):]); ud = STATE.setdefault('userdata', {})
            if nm in ud and parse_qs(u.query).get('overwrite', ['true'])[0] == 'false': return self._j({'error': 'exists'}, 409)
            ud[nm] = body; return self._j({'path': nm})
        j = json.loads(body or b'{}')
        if u.path == '/prompt':
            p = j.get('prompt') or {}
            bad = [k for k, v in p.items() for x in v.get('inputs', {}).values() if isinstance(x, list) and len(x) == 2 and str(x[0]) not in p]
            if bad: return self._j({'error': {'type': 'prompt_outputs_failed_validation', 'message': 'bad link'}, 'node_errors': {bad[0]: {'class_type': '?', 'errors': [{'message': 'missing input', 'details': ''}]}}}, 400)
            pid = str(uuid.uuid4()); STATE['prompts'].append(p)
            threading.Thread(target=run_prompt, args=(pid, p, j.get('client_id', '')), daemon=True).start(); return self._j({'prompt_id': pid, 'number': len(STATE['prompts']), 'node_errors': {}})
        if u.path == '/interrupt':
            if STATE['running']: STATE['interrupt'].add(STATE['running'])
            return self._j({})
        if u.path == '/queue': return self._j({})
        self._j({'error': 'nf'}, 404)


def serve(port):
    s = ThreadingHTTPServer(('127.0.0.1', port), H); s.daemon_threads = True
    threading.Thread(target=s.serve_forever, daemon=True).start(); return s


if __name__ == '__main__':
    serve(int(sys.argv[1]) if len(sys.argv) > 1 else 18188); print('fake ComfyUI running'); threading.Event().wait()
