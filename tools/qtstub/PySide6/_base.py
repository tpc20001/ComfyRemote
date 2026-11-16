"""Permissive Qt stand-in for smoke tests: any attribute/call works; subclassing works; enums OR together."""
import sys
CALLS = []
class _Meta(type):
    def __getattr__(cls, n):
        if n.startswith('__'): raise AttributeError(n)
        return _Any()
class _Any(metaclass=_Meta):
    def __init__(self, *a, **k): pass
    def __getattr__(self, n):
        if n.startswith('__'): raise AttributeError(n)
        return _Any()
    def __call__(self, *a, **k): return _Any()
    def __or__(self, o): return _Any()
    __ror__ = __and__ = __rand__ = __invert__ = __xor__ = __or__
    def __add__(self, o): return 0
    __radd__ = __sub__ = __rsub__ = __mul__ = __rmul__ = __truediv__ = __rtruediv__ = __add__
    def __iter__(self): return iter([])
    def __bool__(self): return False
    def __int__(self): return 0
    def __float__(self): return 0.0
    def __index__(self): return 0
    def __len__(self): return 0
    def __lt__(self, o): return False
    __gt__ = __le__ = __ge__ = __lt__
    def __eq__(self, o): return self is o
    def __hash__(self): return id(self)
    def __str__(self): return ''
    def __getitem__(self, k): return _Any()
    def __enter__(self): return self
    def __exit__(self, *a): return False
class Signal:
    def __init__(self, *a): self.slots = []
    def __set_name__(self, owner, name): self.name = name
    def __get__(self, obj, tp=None):
        if obj is None: return self
        b = obj.__dict__.get('_sig_' + self.name)
        if b is None: b = obj.__dict__['_sig_' + self.name] = _Bound()
        return b
class _Bound:
    def __init__(self): self.slots = []
    def connect(self, f, *a): self.slots.append(f)
    def disconnect(self, *a): self.slots = []
    def emit(self, *a):
        for f in list(self.slots): f(*a)
def Slot(*a, **k): return lambda f: f
class QTimer(_Any):
    TIMERS = []
    def __init__(self, *a): self.timeout = _Bound(); QTimer.TIMERS.append(self)
    def start(self, *a): pass
    def stop(self): pass
    def setSingleShot(self, *a): pass
    @staticmethod
    def singleShot(ms, fn=None, *a):
        f = fn if callable(fn) else (a[0] if a and callable(a[0]) else None)
        if f: CALLS.append(f)
def make(names):
    mod = {}
    for n in names: mod[n] = type(n, (_Any,), {})
    return mod
