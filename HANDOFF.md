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
1. ~~布局切换器~~ ✅ 2026-11-18：`330_layout_switcher.py`（ours-864 第一版 / ours-873 扫描光+HUD 四角）
   - 四套布局直接映射 dock 内置工作区：经典 Default / 简易 Small Screen / 专业 Standard / 极简 Minimal
   - 仍可做：真高斯模糊（要抓纹理 + 多趟 box blur）、布局卡片里的实时缩略图
2. ~~PNG 头像拖动贴边~~ ✅ 2026-11-18：`332_png_edge_snap.py`（ours-870）
   - 24px 画布边缘吸附、X/Y 独立（角上双吸）、松手写 `snap:left,top` 到图层批注
3. ~~汉化收尾~~ ✅ 2026-11-18：第二十批（`331_zh_batch20_status.py`，ours-866）
   - `tr()` 覆盖 617/618（唯一没翻的是本来就是中文的「当前渲染」）；直接画的英文 0
4. ~~调色~~ ✅ 2026-11-18 数字版：`334_vintage_matrix.py`
   - 只有拟合表 4.84/4.93/4.60 → +径向 3.22/2.92/2.67 → **+残差矩阵 3.01/2.68/2.47（平均 2.94→2.72）**
   - 径向系数网格搜索已到极限（最好 3.14/2.84/2.65），别再动径向
   - 只有 `inbox/原图.png → inbox/调色.png` 是配对前后帧，其它"一针/二十二针"不是那一对
5. 文字动画器导入 ✅（`314_ffx_text_animator.py`，内置「蒸发」）
6. S_ 系列效果 ✅（`131_sapphire_fx.py` 四个效果参数集已补齐，仍是"近似 Sapphire"）
7. ~~字体缺失提示~~ ✅ 2026-11-18：`333_missing_font_hint.py`（ours-874）
8. 上架时才做：R8、签名校验强化（APK 文件名已由 `319_apk_filename.py` 改成 ShimoveAex-<version>.apk）

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

## 13. 工具栏改版（用户 2026-11-18 01:37 定的方案）

### 第一版：把「快捷」按钮挪到菜单栏（现在就做）
- 现状：`204_shortcut_at_brand_slot.py` 把快捷键入口做成**圆形 PNG 图片按钮**，
  放在工具栏最左边（原蓝色 A 的位置）
- 改成：
  1. 工具栏最左边**不再画任何图片**（移除那段 image 绘制，槽位留空或直接不占位）
  2. 在**顶部菜单栏「帮助」后面**加一个普通文字按钮「**快捷**」，
     字号、高度、间距与「文件/编辑/…/帮助」完全一致
  3. 点击行为不变：展开/收起原来的快捷键面板（`ours-shortcut-open` 那个 data 开关）
- 验证：菜单栏出现「帮助 快捷」相邻两项；点「快捷」面板照旧弹出；左侧不再有头像图标

### 第二版：左侧原位置改成账号入口（交给接账号的会话）
- 位置：工具栏最左（原 PNG 按钮那个槽）
- 未登录：显示「**登录**」文字按钮（低对比，与工具栏风格一致）
- 已登录：显示**用户头像**（无头像时用用户名首字圆形占位）
- 点击：
  - 未登录 → 打开登录/注册页
  - 已登录 → 弹出个人信息卡：头像、昵称、**性别、生日、个性签名**，均可编辑并保存
- 后端：`GET /me`、`PUT /me`（字段放 `profile` 或 `prefs_json` 里的 `profile`）
- 视觉：与工具栏同高（26px 左右），圆形头像，hover 有提示

### 本地预览工具（换图标前先看效果）
```bash
cd /storage/emulated/0/work/effectcraft
python3 tools/icon-preview.py                # 预览当前 tools/app-icon.png
python3 tools/icon-preview.py 新图.png        # 预览指定图
# 输出：builds/preview/icon-check.png（= 桌面裁切+圆角后的真实效果）
```
模拟规则：四边各裁 16.7%（只留中间 66.7%）+ 圆角 22%。
满意后覆盖 `tools/app-icon.png` 再推送，构建会自动生成全套尺寸。

---

## APP-交接（2026-11-18 06:45）——App 侧当前任务

## 0. 一句话现状
App 能跑（877 已出），但**用户要的三件事还没生效**：布局按钮样式、布局真正重排、点了秒关。
上一轮会话上下文已满（299M），必须换新会话接手。

## 1. 当前版本与包
- 最新包：`ours-877`（`ShimoveAex-0.52.1.apk`）
- 版本号 0.52.1（补丁 `320_version.py`）
- 包名 `com.shimoveaex.effects`，应用名 `ShimoveAex`

