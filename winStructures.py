import ctypes
from ctypes import wintypes

if ctypes.sizeof(ctypes.c_void_p) == 8:
    LRESULT = ctypes.c_longlong
    WPARAM = ctypes.c_ulonglong
    LPARAM = ctypes.c_longlong
else:
    LRESULT = ctypes.c_long
    WPARAM = ctypes.c_uint
    LPARAM = ctypes.c_long

HCURSOR = ctypes.c_void_p

WNDPROCTYPE = ctypes.WINFUNCTYPE(
    LRESULT,
    wintypes.HWND,
    wintypes.UINT,
    WPARAM,
    LPARAM
)

class BITMAP(ctypes.Structure):
            _fields_ = [
                ("bmType", ctypes.c_long),
                ("bmWidth", ctypes.c_long),
                ("bmHeight", ctypes.c_long),
                ("bmWidthBytes", ctypes.c_long),
                ("bmPlanes", ctypes.c_ushort),
                ("bmBitsPixel", ctypes.c_ushort),
                ("bmBits", ctypes.c_void_p),
            ]

class PAINTSTRUCT(ctypes.Structure):
    _fields_ = [
        ("hdc", wintypes.HDC),
        ("fErase", wintypes.BOOL),
        ("rcPaint", wintypes.RECT),
        ("fRestore", wintypes.BOOL),
        ("fIncUpdate", wintypes.BOOL),
        ("rgbReserved", ctypes.c_byte * 32),
    ]

class WNDCLASS(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROCTYPE),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", HCURSOR),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
        ]