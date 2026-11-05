# G1-B1 安全通信与配对：本轮结果

日期：2026-11-05。实现：[MarcoTV PR #3](https://github.com/Pilipala9919/MarcoTV/pull/3)，固定提交 `fa268c2830e40a59acb7b0600f63bfe5a710decf`。本仓仅同步报告/架构，不复制 GPL 实现到拟 Apache 的代码域。

**真实 Android9 电视 TLS 可行性已验证；完整人工配对/撤销会话尚未验收，因此 G1-B1 整体未通过，不进入 G1-B2。** 用户明确暂时不方便在电视旁，允许先完成可自动验证部分。没有以模拟点击、主机批准夹具或单元测试冒充真实电视授权。

## 交付及证据

| 交付/能力 | 本轮证据 | 限制 |
|---|---|---|
| AndroidKeyStore + 平台 TLS | D：MiTV-ASTP0 / Android9 / API28 / 固件22.8.30.1385，真实 TLS1.2 与 ECDHE-ECDSA-AES128-GCM-SHA256 握手通过 | 只验证该机当前固件；不是系统安全补丁审计 |
| 独立设备身份 | D：私钥 getEncoded()==null；KeyInfo 报硬件支持；进程重启后 pin 保持 | 不是独立硬件 attestation，不外推重装/卸载 |
| Windows 先验身份再发票据 | C/T/D：CERT_REQUIRED + 带外 PEM 唯一信任根、自签名/有效期/完整 leaf pin/CN 校验；真实错误 pin、信任根、身份拒绝 | 真机诊断发送应用数据为0；没有发票据或批准 |
| 会话/票据/seq/challenge/撤销 | C：独立代码完成；T：24策略场景/126断言、8实际Java主机TLS场景通过 | 主机夹具的批准不是电视人工批准；真正批准后会话尚未实测 |
| 证书与帧失败测试 | T：11个Windows测试通过，含过期、尚未生效、坏自签名、错误身份与EOF/超长/期限 | 使用合成证书和主机TLS，不能替代D |
| Android 构建 | B：独立debug APK API28编译、D8 min23，签名与安装通过 | 不同包/签名，不修改稳定MarcoTV，无发布 |
| 假执行器隔离 | C/B：命令只增加fakeCount；DEX不含MarcoFocusController/HomeView/自动批准夹具 | 真实桌面始终未接入 |
| 真实人工配对/拒绝/撤销 | **未执行** | 必须电视本机操作，不能由代理自动批准 |

本轮还重跑原有17个离线套件通过。独立 APK 在开发机与安装电视后的哈希一致：`4fc286775712be27dbd2368bd60c1d0087ce0a16f2328cf366ec9f9b429d300f`。最终设备记录起点为 **2026-11-05 19:06:20 北京时间**。Windows Python3.13.13 / OpenSSL3.0.19。证据：[去地址JSON](evidence/g1-b1-tls-20261105.json)。

实际TLS经LAN，不是adb forward。既有已授权ADB仅用于安装独立测试包、启动无输入的60秒握手诊断、带外证书读取和日志采集。诊断路径没有票据、批准或应用命令解析；测试结束已force-stop，确认无进程及端口不再可连接。该清理不是用户主动撤销证据。独立验证包仍安装在电视供后续人工操作，当前未运行。

## 源码、协议与复现入口

- [完整安全协议与G1-A接网审查](https://github.com/Pilipala9919/MarcoTV/blob/fa268c2830e40a59acb7b0600f63bfe5a710decf/docs/G1_B1_SECURITY_PROTOCOL.md)
- [详细真机报告与待验收表](https://github.com/Pilipala9919/MarcoTV/blob/fa268c2830e40a59acb7b0600f63bfe5a710decf/docs/G1_B1_REPORT.md)
- [构建/Windows/人工配对操作手册](https://github.com/Pilipala9919/MarcoTV/blob/fa268c2830e40a59acb7b0600f63bfe5a710decf/security-spike/README.md)
- [AndroidKeyStore身份](https://github.com/Pilipala9919/MarcoTV/blob/fa268c2830e40a59acb7b0600f63bfe5a710decf/security-spike/src/com/pilipala/remoteprobe/DeviceIdentity.java)
- [电视本机开启/批准/撤销UI](https://github.com/Pilipala9919/MarcoTV/blob/fa268c2830e40a59acb7b0600f63bfe5a710decf/security-spike/src/com/pilipala/remoteprobe/ProbeActivity.java)
- [TLS有界传输](https://github.com/Pilipala9919/MarcoTV/blob/fa268c2830e40a59acb7b0600f63bfe5a710decf/security-spike/src/com/pilipala/remoteprobe/ProbeServer.java)
- [会话策略与唯一假执行器](https://github.com/Pilipala9919/MarcoTV/blob/fa268c2830e40a59acb7b0600f63bfe5a710decf/security-spike/src/com/pilipala/remoteprobe/SessionPolicy.java)
- [严格证书校验Windows客户端](https://github.com/Pilipala9919/MarcoTV/blob/fa268c2830e40a59acb7b0600f63bfe5a710decf/security-spike/tools/client.py)
- [真实设备无配对握手诊断](https://github.com/Pilipala9919/MarcoTV/blob/fa268c2830e40a59acb7b0600f63bfe5a710decf/security-spike/tools/probe_device.py)

## 安全设计调整

- 单次256-bit票据120秒，正确提交立即消费；电视批准最长30秒且不超出窗口；批准后会话5分钟、空闲15秒注销，绑定当前TLS连接。断线没有永久凭据恢复，需新窗口/新票据/新批准。
- 会话内严格递增seq，重复或乱序撤销；服务端快照发放1000ms单次challenge，过期不能加假计数。TLS/密码学由平台完成，没有自创加密。
- 独立协议使用TLS有界ASCII行，非早期WSS完整产品设计；每帧≤4096字节，10认证帧/秒，串行一连接，无应用队列。
- 首次Android9握手发现KeyStore的digest用途不兼容；允许Conscrypt已摘要TLS签名使用DIGEST_NONE后成功，未关闭证书验证。报告保留失败及修正边界。
- debug带外文件通过已有ADB授权提取，这不是最终扫码/秘密保管方案；生产不得带debug、诊断启动入口或主机自动批准夹具。TLS系统版本的长期补丁、完整SBOM仍须另审。

## G1-A 接网审查结论

控制器本身保持不变。发现适配时必须解决：`prepare()`若在UI出队时才起算TTL会延长旧指令生命；若用新snapshot替换客户端旧revision会掩盖本地冲突；跨线程仅排队disconnect可能晚于旧动作；内存MOVED不等于HomeView渲染完成。本次challenge为服务端起算，但尚未绑定真实focus/layout revision。G1-B2必须保存原始服务器Snapshot/epoch、单调截止、原子撤销标志，UI提交前取最早到期值再次核对，不能在集成时重新解释旧命令为新命令。

## 下一步及验收门槛

你方便操作电视时，按手册完成“本机开启→Windows严格验身份→电视批准/拒绝→假计数→电视主动撤销”，再逐次验证重放、challenge过期、真实空闲超时、断线和Activity暂停。保留双方对应日志与本机操作证据。票据不要贴入聊天或提交仓库。

本轮不继续真实桌面接入。只有G1-B1人工会话验收通过，才进入 **G1-B2：正式接入HomeView与MarcoFocusController**。这以最新用户阶段定义为准，替代早期文档把B2称为“只做会话”的拆分。


实现提交的 [PR CI](https://github.com/Pilipala9919/MarcoTV/actions/runs/42016961345) 和 [push CI](https://github.com/Pilipala9919/MarcoTV/actions/runs/42016951537) 已完成且均成功，独立TLS策略/Android构建步骤通过；两次上传产物数均为0。CI不替代上述人工会话验收。
