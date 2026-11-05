# G0 Windows 复测手册

所有命令在MarcoRemote根执行。先让电视保持开机、同一LAN；确认设备IP，勿将历史IP当identity。只针对用户指定设备探测，不扫描网段。原始输出保存到被忽略的private目录；本手册占位符需要替换。

## 1. 准备固定工具

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r tools/requirements-g0.txt
New-Item -ItemType Directory -Force private | Out-Null
.\.venv\Scripts\python.exe -m pip freeze > private/environment.txt
$tvIp = '<电视当前IPv4>'
$lanIp = '<Windows物理以太网或Wi-Fi IPv4>'
$adbPath = '<已有Android platform-tools的adb.exe绝对路径>'
$tvSerial = $tvIp + ':5555'
```

requirements锁定协议提交和直接运行依赖；传递依赖未全锁，保留freeze以重现实验，本次不是供应链全量审计。没有安装完整上游demo的pynput/pyaudio，不捕获全局键盘、不发语音/电源键。开发工具许可说明见报告；依赖只装venv，不复制到产品。

## 2. 只读设备检查

如果电视已有用户批准的ADB网络连接，可连接并读取；没有既有授权时**不要自动启用调试或改系统设置**，先跳过adb参数做网络探测。

```powershell
& $adbPath connect $tvSerial
& $adbPath -s $tvSerial shell getprop ro.product.model
& $adbPath -s $tvSerial shell getprop ro.build.version.release
.\.venv\Scripts\python.exe tools/g0_probe.py --host $tvIp --interface $lanIp --adb $adbPath --serial $tvSerial --output private/g0-probe.json
```

无ADB的版本：

```powershell
.\.venv\Scripts\python.exe tools/g0_probe.py --host $tvIp --interface $lanIp --output private/g0-network-only.json
```

成功仅表示probe执行完；逐项检查result、exit、records，不能用脚本exit0宣称有v2。TCP open只证明监听，不能证明协议。mDNS零条要同时考虑物理网卡选错、多播隔离、路由、设备休眠；不要自动关闭Windows防火墙。refused与timeout保留不同错误，不均写成“不支持”。读取/proc失败则标unknown，不把空结果当无监听。

## 3. 配对与交互测试

只有发现兼容服务/端口可达才进入成功路径验证；当前小米本轮已经在连接阶段失败，不必反复要配对码。实验工具因上游CERT_NONE必须显式确认lab模式；只用于指定可信测试LAN，不能据此通过生产TLS安全门槛。

```powershell
.\.venv\Scripts\python.exe tools/g0_session.py --host $tvIp --identity private/identity/this-tv --pair --accept-lab-unverified-server | Tee-Object private/g0-session.jsonl
```

保持同一进程、同一配对socket，电视显示六字符hex后在隐藏输入提示输入，**不写命令行参数、不截图归档配对码**。secret_ack才是协议配对完成；然后必须等session_ready。证书/私钥保留在每电视单独目录，不提交。若交互主机管道影响隐藏输入，去掉Tee-Object在正常PowerShell终端运行，再仅整理非秘密事件。

在电视无敏感操作的普通桌面上，手工依次输入 `right`、`left`、`down`、`up`，每个之后观察并回答yes/no/unknown；边界不动不能直接算失败，先把焦点置于可移动区域。工具只发SHORT方向键，不含确定、主页、电源、音量、文本或shell。key_queued不是电视执行ACK；人工观察记为D-human，视频/截图另标，不能标成自动图像验证。

输入 `reconnect`，确认local_disconnect→reconnected且沿用同identity，无需再输入配对码；再手动发左右各一次确认有效。输入quit退出；随后重新运行不带--pair验证进程重启后的身份复用：

```powershell
.\.venv\Scripts\python.exe tools/g0_session.py --host $tvIp --identity private/identity/this-tv --accept-lab-unverified-server
```

记录首次配对、会话握手、四向可见变化、主动断开、同进程重连、重启进程重连分别的结果。库没有逐键应用效果ACK，不记录“已成功控制全系统”。固件/Remote Service版本/测试App/网络与时间必须随报告保存；不同端口的证书固定策略尚不在此工具实现中。

## 4. 日志与证据判定

建议每次运行用独立目录保存probe JSON、session事件、freeze、型号/固件及观察表。不要用上游DEBUG日志：可能包含PIN、文本或其他环境信息。runner屏蔽第三方日志，仅记事件/错误类型；其成功路径目前未经过真机验证。原始包/监听信息只本地保存，向PR提交人工审查后的摘要：设备别名、型号、系统、端口结果、错误码、时间、证据类别；不得上传identity目录或完整原始网络日志。

| 结果 | 合法结论 |
|---|---|
| 没ADB、没发现、TCP timeout | 当前网络无法确认；身份/服务均待验证 |
| ADB身份确认、已知包缺失、TCP refused | 当前设备状态无可达v2；仍不能断言永久不支持 |
| TCP open但Polo失败 | 端口可达，协议/配对未通过 |
| secret_ack + session_ready | 配对与协议握手成功；方向键效果待观察 |
| key_queued但无观察 | 仅客户端发送，设备效果unknown |
| 真机焦点变化 + 重连后再成功变化 | 对本机/本App确认方向键与身份复用，非所有品牌/输入类型 |

测试脚本回归：`python -m unittest discover -s tests -v`。上游协议测试需另检出固定SHA并安装pytest/pytest-asyncio；执行其tests，报告T而非D。不要为让测试通过改稳定版代码、系统服务或权限。
