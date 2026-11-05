# G0：Android 9 小米电视验证报告

日期：2026-11-05，Asia/Shanghai。范围已按本轮要求调整为 Windows 真机验证，不开发完整 iOS、桌面接收端或游戏手柄。分支 `research/g0-xiaomi-tv`；Marco TV 检出未修改、未切分支、未安装 APK、未增加权限。

## 结论

**D（真实设备）：已成功通过既有 ADB 授权连接 MiTV-ASTP0，Android 9/API 28、固件 `22.8.30.1385`。当前状态下未能建立 Android TV Remote v2 连接，配对在 TCP 连接阶段失败。G0 的“v2 可用性成功门槛”未通过。** 这是对这台设备本次配置的结论，不是对整个型号或全部小米电视的永久否定。

ADB 仅用于身份、包与监听信息读取；没有执行 `input keyevent`，因此不存在把 ADB 控制伪装成 v2 成功的问题。没有尝试安装 Google 服务、启用服务、更改防火墙、root 或切换系统桌面。

分级：**C=固定源码依据；T=本次自动化/mock测试；D=真实设备/网络观测；P=拟议设计或待验证**。D 中区分“可到达设备”“协议建立”“用户可见输入效果”，不能相互代替。

## 真机证据

可公开的去地址摘要：[g0-20261105.json](evidence/g0-20261105.json)。原始日志保留在本地 `private/g0-probe.json`、`private/g0-session.jsonl`，已被Git忽略；不要上传原始监听表、私钥、完整服务名、配对码或环境地址。摘要带原始probe文件SHA-256，仅证明归档对应关系，不是第三方设备认证。

| ID | 实际执行 | 结果 | 边界 |
|---|---|---|---|
| D01 | 既有adb连接，再读model/release/sdk/display.id | MiTV-ASTP0、9、28、22.8.30.1385 | ADB可用不表示v2可用 |
| D02 | `pm list packages -u com.google.android.tv.remote`、`pm path com.google.android.tv.remote.service` | 前者exit0为空；后者exit1为空；补充dumpsys明确Unable to find package | 针对已知包名，不排除其他包实现兼容协议 |
| D03 | 物理以太网源地址绑定，6466/6467各三轮TCP连接 | 六次均ConnectionRefusedError / 10061 | 当前IPv4端点；不是全网扫描，也不是历史状态 |
| D04 | 指定同一物理网卡浏览 `_androidtvremote2._tcp.local.` 15秒 | 流程完成，记录0条 | mDNS阴性受网络/多播影响，不能单独证明不支持 |
| D05 | 读取 `/proc/net/tcp` 与 `/proc/net/tcp6` | 两次exit0，可见LISTEN记录无6466/6467 | 可读取表的快照，无持续抓包；`ss`不存在，未用它作为证据 |
| D06 | 固定androidtvremote2调用 `async_start_pairing` | 12:41:26尝试，12:41:28返回CannotConnect，cause=ConnectionRefusedError | 未进入TLS/Polo，未显示/提交配对码 |
| D07 | 查询remote相关包 | 存在小米remotecontroller服务与其他remote包 | 名称不证明v2；不探测其未审核私有协议 |

主probe开始于12:40:34北京时间，摘要时间以UTC记录；IPv6表是随后补充读取，摘要的utc是运行起点，并非所有观测同时发生。原始环境地址只在本地日志。设备上Marco TV包的版本查询为0.15.0/versionCode36（补充只读查询）；未据此测试任何原生远程功能。

协议失败日志的非秘密内容：

```text
2026-11-05T04:41:26.539885Z pair_start_attempt
2026-11-05T04:41:28.606433Z failed CannotConnect cause=ConnectionRefusedError
2026-11-05T04:41:28.606477Z local_disconnect_finally
```

`local_disconnect_finally` 仅代表客户端清理，**不是建立过远程会话再成功断开**。方向键、电视侧释放、断开后重连均未能执行，不把失败重复连接称为成功重连。

## 能力矩阵

