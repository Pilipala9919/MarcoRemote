# Marco Remote 技术研究

研究日期：2026-11-05（Asia/Shanghai）。范围：指定的六个公开项目，以及 Marco TV 0.15.0 基线。初轮仅交付本文与架构文档；后续G0已新增 [真实设备报告](G0_DEVICE_REPORT.md)、[复测手册](G0_RUNBOOK.md)、[原生焦点备选](G0_NATIVE_FALLBACK.md) 及独立Windows验证脚本。未移植第三方实现，未修改、构建或安装本机稳定版应用。

**G0更新（D）：** 已用Windows连接真实MiTV-ASTP0/Android9；三轮6466/6467拒绝连接、15秒指定网卡mDNS无v2记录、已知Google Remote Service包未找到，协议配对首步CannotConnect。方向键/成功会话断开重连未验证。后文§9“尚未执行”是初轮研究时点记录，当前状态以G0报告为准，不能继续当作没有接触过真机。原生备选仅控制Marco自身卡片焦点，属于P，尚无实现/设备成功证据。

**G1-A 更新：** 已交付纯焦点控制器与测试；安全会话及可见焦点目标尚未完成，证据见 [G1 报告](G1_DEVICE_REPORT.md)。本文初轮与 G0 时点的“尚无实现”不再代表纯控制器状态，但仍适用于原生网络端点。

## 1. 结论与证据等级

推荐采用 **iOS 原生控制器 + 三类独立适配器**：Android TV Remote v2 用于电视按键/焦点；Marco 管理适配器用于桌面配置；自有加密协议与电脑接收端用于真正的鼠标/键盘。无服务的 Android 电视不能仅凭安装 Marco TV 获得全局输入能力。架构决策、接口及验收门槛见配套文档。

全文使用以下等级，避免把源码、作者描述和实机结果混为一谈：

| 标记 | 含义 | 能证明什么 |
|---|---|---|
| C | 本次固定提交的源码已检查 | 函数、分支、数据流、许可声明确实存在；不证明硬件行为 |
| T | 本次实际运行测试 | 仅覆盖明确列出的测试和环境 |
| O | 官方平台文档 | 平台约束；厂商实现仍需测试 |
| U | 上游作者描述或测试文件 | 未在本次设备上复现，不升级为 T |
| P | 工程推断、建议或待验证设计 | 必须通过架构文档的验证门槛才能承诺支持 |

| 结论 | 等级与直接依据 |
|---|---|
| Remote v2 是 TLS + varint 长度前缀 protobuf；6467 配对，6466 控制 | C：[V1]、[V2]、[V3]；T：134 项 Python 测试通过，但没有连接电视 |
| androidremote 的触控板输出 DPAD，不是真正鼠标 | C：[A1] `Touchpad → onKey → sendKey`，滑动距离被量化为方向键 |
| 普通 Android 应用没有任意跨应用注入权限 | O：[O1] `INJECT_EVENTS` 为 signature；C：[M4] 现有无障碍配置没有取窗口树/发手势能力 |
| Sofatap 已区分桌面鼠标与电视节点光标 | C：[S7] 明确 `rawMouse=false`、`drag=false`、`hardwareQualified=false`；不能称为全电视鼠标方案 |
| PhoneHttp 能服务管理页面，不能直接充当持续低延迟控制传输 | C：[M1] 普通 ServerSocket、每请求关闭、正文落盘；P：另建控制传输 |
| “使用 TLS”不等于已经校验电视身份 | C：[A3] 接受任意服务器证书；[V1] `CERT_NONE`；P：自有协议严格固定证书，v2 增加配对后证书绑定实验 |
| Penput 的低开销路径有参考价值，现有 UDP 安全模型不适合直接采用 | C：[P1] 依赖来源地址、无消息认证/序号；[P2] 最新绝对坐标覆盖；P：不能将此丢弃规则套到相对位移 |
| androidremote 没有找到覆盖原创代码的项目许可证 | C：固定树中无 LICENSE/COPYING/NOTICE，README 仅声明外来 proto 来源 [A5]；不得据此复制 Kotlin 实现 |

## 2. 研究基线及可复现性

检出上游默认分支当日 HEAD，以下 SHA 是本文唯一源码基准，不把 HEAD 当作各项目正式发布版。固定提交链接见文末证据索引。

| 项目 | 固定提交 SHA | 提交时间（原仓库时区） |
|---|---|---|
| theharisshah/androidremote | `12e9438699bc558f9ff80e09aca5edf26b04dc14` | 2026-08-22 +05:30 |
| tronikos/androidtvremote2 | `f49cf04703af1565e6216f1fc095b7d0477ca4a4` | 2026-11-02 -08:00 |
| chekusu/sofatap | `9ec71a05f1cc137972f111e3527c8a869640a199` | 2026-11-03 +09:00 |
| eunhhu/penput | `1d7d11a0594127e2c682d7910a6677ce6d4909b9` | 2026-10-26 UTC |
| KDE/kdeconnect-kde | `aee1439f80dc1870117825edb3be70aed6e75479` | 2026-11-04 +01:00 |
| Genymobile/scrcpy | `a60891aea193d92e7e5c3942700eca63f9d19a5f` | 2026-10-08 +02:00 |
| Pilipala9919/MarcoTV | `a9d6cb8b64fd2e9030c82addd22edc40a5e755c0` | 2026-11-04 +08:00 |

**T/C：本机基线核对。** `D:\Marco` 开始时为空；实际稳定版检出位于 `D:\TV`，origin 为指定 MarcoTV URL，HEAD 与表中一致。[M5] manifest 为 `versionName=0.15.0`、`versionCode=36`。`git status --short` 只有已存在的未跟踪文档 `docs/项目复审-2026-11-04.md`，未处理它。本次研究与测试检出放在 `%LOCALAPPDATA%\Temp\marco-remote-research-20261105`，没有把上游实现加入 `D:\Marco`。

本机稳定版两文件 SHA-256（用于交付后确认未动）：

- `PhoneHttp.java`：`127731D1CCAD69F594ECEBDB57D55CFEEB37E5D3CDE5540B512593F92A9401B2`
- `PhoneManager.java`：`C51151E609F66F8F39E5A1A5DE3502B22217ECFD59FC854C58BDBB7AB1F81C09`

## 3. 六个项目逐项研究

### 3.1 androidremote：Android TV v2 的 Android 客户端参考

**C，发现链：** [A2] `TvDiscovery → NsdManager.discoverServices(_androidtvremote2._tcp) → resolveService → 设备列表`。每次解析使用独立监听器，避免并发复用异常。UI 支持手工地址作为发现失败时的入口；发现报文和名字不构成认证。

**C，协议链：** [A4] `PairingSession.begin → Tls.connect → pairing_request/options/configuration → configuration_ack`；`complete(code) → PairingSecret.compute → secret → secret_ack`。六字符是十六进制，不是六位十进制 PIN。digest 输入为双方 RSA modulus/exponent 的无符号大端表示及代码最后两字节；首字节用于校验。不能把 Java BigInteger 的符号补零带入摘要。[A6]

**C，实时链：** [A7] `RemoteClient` 接收电视驱动的 configure/set_active/start，维护 feature 交集，读循环回复 ping；写入交给单独 executor，防止 UI 阻塞及帧交错。这个模块拆分方式值得参考，具体 Kotlin 实现当前不得复制。

**C，触控板：** [A1] `detectTapGestures → DPAD_CENTER`；`detectDragGestures → travel 累积 → 按主轴消耗 step → DPAD_*`。没有从这里通向桌面 dx/dy 鼠标注入的路径。**U：** README 的小米电视验证、待机唤醒等叙述是作者经验，本次没有复现，更不能扩展为所有小米/国产电视支持。[A5]

