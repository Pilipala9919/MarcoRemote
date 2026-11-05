# Marco Remote

Marco Remote 是面向电视与电脑的遥控项目，目前处于技术验证阶段。现阶段优先验证 **Marco TV 自身卡片区域的四方向焦点控制**；尚未提供可发布的 iOS 客户端或真实桌面 LAN 遥控服务。G1-B1 独立验证服务仅用于假输入测试。

## 当前进度

| 阶段 | 结果 | 不代表什么 |
|---|---|---|
| G0：Android TV Remote v2 | 真实 Android 9 小米电视可通过既有 ADB 到达，但本次 v2 端口拒绝、配对未建立 | 不代表该机已支持 v2 遥控，也不外推全部小米电视 |
| G1-A：纯焦点控制器 | MarcoTV 独立功能分支已实现并测试，Android 构建通过；真实电视 ART 的逻辑测试通过 | 没有接入 HomeView、TLS、电视授权或 LAN 请求，未证明可见焦点移动 |
| G1-B1：安全通信与配对 | 自动化、Android构建及报告所列真实电视授权会话测试通过，含撤销、重放、空闲/绝对期限；等待阶段审查 | 仅假输入；不同场景的受测版本与未测项目单列，不代表真实焦点控制 |
| G1-B2：真实焦点接入 | 等待B1验收 | 不提前接入HomeView/MarcoFocusController |

本轮不做完整 iOS、跨应用遥控、Windows/macOS 输入接收端、电脑鼠标或虚拟游戏手柄。不增加无障碍、root 或系统输入注入权限，不自动发布 APK。

## 文档入口

- [G1-B1 安全通信/配对报告](docs/G1_B1_REPORT.md)
- [G1 实际验证报告与能力矩阵](docs/G1_DEVICE_REPORT.md)
- [G0 真机报告](docs/G0_DEVICE_REPORT.md)、[G0 复测手册](docs/G0_RUNBOOK.md)
- [原生焦点备选设计](docs/G0_NATIVE_FALLBACK.md)
- [架构决策](docs/REMOTE_ARCHITECTURE.md)、[开源项目研究](docs/REMOTE_RESEARCH.md)
- [拟采用许可证与依赖准入](docs/LICENSE_POLICY.md)

证据分开记录：C=固定源码；T=自动化测试；D-runtime=真实设备上的逻辑执行；D-UI=真实授权网络请求造成可见变化；P=设计。主机测试、Android 构建、设备运行时测试都不能替代 D-UI。

## Windows 验证

本仓库保留 G0 的 v2 实验工具，固定版本见 [requirements-g0.txt](tools/requirements-g0.txt)。其服务端身份校验存在已记录的实验限制，只用于 G0 手册中的指定设备研究，**不是 G1 安全客户端**，也不能套用到新的原生控制接口。

G1-A 的生产类与测试位于 [MarcoTV](https://github.com/Pilipala9919/MarcoTV) 的 `codex/g1-native-focus` 分支。在该检出中配置项目 JDK 后运行：

```powershell
python scripts/test_marco_focus.py
```

真实电视 ART 复测方法见 G1 报告；它不会安装 APK 或操作桌面。当前没有真实焦点网络命令；B1 Windows 假输入客户端见安全验证报告。请勿把测试用 `beginAuthorizedLease()` 当成认证入口。

## 许可证状态

**拟为 MarcoRemote 今后原创且可独立分发的代码采用 Apache-2.0；当前尚未正式增加根 LICENSE，该提案不等于已经授权全仓复用。** 公共可见性本身不是开源许可，详见 [GitHub 的许可说明](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)。

MarcoTV 中本轮新增控制器和测试遵循该仓库既有 **GPL-3.0-only**。不会因 Remote 的拟议许可证而改变 TV 代码的许可证。第三方准入按具体版本、文件与分发用途分别审核；G0 测试依赖通过不代表允许打包到产品。当前没有复制本轮六个研究项目的实现到 G1 控制器。

## 分支与验收

MarcoTV 代码通过功能分支 PR 审查；MarcoRemote 的 G1 文档分支基于 G0 分支，G0 PR 合并前使用堆叠 PR，避免混入旧研究差异。没有修改两仓 main，也没有发布 APK。B1 真机证据、失败修复与剩余边界已交付，等待用户审查；通过后才进入 B2 真实焦点适配。
