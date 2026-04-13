from BitmapRenderer import BitmapRenderer
import ctypes
from ctypes import wintypes
from typing import Final

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
HCURSOR = ctypes.c_void_p

gdi32 = ctypes.windll.gdi32

WM_PAINT = 0x000F
SRCCOPY = 0x00CC0020
IMAGE_BITMAP = 0
LR_LOADFROMFILE = 0x00000010

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

bitmap = user32.LoadImageW(
    None,
    "images.bmp",  
    IMAGE_BITMAP,
    0,
    0,
    LR_LOADFROMFILE
)

if not bitmap:
    raise RuntimeError("Failed to load bitmap")

user32.DefWindowProcW.restype = LRESULT

WM_DESTROY: Final[int] = 0x0002

class PAINTSTRUCT(ctypes.Structure):
    _fields_ = [
        ("hdc", wintypes.HDC),
        ("fErase", wintypes.BOOL),
        ("rcPaint", wintypes.RECT),
        ("fRestore", wintypes.BOOL),
        ("fIncUpdate", wintypes.BOOL),
        ("rgbReserved", ctypes.c_byte * 32),
    ]


def py_wnd_proc(hwnd, msg, wparam, lparam):
    if msg == WM_DESTROY:
        user32.PostQuitMessage(0)
        return 0
    elif msg == WM_PAINT:
        ps = PAINTSTRUCT()
        hdc = user32.BeginPaint(hwnd, ctypes.byref(ps))

        mem_dc = gdi32.CreateCompatibleDC(hdc)

        old_obj = gdi32.SelectObject(mem_dc, bitmap)

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

        bmp = BITMAP()
        gdi32.GetObjectW(bitmap, ctypes.sizeof(bmp), ctypes.byref(bmp))
        gdi32.SetStretchBltMode(hdc, 0x0002);
        # gdi32.BitBlt(
        #     hdc,
        #     0, 0,
        #     bmp.bmWidth,
        #     bmp.bmHeight,
        #     mem_dc,
        #     0, 0,
        #     SRCCOPY
        # )

        gdi32.StretchBlt(
            hdc,
            0, 0,
            800,
            600,
            mem_dc,
            0, 0,
            bmp.bmWidth,
            bmp.bmHeight,
            SRCCOPY
        )

        gdi32.SelectObject(mem_dc, old_obj)
        gdi32.DeleteDC(mem_dc)
        user32.EndPaint(hwnd, ctypes.byref(ps))
        print("it was called")
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
