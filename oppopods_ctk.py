"""
OppoPods-Win CTk — OPPO Enco Free4 Desktop Controller
CustomTkinter + WinSock2 RFCOMM
"""

import ctypes, struct, time, winreg, threading
import os as _os
import ctypes, struct, time, winreg, threading
import customtkinter as ctk
from PIL import Image

# ---- Icons ----
_ICON_PATH = {}
_BASE = _os.path.dirname(_os.path.abspath(__file__))
_ICON_PATH["L"] = _os.path.join(_BASE,"left.png")
_ICON_PATH["R"] = _os.path.join(_BASE,"right.png")
_ICON_PATH["C"] = _os.path.join(_BASE,"cang.png")

# ============================================================
# Bluetooth Winsock
# ============================================================
AF_BTH, BTHPROTO_RFCOMM, CH = 32, 3, 15

class _G(ctypes.Structure):
    _fields_=[("a",ctypes.c_uint32),("b",ctypes.c_uint16),("c",ctypes.c_uint16),("d",ctypes.c_uint8*8)]
class _S(ctypes.Structure):
    _pack_=1
    _fields_=[("x",ctypes.c_ushort),("y",ctypes.c_ulonglong),("z",_G),("p",ctypes.c_uint32)]

_W=ctypes.WinDLL("ws2_32.dll")
_W.WSAStartup.argtypes=[ctypes.c_uint16,ctypes.c_void_p]; _W.WSAStartup.restype=ctypes.c_int
_W.WSACleanup.restype=ctypes.c_int
_W.WSAGetLastError.restype=ctypes.c_int
_W.socket.restype=ctypes.c_void_p; _W.socket.argtypes=[ctypes.c_int]*3
_W.closesocket.restype=ctypes.c_int; _W.closesocket.argtypes=[ctypes.c_void_p]
_W.connect.restype=ctypes.c_int; _W.connect.argtypes=[ctypes.c_void_p]*3
_W.send.restype=ctypes.c_int; _W.send.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int]
_W.recv.restype=ctypes.c_int; _W.recv.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int]
_W.ioctlsocket.restype=ctypes.c_int; _W.ioctlsocket.argtypes=[ctypes.c_void_p,ctypes.c_long,ctypes.c_void_p]

_sock=None; _lock=threading.Lock()

def bt_addr():
    try:
        k=winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r"SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Devices")
        for i in range(1000):
            try: sub=winreg.EnumKey(k,i)
            except: break
            if len(sub)==12: winreg.CloseKey(k); return int(sub,16)
        winreg.CloseKey(k)
    except:pass
    return None

def bt_connect(addr):
    global _sock
    if _sock: bt_disconnect()
    _W.WSAStartup(0x0202,(ctypes.c_ubyte*400)())
    s=_W.socket(AF_BTH,1,BTHPROTO_RFCOMM)
    a=_S(); a.x=AF_BTH; a.y=addr; a.p=CH
    if _W.connect(s,ctypes.byref(a),ctypes.sizeof(_S))!=0:
        _W.WSACleanup();return False
    m=ctypes.c_ulong(1); _W.ioctlsocket(s,0x8004667E,ctypes.byref(m))
    _sock=s; return True

def bt_disconnect():
    global _sock
    if _sock: _W.closesocket(_sock); _sock=None
    _W.WSACleanup()

def bt_send(data):
    if not _sock:return
    with _lock:
        if isinstance(data,list):
            for d in data: _W.send(_sock,d,len(d),0); time.sleep(0.2)
        else: _W.send(_sock,data,len(data),0)

def bt_recv(timeout=0.5):
    if not _sock:return[]
    pkts=[]; end=time.time()+timeout
    while time.time()<end:
        b=(ctypes.c_ubyte*256)(); g=_W.recv(_sock,b,256,0)
        if g>0: pkts.append(bytes(b[:g]))
        elif g<0 and _W.WSAGetLastError()==10035: time.sleep(0.03); continue
        else: break
    return pkts

# ============================================================
# OPPO Protocol
# ============================================================
BATTERY=bytes([0xAA,0x07,0x00,0x00,0x06,0x01,0xF0,0x00,0x00])
QUERY_ANC=bytes([0xAA,0x09,0x00,0x00,0x0C,0x01,0x00,0x02,0x00,0x01,0x01])