| 能力 | C 源码依据 | T 自动化 | D 当前小米真机 | P/下一步 |
|---|---|---|---|---|
| 设备身份/网络可达 | probe固定只读命令 | 未用mock证明设备身份 | 已读取真实型号/固件，ADB可达 | 后续复测仍重新确认身份 |
| v2发现 | zeroconf固定版本API | 不等于真实发现 | 15秒未发现 | 路由变动/服务变化后再测 |
| v2端口/TLS | androidtvremote2默认6467/6466 | TCP结果分类测试通过 | 端口拒绝，TLS未发生 | 不得声称证书一致/加密验证通过 |
| v2配对 | async_start_pairing/finish_pairing | 上游pairing测试通过 | 连接失败，未配对 | 有服务电视再测试secret_ack |
| v2方向键 | send_key_command→remote_key_inject | 上游remote测试通过 | 未执行 | 需可见焦点变化证据 |
| v2断开/重连 | disconnect/async_connect | 上游生命周期测试通过 | 未建立会话，不适用成功判定 | 复用同identity再连并再次按键 |
| Marco原生卡片焦点 | HomeView现有row/selected逻辑 | 新接口未实现、未测试 | 未验证 | 设计见备选方案 |
| 自动路线选择 | 当前没有实现 | 未测试 | 未验证 | scope/能力/授权/foreground共同选择 |
| 跨应用输入/鼠标/手柄 | 不在本轮范围 | 未测试 | 未验证 | 不扩展 |

## 自动化证据（独立于真机）

- **T01**：`python -m unittest discover -s tests -v`：4 tests，OK。验证方向键白名单拒绝power/enter/home/shell/text、拒绝与超时不被判成功、TCP指定源地址及socket关闭。代码：[test_g0_tools.py](../tests/test_g0_tools.py)。mock不会产生D级证据。
- **T02**：本轮重跑固定 `androidtvremote2@f49cf04703af1565e6216f1fc095b7d0477ca4a4` 全部tests：**134 passed in 1.03s**。此前研究的1.27秒是另一次运行，不能混写。Python3.13，pytest9.2.0；详细依赖见requirements与操作手册。
- session runner仅真实执行了连接失败路径。成功配对、交互输入、重连、证书兼容分支尚未真机执行，也未宣称此小工具已成为生产遥控适配器。

## 工具审核与使用边界

使用之前已检查androidtvremote2的Apache-2.0许可证、配对/remote/base调用链，固定原研究SHA，不使用无项目许可的androidremote代码。本轮只用库API，不复制proto或实现。新增两个Python脚本是本项目验证代码；未自行给整个项目改许可证。

新增发现依赖zeroconf 0.148.0的PyPI元数据为LGPL-2.1-or-later，[上游发行页](https://pypi.org/project/zeroconf/0.148.0/)及本地已安装metadata均已查阅；仅作为独立venv中的开发测试依赖，未复制/修改/打包进产品。直接依赖元数据：ifaddr0.2.0 MIT，aiofiles25.1.0 Apache-2.0，cryptography50.0.2 Apache-2.0 OR BSD-3-Clause，protobuf7.36.2 BSD-3-Clause。此处为开发工具准入审查，不是完整传递依赖SBOM或未来App分发批准。

**C：** upstream `_load_cert_chain` 设 `CERT_NONE`，没有服务器pin。runner强制显式 `--accept-lab-unverified-server`，只供指定目标、可信测试网络验证；不自动安全降级，不沿用到生产。此次TCP即失败，没有秘密传到电视，也未证明TLS安全。原生备选的安全端点必须另行实现。

## 可重复复测与无法连接时的交付

完整步骤、配对/方向键/重连与日志判定见 [G0_RUNBOOK.md](G0_RUNBOOK.md)。当前并非“没有真机连接”：真实ADB与探测已经完成，缺少的是v2服务连接。无需用户提供配对码，因为此次未到显示码阶段。以后同机服务状态改变或新增有服务设备时可直接按手册复测，无需开发iOS。

## 下一阶段最小任务

1. **优先Marco原生最小切片**：先在独立MarcoTV功能分支做纯焦点状态转换/保护条件测试，再接一个用户主动开启的受限安全会话；只允许卡片区四方向+只读焦点，不接确定/应用启动。当前没有修改MarcoTV。
2. Windows终端对该新接口执行“授权→快照→一次方向→验证revision→断开→重新授权”，由电视画面证明焦点变化；本机操作与remote冲突、前后台、弹窗、过期都要拒绝旧命令。
3. 若有自带Remote Service的电视，只复用现有G0 runner验证配对/四向/重连；记录服务版本、系统和固件，并另做6467/6466证书绑定spike。当前小米不为此安装系统服务。
4. 两条路线各有至少一个真实正例后，再实现统一选择器的确定性测试和最小客户端；完整iOS与桌面receiver继续后置。

源码定位见 [G0_NATIVE_FALLBACK.md](G0_NATIVE_FALLBACK.md) 与既有 [REMOTE_RESEARCH.md](REMOTE_RESEARCH.md) 的V1–V5、M1–M6。报告不将未实现设计或上游mock测试提升为真实设备支持。
