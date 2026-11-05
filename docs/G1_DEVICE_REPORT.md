# G1-A 实际验证报告：纯焦点控制器

日期：2026-11-05，Asia/Shanghai。MarcoTV [实现 PR #2](https://github.com/Pilipala9919/MarcoTV/pull/2)，提交 `8ab4ec1dc0c82d1abb1c0b1662128359a19955d9`，基于 main 的 `a9d6cb8b64fd2e9030c82addd22edc40a5e755c0`；工作在独立功能分支。G0 文档 PR 仍开放，本仓 G1 文档以 G0 为父分支，不自动合并 main。

## 验收结论

**按用户允许的替代交付范围，已完成纯 MarcoFocusController 与自动化测试。安全会话和 HomeView 适配器尚未实现，因此 G1 最终目标“经过授权的 LAN 请求使真实电视桌面卡片焦点可见变化”未完成、未通过。** 电视可连接；缺口不是没有设备，也不是等待用户授权，而是安全/UI 集成尚未交付。没有为演示开未认证网络接口。

| 验收层 | 本次结果 | 严格边界 |
|---|---|---|
| 单元/领域测试（T） | **通过**：18 场景、2,736 个枚举转换、23,233 断言；全量 17 套件通过 | 合成布局/假时钟，不代表真实物理遥控、弹窗或 socket 故障已验证 |
| Android 构建（B） | **通过**：标准/受限 API28 编译、D8 min23；附带 Lite API14 回归产物 | 独立本地验证签名；未安装 APK，不是正式发行产物 |
| 真实电视运行时（D-runtime） | **通过，仅纯逻辑**：真实 MiTV-ASTP0 Android9 的 ART 独立测试进程运行同一套测试 | 不在 Marco TV Activity 内；没有 HomeView 绘制，也没有 LAN 请求 |
| 真实电视端到端（D-UI） | **未执行/未通过** | TLS、电视批准、临时网络会话、Windows LAN 客户端及可见焦点证据均缺失 |

C=固定源码依据；T=主机自动化；B=构建；D-runtime=设备运行时；D-UI=授权网络输入的用户可见效果；P=后续设计。不能将任一前层升级为后层。

## 源码与调用链（C）

全部为本轮原创代码，无第三方实现拷贝，遵循 MarcoTV 的 GPL-3.0-only。

| 来源文件 | 调用链/可核实结论 |
|---|---|
| [MarcoFocusController.java](https://github.com/Pilipala9919/MarcoTV/blob/8ab4ec1dc0c82d1abb1c0b1662128359a19955d9/app/src/main/java/com/pilipala/tvhome/MarcoFocusController.java) | `prepare → execute → surfaceStatus → row/selected 更新 → Result`；只允许四向枚举；左右边界不进侧栏，上下跳空行并保留每行选择；不调用 KeyEvent |
| 同文件的 `replaceLayout/localFocus/setBlocked` | 两个 revision、同尺寸布局变更、本地边界按键和离开后返回位置都使旧快照失效；各 blocker 独立；新增阻止状态撤销执行许可 |
| 同文件的 `beginAuthorizedLease/disconnect/destroy/now` | 进程内许可围栏、到期拒绝、断连取消、销毁不可恢复、单调时钟回退关闭；**不是认证实现** |
| [MarcoFocusChecks.java](https://github.com/Pilipala9919/MarcoTV/blob/8ab4ec1dc0c82d1abb1c0b1662128359a19955d9/scripts/MarcoFocusChecks.java) | 直接调用生产控制器；18 场景包括指定保护条件；小布局枚举不是整个状态空间形式化证明 |
| [test_marco_focus_device.py](https://github.com/Pilipala9919/MarcoTV/blob/8ab4ec1dc0c82d1abb1c0b1662128359a19955d9/scripts/test_marco_focus_device.py) | 编译同一源码和测试→D8→ADB 推送唯一临时 JAR→独立 app_process→检查完成标志→删除临时文件；没有输入注入 |
| [G1_FOCUS_CONTROLLER.md](https://github.com/Pilipala9919/MarcoTV/blob/8ab4ec1dc0c82d1abb1c0b1662128359a19955d9/docs/G1_FOCUS_CONTROLLER.md) | 完整类型/API 契约、调用线程及后续适配边界 |

没有生产代码调用控制器。本轮对 HomeView、MainActivity、PhoneHttp、PhoneManager 和 AndroidManifest 与基线逐字节核对一致；没有新增无障碍/root/系统注入权限，没有修改稳定检出。局部代码进入 APK 并不表示它已经接入真实 UI。

## 真机执行过程与证据

公开摘要：[g1-20261105.json](evidence/g1-20261105.json)。包含源码 SHA-256、APK/DEX 哈希、运行时间、去地址设备信息、完整领域测试结果和未验收原因。原始日志留在功能工作树被忽略的 `private/g1-art.json`；构建/主机日志在 `build/g1-*`。公开摘要不含序列号、IP、私钥、票据或授权码。

1. 使用 G0 已有 ADB 授权连接设备，只读确认 `ro.product.model=MiTV-ASTP0`、Android=9、SDK=28、固件=`22.8.30.1385`。
2. 在 Windows 编译**当前提交中的生产控制器和同一套测试**；源码哈希已与 Git blob 核对。D8 min23 生成测试 JAR，SHA-256 为 `1777c103ab37dde904afbff63ce5ad476b8335dd306612cfa5680b434d1429f3`。
3. 最终归档的设备运行开始于 **2026-11-05 13:07:32 北京时间**。通过既有 ADB 把 JAR 放在 `/data/local/tmp` 的专用唯一文件，运行独立 `app_process`。退出码 0，完成标志：

   ```text
   PASS MarcoFocusChecks: 18 scenarios, 2736 enumerated transitions, 23233 assertions
   ```

4. finally 删除该确切临时文件，清理命令成功。没有安装 APK、启动/替换桌面、执行 ADB keyevent、改变权限或运行输入服务。测试作用域是 shell 启动的独立进程，不证明普通应用中的 Activity/Looper 生命周期适配正确。

**没有可见焦点截图或网络成功日志，因为相应链路尚未实现。** ART 中的模拟弹窗/失焦/断连/超时只证明状态机拒绝旧命令；不能当成实际电视 UI 或网络故障处理的成功证据。

## 已验证与未验证能力矩阵

| 能力/场景 | C/T | D-runtime | D-UI / 下一门槛 |
|---|---|---|---|
| 自有卡片四向、边界、跳空行 | 预期位置表与枚举不变量通过 | 同测试通过 | HomeView 真实卡片适配未实现 |
| 焦点 revision / 本地遥控冲突 | 同位置按键及位置往返均拒绝旧命令 | 合成事件通过 | 物理遥控器与网络请求交错未测 |
| 布局 revision / 删除重排 | 缩减、空布局、恢复、同尺寸重排通过 | 合成布局通过 | 真实应用扫描/隐藏/移动卡片事件桥接未测 |
| 失焦/暂停/屏幕关闭 | 独立 blockers 与撤销通过 | 合成事件通过 | Activity/窗口/锁屏真实事件未测 |
| 弹窗/抽屉/最近任务/移动/预览/屏保 | 全枚举覆盖；交叠状态不互相解除 | 合成事件通过 | 实际表面状态聚合尚未接入 |
| 断连/重新连接 | 旧 epoch 不可重放，新许可明确重建 | 调用 disconnect 模拟通过 | TCP/TLS EOF、心跳丢失和重新批准未测 |
| 超时 | 会话/命令精确截止、截止前 1ms、回退时钟 | 假时钟通过 | 真计时器与网络队列延迟未测 |
| 临时许可与队列取消 | 单次命令对象、所属实例、线程约束通过 | 同测试通过 | 没有真实网络 session/命令队列/限流或 commandId 缓存 |
| TLS 与完整 pin | 未实现 | 未测 | 需审核并实测后才发送配对票据 |
| 明确电视批准/撤销 | 未实现；测试直接调用许可方法 | 未测 | 需要电视 UI、独立短期票据及撤销入口 |
| Windows LAN 客户端 | 未实现；当前 CLI 只是测试运行器 | 未测 | 安全会话通过后实现最小四向/快照客户端 |
| 可见焦点变化 | 没有 UI 接入 | 不适用 | **G1 最终验收未通过** |

## Windows 复测

在 MarcoTV 功能分支配置项目 JDK/Android 工具链后：

```powershell
python scripts/test_marco_focus.py
# $adb 和 $serial 由本地环境设置；设备必须已有开发授权。
python scripts/test_marco_focus_device.py --adb $adb --serial $serial --output private/g1-art.json
```

第一条不需要电视。第二条仅做上述 ART 逻辑验证，不能用它作为 Windows LAN 客户端。脚本失败需保留退出码及报告，不能把仅有 push 成功判定为通过。不要上传本地完整环境信息。

Android 构建使用既有 `scripts/build.py`、`--restricted` 和 `scripts/build_lite.py`，随后 `python scripts/test_offline.py`。新工作树需配置自己的本地验证 key；不要覆盖或拷贝稳定版签名 key。本次三个本地构建 exit0，APK 签名与对齐校验通过。标准版 SHA-256：`438807c5125dc1cca7fa9f4a0a8e03174eb3d38d883f6b9fb1f119d075b48588`，其他产物及独立验证证书指纹见证据 JSON。它不是官方证书，不能用于升级正式安装。

全量套件最终 **17/17，24.53 秒**。首次全量尝试因新工作树缺少受限版产物而中止，补建受限版和 Lite 后重跑成功；首次构建的外层日志收集发生 Windows 编码错误，已用按字节保存的完整构建重跑替代，不把日志采集异常说成代码编译失败。既有受限版检查输出中的“official signing identity”只是两个 APK 签名相同比较，本报告没有据此声称官方签名。

CI 已加入焦点测试；push/PR 不自动上传 APK，仅手动触发才可归档产物。最初继承旧自动上传策略的两个 CI 运行已取消，后续运行使用新保护条件。本报告的 17/17 指本地已完成运行。另外已核实当前提交的 [PR CI](https://github.com/Pilipala9919/MarcoTV/actions/runs/41972228595) 与 [push CI](https://github.com/Pilipala9919/MarcoTV/actions/runs/41972222957) 均成功，新增焦点测试步骤 success；两次上传产物数均为 0。旧的两个已取消运行也均无上传产物。

## 下一阶段最小任务与停止条件（P）

1. **G1-B1 TLS/授权隔离验证**：候选 Android 平台 TLS + AndroidKeyStore；固定协议版本、身份/pin、私钥生命周期，完成 Android9 与 Windows 握手；错误 pin/过期票据/拒绝授权时不得发送或执行输入。新临时凭据独立于 PhoneHttp/PhoneManager。许可与安全审核见 [LICENSE_POLICY.md](LICENSE_POLICY.md)。
2. **G1-B2 安全会话**：用户在电视主动开启，120 秒一次性票据与明确批准，5 分钟会话、随时关闭、心跳/EOF/超时注销；帧 4KiB、排队 4 条、每秒 10 步、commandId/seq 去重。以上传输层参数目前是设计，不是控制器已经提供的功能。
3. **G1-B3 UI 适配器与 Windows 客户端**：所有真实生命周期/弹窗/本地遥控/触摸/布局事件汇入控制器；同一 UI 回调中重查条件并提交 row/selected、滚动及绘制。不能用新快照替换客户端旧 revision 来掩盖冲突，也不跨网络重连重放旧命令。
4. **G1-B4 真机验收**：先取得电视批准，再在 Windows 获取快照并四向各执行一次；保存动作前后画面、命令 ID、revision、拒绝原因与时间。依次实际触发失焦、弹窗、物理遥控冲突、断开连接和会话超时；每个旧请求必须拒绝且画面不被抢回。重连必须新授权。无真实证据则仍不能标 D-UI 通过。

当前不因原生未就绪而自动切换 ADB/v2 或系统作用域；也不开始完整 iOS、电脑接收端或手柄。两路线统一能力模型仍是 P，须保留 `scope=marcoOwnApp` 与 `scope=tvSystem`，不能以本轮逻辑测试把 `available/verified` 自动设为 true。
