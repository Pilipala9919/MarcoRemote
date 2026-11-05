# G1-B1 安全通信与配对：验证结果

更新：2026-11-06，Asia/Shanghai。实现：[MarcoTV PR #3](https://github.com/Pilipala9919/MarcoTV/pull/3)。最终受测代码 `943580c894ca1083d276ad1ddbf72ac37c5c8cbe`；本仓仅同步文档/脱敏证据，不将 GPL 实现复制到拟 Apache 的代码域。

**真实 Android 9 小米电视与 Windows 已完成报告所列的本机批准 TLS 假输入会话测试，包括主动撤销和五分钟绝对期限。技术验证结果等待 G1-B1 用户审查，不自动进入 G1-B2。** 此结论更新了 11 月 5 日“仅完成 TLS、人工会话待测”的状态。真实桌面焦点仍未接入。

## 三层结果

| 层次 | 结果 | 证据边界 |
|---|---|---|
| 单元/自动化 T | **通过** | 24 策略场景/126 断言；后台关闭回归含同步撤权、线程隔离、32 并发请求和幂等；11 个 Windows 证书/帧测试、8 个 Java 主机 TLS 测试；原有 17 离线套件通过 |
| Android 构建 B | **通过** | 最终独立 debug probe API28 编译、D8 min23、签名/安装；本地与已安装 APK 哈希一致。标准/受限/Lite CI 也成功，未上传 APK |
| 真实电视 D-session | **下列场景已取得成功证据** | 用户实体遥控主动开启/拒绝/批准/撤销，实际 LAN TLS；不是主机自动批准夹具。失败尝试、修复及版本分别记录 |
| 真实可见焦点 D-UI | **未执行** | 仅 fakeCount 变化，不调用 HomeView/MarcoFocusController，不代表四方向桌面控制可用 |

设备为 MiTV-ASTP0、Android 9/API28、固件 `22.8.30.1385`；Windows Python 3.13.13 / OpenSSL 3.0.19。C=固定源码；T=主机测试；B=构建；D=真实设备证据，不相互替代。

## 真实设备能力矩阵

早期证据：[TLS/KeyStore JSON](evidence/g1-b1-tls-20261105.json)。人工补测：[11 次尝试的双端事件与哈希](evidence/g1-b1-manual-20261106.json)。不同场景在不同提交上运行，最终提交只重测了五分钟会话，不能描述为全部在最终 APK 重新通过。

| 能力 | 实际证据 | 判定/限制 |
|---|---|---|
| AndroidKeyStore + 平台 TLS | D：非导出私钥、KeyInfo hardwareBacked=true；TLS1.2 / ECDHE-ECDSA-AES128-GCM-SHA256；进程重启 pin 保持 | 指定机型/固件通过；非硬件 attestation，未测试整机重启/卸载 |
| Windows 先验身份再发票据 | C/T：CERT_REQUIRED + 带外唯一 PEM、完整 pin、有效期/自签名/CN；D：错误 pin/根/身份拒绝且应用字节为 0；每次人工会话均先 certificate_verified 后 PENDING | 过期/未来/坏签名证书仅 T 合成测试，不冒充 D |
| 本机拒绝 | 01b：用户选拒绝，TV LOCAL_DENY；客户端 DENIED_OR_EXPIRED，无 GRANTED | D 通过；fa268c |
| 明确批准与假输入 | 多轮 LOCAL_APPROVE → GRANTED → FAKE_APPLIED 1；用户看到计数 1 | D 通过；真实桌面不在执行链 |
| 重放保护 | 03：重复 seq 返回 REPLAY，listener 关闭，无 FAKE_APPLIED | D 通过；fa268c |
| challenge 过期 | 04：等待约 1.2 秒，STALE_CHALLENGE，无 FAKE_APPLIED | D 通过；fa268c；不是票据自然过期 |
| Windows 主动断开 | 06：客户端 close，TV EOFException → LISTENER_CLOSED | D 通过；fa268c；不是物理 Wi-Fi 故障 |
| 电视按钮撤销 | 08：LOCAL_REVOKE_REQUEST → LOCAL_REVOKE → LISTENER_CLOSED、Windows EOF；用户确认页面仍在 | 修复复测通过；b704b2a；早期 02/07 崩溃保留为失败 |
| 15 秒空闲关闭 | 09：最后 SNAPSHOT 后约 15.017 秒 TV SocketTimeoutException，计数未增加 | D 通过；b704b2a；早期 05 被操作/崩溃中断，无效 |
| Activity 暂停取消 | 10：约 60 秒时小米屏保触发 LIFECYCLE_PAUSE，持续保活的会话仍关闭 | D 通过暂停取消；不是五分钟到期证据 |
| 五分钟绝对期限 | 11：59 次 PONG 后，Windows 同一单调时钟测得批准后 301.068 秒 EOF；TV 自身日志约 300.040 秒关闭；期间无暂停/撤销 | D 通过；943580c；到期后观察到屏保恢复 |
| 120 秒票据/30 秒待批准到期、5 次错误票据、跨连接凭据、旧票据重用、限流 | C/T 策略与传输测试 | 未逐项真机负例测试，不能标成 D |
| HomeView revision/本地遥控/弹窗/布局/失焦下的最终提交 | G1-A T + 本轮 C 审查 | 未接入、无 D-UI；下一阶段必须单独验证 |

最后一轮北京时间 **2026-11-06 00:21:09.874** 获准，**00:26:10.942** Windows 观察断开。跨机时钟未同步，不将双端时间差当作延迟测量。最终安装包 SHA-256：`d85a1fe9cede1d89a114647e17599194977b3baf50a779bc0781d1569e26a92f`，与本地一致。

实际连接经 LAN，不用 adb forward/reverse。既有授权 ADB 只用于安装/打开独立验证页、带外证书/票据读取与日志；本机批准没有被自动点击替代。原始秘密文件/地址/完整设备日志留在忽略目录；公开 JSON 保留脱敏事件、原始文件哈希和来源提交。

## 实机发现的问题及调整

1. 早期 Android 9 Conscrypt 的已摘要 TLS 签名要求 KeyStore DIGEST_NONE，首次失败为 `Incompatible digest`。增加独立试验密钥的允许用途后实际握手通过；没有导出密钥或关闭校验。
2. 用户按撤销时，旧实现从 UI 线程调用 TLS close_notify，触发 `NetworkOnMainThreadException` 并退出验证页。根因链为 `onClick → ProbeActivity.stop → ProbeServer.close → ConscryptFileDescriptorSocket.close`。`b704b2a701f3ab02676e2cd001dcdec1304ae030` 同步撤销授权，再由唯一后台线程关闭传输；新增回归测试并由 08 实机复测确认。不能仅凭旧版 EOF 就声称安全撤销 UI 已通过。
3. 10 被屏保提前打断；`943580c` 只在明确批准的会话内设置窗口亮屏标记，stop/暂停/到期时清除。未修改系统屏保配置或增加权限。11 据此隔离了绝对期限验证，到期后实际恢复屏保。修复后的 08–11 时段，保留的 crash buffer 没有新 FATAL EXCEPTION。

## 协议、源码与复现

- [安全协议及 G1-A 接网一致性审查](https://github.com/Pilipala9919/MarcoTV/blob/943580c894ca1083d276ad1ddbf72ac37c5c8cbe/docs/G1_B1_SECURITY_PROTOCOL.md)
- [TV 完整报告、版本与 APK 对应表](https://github.com/Pilipala9919/MarcoTV/blob/7d435c3473c1544711dbdd4356a53503bf98d401/docs/G1_B1_REPORT.md)
- [构建、Windows 命令及双端日志采集](https://github.com/Pilipala9919/MarcoTV/blob/7d435c3473c1544711dbdd4356a53503bf98d401/security-spike/README.md)
- [AndroidKeyStore 身份](https://github.com/Pilipala9919/MarcoTV/blob/943580c894ca1083d276ad1ddbf72ac37c5c8cbe/security-spike/src/com/pilipala/remoteprobe/DeviceIdentity.java)、[本机授权 UI](https://github.com/Pilipala9919/MarcoTV/blob/943580c894ca1083d276ad1ddbf72ac37c5c8cbe/security-spike/src/com/pilipala/remoteprobe/ProbeActivity.java)
- [会话策略及唯一假执行器](https://github.com/Pilipala9919/MarcoTV/blob/943580c894ca1083d276ad1ddbf72ac37c5c8cbe/security-spike/src/com/pilipala/remoteprobe/SessionPolicy.java)、[TLS 传输](https://github.com/Pilipala9919/MarcoTV/blob/943580c894ca1083d276ad1ddbf72ac37c5c8cbe/security-spike/src/com/pilipala/remoteprobe/ProbeServer.java)、[后台关闭](https://github.com/Pilipala9919/MarcoTV/blob/943580c894ca1083d276ad1ddbf72ac37c5c8cbe/security-spike/src/com/pilipala/remoteprobe/BackgroundClose.java)
- [严格证书校验 Windows 客户端](https://github.com/Pilipala9919/MarcoTV/blob/943580c894ca1083d276ad1ddbf72ac37c5c8cbe/security-spike/tools/client.py)、[策略/关闭回归入口](https://github.com/Pilipala9919/MarcoTV/blob/943580c894ca1083d276ad1ddbf72ac37c5c8cbe/security-spike/tools/test_policy.py)

协议仍为成熟平台 TLS 上的有界 ASCII 行；256-bit 单次票据 120 秒、等待批准最多 30 秒；连接绑定会话 5 分钟、空闲 15 秒；严格 seq、服务端起算 1 秒 challenge、10 帧/秒。断线无凭据恢复，需重新本机开启/批准。不复用 PhoneHttp 凭据。

最终代码的 [PR CI](https://github.com/Pilipala9919/MarcoTV/actions/runs/42063767912) 与 [push CI](https://github.com/Pilipala9919/MarcoTV/actions/runs/42063758656) 均成功，上传产物为 0。CI 包含策略/关闭测试、Android 构建；11/8 个主机 TLS 测试在 Windows 本地运行，人工 D 单列。完整验证不是第三方安全审计，也未完成系统补丁/传递依赖完整 SBOM 审查。

## 下一阶段最小任务与门槛

**等待用户验收 G1-B1，才进入 G1-B2。** 本轮不合并 main，不发布 APK，不开发 iOS、电脑输入或游戏手柄。

1. 将原始服务端 Snapshot/epoch/layoutRevision/focusRevision 与安全会话 generation、单次 challenge 绑定，禁止执行前重新拍快照掩盖本地冲突。
2. UI 提交前校验原子撤权和最早截止时间；不得在网络排队后重新从 `prepare()` 起算 TTL。明确 UI 提交与撤销的先后边界。
3. 添加仅自身卡片区的 HomeView 适配器；无通用 KeyEvent、包名/Intent/坐标注入。内存 MOVED 不等于绘制成功，失败不得回报可见成功。
4. Windows 四向请求实测，以及本地遥控、弹窗、布局变化、失焦、断线、超时取消；保存可见焦点证据。

消费者扫码引导、debug/诊断入口移除、凭据轮换和产品级 DoS 防护仍属后续范围。当前 ADB 带外配对属于开发信任边界，不能直接当作产品发布方案。