**C/P，安全缺口：** [A3] `AcceptAnyServerCertificate` 不验证服务端身份；配对计算绑定当次证书，并不自动让之后每次连接验证同一台电视。研究应复核实现而非采信注释的安全保证。Marco 的 v2 适配器须另做服务端证书固定及证书变更重新配对；6467 与 6466 是否使用同证书必须实机确认，不能默认允许第二个端口的任意证书。

### 3.2 androidtvremote2：可测试的 v2 协议依据

**C：** [V1] `AndroidTVRemote.async_start_pairing → PairingProtocol`；`async_connect → RemoteProtocol`；证书由 `certificate_generator.py` 生成并保存，正常重连复用 identity。默认端口 6467/6466；`_load_cert_chain` 同时设置 `check_hostname=False`、`CERT_NONE`。证书文件是认证资产，不是可以随意清除的缓存。

**C/T：** [V3] `ProtobufProtocol.data_received` 累积 TCP 字节，处理 varint 跨包及 body 跨包；发送先长度再 protobuf。不可假定一次 read 等于一条消息，也不可用单字节长度。本次 `test_base.py` 等测试通过，包含分片/合包/损坏长度场景。[V5]

**C：** [V4] `RemoteProtocol._handle_message → feature 交集 → remote_configure / remote_set_active / remote_start`；`remote_ping_request → remote_ping_response`；`send_key_command → remote_key_inject`；`send_text → remote_ime_batch_edit` 使用 IME counter/field counter；`send_launch_app_command → remote_app_link_launch_request`。文本字段必须结合电视当前输入上下文验证，不能宣称任意应用、任意语言、任意焦点都能直接输入。

**C/P：** 已研究 schema 和客户端没有可用的通用连续鼠标 dx/dy API。[V6] 包含按键、IME、音量、语音等消息，不能据“协议远程控制”推断鼠标支持；此结论限制在已知实现，并非宣称所有未公开扩展绝不可能。Python 库适合作为测试参考端，不建议为了 iOS 嵌入 Python 运行时。

**C：** 断链后 `_async_reconnect` 退避；证书拒绝与普通网络故障分开处理。[V1] Marco 也应区分未配对、证书变化、服务缺失和临时断网，不能统一显示“连接失败”。语音有独立会话、分片及超时逻辑，增加音频权限和机型变量；建议排在按键/文本验收之后。[V4]

### 3.3 Sofatap：最接近 iOS + 桌面接收端的参考

**C，手势链：** [S1] `NativeControls.TouchSurface → touchesBegan/Moved/Ended/Cancelled → TouchGestureState → 动作回调`。接触点按 identity 追踪，多指使用质心；取消、切换设备、改变手势配置会结束旧动作。[S2] 状态机独立于网络，支持单击、双击、长按拖拽、多指滚动及取消。源码参数包含 300 ms hold、280 ms 双击窗口、桌面移动 3 point 起步阈值及静止容差 7 point。这些是该版本参数，不是 Marco 的已测最优值。

**C，位移映射：** [S2] `DesktopPointerMotion.feed` 用 UIKit point/s 估速度，平滑速度估计而不平滑方向/位移，增益由 1 增至 2.2；长间隔重置速度。这样设计意在减少停止后的拖尾，效果仍需实测。不要把 UIKit point 当作 iPhone 物理像素再乘屏幕 scale，也不要把电视焦点步进与桌面加速共用。

**C，低延迟链：** [S3] `moveFromTouch → move → flushMovement → sendMovement → WebSocket → ACK → drain`。触摸回调立即尝试发送，另有 60 Hz timer 排空；并非一律等显示帧再发。LAN 最多 12 个移动在途，peer 路由 8 个；未发相对位移做求和，120 ms 旧批次过期，最老 ACK 过久阻塞继续入队。拖拽尾部必须先处理再 mouse-up，失败后关闭并释放。窗口值和源码中延迟注释不是本次测量。

**C，配对与传输：** [S4] URI 带 host/port/token/fingerprint；iOS 固定 DER leaf SHA-256，再用指定 anchor/SSL policy 校验，不是无条件接受自签名；配对库写入 Keychain，`WhenUnlockedThisDeviceOnly`。[S5] 主机持久化证书与 32 字节随机 token，Windows 使用 DPAPI、非 Windows 采用权限受限文件。当前主机是一个 receiver token，不能等同于每手机独立授权、独立撤销。

**C，接收链：** [S6] `.NET Kestrel HTTPS /control → 拒绝 Origin → Bearer 常量时间比较 → 单控制者 semaphore → WebSocket → Protocol.Parse → ActionSession.Execute → IInputInjector.Apply`。64 KiB 帧上限，20 秒完整消息空闲预算；断开 finally `ReleaseAll`。拒绝 Origin 只是挡浏览器跨站入口，真正认证仍是 token + TLS。

**C，重复与结果语义：** [S10] `ActionSession` 缓存 UUID、内容摘要及 ACK；同 ID 不同内容拒绝，失败也缓存，避免部分注入后重试。ACK 表示该处理阶段结果，不证明应用 UI 达到目标。内存缓存有会话动作数量/文本额度上限，不能在高频长期会话中无限增长。

**C，发现：** [S11] `_sofatap-peer._tcp` 的 Bonjour service name 使用截断 fingerprint 作路由提示，最终仍验证完整 TLS pin。[S12] peer bridge 不终止 TLS。这个路径是可选 peer 机制，不应概括成所有平台已有同一套 LAN 自动发现。

**C，Android TV 限制：** [S7] `InputBridge.snapshot` 明确只提供 overlayCursor/nodeClick/scroll/global actions 等条件能力；[S8] `SofatapAccessibilityService.performInput → 节点收集/命中 → ACTION_CLICK/ACTION_SCROLL/performGlobalAction`，不是 `InputManager` 原生鼠标。overlay 画得出来不表示视频 Surface、游戏或自绘界面能接收鼠标。源码主动标记尚未硬件认证。另有 `RemoteV2Client` 与 IME 服务，但它们也不能自动赋予 raw mouse 能力。[S9]

### 3.4 Penput：轻量坐标流的取舍

**C，发送链：** [P3] `TouchPadUIView → updateTouch → 串行队列 → CADisplayLink.onFrame → sendMoveIfNeeded → NWConnection(.udp)`。HELLO 传客户端宽高，MOVE 传 u16 大端 x/y，PING/PONG 用同端单调时钟估 RTT。网络 MOVE 实际承载绝对位置；所谓 relative 模式先在手机端积分、限制在客户端画布，再发送绝对坐标。不是服务器端原生相对鼠标流。

**C，接收链：** [P1] `serve_udp → CLI approval → SocketAddr 绑定 → move_absolute`；[P2] 工作线程把最新坐标覆盖到单槽，再计算 `x/client_w*screen_w`、`y/client_h*screen_h`，调用 Enigo `Coordinate::Abs`。绝对坐标允许覆盖中间点；相对 dx/dy 若直接“只保留最后一包”会丢距离。屏幕范围、主屏选取和多屏负坐标都需要重新设计。[P2]

**C/P，边界：** UDP 仅比较来源 SocketAddr，超时 5 秒，没有代码可见的加密、消息认证、序号/重放窗口；CLI 人工同意不补足报文完整性。[P1] WebSocket 路径同样复用 approval/单客户端槽，不能因为叫 WebSocket 就视为 WSS。[P4] 本次未做攻击实验，只确认实现缺失。`Cargo.toml` 有 mdns-sd 依赖，但所查 `main/http/udp/websocket` 入口没有发现其调用；不能把依赖表写成“已实现 mDNS 发现”。[P5]

**P：** 可研究的思路是紧凑数据、限制队列和独立输入线程；不建议采用当前线协议或承诺“UDP 必然更快”。UDP 还需要丢包/乱序/鉴权/按钮可靠投递机制，MVP 优先有界 WSS。

### 3.5 KDE Connect：设备身份、插件与系统后端

