# G1-B2 真机验证报告

更新：2026-11-07（Asia/Shanghai）。**核心目标已达成：Windows 经电视批准的 TLS 会话发送 RIGHT，真实 HomeView 的选中焦点从 Marco Movie 移至右侧 Moonlight。完整验收矩阵未完成，PR 保持草稿。**

## 版本与范围

- 设备：小米 MiTV-ASTP0，Android 9 / API 28。
- 并排包：`com.pilipala.tvhome.focuslab`，UID 10040；正式包 UID 10059、B1 验证包 UID 10039。应用代码来自 MarcoTV `6247892d43ad05871c19a5fa606b8dbc0d057911`，后续提交仅增加测试采集和报告。
- 已安装 APK SHA-256：`8d42859890b23b9ac6a262a5a8eb2016506df898abfb14d10f159400b4288cc1`，沿用先前本机/安装比对记录。本轮没有重装或发布 APK，没有更换默认桌面，没有修改 main。
- 实现：[MarcoTV PR #4](https://github.com/Pilipala9919/MarcoTV/pull/4)；报告：[MarcoRemote PR #4](https://github.com/Pilipala9919/MarcoRemote/pull/4)。[源码调用链、审查说明和完整矩阵](https://github.com/Pilipala9919/MarcoTV/blob/d1ba74581587c58a56cb55d1c1a222d29034256d/docs/G1_B2_HOME_FOCUS.md)。

配对文本由用户扫描电视 QR 后直接粘贴到 Windows 隐藏输入，电视实体批准。客户端复用正式 pin/证书校验路径；没有从 ADB 读取票据、使用诊断凭据或模拟批准。ADB 仅用于受控测试包启动、页面替换和日志/画面采集。公开证据不含 QR、票据或会话密钥。

## 三类结果分开记录

| 类别 | 结果 | 证据范围 |
|---|---|---|
| 自动化测试 | 通过 | 16 项主机 TLS/CLI 测试于 11 月 7 日复测，7.818 秒；既有 Java 组合断言及 17 套离线回归见原报告。合成证书与 UI 夹具不是真机 |
| Android 构建 | 通过，沿用原构建 | 并排 APK 编译、D8、签名、对齐、安装及哈希比对已完成。本次报告/采集工具修改未改 Android 应用，不声称重新构建 |
| 小米电视实测 | 下表逐项记录 | RIGHT 有前后截图、状态与用户确认；其余测试按各自日志范围登记，未测项不外推 |

[主机复测](https://github.com/Pilipala9919/MarcoTV/blob/d1ba74581587c58a56cb55d1c1a222d29034256d/docs/evidence/g1-b2-host-rerun-20261107.json) · [构建/安装记录](https://github.com/Pilipala9919/MarcoTV/blob/d1ba74581587c58a56cb55d1c1a222d29034256d/docs/evidence/g1-b2-install-20261106.json)

## 真实设备矩阵

以下链接均固定到证据提交，时间为电视日志的本地时间。

| 场景 | 结果与限制 | 证据 |
|---|---|---|
| 批准后 RIGHT | 通过。23:28:43 STEP MOVED；行列 0/0 → 0/1，focusRevision 4 → 5，epoch/layoutRevision 不变。人工检查前后截图确认焦点移动，卡片排列不变 | [状态与原始画面](https://github.com/Pilipala9919/MarcoTV/tree/d1ba74581587c58a56cb55d1c1a222d29034256d/docs/evidence/g1-b2-right-20261107) |
| 重复序号 | 拒绝/断开通过。23:31:18 双端 REPLAY，随后 EOF 和会话结束；未单独记录该轮最终位置截图 | [重放](https://github.com/Pilipala9919/MarcoTV/blob/d1ba74581587c58a56cb55d1c1a222d29034256d/docs/evidence/g1-b2-replay-20261107.json) |
| 实体遥控打开设置撤销 | 通过。23:33:47 会话结束、Windows EOF，应用仍前台，用户确认正常；未观察到 NetworkOnMainThreadException 或崩溃 | [撤销](https://github.com/Pilipala9919/MarcoTV/blob/d1ba74581587c58a56cb55d1c1a222d29034256d/docs/evidence/g1-b2-revoke-20261107.json) |
| 休眠/唤醒 | 休眠断连通过。23:35:31 会话先结束，系统随后停止验证进程；唤醒回小米桌面。重新打开验证版后采样无监听。不代表应用后台存活或自动返回 Marco | [休眠及系统停止事件](https://github.com/Pilipala9919/MarcoTV/blob/d1ba74581587c58a56cb55d1c1a222d29034256d/docs/evidence/g1-b2-sleep-20261107.json) |
| 活跃会话页面替换 | 指定场景通过。23:37:57 旧连接 EOF，同进程旧 Activity 销毁、新 Activity 创建，画面正常。使用 NEW_TASK/CLEAR_TASK；不覆盖配置变化恢复或重建队列中的旧 STEP | [记录与画面](https://github.com/Pilipala9919/MarcoTV/tree/d1ba74581587c58a56cb55d1c1a222d29034256d/docs/evidence/g1-b2-recreate-20261107) |
| 本地物理遥控冲突 | 指定右键场景通过。23:41:20 旧快照命令返回 STALE_FOCUS，不是过期或通用撤销；未保存该轮最终截图 | [冲突](https://github.com/Pilipala9919/MarcoTV/blob/d1ba74581587c58a56cb55d1c1a222d29034256d/docs/evidence/g1-b2-local-conflict-20261107.json) |
| 过期命令 | 通过。等待 1.2 秒后返回 STALE_CHALLENGE；前后 STATE 均为 `1 1 4 0 3`，焦点/版本不变 | [期限](https://github.com/Pilipala9919/MarcoTV/blob/d1ba74581587c58a56cb55d1c1a222d29034256d/docs/evidence/g1-b2-deadlines-20261107.json) |
| 空闲超时 | 通过。不发保活，Windows 15.008 秒后直接观察 EOF，23:44:49 电视结束会话，进程仍在，用户确认正常 | 同上；不是五分钟绝对期限测试 |
| 独立物理断网/静默丢包 | **未验证**。用户暂无法在电视 UI 外仅断开电视网络；打开设置会先触发撤销，不能替代网络故障 | 主机 TCP 断链测试仅属自动化证据 |

真实握手成功的依据是经过固定证书校验代码获得会话并执行真实 STATE/STEP；未另存完整握手抓包或逐字控制台记录。正常 RIGHT 脚本调用了 CLOSE，电视记录会话结束，但没有独立保存 CLOSED 回执。

## 失败、误操作与工具改进

- 初次用户只扫码，未把配对文本送入 Windows，没有批准弹窗或移动；补全既定流程后成功，未绕过验证。
- 首次物理冲突测试用户错过 NOW，命令返回 MOVED，保留为[未验证](https://github.com/Pilipala9919/MarcoTV/blob/d1ba74581587c58a56cb55d1c1a222d29034256d/docs/evidence/g1-b2-local-missed-20261107.json)。工具在 STATE 之前增加 5 秒倒计时后复测通过，未延长服务端安全期限。
- 休眠时系统停止进程，采集脚本的 pidof 因此失败，原文件缺少 alive/asleep 字段。补充系统休眠、停止和唤醒事件，没有伪造缺失字段。系统停止与崩溃不同，此轮不主张后台存活。
- 页面重开有一次短暂闪烁，与测试主动替换页面时点一致；后续实机截图显示正常桌面。

## 剩余风险与下一步最小任务

1. 在具备条件时，独立中断电视链路/制造静默丢包，恢复后检查服务端撤权、旧凭据失败以及重新批准后恢复。当前是明确的设备测试阻塞。
2. 补齐 B2 其余三方向/边界、拒绝授权、错误证书不发送票据、CLOSE 回执、五分钟绝对期限、票据到期和旧凭据重连的独立真机记录。已有主机测试和 B1 实测不替代 B2。
3. 按风险补充配置恢复、排队旧命令和其他实体按键竞态；不要把这次任务替换扩大为所有生命周期通过。
4. 完整矩阵和代码审查通过后再申请 G1-B2 整体验收。暂不进入 iOS、跨应用、电脑输入或手柄扩展；不自动合并、发布 APK 或修改系统权限。

Android 9 系统 TLS 补丁状态、外部扫码渠道、首个私有 IPv4 选择与单连接窗口的占用风险仍保留在实现报告中。并排包采用独立 UID；将来正式包启用时必须继续生成自身身份，不迁移验证包密钥。
