from BitmapRenderer import BitmapRenderer
import ctypes
from ctypes import wintypes
from typing import Final

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
HCURSOR = ctypes.c_void_p

if ctypes.sizeof(ctypes.c_void_p) == 8:
    LRESULT = ctypes.c_longlong
    WPARAM = ctypes.c_ulonglong
    LPARAM = ctypes.c_longlong
else:
    LRESULT = ctypes.c_long
    WPARAM = ctypes.c_uint
    LPARAM = ctypes.c_long


WNDPROCTYPE = ctypes.WINFUNCTYPE(
    LRESULT,
    wintypes.HWND,
    wintypes.UINT,
    WPARAM,
    LPARAM
)

user32.DefWindowProcW.argtypes = (
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)

user32.DefWindowProcW.restype = LRESULT

WM_DESTROY: Final[int] = 0x0002

def py_wnd_proc(hwnd, msg, wparam, lparam):
    if msg == WM_DESTROY:
        user32.PostQuitMessage(0)
        return 0
    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

wnd_proc = WNDPROCTYPE(py_wnd_proc)



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

hInstance = kernel32.GetModuleHandleW(None)

class_name = "WindowClass"
windowName:str = "Window"

wndclass = WNDCLASS()
wndclass.lpfnWndProc = wnd_proc
wndclass.lpszClassName = class_name
wndclass.hInstance = hInstance
wndclass.hCursor = user32.LoadCursorW(None, 32512)
wndclass.hbrBackground = ctypes.c_void_p(5)  # COLOR_WINDOW + 1

atom = user32.RegisterClassW(ctypes.byref(wndclass))
if not atom:
    raise RuntimeError(ctypes.FormatError(kernel32.GetLastError()))

WS_OVERLAPPEDWINDOW: Final[int] = 0x10CF0000
X: Final[int] = 100
Y: Final[int] = 100
width: Final[int] = 800
height: Final[int] = 600

menu = user32.CreateMenu()

hwnd = user32.CreateWindowExW(
    0, 
    class_name,
    windowName,
    WS_OVERLAPPEDWINDOW,
    X, Y, width, height,
    None,
    menu,
    hInstance,
    None
    )
if not hwnd:
    raise RuntimeError("CreateWindowEx failed: " + ctypes.FormatError(kernel32.GetLastError()))

error_code = kernel32.GetLastError()
message = ctypes.FormatError(error_code)

print(f"Error {error_code}: {message}")

user32.ShowWindow(hwnd, 1)
user32.UpdateWindow(hwnd)

msg = wintypes.MSG()
while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
    user32.TranslateMessage(ctypes.byref(msg))
    user32.DispatchMessageW(ctypes.byref(msg))