## 2. 必须修的（用户 877 实测反馈）
### 2.1 「布局」入口不是按钮
- 现状：画布右上角只有**两个字「布局」**，还是纯文字，位置还跑到顶栏外
- 要求：做成**像「曲线」「插件」那样的工具栏按钮**（约 44×26，同字号同风格）
- 位置：**画布内部右上角**，偏移 8px（不是窗口右上角）
- 相关补丁：`330_layout_switcher.py`（`draw_layout_switcher`）

### 2.2 点开立刻被关掉
- 现状：点「布局」后同一帧又被遮罩判成"点空白"，面板闪一下就关
- 要求：入口在展开期间不绘制；遮罩在打开后 250ms 内不响应"点空白"
- 上一轮说已经修了，**877 上仍有问题，需复测确认**

### 2.3 布局切换后界面没变化（最严重）
- 现状：`set_workspace(Default/SmallScreen/Standard/Minimal)` 调了但界面不重排
- 要求：不依赖 dock 工作区，改成**直接控制面板显隐与比例**：
  - 经典：项目面板 + 时间线 + 属性面板 全显示
  - 简易：隐藏项目面板，时间线压到 35%
  - 专业：三个面板全显示，时间线 45%
  - 极简：只留预览 + 细时间线，其余隐藏
- 验证标准：切到「极简」时，项目面板和时间线必须消失

### 2.4 健壮性（HANDOFF 第 12 节，必须满足）
- 读不到设置 → 回落经典布局
- 切换失败 → 保持原布局，写 `DCIM/EffectCraft/layout-error.txt`
- 异常不冒泡到主循环

## 3. 已取消的需求
- ❌ PNG 拖动贴边：**取消，不要做**
- ❌ 「快捷」按钮挪到菜单栏：**已完成，不要再动**

## 4. 工作方式（用户强烈要求，必须遵守）
1. **push 完立刻结束本轮**，只回一行「已推 ours-XXX，我盯着」
2. **禁止在单轮里 sleep 超过 30 秒**；用 goal 自动续轮来等构建
3. 构建没好 → 结束本轮；好了 → 回「成功 + 链接」；失败 → 自己修自己重推
4. 一次改完 3~4 个相关问题再推，不要一轮一件
5. **先做编译提速**（见第 5 节），否则每轮都 20 分钟

## 5. 编译提速（第一件事就做这个）
- 给 `.github/workflows/build-ours.yml` 加 Rust 缓存：
  `artcraft/source/effectcraft/target` 和 `~/.cargo`，key 用 Cargo.lock 哈希
- 目标：改 UI 代码后 3~6 分钟出包
- 若 token 没有 Workflows 权限，把改动写成 `build-ours.debug.yml`，让用户手动合并

## 6. 铁律
- 不碰 `/storage/emulated/0/QQagent`
- 只改 `.github/workflows/build-ours.yml`（根目录那个不生效）
- push 前 `tools/preflight.py` + `tools/precheck.py` 都要过（只改 1~2 个文件时可只跑 precheck）
- 补丁只覆盖不删除；补丁名决定顺序
- 翻译行含英文双引号必须转义 `\"`

## 7. 验收清单（修完对着这几条自查）
- [ ] 画布内右上角有「布局」按钮，样式同「曲线」
- [ ] 点开不闪退、不秒关
- [ ] 切「极简」→ 项目面板和时间线消失
- [ ] 切回「经典」→ 全部恢复
- [ ] 写坏配置 → 下次启动仍是经典布局，不崩
- [ ] 出包后能覆盖安装（签名不变）

## 14. 当前状态（2026-11-18 06:50，交接给新会话）

### 最新可用包
**ours-888**（commit `fac2dc85`）：`https://github.com/15672633750y/effectcraft-ours/releases/download/ours-888/ShimoveAex-0.52.1.apk`

### 888 里有什么
- 布局切换器 v2（`330_layout_switcher.py`）
  - 入口：画布内右上角 8px，**工具栏风格按钮**（26px 高、4px 圆角、switch_well 底、12pt），展开时不画
  - 卡片缩略图 = **真实布局**：直接遍历 `crate::dock::ours_layout(id).root` 的 Node 树画（Split 按真实比例、Tabs 按面板类型画预览/时间轴/列表）
  - 点击后**整屏竖直光带**扫过（0.85s），布局名 46pt、主题色、10px 字距 + 三层辉光 + 下划线
  - 展开态 HUD 四角短线保留；旧的"沿边框跑的小点"已删
- 布局切换是真的（`337_layout_robust.py` + `dock::ours_layout`）
  - classic / simple / pro / minimal 四套布局树，切「极简」只剩合成预览（项目面板与时间线消失）
  - `catch_unwind` 包住切换；失败保持原布局并写 `DCIM/EffectCraft/layout-error.txt`
  - 第一帧归一化：布局 id 缺失/未知/损坏 → 回落 classic
