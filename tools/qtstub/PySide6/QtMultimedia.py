from ._base import _Any, Signal, Slot, QTimer, make, CALLS
def __getattr__(n):
    if n.startswith('__'): raise AttributeError(n)
    c = type(n, (_Any,), {}); globals()[n] = c; return c
def qInstallMessageHandler(*a): pass
