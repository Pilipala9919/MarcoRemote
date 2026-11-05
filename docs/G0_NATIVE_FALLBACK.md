# Marco TV 原生桌面焦点备选（P：尚未实现）

## 源码依据与严格范围

本次只读取 `D:\TV`，HEAD仍为 `a9d6cb8b64fd2e9030c82addd22edc40a5e755c0`，现有分支为 `codex/feedback-reporting`，未切换/修改。公开基线的相关证据：

- **C**：[HomeView.java 676–808](https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/app/src/main/java/com/pilipala/tvhome/HomeView.java#L676-L808)：方向输入改变row/selected；但通用onKeyDown首先可能转交recents/mover/edge等；onKeyUp的确认会调用host.launch/设置/网络/播放控件。因此禁止远程调用整个onKeyDown/onKeyUp或dispatchKeyEvent作为“受限焦点”实现。
- **C**：[PhoneManager.java](https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/app/src/main/java/com/pilipala/tvhome/PhoneManager.java)：显式电视批准、generation失效、主线程执行、revision冲突可作为生命周期参考；现有cookie/HTTP不能自动成为新永久控制凭据。
- **C**：[PhoneHttp.java](https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/app/src/main/java/com/pilipala/tvhome/PhoneHttp.java)：普通明文短连接，不新加高频输入路由。
- **C**：[home_accessibility.xml](https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/app/src/main/res/xml/home_accessibility.xml)：现有Home兼容无障碍与新方案无关。这里不添加无障碍、悬浮窗、INJECT_EVENTS或shell授权，不使用TaskBridgeServer。

## 最小接口

P：独立 `MarcoFocusController` 在Marco TV进程内调用受限的**卡片区焦点状态转换方法**，不模拟Android系统事件；单步只改变自有row/selected及必要绘制/滚动状态。先保持本地遥控器原有逻辑，避免为复用大幅改写稳定导航。

| 命令 | 参数 | 可观察结果 |
|---|---|---|
| focus.snapshot | 已授权session | opaque焦点ID、focusRevision、layoutRevision、availability；默认不返回应用名/列表 |
| focus.step | up/down/left/right；expectedFocusRevision；expectedLayoutRevision；commandId；epoch | 新焦点ID/revision，或边界no_change，或明确拒绝 |
| session.close | session/epoch | 清队列、注销该scope授权 |

不接受任意keycode、Intent、包名、URL、坐标、文本、文件路径、脚本。MVP不提供confirm/back/home/menu、长按、自动连发、启动应用或改变配置。左右到边界返回no_change，不打开edge；首行向上不进入header/播放行；空行跳过或返回no_target。焦点已有header/弹窗/抽屉/最近任务/移动卡片/屏保时返回unsupported_surface，不能自动唤醒、退出弹窗或抢回前台。

P：每条命令在UI线程**执行当下**检查：当前Activity存活、resumed且窗口有焦点、屏幕交互中、处于允许的卡片表面、不是本地移动/配置预览状态、session/epoch有效、deadline未过、两个revision匹配。暂停/窗口失焦/弹窗覆盖/本地导航/布局变化使旧快照失效；close使generation变化。迟到任务必须在修改状态前再次检查，不只在网络接收时检查。

为避免与本地遥控器互相争抢，本地输入使focusRevision增加，暂停remote控制直到获取新快照并重新开始手势。会话不跨Activity重建恢复；只报state_changed，不假定旧index对应同一卡片。移动后的ACK代表Marco内部焦点状态已提交，画面最终显示仍需真机验证。

## 网络和授权（P）

使用独立受限TLS端点，沿用架构中“二维码pin+短期高熵单次票据+电视批准”的信任原则；首期**会话级授权即可，不做持久后台常驻**。只授权 `marco.focus`，不能获得旧管理backup/upload权限。TV明确显示控制来源、剩余有效期与关闭入口；生命周期结束主动断开。无需接收端系统敏感权限，既有INTERNET权限下实现；若未来改变targetSDK，本地网络许可适配另审，不在本次变更。

QR生命周期120秒，控制会话建议5分钟、心跳5秒/15秒断开；这些是P默认值，需要实测。独立端口只在用户显式启用时绑定所选LAN，配对完成也不能绕过前台scope检查。帧≤4KiB、每秒≤10步、待执行≤4条，超出返回busy；不缓存过期步骤，也不在重连后重播。重复commandId同内容返回旧结果，不同内容拒绝；有限缓存与seq高水位结合。

TLS实现/自签名identity在Android9的兼容性、服务发现与二维码策略仍待spike。可先完成纯焦点转换测试再做transport，但不能以临时明文HTTP+固定token的验证版作为可发布安全方案。Windows验证客户端也使用严格pin后才提交票据；不继承v2研究工具的CERT_NONE例外。

## 两路线的统一能力选择

P：可以统一**动作意图与能力描述**，不能统一权限或伪称相同作用域。

```text
Capability = {action, scope, surface, supported, available,
              evidenceLevel, trustState, endpointId, revision}
AndroidTvV2: navigation.step / scope=tvSystem / surface=systemFocus
MarcoNative: navigation.step / scope=marcoOwnApp / surface=cards
```

`supported`与`available`分开：服务能力已知但未授权/不在前台时available=false。D级设备验证与运行时hello宣称分别记录，不因发现mDNS便标verified。

| 用户意图/运行条件 | 选择结果（P） |
|---|---|
| 明确“Marco卡片焦点”，原生端点已授权且允许表面可用 | 优先MarcoNative，权限最小且可回报焦点revision |
| 明确“电视遥控”，已配对v2 Ready | AndroidTvV2；必须允许system scope，不能假装仅限Marco |
| v2不可达，但MarcoNative可用 | 展示可用的“Marco桌面”模式；只有用户已选择ownApp意图/已授权scope才自动选原生 |
| 原生失焦/进入其他App，v2在线 | 停止当前手势，不静默切到系统scope；用户明确切模式后才用v2 |
| 双端点同名或同IP | 不自动认定同物理设备；需认证identity关联或用户确认 |
| 两者都不可用 | 明确unsupported/offline/permission，既不启用ADB也不安装服务 |

选择按**每个动作能力**而非整机类型，一次手势/session绑定一个endpoint。切换前取消队列、递增generation；不把原生未确认step在v2重发，不把v2按键重复发送成原生step。证书变化、被撤销和授权失败都禁止自动fallback；普通网络失效也不能提升scope。选择器测试应覆盖两端可用、scope不匹配、失焦、旧ACK、两个同名设备与无路由六类情况，目前均未实现。

## 最小后续PR拆分

1. MarcoTV独立功能分支：原创纯焦点转换及边界/空行/表面/revision测试；不改main、不增权限。
2. 会话级安全端点：TLS/pin/TV批准/限流/失焦停止；Windows命令行客户；所有边界先假业务后真机。
3. 真机：授权后四向各一次，画面+状态revision相符；本地键争用、弹窗、切App、断开、过期都拒绝输入。通过后才能把本方案标D。
4. 统一能力选择器：纯函数/状态机测试，随后再最小移动端UI；完整iOS、电脑receiver和手柄仍不在此阶段。
