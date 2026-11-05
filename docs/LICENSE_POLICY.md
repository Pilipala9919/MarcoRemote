# 许可证提案与第三方准入记录

审查日期：2026-11-05。本文件是项目采用方案及工程准入状态，不是新增的全仓授权文本。

## 自有代码

| 范围 | 拟采用/当前许可 | 当前状态 |
|---|---|---|
| MarcoRemote 原创、独立客户端/工具 | **拟采用 Apache-2.0** | 本仓库尚无根 LICENSE；落实许可文本、版权归属及既有贡献核对前，不声称已按 Apache-2.0 开源 |
| MarcoTV 的 MarcoFocusController 与测试 | **GPL-3.0-only，已随源文件标注** | 遵守 MarcoTV 既有 LICENSE，不复制到 Remote 后另行宣称为 Apache |
| 第三方文件/生成代码/资源 | 各自原许可 | 必须逐项审核，不能用仓库拟议许可覆盖 |

选择 Apache-2.0 是对未来独立原创代码的建议；它包含版权及专利授权和分发条件。若正式采用，应随分发保留许可、适用声明、上游 NOTICE 及修改说明，依据 [Apache-2.0 正文](https://www.apache.org/licenses/LICENSE-2.0)。在没有许可时默认版权约束仍适用，公共仓库仅允许 GitHub 平台定义的查看/fork 等行为，依据 [GitHub 官方说明](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)。

TV 当前许可证证据：[固定基线 LICENSE](https://github.com/Pilipala9919/MarcoTV/blob/a9d6cb8b64fd2e9030c82addd22edc40a5e755c0/LICENSE)。本轮没有将 Remote 的文档提案用于重许可 TV 或第三方代码。

## 六个研究项目

下表是**准入范围**，不是只看仓库名即批准全部文件。固定版本、许可证文件和调用链见 [REMOTE_RESEARCH.md](REMOTE_RESEARCH.md) 的许可审计。

| 项目 | 已读许可/固定版本 | 准入决定 |
|---|---|---|
| androidremote | `12e9438`，未找到覆盖原创实现的项目许可 | 只作源码研究；不复制、翻译或移植实现 |
| androidtvremote2 | `f49cf04703af1565e6216f1fc095b7d0477ca4a4`，Apache-2.0 | 仅固定版本 G0 独立 Python 测试工具可用；未批准其无服务器 pin 的 TLS 模式用于产品 |
| sofatap | `9ec71a0`，MIT | 可作候选参考；G1 未引入。复制前核对具体文件/依赖并保留版权许可 |
| penput | `1d7d11a`，MIT | 仅研究；其现有未认证 UDP 路线不满足本项目安全准入 |
| kdeconnect-kde | `aee1439`，逐文件 GPL/其他声明 | 仅研究；不移植到拟 Apache 的独立客户端，不能以顶层许可替代逐文件审计 |
| scrcpy | `a60891a`，Apache-2.0 | 研究/既有开发工具；ADB shell 输入能力不作为普通应用权限方案；未复制控制实现 |

## G0 开发工具依赖（不是 G1 产品运行依赖）

来源：固定 [requirements-g0.txt](../tools/requirements-g0.txt)、G0 已安装包 metadata 与 [G0 工具审核](G0_DEVICE_REPORT.md)。本轮没有升级依赖或重新进行完整传递依赖扫描。

| 依赖 | 版本 | 已读许可 | 准入范围 |
|---|---|---|---|
| androidtvremote2 | 上表完整 commit | Apache-2.0 | 独立测试环境 API 调用 |
| aiofiles | 25.1.0 | Apache-2.0 | G0 测试依赖 |
| cryptography | 50.0.2 | Apache-2.0 OR BSD-3-Clause | G0 测试依赖；二进制附带组件仍需分发前复审 |
| protobuf | 7.36.2 | BSD-3-Clause | G0 测试依赖；proto/生成代码单独审核 |
| zeroconf | 0.148.0 | LGPL-2.1-or-later | 只在隔离开发环境执行；未批准静态打包/移动端分发 |
| ifaddr | 0.2.0 | MIT | G0 测试依赖 |

此表不是完整 SBOM，也不是漏洞扫描通过记录。G1-A 的新增 Java 控制器与测试没有引入第三方库；构建和设备测试使用现有 JDK、Android SDK/D8、ADB 工具链，工具许可与产品许可分开。G1-A 不实现 TLS。

## G1-B 进入产品依赖的门槛

1. 记录精确版本/commit、下载来源、文件哈希、直接及传递依赖、许可证/NOTICE/生成代码来源；版本变更重新审核。
2. 判定实际用途：开发工具、动态运行库、复制代码、静态合并或应用商店分发；满足各自义务后才能批准对应用途。
3. 安全单独审核：TLS 协议版本、证书/完整 pin 校验、私钥储存、随机数、撤销、日志泄密与失败处理。许可证允许不能替代安全审查。
4. Android 平台 TLS/AndroidKeyStore 是候选，需 Android 9 真机兼容和 Windows 严格 pin spike；**本轮尚未批准任何完整安全会话实现**。
5. 没有来源许可、需要敏感输入权限或不能明确关闭认证失败路径的实现不进入产品。不得为赶真机演示引入固定明文 token/HTTP 遥控入口。


## G1-B1 本轮补充

独立测试包与 Windows 客户端位于 MarcoTV `security-spike`，原创 GPL-3.0-only；未复制到 MarcoRemote 后重许可。Android使用平台JSSE/AndroidKeyStore，Windows客户端仅Python标准库ssl。证书测试复用已审查的cryptography50.0.2开发依赖，未进入APK。真实TLS兼容/负例已记录在 [B1报告](G1_B1_REPORT.md)，这不是独立安全审计或产品分发准入。正式消费者扫码/配对、debug移除、系统补丁和传递依赖SBOM仍需另审。早期“尚无TLS实现”描述属于G1-A时点，由此记录更新。
