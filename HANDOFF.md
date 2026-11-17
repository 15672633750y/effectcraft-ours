# ShimoveAex 交接文档（2026-11-17 定稿版）

> 给任何接手这个项目的会话：先读这一份，再动手。所有结论都是实测得出的，别重走弯路。

## 0. 项目一句话
在 GitHub Actions 上把开源的 EffectCraft（storytold/effectcraft v0.24.1）打成安卓 APK，
套上 `builder/` 里的 Android 外壳，用 300 多个补丁改造 UI/汉化/特效，产出 **ShimoveAex**。

- 仓库：`15672633750y/effectcraft-ours`
- 工作区：`/storage/emulated/0/work/effectcraft/`
- 推送工具：`python3 tools/push.py "<msg>" '{"<远端路径>":"<本地文件>"}'`
- 检查工具：`tools/preflight.py`（干净树上跑全部补丁）+ `tools/precheck.py`（静态守卫）
- 令牌：`/data/user/0/com.deepseek.harness/files/.ec_token`（fine-grained，不过期）
- 到期检查：`python3 tools/token_check.py`

## 1. 铁律（违反会出事）
1. **绝对不要碰 `/storage/emulated/0/QQagent`**（用户明确禁止）
2. 真正生效的工作流是 **`.github/workflows/build-ours.yml`**；根目录 `build-ours.yml` 是历史残留，改它没用
3. 推送前 **preflight + precheck 都通过** 才 push
4. 补丁**只覆盖、不删除**；一次推一批，推完等出包
5. 每个补丁必须有 `if __name__ == "__main__": main()` 和 MARKER 幂等检查
6. 补丁按**文件名字典序**应用（`2xx` < `5xx` < `99_` < `zz_`），锚点不能依赖排在自己后面的补丁
7. **翻译行里含英文双引号必须转义成 `\"`**，否则 Rust 字符串断裂（踩过两次）
8. 本地 `builder/` 极易被改脏导致 preflight 白过；必要时用 `tmp/artcraft-0.5.0.tar.gz` 还原纯净树
9. 用户说"失败了"时：**先查日志定位，再改，不要猜**

## 2. 已定稿，不要改
| 项 | 值 |
|---|---|
| 应用名 | `ShimoveAex` |
| 包名 | `com.shimoveaex.effects` |
| 版本 | `0.52.1`（补丁 `320_version.py`） |
| 图标 | `tools/app-icon.png`（1024 PNG，见第 3 节规范） |
| 签名 | 用户 keystore，别名 `shimove`；GitHub Secrets `KEYSTORE_BASE64` / `KEYSTORE_PASSWORD` |
| 官方签名指纹 | `6461ee2dbcdb7882575242218895f6ac4cab24abdfa97353bbe0d702bb4a75a3` |
| 开屏 | Canvas 自绘 + 圆角 22% + 淡入淡出，总时长不得超过默认开屏 |
| 引擎版本 | v0.24.1（上游） |

### 签名相关补丁
- `310_signing_alias.py`：builder 里别名改成 `${ARTCRAFT_KEY_ALIAS:-shimove}`
- `304_signature_verify.py`：指纹写死校验；不符只 Toast「非官方版本」+ logcat，**不阻止启动**；
  支持 `DCIM/EffectCraft/devmode.txt` 全跳过、`allowed-signatures.txt` 逐行白名单
- `303_signature_record.py`：每次启动把指纹写到 `DCIM/EffectCraft/signature.txt`

## 3. 图标规范（重要，踩过巨坑）
### 源图要求
- **PNG**，1024×1024，白底，不要 JPG
- 人物宽度约占画布 **56%**（51%~60% 可调）
- 人物下沿落在画布 **83.3%** 高度处（下方留 16.7%，正好等于启动器裁切量）
- 左右居中

### 构建链路
`tools/app-icon.png` → workflow `cp ours/tools/app-icon.png` → `artcraft/lib/app_icons.py` 生成：
`mipmap-*/ic_launcher.png`、`drawable-xxxhdpi/ic_launcher_foreground.png`、
`drawable/ic_launcher_background.xml`、`drawable-nodpi/splash_icon.png`（开屏 512）、`mipmap-anydpi-v26/ic_launcher.xml`

### 致命坑（务必记住）
`app_icons.py` 的 `_foreground()` 原来会 **`split()[3].getbbox()` 裁到内容边界再缩到 62% 居中**，
导致**无论源图怎么加白边、怎么下移，桌面图标都一模一样**。
已由 `315_icon_no_trim.py` 改成整张画布等比铺满，构图才真正生效。

### 排查顺序
`改动有没有进包/有没有被脚本改掉` → `构建脚本` → 最后才是 `启动器裁切`。
系统图标缓存也会骗人：重启或清缓存才刷新。

