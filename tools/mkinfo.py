"""從 ComfyUI 原始碼（nodes.py、comfy_extras/*.py）用 AST 讀出各節點的輸入定義 → 假的 /object_info（測試用）。
用法：python tools/mkinfo.py <ComfyUI 資料夾> tools/testdata/object_info.json
只讀程式碼、不執行。抓不準的（下拉選項是函式算出來的）一律當成下拉選單（COMBO），選項給 ['?']."""
import ast, sys, json, pathlib

WT = {'Int': 'INT', 'Float': 'FLOAT', 'String': 'STRING', 'Boolean': 'BOOLEAN'}


ENUM = {}                                                                    # Class.NAME = "字串"（enum 常數）


def _const(n):
    if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and (n.value.id, n.attr) in ENUM: return ENUM[(n.value.id, n.attr)]
    try: return ast.literal_eval(n)
    except Exception: return None


def _enums(tree):
    for c in ast.walk(tree):
        if isinstance(c, ast.ClassDef):
            for a in c.body:
                if isinstance(a, ast.Assign) and isinstance(a.value, ast.Constant) and isinstance(a.value.value, str):
                    for t in a.targets:
                        if isinstance(t, ast.Name): ENUM[(c.name, t.id)] = a.value.value


def _kw(call, name):
    for k in call.keywords:
        if k.arg == name: return k.value
    return None


def _v3_input(call):
    """io.Int.Input("seed", ...) → (名字, spec, optional)。不是 .Input 回 None."""
    f = call.func
    if not (isinstance(f, ast.Attribute) and f.attr == 'Input' and isinstance(f.value, ast.Attribute)): return None
    typ = f.value.attr
    if not call.args: return None
    name = _const(call.args[0])
    if not isinstance(name, str): return None
    opt = bool(_const(_kw(call, 'optional')) or False)
    o = {}
    if _const(_kw(call, 'control_after_generate')): o['control_after_generate'] = True
    if _const(_kw(call, 'force_input')) or _const(_kw(call, 'socketless')) is False and False: o['forceInput'] = True
    if typ in WT:
        d = _kw(call, 'default'); dv = _const(d) if d is not None else None
        if dv is not None: o['default'] = dv
        return name, [WT[typ], o], opt
    if typ == 'Combo':
        ops = _kw(call, 'options'); L = _const(ops) if ops is not None else None
        return name, [L if isinstance(L, list) and L else ['?'], o], opt
    if typ == 'DynamicCombo':
        opts = []
        ol = _kw(call, 'options')
        for el in (ol.elts if isinstance(ol, (ast.List, ast.Tuple)) else []):
            if isinstance(el, ast.Call) and el.args:
                key = _const(el.args[0]); sub = {}
                ins = el.args[1] if len(el.args) > 1 else _kw(el, 'inputs')
                for s in (ins.elts if isinstance(ins, (ast.List, ast.Tuple)) else []):
                    r = _v3_input(s) if isinstance(s, ast.Call) else None
                    if r: sub[r[0]] = r[1]
                opts.append({'key': key, 'inputs': {'required': sub}})
        return name, ['COMFY_DYNAMICCOMBO_V3', {'options': opts}], opt
    if typ == 'Autogrow': return name, ['COMFY_AUTOGROW_V3', {}], opt
    return name, [typ.upper(), o], opt


def _v3(tree, out):
    for call in ast.walk(tree):
        if not (isinstance(call, ast.Call) and getattr(call.func, 'attr', '') == 'Schema'): continue
        nid = _const(_kw(call, 'node_id'))
        ins = _kw(call, 'inputs')
        if not isinstance(nid, str) or not isinstance(ins, (ast.List, ast.Tuple)): continue
        req, opt = {}, {}
        for el in ins.elts:
            r = _v3_input(el) if isinstance(el, ast.Call) else None
            if r: (opt if r[2] else req)[r[0]] = r[1]
        out[nid] = {'input': {'required': req, 'optional': opt}, 'input_order': {'required': list(req), 'optional': list(opt)}}


def _v1_spec(v):
    if not isinstance(v, ast.Tuple) or not v.elts: return None
    t = v.elts[0]; o = _const(v.elts[1]) if len(v.elts) > 1 else {}
    o = o if isinstance(o, dict) else {}
    tc = _const(t)
    if isinstance(tc, str): return [tc, o]
    if isinstance(tc, list): return [tc or ['?'], o]
    return [['?'], o]


def _v1(tree, out):
    classes = {}
    for c in ast.walk(tree):
        if not isinstance(c, ast.ClassDef): continue
        for f in c.body:
            if isinstance(f, ast.FunctionDef) and f.name == 'INPUT_TYPES':
                for r in ast.walk(f):
                    if isinstance(r, ast.Return) and isinstance(r.value, ast.Dict):
                        sec = {}
                        for k, v in zip(r.value.keys, r.value.values):
                            kk = _const(k)
                            if kk in ('required', 'optional') and isinstance(v, ast.Dict):
                                sec[kk] = {_const(a): _v1_spec(b) for a, b in zip(v.keys, v.values) if isinstance(_const(a), str) and _v1_spec(b)}
                        classes[c.name] = sec; break
    maps = {}
    for a in ast.walk(tree):
        if isinstance(a, ast.Assign) and any(getattr(t, 'id', '') == 'NODE_CLASS_MAPPINGS' for t in a.targets) and isinstance(a.value, ast.Dict):
            for k, v in zip(a.value.keys, a.value.values):
                if isinstance(_const(k), str) and isinstance(v, ast.Name): maps[_const(k)] = v.id
    for nid, cn in maps.items():
        if cn in classes:
            s = classes[cn]
            out[nid] = {'input': {'required': s.get('required', {}), 'optional': s.get('optional', {})},
                        'input_order': {'required': list(s.get('required', {})), 'optional': list(s.get('optional', {}))}}


def main(root, dst):
    root = pathlib.Path(root); out = {}
    for p in [root / 'nodes.py'] + sorted((root / 'comfy_extras').glob('*.py')):
        if not p.exists(): continue
        try: tree = ast.parse(p.read_text(encoding='utf-8'))
        except Exception as ex: print('略過', p.name, ex); continue
        _enums(tree); _v1(tree, out); _v3(tree, out)
    pathlib.Path(dst).write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding='utf-8')
    print(f'{len(out)} 個節點 → {dst}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