**C，发现与加密链：** [K1] `LanLinkProvider → mDNS/UDP discovery → TCP → configureSslSocket → encrypted → secure identity → addLink`。UDP 默认 1716，TCP 监听选择 1716–1764。[K2] 已信任 peer 使用保存证书作为信任依据并 `VerifyPeer`，未配对使用 `QueryPeer`；`addLink` 比对证书身份与 deviceId，同设备替换 socket 时拒绝证书改变。[K1] 不能照搬“发现到同名就覆盖已配对设备”。

**C，配对链：** [K3] `PairingHandler.packetReceived/requestPairing/acceptPairing → pairingDone`，带请求时间及超时状态；verificationKey 对双方公钥和配对时间摘要后取可比对短码。用户确认发生在加密链路的设备身份上，不是只确认网络地址。[K4] `Device` 负责配对状态、插件加载和网络包分发。

**C，输入链：** [K5] `MousepadPlugin.receivePacket → AbstractRemoteInput.handlePacket`，编译时选择 Windows/macOS 后端；[K6] Windows 使用 SendInput；[K7] macOS 检查 AX trust 并调用 CGEvent 系列，拖拽与普通移动事件类型不同。这种“协议与平台注入解耦”值得采用，但 Qt/KDE 插件体系对 Marco 的小型接收端偏重是工程判断（P），不是性能实测结论。

**C/P，许可：** 所查 LAN/mousepad 文件是 `GPL-2.0-only OR GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL`，可按 GPL-3.0-only 分支审查与 Marco TV 的组合；不能用一句“KDE 都是 GPLv2”概括。仓库还有 LGPL/MIT 等其他文件，必须逐文件检查，尤其不要直接把 GPL 鼠标后端粘入计划独立发行的 iOS 客户端。[K8]

### 3.6 scrcpy：解释为什么“能注入”不代表普通 APK 能注入

**C，默认部署链：** [R1] 桌面端通过 ADB 部署并以 `CLASSPATH=… app_process` 启动 server；[R2] `Controller` 读控制消息，按消息类型执行 key/text/touch/scroll/UHID；[R3] `Device.injectEvent → wrappers.InputManager.injectInputEvent` 反射系统接口，代码处理 `INJECT_EVENTS permission` 错误。关键是 ADB/shell 执行身份和设备授权，反射本身不会提升普通 APK 的权限。

**C，HID 路线：** [R4] `UhidManager` 打开 `/dev/uhid` 创建 HID 设备；[R5] 文档也提示旧 Android 上权限失败。AOA/OTG 是另一条有线 USB 路径，可不依赖 ADB，也不能因此推出 iPhone 局域网控制无需权限。[R6]

**P：** scrcpy 更适合独立、明确开启的开发诊断或未来高级 ADB 后端，不做 Marco Remote 日常控制的必要条件。不把 ADB 端口开放、root、系统签名、启动 shell bridge 包装成“普通局域网配对”。MVP 不需要视频流；视频、音频和控制可分离的经验可参考，但不能借镜像延迟数字为触控板背书。[R1]、[R2]

## 4. Android TV 权限能力矩阵

| 路线 | 实际权限/前提 | 能做什么 | 不能据此承诺 | 证据 |
|---|---|---|---|---|
| Google/Android TV Remote v2 | 电视存在兼容 Remote Service；用户完成电视码配对 | 已知按键、IME、应用链接、状态 | 全局鼠标、任意国产电视支持、断电唤醒 | C：[V1]–[V6]；兼容性 P |
| Marco TV 普通应用 | 自身 UID/窗口、用户开启互联 | 自己的配置/卡片/壁纸/备份 | 跨应用 MotionEvent 注入 | C：[M2]；O：[O1] |
| 现有 HomeKeyService | 用户显式启用无障碍 | Home 兼容过滤、系统最近任务等既有动作 | 已有节点读取、任意坐标点击/拖动 | C：[M4] XML `canRetrieveWindowContent=false`，未声明 canPerformGestures |
| 新的可选无障碍接收端 | 用户另行开启；节点/手势能力显式声明 | 可访问节点动作、全局动作；API 24+ 可条件发触屏手势 | 真正鼠标、所有应用命中、不中断现有触摸 | O：[O2] dispatchGesture 会取消进行中手势；C：[S7][S8] |
| shell/ADB bridge | 用户开发者授权、受限 shell 进程 | 取决于系统/OEM的事件注入与管理能力 | 普通网络 token 等同 ADB 权限 | C：[R1]–[R4]、[M6] |
| 系统/OEM集成 | 对应签名或 OEM授予的特权 | 取决于系统契约 | 面向所有零售电视的可分发方案 | O：[O1]；P |

**C：** Marco `TaskBridgeServer` 要求 `Process.myUid()==2000`，通过 Binder 及调用 UID 认证，现有职责是固定系统任务操作。[M6] 它不是 PhoneHttp 的远程任意 shell 服务，不能直接接到公网/局域网输入 API；本方案不扩权。

**O：** 当前 Android 官方说明：target 37+ 的 Android 17 本地网络保护包括入站 TCP；target 较低与 Android 16 opt-in 情况不同。[O3] 不能沿用 androidremote README 的版本描述作为新接收端权限依据。电视端 SDK/target 的升级应单独验证，不在本次调整稳定版 manifest。

## 5. PhoneHttp / PhoneManager 可复用范围

**C，完整调用链：** [M3] `MainActivity.onCreate → new PhoneManager(this)`；`HomeView/SettingsNavigator → phone.show`；[M2] `show → 选 Wi-Fi/有线私有 IPv4 → new PhoneHttp(指定接口, port=0)`；[M1] `accept → readHead → Handler.check → 限额读取正文 → handle → response → close`。`MainActivity.onDestroy → phone.destroy`，管理状态明显依附 Activity，不能假设为后台常驻服务。

| 部分 | 已核实行为（C） | 后续处理建议（P） |
|---|---|---|
| 入口与二维码 | 本机显示 `http://地址:随机端口/#连接码`；code 为 16 字节随机数的 hex；5 分钟有效 | 旧浏览器入口保留。新 Remote 使用不同 scheme、证书指纹和一次性配对票据；不互换二维码 |
| 配对授权 | 一个 nonce/IP 锁定请求；电视前台弹允许/拒绝；同一会话只能一手机 | 复用显式电视确认原则；不能复用字段充当多设备永久 identity |
| 会话 | cookie、csrf、approved、generation 内存保存；15 分钟截止；POST 刷新时限；stop 清空 | 多设备持久信任、撤销、重连需要新模块；浏览器 session 不提升为永久 Remote credential |
| 浏览器保护 | Host 严格匹配；POST Origin；HttpOnly + SameSite=Strict；CSRF 常量时间比较；源 IP 绑定 | 保留旧路径规则。它们不提供网络加密，不能替代 TLS；IP 改变也会影响旧会话 |
| HTTP 边界 | 8 KiB header，5 s header deadline；线程池 4–8、队列24、每 IP 8；普通 body 64 KiB，upload 16 MiB，restore 128 MiB | 有界资源和先鉴权再上传的思路复用；HTTP 解析器不改造成 WS/TLS 协议栈 |
| 高频路径 | 每请求新连接、`Connection: close`；body 先落临时文件；UI FutureTask 最长等8秒 | 与手势低延迟目标不相容，新增独立长期控制通道，不调大线程池硬撑 |
| 管理业务 | revision 检查、前台要求、卡片/外观逻辑、预览回滚、单传输互斥 | 未来可在 GPL TV 模块内抽取 domain commands；保留冲突检查和电视确认 |
| 大文件 | 备份/上传/恢复有单传输闸门；恢复交给电视检查及确认 | 与输入队列/连接分离，避免大文件造成队头阻塞；先只保留浏览器管理入口 |
| 清理 | stop 清凭据、generation++、关闭 sockets/pool、取消预览 | 复用生命周期模式；新会话增加释放远程按键和拖拽，generation 不可跨设备复用 |