ANC_MAP={
    "Off":           bytes([0xAA,0x0A,0x00,0x00,0x04,0x04,0x00,0x03,0x00,0x01,0x01,0x01]),
    "Smart":         bytes([0xAA,0x0A,0x00,0x00,0x04,0x04,0x00,0x03,0x00,0x01,0x01,0x80]),
    "Medium":        bytes([0xAA,0x0A,0x00,0x00,0x04,0x04,0x00,0x03,0x00,0x01,0x01,0x20]),
    "Deep":          bytes([0xAA,0x0A,0x00,0x00,0x04,0x04,0x00,0x03,0x00,0x01,0x01,0x10]),
    "Light":         bytes([0xAA,0x0A,0x00,0x00,0x04,0x04,0x00,0x03,0x00,0x01,0x01,0x40]),
    "Adaptive":      bytes([0xAA,0x0B,0x00,0x00,0x04,0x04,0x00,0x04,0x00,0x01,0x01,0x00,0x08]),
    "Transparency":  bytes([0xAA,0x0A,0x00,0x00,0x04,0x04,0x00,0x03,0x00,0x01,0x01,0x04]),
}
def _bld(c,p=b""):
    pl=len(p);tl=7+pl;d=bytearray(2+tl);d[0]=0xAA;d[1]=tl
    d[4]=c&0xFF;d[5]=(c>>8)&0xFF;d[6]=0xF0;d[7]=pl&0xFF;d[8]=(pl>>8)&0xFF
    if pl: d[9:9+pl]=p
    return bytes(d)
SPAT_ON=_bld(0x0403,bytes([0x1B,0x01])); SPAT_OFF=_bld(0x0403,bytes([0x1B,0x00]))
GAME_ON=[bytes([0xAA,0x09,0x00,0x00,0x03,0x04,0x00,0x02,0x00,0x28,0x01]),
         bytes([0xAA,0x09,0x00,0x00,0x03,0x04,0x00,0x02,0x00,0x06,0x01])]
GAME_OFF=[bytes([0xAA,0x09,0x00,0x00,0x03,0x04,0x00,0x02,0x00,0x06,0x00]),
          bytes([0xAA,0x09,0x00,0x00,0x03,0x04,0x00,0x02,0x00,0x28,0x00])]

# 大师调音 (Enco Free4 实际映射: 0=至臻原音 1=纯享人声 2=澎湃低音 3=无效 7=活力动感)
EQ_PRESETS={"至臻原音":0,"纯享人声":1,"澎湃低音":2,"活力动感":7}
EQ_CMD={k:_bld(0x0406,bytes([v])) for k,v in EQ_PRESETS.items()}
QUERY_EQ=_bld(0x010F,bytes())

class PodState:
    def __init__(s):
        s.b={}; s.a="?"; s.w={}; s.conn=False; s.sp=0; s.gm=0; s.eq="?"
    def bat(self,k,v,c): self.b[k]=(v,c)
    def anc(self,v): self.a=v
    def wear(self,k,v): self.w[k]=v

def parse(data,st):
    for p in _spl(data):
        if len(p)<9: continue
        c=p[4]|(p[5]<<8)
        if c==0x8106:_pb(p,st)
        elif c==0x810C:_pa(p,st)
        elif c==0x0204:_pn(p,st)
        elif c in (0x810F,0x0504):_pe(p,st)

def _spl(data):
    pk,i=[],0
    while i<len(data)-1:
        if data[i]==0xAA: tl=data[i+1];n=2+tl
        if i+n<=len(data):pk.append(data[i:i+n]);i+=n;continue
        i+=1
    return pk

def _pb(p,s):
    pl=p[7]|(p[8]<<8);i=9
    while i+1<9+pl and i+1<len(p):
        idx,raw=p[i],p[i+1];i+=2
        n={1:"L",2:"R",3:"C"}.get(idx)
        if n: s.bat(n,raw&0x7F,(raw&0x80)!=0)

