# CipherBox 加密工具箱

一个基于 **PyQt5** 的桌面加解密工具，界面为浅色简约风格。支持 AES、RSA、ECC 加解密，SHA-256、bcrypt 哈希，以及 Base64 编解码。所有运算都在本地完成，不会上传任何数据。

![AES 页面](docs/images/aes.png)

| RSA 公钥加密 | bcrypt 密码哈希 | Base64 编码 |
|---|---|---|
| ![RSA](docs/images/rsa.png) | ![bcrypt](docs/images/bcrypt.png) | ![Base64](docs/images/base64.png) |

## 功能一览

| 页面 | 类型 | 说明 |
|---|---|---|
| **AES** | 对称加密 | 输入密码即可加解密；AES-256-GCM，密码经 Scrypt 派生密钥，密文带防篡改校验 |
| **RSA** | 公钥加密 | 2048 / 3072 / 4096 位；RSA-OAEP(SHA-256) 混合加密，任意长度文本都能加密 |
| **ECC** | 公钥加密 | P-256 / P-384 / P-521 / secp256k1；ECIES（ECDH + HKDF-SHA256 + AES-256-GCM） |
| **SHA-256** | 单向哈希 | 输入时实时计算，可切换大写，显示字符数和 UTF-8 字节数 |
| **bcrypt** | 密码哈希 | 生成哈希（cost 4–16，显示耗时），验证密码是否匹配 |
| **Base64** | 编码 | 支持 URL 安全写法，字符编码可选 UTF-8 / GBK；解码兼容多种写法 |

其他特性：

