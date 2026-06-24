# OppoPods-Win

Windows 桌面端 OPPO Enco Free4 耳机控制工具，通过蓝牙 RFCOMM 协议直接与耳机通信。

**支持的耳机**

OPPO Enco Free4 —— 完整支持（唯一实测型号）

**功能**

电量显示（左耳 / 右耳 / 充电盒，含充电状态 ⚡）

降噪控制：智能、轻度、中度、深度、自适应、通透、关闭

大师调音：至臻原音、纯享人声、澎湃低音、活力动感

空间音效开关

游戏模式开关

系统托盘常驻，悬浮提示显示实时电量

关闭到托盘、开机自启

托盘右键菜单完整控制（降噪 / 调音 / 空间音效 / 游戏模式）

**安装**

```bash
pip install -r requirements.txt
python oppopods_ctk.py
```

**打包为 EXE**

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "OppoPods-Win" --icon "tuopan.ico" \
    --add-data "left.png;." --add-data "right.png;." --add-data "cang.png;." \
    --add-data "tuopan.png;." --add-data "tuopandis.png;." oppopods_ctk.py
```

**使用说明**

1. 在 Windows 蓝牙设置中配对 OPPO Enco Free4
2. 运行 OppoPods-Win.exe，自动连接耳机
3. 主界面可查看电量、切换降噪和调音模式
4. 托盘图标右键菜单可快速控制所有功能
5. 启用“关闭到托盘”后，点 X 最小化而非退出
6. 启用“开机自启”后，开机自动最小化到托盘

**技术原理**

通过 WinSock2 AF_BTH socket 建立蓝牙 RFCOMM 连接（通道 15），使用 OPPO 私有协议（UUID 0000079A-D102-11E1-9B23-00025B00A5A5）与耳机通信。已配对蓝牙地址从注册表 HKLM\SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Devices 读取。

**致谢**

[OppoPods](https://github.com/Leaf-lsgtky/OppoPods) by Leaf-lsgtky —— OPPO 私有协议逆向

[OppoPods](https://github.com/1812z/OppoPods) by 1812z —— 游戏模式兼容实现参考

[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) —— 现代 Python GUI 框架

**License**

GPL-3.0