def _pa(p,s):
    pl=p[7]|(p[8]<<8)
    for j in range(9,min(9+pl-2,len(p)-2)):
        if p[j]==1 and p[j+1]==1:
            v1,v2=p[j+2],p[j+3] if j+3<len(p) else 0
            s.anc({(8,0):"Off",(2,0):"Smart",(0x80,0):"Smart",(0x40,0):"Light",
                   (0x20,0):"Medium",(0x10,0):"Deep",(0,1):"Transparency",
                   (0,2):"Transparency",(4,0):"Transparency",(0,8):"Adaptive"}.get((v1,v2),s.a))

def _pn(p,s):
    pl=p[7]|(p[8]<<8)
    if pl<1:return
    t,c=p[9],p[10] if pl>1 else 0
    if t==1:
        for j in range(c):
            o=11+j*2
            if o+1>=len(p):break
            idx,raw=p[o],p[o+1]
            n={1:"L",2:"R",3:"C"}.get(idx)
            if n: s.bat(n,raw&0x7F,(raw&0x80)!=0)
    elif t==2:
        for j in range(c):
            o=11+j*2
            if o+1>=len(p):break
            comp,st=p[o],p[o+1]
            n={1:"L",2:"R",3:"C"}.get(comp,f"x{comp}")
            l={0:"disc",4:"in-case",5:"removed",7:"wearing"}.get(st,f"0x{st:02X}")
            s.wear(n,l)

EQ_ID={v:k for k,v in EQ_PRESETS.items()}
def _pe(p,s):
    """Parse EQ preset response/notify"""
    pl=p[7]|(p[8]<<8)
    if pl>=1: s.eq=EQ_ID.get(p[9],s.eq)
    if pl>=2: s.eq=EQ_ID.get(p[10],s.eq)  # 0x810F has status byte at [9], preset at [10]