- 工具栏 v1（`336_quick_menu_button.py`）：菜单栏「… 窗口 帮助 快捷」，和菜单标题同一套按钮；`204` 已改空操作（工具栏最左边不再画 PNG）
- **PNG 拖动贴边已取消**（用户要求）：`332` 改空操作，`335` 里去掉触屏兜底与 `ours_edge_snap`

### 已知没做
- 布局切换器的**真高斯模糊**（现在用暗遮罩近似）；卡片里是真结构但**不是实时渲染缩略图**
- 工具栏第二版（账号入口）→ 交给接账号的会话（见第 13 节）
- 上架项：R8、签名校验强化
- RSMB / MB Looks（用户说先放）、快影导入（不做）
- 文档欠账：`builds/FEATURES.md` 的 ❌ 清单过期（22、24–27、30 实际已实现）

### 这一轮定下的干活方式（重要）
1. 改完**只跑 `precheck`**（`python3 tools/precheck.py`，秒级），不再跑全量 preflight
2. **push 完立刻结束本轮**，只回「已推 ours-XXX，我盯着」
3. 下一轮**只查一次**构建状态（一次 curl，不许 sleep 循环）；没好就结束本轮
4. 好了 → 回「ours-XXX 成功 + 链接」；失败 → 自己看日志、修、重推，回「已修已推 ours-XXX」
5. 单轮 sleep 不超过 30 秒，靠 goal 自动续轮等构建
6. 连续失败 3 次以上才把原因和修法一起告诉用户

---

## APP 会话 2 进度（2026-11-18 07:25）

### 已出包，可以直接测（布局四项）
**ours-890 构建成功**（耗时 17.5 分钟）
https://github.com/15672633750y/effectcraft-ours/releases/tag/ours-890

- 「布局」是画布内右上角的 44×26 按钮，与「曲线 / 插件」同款（`330_layout_switcher.py::ours_layout_entry`）
- 点开不秒关：入口那一帧只画发光就返回，遮罩下一帧才出现；另有「250ms 不认点空白」+
  「这次按下必须晚于打开时刻」双保险
- 真重排：`dock::ours_layout()` 四套真布局树（经典=Default、简易=时间线 35%、专业=项目|预览|属性+时间线 45%、极简=只有预览）
- 健壮性：空树算失败、切换 catch_unwind、面板 catch_unwind 一次即永久禁用、失败写
  `DCIM/EffectCraft/layout-error.txt`、切极简后 focused 自动回到合成面板

### 已推、等验证（云账号）
- `340_cloud_http.py`：HTTP 客户端，**ureq 3.5.0**（本来就在 Cargo.lock，rustls+ring，无 C 构建），
  共享 Agent + 10 秒超时，token 存 `XDG_CONFIG_HOME/account.json`
- `342_cloud_health_probe.py`：**隐藏调试入口** —— 打开「帮助 ▸ 关于」，**长按版本号 0.8 秒**，
  底部出现一行 `云服务连接成功（存储 ok，后端 v2.2.0）` 或 `云服务连接失败: <错误>`

### 后端契约（2026-11-18 手机实测，不是猜的）
- `GET /health` → 200，`version 2.2.0`，`storage ok`
- `POST /auth/register` → **201**（不是 200）→ 客户端必须接受任意 2xx，否则注册永远报失败
- `PUT /me {display_name, prefs_json:{profile:{...}}}` → 200，回读一致
- `prefs_json` 上限 **8 KB** → 头像不能塞进 prefs，只能存本地
- 用户名 3~20 位字母数字下划线；密码 ≥8 位且不能是常见密码

### 已写好、未推（等网络层确认）
- `341_account_ui.py`：工具栏最左槽位（未登录「登录」44×26 / 已登录 26px 圆形昵称首字）+
  登录注册面板（用户名、密码、眼睛切换、稍后再说）+ 资料卡（昵称/性别/生日/签名，保存/退出登录）。
  已带 panic 边界：槽位/面板出错只降级，不连累主循环。
  **头像选图与上传还没做**（现在是首字占位）。

### 仍然阻塞：编译缓存
令牌缺 `Workflows: Read and write`，`.github/workflows/build-ours.yml` 推不上去（403）。
缓存改动已写成仓库根 **`build-ours.debug.yml`**，文件头写清了三个真实 bug：
1. 缓存路径写成了 `artcraft/source/effectcraft/target`，真实目录是 `artcraft/build/effectcraft/target`
2. 新 clone 的源码 mtime 全是新的，cargo 判 fresh 失败 → 必须在打补丁前把 mtime 归一
3. concurrency 同组排队 → 新推送要等前一个编完

### 构建耗时实测
888=10 分钟、890=17.5 分钟（同一量级改动）→ 免费 runner 波动很大，**缓存是唯一稳定手段**。