上表依据：[M1]（transport）、[M2]（`show/pair/check/action/main/stop/upload/restore`）、[M3]（lifecycle）。**T：** 18 项测试证实的是 PhoneHttp，不是 PhoneManager 的 Android UI 配对流程。[M7]

## 6. iOS 手势、映射与延迟的可用结论

| 问题 | 已验证依据 | Marco 设计取舍（P） |
|---|---|---|
| 原生还是网页 | C：[S1]、[P3] 都从 UIKit touches 取输入；不能据此量化网页一定慢多少 | SwiftUI 外壳 + UIKit 触面；识别器无网络依赖；网页保留管理 |
| 手指数量改变 | C：[S2] 明确状态转换/取消；[S1] identity 与质心处理 | 1→2、2→1重置基点，禁止质心跳变造成光标跳跃或误点 |
| 低速精度/快速跨屏 | C：[S2] 速度增益；[P3] 亚像素累计 | 输入单位用 point，相对值保留小数；系统后端分别标定，防双重加速 |
| 相对与绝对模式 | C：[P2][P3] Penput 线上为绝对；[S3] 相对量求和 | MVP桌面相对模式；绝对坐标需 displayId/布局版本及负坐标支持 |
| 高频队列 | C：[S3] 有界在途/过期；[P2] 单槽绝对值覆盖 | 相对移动合并求和；按键/点击/拖拽边沿严格有序；不可丢 mouse-up |
| 帧率 | C：[P3] display link发送；[S3] 触摸即时发送+timer兜底 | 从60Hz起步，验证120Hz；不承诺设备实际采样一定120Hz |
| 指标 | C：[S13] 分阶段 histogram；[P3] ping RTT | 分开记触摸投递、发送等待、网络RTT、接收队列、OS提交；光标可见延迟另用高速摄影测 |

没有本次 iPhone/电视/macOS 的触到可见延迟数据；不提供虚构的“低于10 ms”或“达到某产品手感”结论。任何期望值只出现在架构验收目标中。

## 7. Windows / macOS 接收端边界

**C/O：Windows。** Sofatap 的 `IInputInjector → WindowsInput.Apply → SendInput` 维护小数余量和 held 集合，检查部分注入、释放已拥有的按键。[S14] Microsoft 明确 SendInput 受 UIPI 限制，只能注入相同或更低完整性级别；返回值不专门指出 UIPI。[O4] 因此常规接收端应在登录用户桌面运行；对管理员窗口/UAC/锁屏显示不可用，不能通过无条件管理员自启解决。

**C/O：macOS。** [S15] `MacInput → QuartzEventSink → CGEventCreate* / CGEventPost`，检查 AX 信任/事件投递权限和 console session；跟踪 owned keys/buttons，拖拽事件要保留 down 状态。KDE 同样把 macOS 实现放在独立后端。[K7] Apple 有 AX trust 和 post-event access 检查 API。[O5] 这些调用不会自动给予权限，也不证明接收应用消费了事件。

**P：** 桌面共享网络/协议/授权逻辑、平台各自输入后端；托盘/菜单栏负责配对、暂停、撤销与权限状态。用户会话中的 agent 是输入执行者；不采用 Windows Session 0 服务直接操作桌面，也不让无界脚本/任意命令成为遥控协议。中文/emoji、组合键、物理键冲突和多屏 DPI 必须分平台验收。[S14][S15][O4]

## 8. 许可证与代码复用审查

下表是本次工程准入结论，不是对未来所有依赖或发行方式的批准。文件路径、版权声明、第三方 NOTICE、资源及生成文件须一起进入后续物料清单；仅使用一个项目的名称、许可证标签不能替代逐文件审查。

| 来源 | 本次许可证据 | 可考虑复用的条件 | 当前结论 |
|---|---|---|---|
| androidremote | 无项目 LICENSE；[A5] 仅归属两份外来 proto | 原创 Kotlin/UI 需权利人明确授权；proto 如需使用应从原始 Apache 来源取得并保留声明 | 原创实现禁止导入；仅记录观察到的协议行为 |
| androidtvremote2 | [L1] Apache-2.0；[V7] metadata 一致；polo.proto 有 Google 版权 | 保留许可/版权；标记修改；若有 NOTICE 保留其适用内容；检查生成 schema 来源 | 可列为协议/schema/测试参考的候选，本次未复制 |
| Sofatap | [L2] MIT；仓库另有第三方 licenses | 原创代码可在保留版权/许可条件下复用；.NET、QRCoder、Android依赖、Sparkle及素材另查 | iOS状态机/桌面设计优先参考；不批准整仓搬运 |
| Penput | [L3] MIT；[P5] crate metadata 一致 | 保留通知；Enigo/Tokio等锁定版本逐项审查；安全补齐不能省略 | 算法/线程模型参考；现线协议不采用 |
| KDE Connect | [K1][K5][K6][K7] 的多选GPL声明；[K8] LICENSES目录 | 特定文件可选择 GPL-3.0-only，与TV基线组合后履行对应源码、修改说明等义务；依赖/其他文件另审 | 不直接复制到独立 iOS/宽松许可核心；参考模块边界 |
| scrcpy | [L4] Apache-2.0，另有依赖及各文件头 | 同Apache义务，若打包 FFmpeg/SDL/libusb 等需单独审查实际版本与构建选项 | 仅作为可选高级后端依据，不打包整个镜像栈 |
| Marco TV | [L5] GPLv3文本；[M1][M2][M4] SPDX明确 GPL-3.0-only；[M8] NOTICE | TV内提取修改继续GPL-3.0-only、保留声明及对应源码；不能默认为新客户端可改成MIT | 业务复用限定TV模块；新客户端先独立编写 |

**O/P：** GitHub 可浏览/可 fork 不等于获准复制分发无许可代码。[O6] Apache-2.0 与 GPLv3 的兼容方向不能理解为可以把 GPL 文件重许可成 Apache；组合时仍须满足对应 GPL 义务。[O7] GPL 代码与商店分发条款、签名/安装限制之间需要发行前核对，不能未经审查承诺“iOS App Store 一定可上”。本方案优先独立客户端与网络协议互操作，但“分进程/走网络”本身也不是免除派生作品审查的法律保证。

**C/O，schema还要追溯上游：** [V6] `remotemessage.proto` 文件头指向 `louis49/androidtv-remote`；[V2] `polo.proto` 指向AOSP并注明来自louis49的OuterMessage修改。额外核实louis49当前LICENSE为MIT（Copyright 2021 louis49）[L6]，AOSP目录有 `MODULE_LICENSE_APACHE2` 与 `NOTICE` [L7]。因此后续引入schema/生成Swift时，应固定其实际原始版本、保留这些归属与通知，不能只放一份androidtvremote2的Apache许可证便宣称完整审查。本次没有导入schema，原始版本逐行对应仍是引入前门槛。

**本次执行结果：** 除研究目录的上游原样检出外，没有把任何第三方代码、proto、图标、证书、二进制复制到 Marco 项目；两份 Markdown 只含分析、链接及拟定接口。没有为 androidremote 补写或推定许可证。

## 9. 本次测试证据与未验证项

### T1：Marco PhoneHttp

在临时 MarcoTV 检出运行 `python scripts/test_phone_http.py`；JDK 为本机既有 Zulu 17.0.20.1，`JAVA_HOME` 仅在该子进程设置。输出结尾为 `OK 18 phone transport checks`，exit 0。[M7]

通过项：valid_query_decode、duplicate_length、chunked_framing、missing_length、negative_length、get_body、absolute_target、folded_header、header_limit、header_deadline_enforced、stale_part_files_cleaned_on_start、body_roundtrip、slow_headers_do_not_starve_requests、response_is_not_cached、oversized_body_rejected_before_upload、authorization_precedes_upload、temporary_bodies_removed、server_stops_listening。