# ============================================================
# GUI
# ============================================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    # ---- Tray state (persisted) ----
    _tray_enabled=False
    _tray_ref=None

    def __init__(self):
        super().__init__()
        self.title("OppoPods-Win"); self.geometry("460x640"); self.resizable(False,False)
        self.pod=PodState(); self._alive=True
        self.icons={}
        for k,v in _ICON_PATH.items():
            img=Image.open(v)
            w,h=img.size
            self.icons[k]=ctk.CTkImage(img,size=(int(w*100/h),100))
        self._anc_level="Smart"
        self._anc_main="Smart"
        self.protocol("WM_DELETE_WINDOW",self._on_close)
        self._make_ui()
        # Restore tray toggle state from registry
        App._tray_enabled=self._read_tray_state()
        # Always create tray icon (persistent)
        self._create_tray()
        # Auto-start: minimize to tray
        import sys
        if "--minimized" in sys.argv:
            self.withdraw()
        else:
            self.after(300, self._first_connect)

    # ---- Tray state persistence ----
    def _read_tray_state(self):
        try:
            k=winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"Software\OppoPodsWin",0,winreg.KEY_READ)
            v,_=winreg.QueryValueEx(k,"TrayEnabled"); winreg.CloseKey(k)
            return bool(v)
        except: return False

    def _write_tray_state(self,enabled):
        try:
            k=winreg.CreateKey(winreg.HKEY_CURRENT_USER,r"Software\OppoPodsWin")
            winreg.SetValueEx(k,"TrayEnabled",0,winreg.REG_DWORD,int(enabled))
            winreg.CloseKey(k)
        except: pass

    def _toggle_tray(self):
        App._tray_enabled=not App._tray_enabled
        self._write_tray_state(App._tray_enabled)

    # ---- Tray icon (always visible) ----
    def _create_tray(self):
        import pystray
        img=Image.open(_os.path.join(_BASE,"tuopan.png")).resize((32,32))
        ncs="Smart Light Medium Deep".split()
        menu=pystray.Menu(
            pystray.MenuItem("降噪控制",
                pystray.Menu(
                    pystray.MenuItem("降噪",
                        pystray.Menu(
                            pystray.MenuItem("智能",lambda:self._tray_anc("Smart"),checked=lambda _:self.pod.a=="Smart"),
                            pystray.MenuItem("轻度",lambda:self._tray_anc("Light"),checked=lambda _:self.pod.a=="Light"),
                            pystray.MenuItem("中度",lambda:self._tray_anc("Medium"),checked=lambda _:self.pod.a=="Medium"),
                            pystray.MenuItem("深度",lambda:self._tray_anc("Deep"),checked=lambda _:self.pod.a=="Deep"),
                        ),
                        checked=lambda _:self.pod.a in ncs
                    ),
                    pystray.MenuItem("自适应",lambda:self._tray_anc("Adaptive"),checked=lambda _:self.pod.a=="Adaptive"),
                    pystray.MenuItem("通透",lambda:self._tray_anc("Transparency"),checked=lambda _:self.pod.a=="Transparency"),
                    pystray.MenuItem("关闭",lambda:self._tray_anc("Off"),checked=lambda _:self.pod.a=="Off"),
                )
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("空间音效",lambda:self._tray_toggle("sp"),checked=lambda _:bool(self.pod.sp)),
            pystray.MenuItem("游戏模式",lambda:self._tray_toggle("gm"),checked=lambda _:bool(self.pod.gm)),
            pystray.MenuItem("大师调音",
                pystray.Menu(*[pystray.MenuItem(k,lambda v=k:self._tray_eq(v),
                    checked=lambda _,k=k:self.pod.eq==k) for k in EQ_PRESETS])
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("显示",self._show_window,default=True),
            pystray.MenuItem("退出",self._quit_app),
        )
        App._tray_ref=pystray.Icon("oppopods",img,self._battery_tooltip(),menu)
        threading.Thread(target=App._tray_ref.run,daemon=True).start()

    def _show_window(self, icon=None):
        self.after(0,self._pop_at_bottom_right)

    def _quit_app(self, icon=None):
        if icon: icon.stop()
        self.after(0,self._close)

    def _on_close(self):
        if App._tray_enabled:
            self.withdraw()
        else:
            self._close()

    def _close(self):
        self._alive=False
        if App._tray_ref: App._tray_ref.stop()
        bt_disconnect()
        self.destroy()

    # ---- Auto-start ----
    def _check_autostart(self):
        try:
            k=winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",0,winreg.KEY_READ)
            winreg.QueryValueEx(k,"OppoPodsWin"); winreg.CloseKey(k)
            return True
        except: return False

    def _toggle_autostart(self):
        import sys
        try:
            k=winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",0,
                winreg.KEY_SET_VALUE|winreg.KEY_QUERY_VALUE)
        except PermissionError: return
        try:
            winreg.QueryValueEx(k,"OppoPodsWin")
            winreg.DeleteValue(k,"OppoPodsWin")
        except FileNotFoundError:
            exe=sys.executable
            if getattr(sys,'frozen',False):
                cmd=f'"{exe}" --minimized'
            else:
                cmd=f'"{exe}" "{_os.path.abspath(__file__)}" --minimized'
            winreg.SetValueEx(k,"OppoPodsWin",0,winreg.REG_SZ,cmd)
        winreg.CloseKey(k)

    def _pop_at_bottom_right(self):
        sw=self.winfo_screenwidth(); sh=self.winfo_screenheight()
        self.geometry(f"460x640+{sw-460}+{sh-640-40}")
        self.deiconify(); self.lift(); self.focus_force()

    def _battery_tooltip(self):
        parts=[]
        for k,n in [("L","左"),("R","右"),("C","盒")]:
            v=self.pod.b.get(k)
            parts.append(f"{n}:{v[0]}%" if v else f"{n}:--")
        return "  ".join(parts)

    def _update_tray_icon(self):
        if not App._tray_ref: return
        try:
            fname="tuopan.png" if self.pod.conn else "tuopandis.png"
            img=Image.open(_os.path.join(_BASE,fname)).resize((32,32))
            App._tray_ref.icon=img
        except: pass

    def _tray_anc(self,mode):
        if mode in ("Smart","Light","Medium","Deep"):
            self.pod.anc("Smart")
        else:
            self.pod.anc(mode)
        self.after(0,self._redraw)
        def d():
            if mode in ANC_MAP:
                bt_send(ANC_MAP[mode]); time.sleep(0.35)
                bt_send(QUERY_ANC); time.sleep(0.15)
                for p in bt_recv(1.0): parse(p,self.pod)
                self.after(0,self._redraw)
        threading.Thread(target=d,daemon=True).start()

    def _tray_toggle(self,which):
        if which=="sp":
            self.pod.sp^=1
            threading.Thread(target=lambda:bt_send(SPAT_ON if self.pod.sp else SPAT_OFF),daemon=True).start()
        elif which=="gm":
            self.pod.gm^=1
            threading.Thread(target=lambda:bt_send(GAME_ON if self.pod.gm else GAME_OFF),daemon=True).start()

    def _tray_eq(self,val):
        if val in EQ_CMD:
            self.pod.eq=val
            threading.Thread(target=lambda:bt_send(EQ_CMD[val]),daemon=True).start()

    def _make_ui(self):
        FW=ctk.CTkFont(size=14,weight="bold")
        # Header
        h=ctk.CTkFrame(self,fg_color="transparent")
        h.pack(fill="x",padx=20,pady=(16,0))
        self._title=ctk.CTkLabel(h,text="OPPO Pods",font=ctk.CTkFont(size=22,weight="bold"))
        self._title.pack(side="left")
        self.st=ctk.CTkLabel(h,text="连接中...",font=ctk.CTkFont(size=12),text_color="gray")
        self.st.pack(side="right")

        # Card: Battery (3 icons horizontal)
        bc=ctk.CTkFrame(self,corner_radius=12)
        bc.pack(fill="x",padx=20,pady=(12,4))
        ctk.CTkLabel(bc,text="电量",font=FW).pack(anchor="w",padx=16,pady=(12,4))
        self._bars={}; self._lbls={}; self._img_lbls={}
        br=ctk.CTkFrame(bc,fg_color="transparent")
        br.pack(fill="x",padx=16,pady=(0,12))
        for i,key in enumerate(("L","R","C")):
            col=ctk.CTkFrame(br,fg_color="transparent")
            col.grid(row=0,column=i,padx=14)
            img_lbl=ctk.CTkLabel(col,text="",image=self.icons[key])
            img_lbl.pack()
            pct=ctk.CTkLabel(col,text="--%",font=ctk.CTkFont(size=14,weight="bold"))
            pct.pack(pady=(4,0))
            bar=ctk.CTkProgressBar(col,height=12,corner_radius=6)
            bar.pack(fill="x",pady=(4,0)); bar.set(0)
            self._bars[key]=bar; self._lbls[key]=pct; self._img_lbls[key]=img_lbl
        br.grid_columnconfigure((0,1,2),weight=1)

        # Card: ANC
        ac=ctk.CTkFrame(self,corner_radius=12)
        ac.pack(fill="x",padx=20,pady=4)
        ctk.CTkLabel(ac,text="降噪控制",font=FW).pack(anchor="w",padx=16,pady=(12,4))
        # Main row: 降噪 / 自适应 / 通透 / 关闭
        self._anc_btns={}
        mf=ctk.CTkFrame(ac,fg_color="transparent"); mf.pack(fill="x",padx=12)
        for i,(v,t) in enumerate([("Smart","降噪"),("Adaptive","自适应"),("Transparency","通透"),("Off","关闭")]):
            b=ctk.CTkButton(mf,text=t,width=75,font=ctk.CTkFont(size=12),
                            command=lambda v=v:self._set_anc_main(v))
            b.grid(row=0,column=i,padx=4,pady=4)
            self._anc_btns[v]=b
        mf.grid_columnconfigure((0,1,2,3),weight=1)
        # Sub row: 智能/轻度/中度/深度 (only when 降噪 selected)
        self._anc_sub=ctk.CTkFrame(ac,fg_color="transparent")
        self._anc_subs={}
        sf=ctk.CTkFrame(self._anc_sub,fg_color="transparent"); sf.pack(fill="x",padx=12,pady=(0,8))
        for i,(v,t) in enumerate([("Smart","智能"),("Light","轻度"),("Medium","中度"),("Deep","深度")]):
            b=ctk.CTkButton(sf,text=t,width=75,font=ctk.CTkFont(size=11),
                            command=lambda v=v:self._set_anc_level(v))
            b.grid(row=0,column=i,padx=4,pady=2)
            self._anc_subs[v]=b
        sf.grid_columnconfigure((0,1,2,3),weight=1)
        self._anc_sub.pack_forget()  # hidden initially
        self._update_anc_buttons()

        # Card: Features
        fc=ctk.CTkFrame(self,corner_radius=12)
        fc.pack(fill="x",padx=20,pady=4)
        ctk.CTkLabel(fc,text="功能",font=FW).pack(anchor="w",padx=16,pady=(12,4))
        # Row 1: toggles
        tr=ctk.CTkFrame(fc,fg_color="transparent"); tr.pack(fill="x",padx=16,pady=(4,0))
        for col_i,(label,cmd) in enumerate([("空间音效",self._spat_cmd),("游戏模式",self._game_cmd)]):
            box=ctk.CTkFrame(tr,corner_radius=8,fg_color=("gray85","gray25"))
            box.grid(row=0,column=col_i,padx=6,sticky="ew")
            ctk.CTkLabel(box,text=label,font=ctk.CTkFont(size=12)).pack(side="left",padx=(12,4),pady=8)
            ctk.CTkSwitch(box,text="",command=cmd,width=40).pack(side="right",padx=(0,12),pady=8)
        tr.grid_columnconfigure((0,1),weight=1)

        # Row 2: 大师调音
        tr2=ctk.CTkFrame(fc,fg_color="transparent"); tr2.pack(fill="x",padx=16,pady=4)
        eqbox=ctk.CTkFrame(tr2,corner_radius=8,fg_color=("gray85","gray25"))
        eqbox.pack(fill="x",padx=60,pady=(0,4))
        ctk.CTkLabel(eqbox,text="大师调音",font=ctk.CTkFont(size=12)).pack(side="left",padx=(12,4),pady=8)
        self._eq_menu=ctk.CTkOptionMenu(eqbox,values=list(EQ_PRESETS.keys()),command=self._eq_cmd,
                                          font=ctk.CTkFont(size=11))
        self._eq_menu.pack(side="right",padx=(0,8),pady=6)

        # System options (exe only)
        sf2=ctk.CTkFrame(fc,fg_color="transparent"); sf2.pack(fill="x",padx=16,pady=(0,12))
        self._autostart_sw=None
        for col_i,(label,cmd,get_state) in enumerate([
            ("开机自启",self._toggle_autostart,self._check_autostart),
            ("关闭到托盘",self._toggle_tray,lambda:App._tray_enabled)]):
            box2=ctk.CTkFrame(sf2,corner_radius=8,fg_color=("gray85","gray25"))
            box2.grid(row=0,column=col_i,padx=6,sticky="ew")
            ctk.CTkLabel(box2,text=label,font=ctk.CTkFont(size=12)).pack(side="left",padx=(12,4),pady=8)
            sw2=ctk.CTkSwitch(box2,text="",command=cmd,width=40)
            sw2.pack(side="right",padx=(0,12),pady=8)
            if get_state(): sw2.select()
            if label=="开机自启": self._autostart_sw=sw2
        sf2.grid_columnconfigure((0,1),weight=1)

        # 5s auto-refresh, no manual buttons needed
        tr.grid_columnconfigure((0,1),weight=1)

    def _first_connect(self):
        threading.Thread(target=self._connect_thread,daemon=True).start()

    def _connect_thread(self):
        addr=bt_addr()
        if not addr or not bt_connect(addr):
            self.st.configure(text="未连接",text_color="red"); return
        self.pod.conn=True
        self.st.configure(text="已连接",text_color="#4CAF50")
        bt_send(BATTERY); time.sleep(0.3)
        for p in bt_recv(1.0): parse(p,self.pod)
        bt_send(QUERY_ANC); time.sleep(0.3)
        for p in bt_recv(1.0): parse(p,self.pod)
        bt_send(QUERY_EQ); time.sleep(0.3)
        for p in bt_recv(1.0): parse(p,self.pod)
        self.after(0,self._redraw)
        self.after(0,self._update_tray_icon)
        self._start_poller()

    def _start_poller(self):
        def loop():
            tick=0
            while self._alive and self.pod.conn:
                bt_send(BATTERY); time.sleep(0.3)
                for p in bt_recv(0.5): parse(p,self.pod)
                tick+=1
                if tick%3==0:
                    bt_send(QUERY_ANC); time.sleep(0.2)
                    for p in bt_recv(0.4): parse(p,self.pod)
                if tick%6==0:
                    bt_send(QUERY_EQ); time.sleep(0.2)
                    for p in bt_recv(0.4): parse(p,self.pod)
                self.after(0,self._redraw)
                self.after(0,self._update_tray_icon)
                time.sleep(4.5)
        threading.Thread(target=loop,daemon=True).start()

    def _refresh(self):
        def do():
            bt_send(BATTERY); time.sleep(0.3)
            for p in bt_recv(0.8): parse(p,self.pod)
            bt_send(QUERY_ANC); time.sleep(0.3)
            for p in bt_recv(0.8): parse(p,self.pod)
            self.after(0,self._redraw)
        threading.Thread(target=do,daemon=True).start()

    def _reconnect(self):
        self.pod.conn=False; bt_disconnect()
        self.pod=PodState(); self.st.configure(text="连接中...",text_color="gray")
        self.after(0,self._redraw); self._first_connect()

    def _set_anc_main(self,mode):
        self._anc_main=mode
        self._update_anc_buttons()
        self._send_anc(mode)

    def _set_anc_level(self,level):
        self._anc_level=level
        self._anc_main="Smart"
        self._update_anc_buttons()
        self._send_anc(level)

    def _update_anc_buttons(self):
        """Highlight active ANC buttons and toggle sub-row visibility"""
        for v,b in self._anc_btns.items():
            b.configure(fg_color="transparent" if v!=self._anc_main else ("#1F6AA5" if v=="Smart" else "#2FA572"))
        for v,b in self._anc_subs.items():
            b.configure(fg_color="transparent" if v!=self._anc_level else "#1F6AA5")
        if self._anc_main=="Smart":
            self._anc_sub.pack(fill="x",padx=12,pady=(0,8))
        else:
            self._anc_sub.pack_forget()

    def _send_anc(self,mode):
        # Optimistic UI update
        if mode in ("Smart","Light","Medium","Deep"):
            self.pod.anc("Smart")
        else:
            self.pod.anc(mode)
        self._update_anc_buttons()
        # Actually send
        def d():
            if mode in ANC_MAP:
                bt_send(ANC_MAP[mode]); time.sleep(0.35)
                bt_send(QUERY_ANC); time.sleep(0.15)
                for p in bt_recv(1.0): parse(p,self.pod)
                self.after(0,self._redraw)
        threading.Thread(target=d,daemon=True).start()

    def _spat_cmd(self):
        self.pod.sp ^= 1
        threading.Thread(target=lambda: bt_send(SPAT_ON if self.pod.sp else SPAT_OFF),daemon=True).start()

    def _game_cmd(self):
        self.pod.gm ^= 1
        threading.Thread(target=lambda: bt_send(GAME_ON if self.pod.gm else GAME_OFF),daemon=True).start()

    def _eq_cmd(self,val):
        if val in EQ_CMD:
            self.pod.eq=val
            threading.Thread(target=lambda: bt_send(EQ_CMD[val]),daemon=True).start()

    def _redraw(self):
        for k in ("L","R","C"):
            bar=self._bars[k]; lbl=self._lbls[k]
            v=self.pod.b.get(k)
            if v:
                lv,chg=v
                bar.set(lv/100)
                c="#2196F3" if chg else ("#4CAF50" if lv>30 else ("#FF9800" if lv>10 else "#F44336"))
                bar.configure(progress_color=c)
                lbl.configure(text=f"{lv}%" + (" \u26A1" if chg else ""))
            else:
                bar.set(0); lbl.configure(text="--%")
        # Update ANC state from pod
        anc=self.pod.a
        if anc in ("Off","Adaptive","Transparency"):
            self._anc_main=anc
        elif anc in ("Smart","Light","Medium","Deep"):
            self._anc_main="Smart"; self._anc_level=anc
        self._update_anc_buttons()
        # Update tray tooltip with battery
        if App._tray_ref:
            try: App._tray_ref.title=self._battery_tooltip()
            except: pass

        else:
            self._close()

if __name__=="__main__":
    App().mainloop()