## 4. 设置备份（用户很在意）
- 真实位置：`Android/data/<pkg>/files/config/prefs.json`（实测 7950B）
- 镜像：`DCIM/EffectCraft/settings.json`
- 补丁链：`302_settings_backup.py`（骨架）→ `312_settings_save_early.py`（启动 2.5s + onPause 都写）
  → `313_settings_path.py`（多处候选路径）→ `317_settings_external.py`（**真正路径：external/config**）
- 已验证：0.52.1 版能生成 `settings.json` ✅
- 旧包（`com.artcraft.effectcraft.sx`）的设置**迁不过来**：它在内部 `/data/user/0/...`，
  无 root 谁进不去；预设/工程/密钥在公共目录，本来就没丢

## 5. 诊断与清理（已实现）
- `314_debug_files.py` + `316_debug_deeper.py`：启动时把私有目录树（6 层 + 外部）写到 `DCIM/EffectCraft/debug-files.txt`
- `318_cleanup_scripts.py`：一次性删掉 `config/Scripts/` 里的无关大压缩包（LM Arena / DeepSeek Harness /
  XRecorder / 搜图神器 / QQagent），结果写 `cleanup.txt`
- `321_crash_rotate.py`：`crash-*.txt` 只保留最近 5 个

## 6. 汉化
### 机制
- 界面文案表：`crates/ui-egui/src/i18n/ui.rs` 的 `SIMPLIFIED_CHINESE`
  （新条目插在锚点 `];\n/// EFFECTCRAFT_OURS_ZH_BLEND_SOLID_V1` 之前）
- 菜单/参数/效果名：`i18n.rs` / `i18n/prop.rs` / `i18n/effects.rs`（按 id 映射）
- 弹窗走 `crate::i18n::tr(o)`；带 `format!` 的句子配 `tr_args`
- 批次补丁：`28x_zh_batchN.py` / `30x_zh_batchN.py` / `zz*_zh_*.py`

### 现状
- 已完成到第 17 批，效果参数名 1071 条全中文，界面直接硬编码英文基本清零
- 复核仍有约 236 条"候选英文"，真正该翻的约 120~150：
  面板小词（Type slot、SOURCE FOOTAGE）、GPU/渲染提示（Shared GPU preview disabled…）、命令反馈长句
- 不该翻：字体名、快捷键名、测试数据/文件名、行业格式名（NTSC/PAL/HDV/UHD/Cineon）、
  其他语种表项（Servicios/Visa alla/Ukryj EffectCraft）

## 7. 调色（用户会持续优化）
- 文件：`crates/effects/src/ffx_vintage.rs`
- 顺序不能乱：`fitted` → 对比度 → 径向增益(1.10 − 0.16r²) → 饱和度/亮度/色调/暗部(+chroma) → `shown` → amount 混合
- 拟合表 `FIT: [[f32; 20]; 3]`，**参数必须在拟合之后应用**
- 基准：MAE 3.19/2.90/2.67，luma 77.2，对比度 38.4，饱和度 0.181（AE 对应 77.2 / 39.1 / 0.183）
- 验证：同源图只套该效果导出 PNG，对比三通道 MAE / 平均亮度 / 对比度 / 饱和度
- 别重犯：`shown` 提前算导致偏暗；只改 FIT 不动径向增益

## 8. 布局切换器（下一个大功能，用户已定稿交互）
### 入口
- 画布右上角固定两个字 **「布局」**，**没有下拉箭头**，小、低对比、常驻
- 点击：先**微微发光**（120ms）→ **淡出消失**（180ms）

### 打开过程
1. 画面**逐渐模糊**（0 → 8~12px，280ms，缓出）
2. 布局条目**依次插入**：每条间隔 60ms，从左侧进入 + 渐显 + 右移 8px→0（smoothstep 220ms）
3. 每条内容：自绘缩略示意图（**不用别人 logo**）+ 名称 + 一行小字说明

### 选择过程
4. 点击任意一条 → **立即切换布局**（无确认、无二次弹窗）
5. 同时：扫光 + 赛博元素 + 画布中央浮出**该布局名字**（约 900ms）
6. 切换完成：模糊淡出（200ms）→ 名字消失 → 「布局」渐显回来（150ms）
7. 取消（点空白）：反向过程，总时长 ≤ 250ms
8. 任何时刻不许卡住：模糊层 800ms 内必须消失