- **密钥管理**（RSA / ECC）：程序内生成密钥对，导入导出 `.pem` 文件，导出私钥时可设置保护密码，可以「由私钥生成」公钥
- **自动识别密钥格式**：PEM、OpenSSH、X.509 证书、纯 Base64、二进制 DER 都能导入（见[支持的密钥格式](#支持的密钥格式)）
- **界面不卡顿**：生成大密钥、bcrypt 这类耗时运算放在后台线程执行
- **中文错误提示**：密码错误、密文被篡改、密钥类型不对等情况都会给出具体原因，不会崩溃

## 快速开始

### 环境要求

- Python **3.10** 及以上（开发和测试使用 Python 3.12，Windows 10）
- 依赖：`PyQt5`、`cryptography`、`bcrypt`

### 运行

**Windows**：双击 `start.bat`。脚本会检查 Python 和依赖，缺少时自动安装，然后启动程序。

也可以手动运行：

```bash
pip install -r requirements.txt
python main.py
```

> `start.bat` 会带着控制台窗口启动程序，报错信息和崩溃调用栈会直接显示在窗口里，适合调试。

## 打包成 exe

双击 `build.bat`，会依次执行：

1. 检查依赖，缺少 PyInstaller 时自动安装
2. 运行全部测试，**测试不通过就停止打包**（没有安装 pytest 时跳过这一步）
3. 生成多尺寸的程序图标
4. 用 PyInstaller 打包成单个 exe

打包结果在 `dist\CipherBox.exe`（约 40 MB），中间文件在 `build\`，可以随时删除。

注意事项：

- 单文件 exe 每次启动要先解压到临时目录，双击后大约 2–4 秒才出现窗口。想启动更快，可以把 `build.bat` 里的 `--onefile` 改成 `--onedir`，这样会生成一个文件夹，需要整个文件夹一起分发
- exe 没有控制台窗口，出现问题时请用 `start.bat` 运行源码查看报错
- 打包日志中的 `update_exe_pe_checksum` 警告通常是杀毒软件在扫描新生成的 exe，自动重试成功即可忽略

## 使用说明

### AES 对称加密

1. 输入密码
2. 在「输入」框填写明文，点「加密」，结果以 Base64 显示在「输出」框
3. 解密时粘贴密文，用**同一个密码**点「解密」

「输出转为输入」可以把结果移回输入框，方便马上验证解密。

### RSA / ECC 公钥加密

1. 选择密钥长度（RSA）或曲线（ECC），点「生成密钥对」；也可以导入或粘贴已有的密钥
2. **公钥加密**：需要公钥框里有公钥
3. **私钥解密**：需要私钥框里有私钥；私钥加了密码的话会弹框询问

密钥相关操作：

| 操作 | 说明 |
|---|---|
| 导入公钥 | 自动识别格式并转换成标准 PEM。误选了私钥文件时，会自动从私钥中提取公钥 |
| 导入私钥 | 加密的私钥会弹框询问密码，取消则原样保留，解密时再输入 |
| 由私钥生成 | 根据右侧私钥计算出对应的公钥 |
| 导出公钥 | 保存为 `.pem` 文件 |
| 导出私钥 | 可设置保护密码（需输入两次确认），留空则不加密 |

> 公钥可以公开给任何人，用来给你加密消息；私钥只有你自己能用来解密，请妥善保管。

### SHA-256

输入任意文本，下方实时显示 64 位十六进制哈希值。SHA-256 **不能解密**；要确认内容是否被改动，对它重新计算哈希并和原哈希比对即可。

### bcrypt

- **生成哈希**：输入密码，拖动滑块选择 cost（每加 1，计算时间约翻倍），点「生成哈希」。同一密码每次生成的结果都不同，这是因为自带随机盐，属于正常现象
- **验证密码**：输入密码和哈希（可以点「使用上方结果」），点「验证」，结果以绿色（匹配）或红色（不匹配）显示

bcrypt 最多只支持 **72 字节**的密码（一个汉字占 3 字节），超出时会给出提示。

### Base64

- **编码**：勾选「URL 安全」后用 `-` `_` 代替 `+` `/`，适合放进网址或 JWT
- **解码**：自动识别标准和 URL 安全两种写法，缺少末尾的 `=` 或夹杂换行也能解码
- **字符编码**：解码结果乱码或报错时，可以尝试切换 UTF-8 / GBK

> Base64 只是编码，不是加密，任何人都能还原。需要保密请使用 AES / RSA / ECC。

## 支持的密钥格式

| 格式 | 示例开头 | 公钥 | 私钥 |
|---|---|:-:|:-:|
| PEM（SPKI / PKCS#8） | `-----BEGIN PUBLIC KEY-----` / `-----BEGIN PRIVATE KEY-----` | ✓ | ✓ |
| PEM（PKCS#1 / 传统格式） | `-----BEGIN RSA PUBLIC KEY-----` / `-----BEGIN RSA PRIVATE KEY-----` | ✓ | ✓ |
| 加密的 PEM 私钥 | `-----BEGIN ENCRYPTED PRIVATE KEY-----` | — | ✓ |
| OpenSSH | `ssh-rsa AAAA...` / `-----BEGIN OPENSSH PRIVATE KEY-----` | ✓ | ✓（可加密） |
| X.509 证书（PEM / DER） | `-----BEGIN CERTIFICATE-----` | ✓（提取证书中的公钥） | — |
| 无头尾的纯 Base64（DER） | `MIIBIjANBgkqhkiG9w0BAQEFAAOC...` | ✓ | ✓ |
| 二进制 DER 文件 | `.der` / `.cer` | ✓ | ✓ |

文件开头带 BOM（例如用记事本保存的文件）也能正常读取。导入后统一显示为标准 PEM（公钥 SPKI，私钥 PKCS#8）。OpenSSH 格式的 ECC 密钥只支持 P-256 / P-384 / P-521 三种曲线。

## 密文格式

所有密文都是 Base64 字符串。如果需要在其他程序中解密，按下面的布局解析（`‖` 表示字节拼接）：

| 算法 | 密文布局（Base64 解码后） | 参数 |
|---|---|---|
| AES | `salt(16) ‖ nonce(12) ‖ 密文 ‖ tag(16)` | Scrypt(n=2¹⁵, r=8, p=1) 派生 32 字节密钥；AES-256-GCM |
| RSA | `被包装的会话密钥(密钥长度/8) ‖ nonce(12) ‖ 密文 ‖ tag(16)` | 随机 32 字节会话密钥用 RSA-OAEP 包装（MGF1-SHA256，SHA-256，无 label）；正文用 AES-256-GCM |
| ECC | `临时公钥点(未压缩) ‖ nonce(12) ‖ 密文 ‖ tag(16)` | ECDH 共享密钥经 HKDF-SHA256（salt 为空，info = `CipherBox-ECIES-v1` ‖ 临时公钥点）派生 32 字节密钥；AES-256-GCM，AAD 为临时公钥点 |

明文统一按 UTF-8 编码。

## 项目结构

```
encrypt-tool/
├── main.py                 # 程序入口
├── start.bat               # 调试运行 / 运行测试（start.bat test）
├── build.bat               # 打包 exe
├── requirements.txt
├── crypto_core/            # 算法层：只处理字符串，不依赖界面，可单独复用
│   ├── common.py           #   统一异常（CryptoError 等）、Base64、AES-GCM 封装
│   ├── keys.py             #   密钥格式识别、加载、序列化
│   ├── aes_cipher.py
│   ├── rsa_cipher.py
│   ├── ecc_cipher.py
│   ├── hashing.py          #   SHA-256、bcrypt
│   └── base64_codec.py
├── gui/                    # 界面层
│   ├── theme.py            #   颜色和全局样式表（改配色只需改这里）
│   ├── widgets.py          #   卡片、文本框、提示框等通用组件
│   ├── sidebar.py          #   左侧导航栏
│   ├── worker.py           #   后台线程任务
│   ├── main_window.py      #   主窗口，注册导航和页面
│   ├── assets/             #   样式用到的 SVG 图标
│   └── pages/              #   各功能页面
├── tools/make_icon.py      # 生成 exe 图标
├── tests/                  # pytest 测试
└── docs/images/            # README 截图
```

## 开发

运行测试（共 102 个，覆盖算法层和界面流程）：

```bash
python -m pytest
```

或者在 Windows 上执行 `start.bat test`。

新增一个功能页面的步骤：

1. 在 `crypto_core/` 中实现算法，出错时抛出 `CryptoError`（带中文说明），并在 `tests/` 中补充测试
2. 在 `gui/pages/` 中新建页面，继承 `BasePage`；耗时运算用 `self.run(...)` 放到后台执行
3. 在 `gui/main_window.py` 的 `NAV_GROUPS` 和 `self.pages` 中注册，两者的顺序要一致

## 安全说明

- 加解密使用成熟的 [cryptography](https://cryptography.io/) 和 [bcrypt](https://pypi.org/project/bcrypt/) 库实现，但本工具本身没有经过专业的安全审计，处理高度敏感的数据前请自行评估
- AES 的安全性取决于密码强度，请使用足够长、不易猜到的密码
- 私钥一旦泄露，用对应公钥加密的所有内容都能被解密；导出私钥时建议设置保护密码
- 不要用 SHA-256 或 Base64 存储密码；存储密码请使用 bcrypt