测试 socket 绑定 127.0.0.1；没有连接电视或向桌面发送输入。不覆盖 PhoneManager、二维码审批 UI、TLS、鼠标、端到端延迟。

### T2：androidtvremote2

在独立 venv 安装该固定提交及 `[test]` 依赖，在仓库根运行 `python -m pytest -q`，exit 0，输出 **`134 passed in 1.27s`**。环境：Python 3.13；pytest 9.2.0、pytest-asyncio 1.4.1.post1、protobuf 7.36.2、cryptography 50.0.2、aiofiles 25.1.0。测试目录覆盖 framing、pairing、certificate generator、remote handshake/features/text/voice 和客户端生命周期。[V5]

这是 mock/单元测试结果，不是电视配对证据；尤其不证明当前 CERT_NONE 设计抵御中间人，也不证明中文输入的真实应用兼容性。

### 尚未执行

| 项目/场景 | 状态与原因 | 后续证据要求 |
|---|---|---|
| androidremote Gradle测试/电视控制 | 未运行；本次使用Python参考测试验证协议单元行为 | 正式许可确认后可跑JVM测试；电视配对单列 |
| Sofatap .NET接收端测试 | 未运行；项目 target net10.0，本机只有SDK 8.0.421；未改target或安装新SDK | .NET10隔离环境，先dry-run/假输入，再受控窗口实测 |
| Sofatap/Penput iOS测试 | 未运行；当前主机没有Xcode/iOS测试设备上下文 | 手势确定性测试、iPhone真机、弱网/前后台 |
| KDE/scrcpy完整构建与输入 | 未运行；仅源码/许可链研究 | 若进入产品路线，再准备各自依赖及授权设备 |
| Android TV真实配对/无障碍/待机 | 全部待测 | 至少一台Remote Service电视、一台无服务国产电视，记录固件/服务版本 |
| Windows/macOS系统输入与延迟 | 未实测；没有向用户当前桌面发送输入 | 专用测试窗口/设备，多屏DPI、权限拒绝、锁屏、掉线释放 |

## 10. 需要先解决的技术不确定性

1. **v2 证书信任：** 6467与6466证书一致性、更新/清数据后的轮换、服务端是否支持目标 iOS TLS身份。证据不足时保持不可用，不用永久 trust-all 兜底。[A3][V1]
2. **无Google服务电视的能力：** 有无Remote Service不能按品牌推断；无障碍节点、系统手势、受保护窗口逐项测，raw mouse默认false。[S7][O1][O2]
3. **iOS identity生成：** Android v2用RSA客户端证书；Security身份、证书封装及Keychain流程需spike，不能只写“用CryptoKit”假定全部解决。[A6][V2]
4. **中文文本：** IME field counter、替换/插入语义、emoji的UTF-16长度与焦点变化需要真机证明。[V4][S14][S15]
5. **系统延迟：** Wi-Fi拥塞、操作系统鼠标加速、触摸帧率和桌面刷新共同影响体感，不能从发送频率推导可见延迟。[S3][S13][P3]
6. **发行许可：** iOS/桌面新模块的许可证待正式选定；任何实际引入文件先登记来源与义务，特别是androidremote无许可和KDE/Marco的GPL边界。[L1]–[L5][O6][O7]

## 11. 证据索引

以下引用均指向固定提交的来源文件；平台官方文档是2026-11-05查阅版本。函数名与调用链见正文。配套架构中的 R 编号通过本文件对应章节追溯；未标 T 的内容没有本次实机证明。

<!-- SOURCE_INDEX -->