### 选中态：沿用快捷键面板的「多选发光」
- **不填充背景**，只在磁贴矩形外画 **3 圈描边**，外扩 1.5 / 3 / 4.5px
- 颜色用主题强调色 `t.accent`，alpha 递减约 **220 / 120 / 60**
- 线宽 1.0~1.5px，圆角与磁贴一致
- 文字因此不会被白色蒙层压暗，在发光背景上依然清晰
- 选中时最外圈 alpha 从 0 渐入（约 120ms），取消直接消失
```rust
let r = rect.expand(1.5);
ui.painter().rect_stroke(r, radius, Stroke::new(1.5, t.accent.gamma_multiply(0.86)));
ui.painter().rect_stroke(r.expand(1.5), radius, Stroke::new(1.2, t.accent.gamma_multiply(0.47)));
ui.painter().rect_stroke(r.expand(3.0), radius, Stroke::new(1.0, t.accent.gamma_multiply(0.24)));
```
### 实现的现实提醒
- egui 没有内建高斯模糊；**推荐近似**：全屏黑遮罩 + 柔光边框 + 内容 0.98→1.0 缩放
- 真模糊要抓纹理 + 多趟 box blur，移动端注意帧率
- stagger 用 `ctx.input(|i| i.time)`：`let t = ((now - open_at) - i*0.06).clamp(0.0, 1.0);`
- 缓动统一 smoothstep：`t*t*(3.0-2.0*t)`，禁止线性

### 布局内容（4 套，全部复用现有面板）
| 名称 | 特征 |
|---|---|
| 经典 | 当前默认（多面板） |
| 简易 | 上预览 + 下时间线 + 底部标签栏 + 工具图标条（快影风） |
| 专业 | 多面板 + 时间线居中（AE 风） |
| 极简 | 全屏预览，时间线悬浮小条 |

命名用中性词，**不要写 CapCut / Blurrr / After Effects / NodeVideo 等商标**，也不要用别人的 logo。

### 附加（用户想"比它好看"）
- 扫描光线沿边框跑（t 0→1，循环 1.6s）
- HUD 四角短线
- 自定义主色：设置里取色 → 存 prefs，所有发光/描边跟随
- 赛博主题：背景 `#0A0E14`、主色 `#00E5FF`、次色 `#FF2E88` + 扫描线纹理

## 9. 新需求：PNG 头像可拖动贴边（用户刚提）
在 UI 里放 PNG 头像/贴图时，要能**用鼠标/手指拖动**，并能**吸附到画布边缘**（贴边）：
- 拖动时跟随指针，松手吸附最近边（阈值约 24px）
- 吸附后边缘对齐（0 间距），角上可同时吸两条边
- 数据存进图层属性（x/y + 贴边标记），不要只存绝对像素
- 需与现有变换/关键帧体系兼容：拖动即改 `position`，可打关键帧

## 10. 待办清单（按优先级）
1. **布局切换器**（第 8 节，含描边动画 + 赛博字）
2. **PNG 头像拖动贴边**（第 9 节）
3. 汉化收尾（约 120~150 条）
4. 调色继续优化（必须给数字）
5. 文字动画器导入（`inbox/奇峰自由文字出场.ffx` 的「蒸发」，已能读真实数值）
6. S_ 系列效果：`131_sapphire_fx.py` 已有实现，属"近似 Sapphire"，**不要承诺一模一样**
7. 字体缺失提示（小项）
8. 上架时才做：APK 改名 `ShimoveAex-<version>.apk`（补丁 319 锚点需重写）、R8、签名校验强化

## 11. 本次踩过的坑（血泪）
- `302` 用 `installCrashLogger()` 当锚点，但字典序排在 `99_crash_log.py` 之前 → 锚点 0 命中、构建红
- 第 17 批有一行 `("leading: expected a number or "auto"", ...)` 引号未转义 → Rust 语法错误、构建红
- 图标改了十几次没变化，真正原因是最上面的 `getbbox()`，与启动器无关
- 本地 `builder/` 被直接跑补丁改脏 → `preflight` 假通过；要用纯净树
- 改 `.github/workflows/` 需要令牌带 `Workflows: Read and write`，否则 403
- 推送太频繁会把前面的构建挤成 `cancelled`，一轮只推一次

## 12. 布局切换的健壮性要求（用户明确担心"几个布局全不能用"）
必须同时满足这四条，否则不许合入：

1. **布局只负责"摆放"**：每个布局复用现有面板与渲染代码，不允许复制一套绘制逻辑。
   这样坏一个布局不影响其他布局，也不影响引擎/时间线/特效。
2. **读不到设置 → 回落「经典」**：`prefs.json` 里 layout 字段缺失、未知、损坏时，
   一律按经典布局启动，绝不启动到空界面。
3. **切换失败 → 保持原布局**：切换过程包在异常捕获里，出错只记日志（`logcat` + 可选
   `DCIM/EffectCraft/layout-error.txt`），当前画面保持不动。
4. **异常不许冒泡到主循环**：布局代码里的 panic/异常必须被吞掉，不能让整个 UI 崩掉。

最坏情况应只有一种：**永远进经典布局，功能一个不少**。