- **A1** — [androidremote/app/src/main/kotlin/dev/haris/atvremote/ui/RemoteScreen.kt L356-L400](https://github.com/theharisshah/androidremote/blob/12e9438699bc558f9ff80e09aca5edf26b04dc14/app/src/main/kotlin/dev/haris/atvremote/ui/RemoteScreen.kt#L356-L400)
- **A2** — [androidremote/app/src/main/kotlin/dev/haris/atvremote/discovery/TvDiscovery.kt](https://github.com/theharisshah/androidremote/blob/12e9438699bc558f9ff80e09aca5edf26b04dc14/app/src/main/kotlin/dev/haris/atvremote/discovery/TvDiscovery.kt)
- **A3** — [androidremote/protocol/src/main/kotlin/dev/haris/atvremote/protocol/Tls.kt](https://github.com/theharisshah/androidremote/blob/12e9438699bc558f9ff80e09aca5edf26b04dc14/protocol/src/main/kotlin/dev/haris/atvremote/protocol/Tls.kt)
- **A4** — [androidremote/protocol/src/main/kotlin/dev/haris/atvremote/protocol/PairingSession.kt](https://github.com/theharisshah/androidremote/blob/12e9438699bc558f9ff80e09aca5edf26b04dc14/protocol/src/main/kotlin/dev/haris/atvremote/protocol/PairingSession.kt)
- **A5** — [androidremote/README.md](https://github.com/theharisshah/androidremote/blob/12e9438699bc558f9ff80e09aca5edf26b04dc14/README.md)
- **A6** — [androidremote/protocol/src/main/kotlin/dev/haris/atvremote/protocol/PairingSecret.kt](https://github.com/theharisshah/androidremote/blob/12e9438699bc558f9ff80e09aca5edf26b04dc14/protocol/src/main/kotlin/dev/haris/atvremote/protocol/PairingSecret.kt)
- **A7** — [androidremote/protocol/src/main/kotlin/dev/haris/atvremote/protocol/RemoteClient.kt](https://github.com/theharisshah/androidremote/blob/12e9438699bc558f9ff80e09aca5edf26b04dc14/protocol/src/main/kotlin/dev/haris/atvremote/protocol/RemoteClient.kt)
- **V1** — [androidtvremote2/src/androidtvremote2/androidtv_remote.py](https://github.com/tronikos/androidtvremote2/blob/f49cf04703af1565e6216f1fc095b7d0477ca4a4/src/androidtvremote2/androidtv_remote.py)；[androidtvremote2/src/androidtvremote2/certificate_generator.py](https://github.com/tronikos/androidtvremote2/blob/f49cf04703af1565e6216f1fc095b7d0477ca4a4/src/androidtvremote2/certificate_generator.py)
- **V2** — [androidtvremote2/src/androidtvremote2/pairing.py](https://github.com/tronikos/androidtvremote2/blob/f49cf04703af1565e6216f1fc095b7d0477ca4a4/src/androidtvremote2/pairing.py)；[androidtvremote2/src/androidtvremote2/polo.proto](https://github.com/tronikos/androidtvremote2/blob/f49cf04703af1565e6216f1fc095b7d0477ca4a4/src/androidtvremote2/polo.proto)
- **V3** — [androidtvremote2/src/androidtvremote2/base.py](https://github.com/tronikos/androidtvremote2/blob/f49cf04703af1565e6216f1fc095b7d0477ca4a4/src/androidtvremote2/base.py)
- **V4** — [androidtvremote2/src/androidtvremote2/remote.py](https://github.com/tronikos/androidtvremote2/blob/f49cf04703af1565e6216f1fc095b7d0477ca4a4/src/androidtvremote2/remote.py)
- **V5** — [androidtvremote2/tests/test_base.py](https://github.com/tronikos/androidtvremote2/blob/f49cf04703af1565e6216f1fc095b7d0477ca4a4/tests/test_base.py)；[androidtvremote2/tests/test_pairing.py](https://github.com/tronikos/androidtvremote2/blob/f49cf04703af1565e6216f1fc095b7d0477ca4a4/tests/test_pairing.py)；[androidtvremote2/tests/test_remote.py](https://github.com/tronikos/androidtvremote2/blob/f49cf04703af1565e6216f1fc095b7d0477ca4a4/tests/test_remote.py)；[androidtvremote2/tests/test_androidtv_remote.py](https://github.com/tronikos/androidtvremote2/blob/f49cf04703af1565e6216f1fc095b7d0477ca4a4/tests/test_androidtv_remote.py)；[androidtvremote2/tests/test_voice_stream.py](https://github.com/tronikos/androidtvremote2/blob/f49cf04703af1565e6216f1fc095b7d0477ca4a4/tests/test_voice_stream.py)；[androidtvremote2/tests/test_certificate_generator.py](https://github.com/tronikos/androidtvremote2/blob/f49cf04703af1565e6216f1fc095b7d0477ca4a4/tests/test_certificate_generator.py)
- **V6** — [androidtvremote2/src/androidtvremote2/remotemessage.proto](https://github.com/tronikos/androidtvremote2/blob/f49cf04703af1565e6216f1fc095b7d0477ca4a4/src/androidtvremote2/remotemessage.proto)
- **V7** — [androidtvremote2/pyproject.toml](https://github.com/tronikos/androidtvremote2/blob/f49cf04703af1565e6216f1fc095b7d0477ca4a4/pyproject.toml)
- **S1** — [sofatap/ios/SofaTap/Views/NativeControls.swift L345-L435](https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/ios/SofaTap/Views/NativeControls.swift#L345-L435)
- **S2** — [sofatap/ios/SofaTap/Core/TouchGestureState.swift](https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/ios/SofaTap/Core/TouchGestureState.swift)；[sofatap/tests/TouchGestureTests.swift](https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/tests/TouchGestureTests.swift)；[sofatap/tests/PointerMotionTests.swift](https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/tests/PointerMotionTests.swift)
- **S3** — [sofatap/ios/SofaTap/Core/ControllerModel.swift L1046-L1185](https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/ios/SofaTap/Core/ControllerModel.swift#L1046-L1185)；[sofatap/ios/SofaTap/Core/ControllerModel.swift L145-L175](https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/ios/SofaTap/Core/ControllerModel.swift#L145-L175)；[sofatap/ios/SofaTap/Core/ControllerModel.swift L952-L977](https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/ios/SofaTap/Core/ControllerModel.swift#L952-L977)
- **S4** — [sofatap/ios/SofaTap/Core/Pairing.swift](https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/ios/SofaTap/Core/Pairing.swift)；[sofatap/ios/SofaTap/Core/SavedDevice.swift](https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/ios/SofaTap/Core/SavedDevice.swift)
- **S5** — [sofatap/host/Credentials.cs](https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/host/Credentials.cs)
- **S6** — [sofatap/host/ReceiverServer.cs](https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/host/ReceiverServer.cs)
- **S7** — [sofatap/android/receiver/src/main/java/com/chekusu/sofatap/tv/input/InputBridge.java L22-L35](https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/android/receiver/src/main/java/com/chekusu/sofatap/tv/input/InputBridge.java#L22-L35)
- **S8** — [sofatap/android/receiver/src/main/java/com/chekusu/sofatap/tv/input/SofatapAccessibilityService.java](https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/android/receiver/src/main/java/com/chekusu/sofatap/tv/input/SofatapAccessibilityService.java)
- **S9** — [sofatap/android/receiver/src/main/java/com/chekusu/sofatap/tv/RemoteV2Client.java](https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/android/receiver/src/main/java/com/chekusu/sofatap/tv/RemoteV2Client.java)；[sofatap/android/receiver/src/main/java/com/chekusu/sofatap/tv/SofatapInputMethodService.java](https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/android/receiver/src/main/java/com/chekusu/sofatap/tv/SofatapInputMethodService.java)
- **S10** — [sofatap/host/Protocol.cs](https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/host/Protocol.cs)
- **S11** — [sofatap/ios/SofaTap/Core/PeerTransportDiscovery.swift](https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/ios/SofaTap/Core/PeerTransportDiscovery.swift)
- **S12** — [sofatap/ios/SofaTap/Core/PeerTLSBridge.swift](https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/ios/SofaTap/Core/PeerTLSBridge.swift)
- **S13** — [sofatap/ios/SofaTap/Core/PointerTiming.swift](https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/ios/SofaTap/Core/PointerTiming.swift)
- **S14** — [sofatap/host/InputInjector.cs](https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/host/InputInjector.cs)
- **S15** — [sofatap/host/MacInput.cs](https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/host/MacInput.cs)；[sofatap/host/SofaTap.Host.csproj](https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/host/SofaTap.Host.csproj)
- **P1** — [penput/src/udp.rs](https://github.com/eunhhu/penput/blob/1d7d11a0594127e2c682d7910a6677ce6d4909b9/src/udp.rs)；[penput/src/connection.rs](https://github.com/eunhhu/penput/blob/1d7d11a0594127e2c682d7910a6677ce6d4909b9/src/connection.rs)
- **P2** — [penput/src/mouse.rs](https://github.com/eunhhu/penput/blob/1d7d11a0594127e2c682d7910a6677ce6d4909b9/src/mouse.rs)
- **P3** — [penput/ios/PenputIOSClient/UdpTouchClient.swift](https://github.com/eunhhu/penput/blob/1d7d11a0594127e2c682d7910a6677ce6d4909b9/ios/PenputIOSClient/UdpTouchClient.swift)；[penput/ios/PenputIOSClient/TouchPadView.swift](https://github.com/eunhhu/penput/blob/1d7d11a0594127e2c682d7910a6677ce6d4909b9/ios/PenputIOSClient/TouchPadView.swift)
- **P4** — [penput/src/websocket.rs](https://github.com/eunhhu/penput/blob/1d7d11a0594127e2c682d7910a6677ce6d4909b9/src/websocket.rs)
- **P5** — [penput/Cargo.toml](https://github.com/eunhhu/penput/blob/1d7d11a0594127e2c682d7910a6677ce6d4909b9/Cargo.toml)；[penput/src/main.rs](https://github.com/eunhhu/penput/blob/1d7d11a0594127e2c682d7910a6677ce6d4909b9/src/main.rs)；[penput/src/http.rs](https://github.com/eunhhu/penput/blob/1d7d11a0594127e2c682d7910a6677ce6d4909b9/src/http.rs)
- **K1** — [kdeconnect-kde/core/backends/lan/lanlinkprovider.cpp](https://github.com/KDE/kdeconnect-kde/blob/aee1439f80dc1870117825edb3be70aed6e75479/core/backends/lan/lanlinkprovider.cpp)
- **K2** — [kdeconnect-kde/core/backends/lan/lanlinkprovider.h](https://github.com/KDE/kdeconnect-kde/blob/aee1439f80dc1870117825edb3be70aed6e75479/core/backends/lan/lanlinkprovider.h)
- **K3** — [kdeconnect-kde/core/backends/pairinghandler.cpp](https://github.com/KDE/kdeconnect-kde/blob/aee1439f80dc1870117825edb3be70aed6e75479/core/backends/pairinghandler.cpp)
- **K4** — [kdeconnect-kde/core/device.cpp](https://github.com/KDE/kdeconnect-kde/blob/aee1439f80dc1870117825edb3be70aed6e75479/core/device.cpp)
- **K5** — [kdeconnect-kde/plugins/mousepad/mousepadplugin.cpp](https://github.com/KDE/kdeconnect-kde/blob/aee1439f80dc1870117825edb3be70aed6e75479/plugins/mousepad/mousepadplugin.cpp)
- **K6** — [kdeconnect-kde/plugins/mousepad/windowsremoteinput.cpp](https://github.com/KDE/kdeconnect-kde/blob/aee1439f80dc1870117825edb3be70aed6e75479/plugins/mousepad/windowsremoteinput.cpp)
- **K7** — [kdeconnect-kde/plugins/mousepad/macosremoteinput.mm](https://github.com/KDE/kdeconnect-kde/blob/aee1439f80dc1870117825edb3be70aed6e75479/plugins/mousepad/macosremoteinput.mm)
- **K8** — [kdeconnect-kde/LICENSES](https://github.com/KDE/kdeconnect-kde/tree/aee1439f80dc1870117825edb3be70aed6e75479/LICENSES)；[kdeconnect-kde/REUSE.toml](https://github.com/KDE/kdeconnect-kde/blob/aee1439f80dc1870117825edb3be70aed6e75479/REUSE.toml)
- **R1** — [scrcpy/app/src/server.c](https://github.com/Genymobile/scrcpy/blob/a60891aea193d92e7e5c3942700eca63f9d19a5f/app/src/server.c)
- **R2** — [scrcpy/server/src/main/java/com/genymobile/scrcpy/control/Controller.java](https://github.com/Genymobile/scrcpy/blob/a60891aea193d92e7e5c3942700eca63f9d19a5f/server/src/main/java/com/genymobile/scrcpy/control/Controller.java)
- **R3** — [scrcpy/server/src/main/java/com/genymobile/scrcpy/wrappers/InputManager.java](https://github.com/Genymobile/scrcpy/blob/a60891aea193d92e7e5c3942700eca63f9d19a5f/server/src/main/java/com/genymobile/scrcpy/wrappers/InputManager.java)；[scrcpy/server/src/main/java/com/genymobile/scrcpy/device/Device.java](https://github.com/Genymobile/scrcpy/blob/a60891aea193d92e7e5c3942700eca63f9d19a5f/server/src/main/java/com/genymobile/scrcpy/device/Device.java)
- **R4** — [scrcpy/server/src/main/java/com/genymobile/scrcpy/control/UhidManager.java](https://github.com/Genymobile/scrcpy/blob/a60891aea193d92e7e5c3942700eca63f9d19a5f/server/src/main/java/com/genymobile/scrcpy/control/UhidManager.java)
- **R5** — [scrcpy/doc/mouse.md](https://github.com/Genymobile/scrcpy/blob/a60891aea193d92e7e5c3942700eca63f9d19a5f/doc/mouse.md)；[scrcpy/doc/keyboard.md](https://github.com/Genymobile/scrcpy/blob/a60891aea193d92e7e5c3942700eca63f9d19a5f/doc/keyboard.md)
- **R6** — [scrcpy/doc/otg.md](https://github.com/Genymobile/scrcpy/blob/a60891aea193d92e7e5c3942700eca63f9d19a5f/doc/otg.md)
- **M1** — [MarcoTV/app/src/main/java/com/pilipala/tvhome/PhoneHttp.java](https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/app/src/main/java/com/pilipala/tvhome/PhoneHttp.java)
- **M2** — [MarcoTV/app/src/main/java/com/pilipala/tvhome/PhoneManager.java](https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/app/src/main/java/com/pilipala/tvhome/PhoneManager.java)
- **M3** — [MarcoTV/app/src/main/java/com/pilipala/tvhome/MainActivity.java](https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/app/src/main/java/com/pilipala/tvhome/MainActivity.java)；[MarcoTV/app/src/main/java/com/pilipala/tvhome/HomeView.java L790-L850](https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/app/src/main/java/com/pilipala/tvhome/HomeView.java#L790-L850)；[MarcoTV/app/src/main/java/com/pilipala/tvhome/SettingsNavigator.java L50-L65](https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/app/src/main/java/com/pilipala/tvhome/SettingsNavigator.java#L50-L65)
- **M4** — [MarcoTV/app/src/main/java/com/pilipala/tvhome/HomeKeyService.java](https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/app/src/main/java/com/pilipala/tvhome/HomeKeyService.java)；[MarcoTV/app/src/main/res/xml/home_accessibility.xml](https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/app/src/main/res/xml/home_accessibility.xml)
- **M5** — [MarcoTV/app/src/main/AndroidManifest.xml](https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/app/src/main/AndroidManifest.xml)
- **M6** — [MarcoTV/app/src/main/java/com/pilipala/tvhome/TaskBridgeServer.java](https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/app/src/main/java/com/pilipala/tvhome/TaskBridgeServer.java)
- **M7** — [MarcoTV/scripts/PhoneHttpChecks.java](https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/scripts/PhoneHttpChecks.java)；[MarcoTV/scripts/test_phone_http.py](https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/scripts/test_phone_http.py)
- **M8** — [MarcoTV/NOTICE](https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/NOTICE)；[MarcoTV/assets-notes.md](https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/assets-notes.md)
- **L1** — [androidtvremote2/LICENSE](https://github.com/tronikos/androidtvremote2/blob/f49cf04703af1565e6216f1fc095b7d0477ca4a4/LICENSE)
- **L2** — [sofatap/LICENSE](https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/LICENSE)
- **L3** — [penput/LICENSE](https://github.com/eunhhu/penput/blob/1d7d11a0594127e2c682d7910a6677ce6d4909b9/LICENSE)
- **L4** — [scrcpy/LICENSE](https://github.com/Genymobile/scrcpy/blob/a60891aea193d92e7e5c3942700eca63f9d19a5f/LICENSE)
- **L5** — [MarcoTV/LICENSE](https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/LICENSE)
- **O1** — [AOSP AndroidManifest：INJECT_EVENTS signature](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/core/res/AndroidManifest.xml)
- **O2** — [Android AccessibilityService：dispatchGesture与能力声明](https://developer.android.com/reference/android/accessibilityservice/AccessibilityService#dispatchGesture(android.accessibilityservice.GestureDescription,%20android.accessibilityservice.AccessibilityService.GestureResultCallback,%20android.os.Handler))
- **O3** — [Android Local network permission，页面更新2026-11-03](https://developer.android.com/privacy-and-security/local-network-permission)
- **O4** — [Microsoft SendInput：UIPI、返回值与物理键状态](https://learn.microsoft.com/windows/win32/api/winuser/nf-winuser-sendinput)
- **O5** — [Apple AXIsProcessTrusted](https://developer.apple.com/documentation/applicationservices/1460720-axisprocesstrusted)；[Apple CGPreflightPostEventAccess](https://developer.apple.com/documentation/coregraphics/cgpreflightposteventaccess())
- **O6** — [GitHub Licensing a repository：无许可与查看/fork边界](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)
- **O7** — [GNU GPL FAQ：许可兼容与附加限制](https://www.gnu.org/licenses/gpl-faq.en.html)
- **L6** — [louis49/androidtv-remote LICENSE：MIT，2026-11-05查阅main](https://github.com/louis49/androidtv-remote/blob/main/LICENSE)
- **L7** — [AOSP pairing protocol：Apache标记与NOTICE](https://android.googlesource.com/platform/external/google-tv-pairing-protocol/+/refs/heads/main/)

[A1]: https://github.com/theharisshah/androidremote/blob/12e9438699bc558f9ff80e09aca5edf26b04dc14/app/src/main/kotlin/dev/haris/atvremote/ui/RemoteScreen.kt#L356-L400
[A2]: https://github.com/theharisshah/androidremote/blob/12e9438699bc558f9ff80e09aca5edf26b04dc14/app/src/main/kotlin/dev/haris/atvremote/discovery/TvDiscovery.kt
[A3]: https://github.com/theharisshah/androidremote/blob/12e9438699bc558f9ff80e09aca5edf26b04dc14/protocol/src/main/kotlin/dev/haris/atvremote/protocol/Tls.kt
[A4]: https://github.com/theharisshah/androidremote/blob/12e9438699bc558f9ff80e09aca5edf26b04dc14/protocol/src/main/kotlin/dev/haris/atvremote/protocol/PairingSession.kt
[A5]: https://github.com/theharisshah/androidremote/blob/12e9438699bc558f9ff80e09aca5edf26b04dc14/README.md
[A6]: https://github.com/theharisshah/androidremote/blob/12e9438699bc558f9ff80e09aca5edf26b04dc14/protocol/src/main/kotlin/dev/haris/atvremote/protocol/PairingSecret.kt
[A7]: https://github.com/theharisshah/androidremote/blob/12e9438699bc558f9ff80e09aca5edf26b04dc14/protocol/src/main/kotlin/dev/haris/atvremote/protocol/RemoteClient.kt
[V1]: https://github.com/tronikos/androidtvremote2/blob/f49cf04703af1565e6216f1fc095b7d0477ca4a4/src/androidtvremote2/androidtv_remote.py
[V2]: https://github.com/tronikos/androidtvremote2/blob/f49cf04703af1565e6216f1fc095b7d0477ca4a4/src/androidtvremote2/pairing.py
[V3]: https://github.com/tronikos/androidtvremote2/blob/f49cf04703af1565e6216f1fc095b7d0477ca4a4/src/androidtvremote2/base.py
[V4]: https://github.com/tronikos/androidtvremote2/blob/f49cf04703af1565e6216f1fc095b7d0477ca4a4/src/androidtvremote2/remote.py
[V5]: https://github.com/tronikos/androidtvremote2/blob/f49cf04703af1565e6216f1fc095b7d0477ca4a4/tests/test_base.py
[V6]: https://github.com/tronikos/androidtvremote2/blob/f49cf04703af1565e6216f1fc095b7d0477ca4a4/src/androidtvremote2/remotemessage.proto
[V7]: https://github.com/tronikos/androidtvremote2/blob/f49cf04703af1565e6216f1fc095b7d0477ca4a4/pyproject.toml
[S1]: https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/ios/SofaTap/Views/NativeControls.swift#L345-L435
[S2]: https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/ios/SofaTap/Core/TouchGestureState.swift
[S3]: https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/ios/SofaTap/Core/ControllerModel.swift#L1046-L1185
[S4]: https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/ios/SofaTap/Core/Pairing.swift
[S5]: https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/host/Credentials.cs
[S6]: https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/host/ReceiverServer.cs
[S7]: https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/android/receiver/src/main/java/com/chekusu/sofatap/tv/input/InputBridge.java#L22-L35
[S8]: https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/android/receiver/src/main/java/com/chekusu/sofatap/tv/input/SofatapAccessibilityService.java
[S9]: https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/android/receiver/src/main/java/com/chekusu/sofatap/tv/RemoteV2Client.java
[S10]: https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/host/Protocol.cs
[S11]: https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/ios/SofaTap/Core/PeerTransportDiscovery.swift
[S12]: https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/ios/SofaTap/Core/PeerTLSBridge.swift
[S13]: https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/ios/SofaTap/Core/PointerTiming.swift
[S14]: https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/host/InputInjector.cs
[S15]: https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/host/MacInput.cs
[P1]: https://github.com/eunhhu/penput/blob/1d7d11a0594127e2c682d7910a6677ce6d4909b9/src/udp.rs
[P2]: https://github.com/eunhhu/penput/blob/1d7d11a0594127e2c682d7910a6677ce6d4909b9/src/mouse.rs
[P3]: https://github.com/eunhhu/penput/blob/1d7d11a0594127e2c682d7910a6677ce6d4909b9/ios/PenputIOSClient/UdpTouchClient.swift
[P4]: https://github.com/eunhhu/penput/blob/1d7d11a0594127e2c682d7910a6677ce6d4909b9/src/websocket.rs
[P5]: https://github.com/eunhhu/penput/blob/1d7d11a0594127e2c682d7910a6677ce6d4909b9/Cargo.toml
[K1]: https://github.com/KDE/kdeconnect-kde/blob/aee1439f80dc1870117825edb3be70aed6e75479/core/backends/lan/lanlinkprovider.cpp
[K2]: https://github.com/KDE/kdeconnect-kde/blob/aee1439f80dc1870117825edb3be70aed6e75479/core/backends/lan/lanlinkprovider.h
[K3]: https://github.com/KDE/kdeconnect-kde/blob/aee1439f80dc1870117825edb3be70aed6e75479/core/backends/pairinghandler.cpp
[K4]: https://github.com/KDE/kdeconnect-kde/blob/aee1439f80dc1870117825edb3be70aed6e75479/core/device.cpp
[K5]: https://github.com/KDE/kdeconnect-kde/blob/aee1439f80dc1870117825edb3be70aed6e75479/plugins/mousepad/mousepadplugin.cpp
[K6]: https://github.com/KDE/kdeconnect-kde/blob/aee1439f80dc1870117825edb3be70aed6e75479/plugins/mousepad/windowsremoteinput.cpp
[K7]: https://github.com/KDE/kdeconnect-kde/blob/aee1439f80dc1870117825edb3be70aed6e75479/plugins/mousepad/macosremoteinput.mm
[K8]: https://github.com/KDE/kdeconnect-kde/tree/aee1439f80dc1870117825edb3be70aed6e75479/LICENSES
[R1]: https://github.com/Genymobile/scrcpy/blob/a60891aea193d92e7e5c3942700eca63f9d19a5f/app/src/server.c
[R2]: https://github.com/Genymobile/scrcpy/blob/a60891aea193d92e7e5c3942700eca63f9d19a5f/server/src/main/java/com/genymobile/scrcpy/control/Controller.java
[R3]: https://github.com/Genymobile/scrcpy/blob/a60891aea193d92e7e5c3942700eca63f9d19a5f/server/src/main/java/com/genymobile/scrcpy/wrappers/InputManager.java
[R4]: https://github.com/Genymobile/scrcpy/blob/a60891aea193d92e7e5c3942700eca63f9d19a5f/server/src/main/java/com/genymobile/scrcpy/control/UhidManager.java
[R5]: https://github.com/Genymobile/scrcpy/blob/a60891aea193d92e7e5c3942700eca63f9d19a5f/doc/mouse.md
[R6]: https://github.com/Genymobile/scrcpy/blob/a60891aea193d92e7e5c3942700eca63f9d19a5f/doc/otg.md
[M1]: https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/app/src/main/java/com/pilipala/tvhome/PhoneHttp.java
[M2]: https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/app/src/main/java/com/pilipala/tvhome/PhoneManager.java
[M3]: https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/app/src/main/java/com/pilipala/tvhome/MainActivity.java
[M4]: https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/app/src/main/java/com/pilipala/tvhome/HomeKeyService.java
[M5]: https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/app/src/main/AndroidManifest.xml
[M6]: https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/app/src/main/java/com/pilipala/tvhome/TaskBridgeServer.java
[M7]: https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/scripts/PhoneHttpChecks.java
[M8]: https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/NOTICE
[L1]: https://github.com/tronikos/androidtvremote2/blob/f49cf04703af1565e6216f1fc095b7d0477ca4a4/LICENSE
[L2]: https://github.com/chekusu/sofatap/blob/9ec71a05f1cc137972f111e3527c8a869640a199/LICENSE
[L3]: https://github.com/eunhhu/penput/blob/1d7d11a0594127e2c682d7910a6677ce6d4909b9/LICENSE
[L4]: https://github.com/Genymobile/scrcpy/blob/a60891aea193d92e7e5c3942700eca63f9d19a5f/LICENSE
[L5]: https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/LICENSE
[O1]: https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/core/res/AndroidManifest.xml
[O2]: https://developer.android.com/reference/android/accessibilityservice/AccessibilityService#dispatchGesture(android.accessibilityservice.GestureDescription,%20android.accessibilityservice.AccessibilityService.GestureResultCallback,%20android.os.Handler)
[O3]: https://developer.android.com/privacy-and-security/local-network-permission
[O4]: https://learn.microsoft.com/windows/win32/api/winuser/nf-winuser-sendinput
[O5]: https://developer.apple.com/documentation/applicationservices/1460720-axisprocesstrusted
[O6]: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository
[O7]: https://www.gnu.org/licenses/gpl-faq.en.html
[L6]: https://github.com/louis49/androidtv-remote/blob/main/LICENSE
[L7]: https://android.googlesource.com/platform/external/google-tv-pairing-protocol/+/refs/heads/main/
