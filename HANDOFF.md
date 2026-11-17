# 交接文档（新会话先读这个）

## 一句话
EffectCraft Sx = `storytold/effectcraft` 的补丁版，在 GitHub Actions 构建：
仓库 `15672633750y/effectcraft-ours`，工作流 `build-ours.yml`。
**最新可用包看 Releases 最新 tag**：https://github.com/15672633750y/effectcraft-ours/releases

## 铁律（必须遵守）
1. **绝对不要碰 `/storage/emulated/0/QQagent`**（用户明确禁止）。
2. 推送前必须依次跑：
   ```
   python3 tools/preflight.py    # 全部补丁能否打上
   python3 tools/precheck.py     # 静态检查（重复定义 / 已删变量 / 借用冲突）
   ```
   两个都 OK 才 `python3 tools/push.py "<说明>" '{"<远端路径>":"<本地文件>"}'`。
3. **只覆盖补丁文件，不删除**：远端残留的补丁照样会被应用，删本地会导致构建失败（踩过坑）。
4. 定时查构建：`gh` API 用 token `cat /data/user/0/com.deepseek.harness/files/.ec_token`。
   失败要自己查日志、自己修、自己重推，不要让用户催。
5. 不要承诺"一模一样"：Sapphire/Looks/RSMB 闭源，只能近似，用像素误差说话。

## 目录
- `ours-patches/` 160+ 个补丁，按文件名字典序应用；每个必须有 `if __name__ == "__main__": main()`
- `tools/preflight.py` / `tools/precheck.py` / `tools/push.py`
- `inbox/` 用户放进来的素材、截图、预设
- `builds/FEATURES.md` 全部需求与状态；`builds/NIGHT_LOG.md` 逐轮记录；`TODO.md`

## 已完成（要点）
- 三条彩调色拟合 AE（参考帧 RGB 77.7/77.7/73.4 vs AE 77.8/77.7/73.3；MAE≈3）
- 预设导入（.ffx/.gp/JSON）+ 预设库面板 + 保存为 .ffx
- 快捷键面板（P/S/R/T/A、裁剪、裁剪前后、U、预合成 Ctrl+Shift+C、音频频谱 L、多选 M）
- 长按/多选开关、预合成多图层、面板折叠/拖动/穿透、输入框每次点击弹键盘
- CapCut 导出、系统分享、NV 导入、崩溃取证
- 汉化 19 批（`ui.rs` 表 3302 行）、开屏自绘 View、签名指纹校验、文字动画器「蒸发」

## 未完成
1. **汉化**：已收口到 0 英文（2026-11-17 12:00，ours-808）
   - `ui.rs` 表 3302 行；`tr()` 覆盖 610/610；直接画的英文 0（只剩两行 Download 路径提示不翻）
   - 效果参数名 1071 条全部有中文（`prop::name` 兜底查表，见 `zzzzzzzzzzzzzzzzz_zh_prop_fallback.py`）
   - 新加字符串请按「第十八/十九批」的做法：普通文案进 `ui.rs` 表；`format!` 拼出来的改成 `tr_args`
2. 文字动画器导入：已支持 `.ffx` 的 `Evaporate Animator` → 内置「蒸发」预设（`314_ffx_text_animator.py`）
   - 其它 AE 文字动画器还没做；要加就往 `presets/text_animators.json` 加条目 + 在 `ffx_text_presets` 认名字
3. S_射线 / S_辉光 / S_阴影 / S_TextureFlux：**不是空壳**（`131_sapphire_fx.py` 有真实实现）
   - 2026-11-17 已把四个效果的 Sapphire 参数集补齐并接进渲染（ours-812/814/815）：
     射线（Reverse/Rays Color/Source Opacity/Bg Brightness/From Alpha/Under Source/Affect Alpha）、
     辉光（Width X、Y/Light Background/Show▸Threshold）、
     阴影（Shift X、Y 优先于 Distance+Direction/Fg Opacity）、
     流光（Shift X、Y/Color 0、1/Brightness/Bg/Bubble/Input、Output Opacity）
   - `ffx_values.rs` 的名字映射同步补齐，导入 `.ffx` 时这些值能真正写进效果
4. RSMB 运动模糊、MB Looks（用户说先放着）
5. 字体缺失提示（缺字体时提示放 /sdcard/Fonts/）

## 环境坑
- 本机**没有 Rust 工具链**，编译错误只能等 CI；所以 precheck 是唯一防线
- 补丁编号字典序：`2xx` < `5xx`，要晚于某补丁生效就起名 `zz_`/`99_`
- 构建并发组已改成 per-run，不会互相取消
# trigger 1794872140

<!-- token 验证 09:32 -->

## 2026-11-17 交接补充（应用户要求，交给新会话）
### 已定稿、不要改
- 应用名 `ShimoveAex`，包名 `com.shimoveaex.effects`
- 图标：`tools/app-icon.png`（1024，用户新画的 SA 图，白底干净版）
- 签名：用户的 keystore，别名 `shimove`，密钥在 `DCIM/EffectCraft/keys/`，
  GitHub Secrets `KEYSTORE_BASE64` / `KEYSTORE_PASSWORD` 已配好
- 官方签名指纹（SHA-256）：
  `6461ee2dbcdb7882575242218895f6ac4cab24abdfa97353bbe0d702bb4a75a3`
- 工作流真身是 `.github/workflows/build-ours.yml`（根目录 build-ours.yml 不生效，别再改错）
- `310_signing_alias.py` 把 builder 的别名改成 `${ARTCRAFT_KEY_ALIAS:-shimove}`
- **绝不碰 `/storage/emulated/0/QQagent`**

### 待做（按优先级）
1. **开屏界面**：黑底 + 圆角图标（512 drawable，不要拉伸 mipmap）+ 主标题 `Shimove Aex`
   + 副标题 `本软件由施信开发 · 基于开源项目`；图标淡入 350ms、文字延迟 120ms 跟上；
   **总时长不得超过当前默认开屏时间**（约 1~2 秒，1 秒到点必须进主界面，另加 1.5 秒兜底）
2. **签名指纹写死**：把上面的 SHA-256 写进校验；签名不符只提示「非官方版本」不阻止启动；
   支持 `DCIM/EffectCraft/devmode.txt` 跳过 + `allowed-signatures.txt` 允许清单
3. **汉化收尾**：剩约 200 条真该翻的（命令长句/效果控件零散/面板提示），
   注意：含英文引号的翻译行必须转义成 \" ，否则 Rust 字符串断裂（踩过两次）
4. 文字动画器导入（inbox/奇峰自由文字出场.ffx 的「蒸发」）
5. S_射线/S_辉光/S_阴影/S_TextureFlux 真实实现（现在空壳）
6. RSMB、MB Looks（用户说先放着）；字体缺失提示

### 推送纪律
`python3 tools/preflight.py` + `python3 tools/precheck.py` 都 OK 才 push；
一次只推一批，推完等出包；失败自己查日志自己修，成功才通知用户。

### 开屏现状（重要，别走老路）
官方开屏用的是 windowBackground 贴图路径，会把图**裁切**（底部硬切边）并在边缘产生**黑斑**
（源图与打包内的图标文件都验证过是干净的：源图 0.02% 深色噪点、包内 0.00%）。
所以必须改成**自绘 View**：加载 512 drawable → 自己画圆角(22%) → 等比缩放不裁切 → 淡入淡出。

## 调色（ffx_vintage）交接说明 —— 任何会话接手前先读这段
### 文件与结构
- 实现：`crates/effects/src/ffx_vintage.rs`
- 处理链（顺序不能乱）：
  `fitted(base[0..2])` → 对比度 → 径向增益（1.10 − 0.16·r²）→ 饱和度/亮度/色调/暗部 (+chroma)
  → `shown` → 按 amount 混合
- 拟合表：`FIT: [[f32; 20]; 3]`，三次多项式，三通道各 20 个系数
- **参数必须在拟合之后应用**，否则 AE 的参数语义对不上

### 已知基准（2026-11-16 实测，别改坏）
- 用户 `原图.png` → AE `调色.png`，57 600 采样点
- 拟合误差 MAE ≈ 3.19 / 2.90 / 2.67（R/G/B）
- luma 77.2（AE 77.2）、对比度 38.4（AE 39.1）、饱和度 0.181（AE 0.183）
- 交叉验证用户自己导的 `Frame3.png`：MAE 3.01 / 2.88 / 2.60、luma 77.2 vs 77.2、
  对比度 39.3 vs 39.0、饱和度 0.177 vs 0.183

### 验证方法
1. 用同一张源图，App 里只套这个效果、默认参数，导出 PNG
2. 与 AE 导出对比：算三通道 MAE、平均亮度、对比度（std）、饱和度
3. **必须给数字**：只有"看着不对"无法定位；说"暗部偏红 3 点 / 高光 luma 82"才能改

### 受过的伤（不要重犯）
- `Frame2.png` 偏暗（luma 55.4）→ `shown` 提前计算 + `base_pass` 门控导致，已在 245/247 修
- 拟合值和参数混用顺序错 → 视觉完全跑偏
- 改曲线时若只改 FIT 不动径向增益/对比度，会和之前的校准结果打架

## 汉化交接说明
### 机制
- 界面文案表：`crates/ui-egui/src/i18n/ui.rs` 里的 `SIMPLIFIED_CHINESE`
  （新条目插在 `];\n/// EFFECTCRAFT_OURS_ZH_BLEND_SOLID_V1` 这个锚点之前）
- 菜单/参数/效果名：`i18n.rs` / `i18n/prop.rs` / `i18n/effects.rs`（按 id 映射）
- 弹窗走 `crate::i18n::tr(o)` 中心化翻译；带 `format!` 的句子要配合 `tr_args`
- 补丁文件名决定应用顺序（字典序），新批次用 `30x_zh_batchNN.py`

### 现状（2026-11-17 复核）
- 已完成到第 17 批；界面直接硬编码的英文基本清零
- 我复核后仍有约 236 条"候选英文"，其中真正该翻的约 120~150：
  面板小词（Type slot、SOURCE FOOTAGE）、GPU/渲染提示（Shared GPU preview disabled…）、命令反馈长句
- 不该翻的：字体名、快捷键名、测试数据/文件名、行业格式名（NTSC/PAL/HDV/UHD/Cineon…）、
  其他语种表项（Servicios/Visa alla/Ukryj EffectCraft）

### 踩过的坑（必读）
- **含英文双引号的翻译行必须转义成 `\"`**，否则 Rust 字符串断裂、整条构建失败（踩过两次，
  例子：`("leading: expected a number or \"auto\"", ...)`）
- 补丁锚点若依赖别的补丁插入的行，要确认**字典序在自己之前**（`293` 曾排到 `59` 前面而失败）
- 每个补丁都要有 MARKER 幂等检查，重复运行不能报错

## 剩余待办总览（按优先级）
1. 调色继续优化（见上面的交接说明，必须给数字）
2. 汉化收尾：约 120~150 条（界面小词 + GPU 提示 + 命令反馈）
3. 开屏细节微调：1 秒硬性时长不能变；圆角 22%；fit-center 不裁切
4. 文字动画器导入（`inbox/奇峰自由文字出场.ffx` 的「蒸发」，已有真实数值读取）
5. S_ 系列效果：131 已有实现，属"近似 Sapphire"，不要承诺"一模一样"
6. RSMB、MB Looks（用户说先放着）
7. 字体缺失提示（小项）

## 布局切换器（下一轮的主任务）
### 交互规格（用户定的）
- 入口：**画布右上角一个按钮**（就是当前"预览"标题栏那块），点击向下展开面板，面板尽量矮
- 面板内容：每个布局一行「**缩略示意图 + 名称**」（缩略图按布局画几个色块示意，不要用别人的 logo）
- 选中态：**沿用快捷键面板的"多选发光"做法**（见下）
- 切换时：播放过渡动画 + 屏幕中部短暂显示新布局名字（约 700ms 淡出）
- 布局命名用中性词：经典 / 简易 / 专业 / 极简（副标题可写风格描述，不写 CapCut/Blurrr/AE 等商标）

### 「多选发光」怎么做的（用户特别交代要写清楚）
在 `crates/ui-egui/src/app/frame.rs` 的快捷键面板里，「多选 M」那个磁贴选中时的画法：
1. **不填充背景**，只在磁贴矩形外画 **3 圈描边**，半径依次外扩 1.5 / 3 / 4.5 px
2. 三圈颜色都用主题强调色 `t.accent`，透明度递减：约 220 / 120 / 60（越外越淡）
3. 描边宽度都是 1.0~1.5 px，圆角 `CornerRadius` 与磁贴一致
4. 因此文字和图标**不会被白色蒙层压暗**，在发光背景上依然清晰
5. 动画：选中时最外圈 alpha 从 0 渐入（约 120ms），取消时直接消失

代码骨架（egui）：
```rust
let r = rect.expand(1.5);
ui.painter().rect_stroke(r, radius, Stroke::new(1.5, t.accent.gamma_multiply(0.86)));
ui.painter().rect_stroke(r.expand(1.5), radius, Stroke::new(1.2, t.accent.gamma_multiply(0.47)));
ui.painter().rect_stroke(r.expand(3.0), radius, Stroke::new(1.0, t.accent.gamma_multiply(0.24)));
```

### 额外可加（用户想要的"比它好看"）
- 扫描光线：沿选中卡片边框移动一段高光（t 0→1，循环 1.6s）
- HUD 角标：四角短线段
- 自定义主色：设置里取色 → 存 prefs，所有发光/描边跟随
- 赛博主题：背景 #0A0E14、主色 #00E5FF、次色 #FF2E88 + 扫描线纹理

### 布局切换按钮的最终形态（用户强调）
- **位置固定**：悬浮在画布（视频预览区）**右侧边缘垂直居中**，不随布局改变，不占布局空间
- **必须极小**：约 28×28 dp 的圆角方块（或 24×24 图标按钮），不能挡住预览内容
- **尽量透明**：默认 alpha ≈ 0.35，只在悬停/按下时升到 0.9；内容用单色图标（三个小方块叠层示意）
- 点击后面板**向下展开**，面板本身也尽量矮（一行一个布局，行高 44dp 左右）
- 面板出现时自动避让：如果右侧空间不够就往左展开
- 键盘/鼠标用户：可以再加一个快捷键（可选，不强制）

### 布局切换器的最终交互（替代上面的小按钮方案，以此为准）
- **入口不要按钮**：画布右上方就一行小字「**布局 ▾**」（12sp 左右、低对比灰），点击展开
- 展开时：**整个画面加一层高斯模糊**（从 0 渐到约 8~12px，250ms，缓出），同时压一层 30% 黑遮罩
- 面板内容：每个布局**一条**，从**左侧依次缓入**（stagger 约 60ms），每条同时渐显 + 轻微右移 8px→0
  - 每条：左侧缩略示意图（自己画的色块，不用别人 logo）+ 名称 + 一行小字说明
- 选中态：三圈发光描边（见上文"多选发光"），当前布局右侧显示一个勾
- 点击某条：立即切换布局 → 模糊层 200ms 淡出 → 画布中央浮出一行**布局名字（带赛博风格：细描边、扫描线、短暂故障抖动，约 900ms 后淡出）**
- 关闭：点遮罩空白处 / 再点「布局 ▾」/ 选完自动关
- 面板本身：宽度约 300dp，左对齐贴屏幕左边 16dp，条目高 52dp

#### 实现要点（egui）
- 高斯模糊：egui 没有内建，用「先抓一帧到纹理再模糊」成本高；**推荐做视觉近似**：
  全屏半透明黑遮罩 + 面板后面一层 1.5px 的柔光边框 + 内容轻微缩放(0.98→1.0)，观感接近"背景化"；
  若一定要真模糊，用 `egui::TextureHandle` + 多趟 box blur，注意移动端帧率
- stagger：用 `ctx.input(|i| i.time)` 与每条索引算延迟：`let t = ((now - open_at) - i*0.06).clamp(0,1);`
- 缓动：`t*t*(3.0-2.0*t)`（smoothstep）就够顺滑

### 布局切换 —— 最终时序（以此为准，覆盖前面的描述）
按钮形态：画布右上角固定「**布局 ▾**」两个字 + 下拉箭头（小、低对比，常驻）

**打开阶段**
1. `t=0`   点击 → 「布局 ▾」**渐隐消失**（150ms）
2. `t=0`   同时画面开始**逐渐模糊**（0 → 8~12px，280ms，缓出）
3. `t=180` 布局条目**依次插入**：每条 60ms 间隔，从左侧进入 + 渐显 + 轻微右移 8px→0（smoothstep，220ms）
4. 全部出现后静止，等待点击

**选择阶段**
5. 点击任意一条 → **立即切换布局**（不做任何确认、不弹二次框）
6. 同时触发切换动画：**扫光 + 赛博元素**在画布中央浮出**该布局的名字**（约 900ms）
7. 切换完成的同时：模糊**淡出变清晰**（200ms）
8. 布局名字淡出消失
9. 「布局 ▾」**渐显回来**（150ms），回到常态

**取消阶段**（点空白处）
- 面板淡出 → 模糊淡出 → 按钮渐显（同样的反向过程，总时长不超过 250ms）

**手感要求**
- 所有过渡用 smoothstep（`t*t*(3-2t)`），禁止线性
- 任何时刻不允许卡住：模糊层 800ms 内必须消失在极端情况下

### 布局按钮 最终定稿（覆盖上一条里的箭头描述）
- 按钮就是**「布局」两个字**，**没有下拉箭头**
- 点击瞬间：「布局」先**微微发光**（描边/文字亮度升到 1.2 倍，约 120ms），然后**淡出消失**（180ms）
- 之后按上一条时序：模糊渐入 → 布局条依次插入 → 点击切换 → 扫光/赛博字 → 模糊淡出 → 「布局」渐显回来

## 图标规范（任何会话接手做图标都照这个来）
### 源图要求
- 格式：**PNG**，1024×1024，白底（#FFFFFF），不要 JPG
- 人物宽度：约占画布 **56%**（想小一点 51%，别超过 60%）
- 人物下沿：落在画布 **83.3%** 的高度处（即下方留 16.7%）
  原因：启动器会裁掉四边各 16.7%，83.3% 正好是"可见区底边"，裁完人物贴底不切
- 左右居中
- 来源：用户会直接发 PNG；若只发截图是不行的（截图有压缩和界面）

### 落盘与构建
1. 把源图存成 `tools/app-icon.png`（1024 PNG，原样保存，不要自己缩放）
2. 推送仓库 → `build-ours.yml` 里那步 `cp ours/tools/app-icon.png $GITHUB_WORKSPACE/app-icon.png`
3. 构建脚本 `artcraft/lib/app_icons.py` 生成：
   - `mipmap-*/ic_launcher.png`（legacy，各密度）
   - `drawable-xxxhdpi/ic_launcher_foreground.png`（自适应前景）
   - `drawable/ic_launcher_background.xml`（背景色，从图里取）
   - `drawable-nodpi/splash_icon.png`（开屏用，512，不裁切）
   - `mipmap-anydpi-v26/ic_launcher.xml`（自适应声明）

### 关键坑（2026-11-17 踩过，必须记住）
- `app_icons.py` 原本 `_foreground()` 会 **`split()[3].getbbox()` 裁到人物边界再缩到 62% 居中**，
  所以**无论怎么调源图的白边和位置，桌面图标都不会变**。
- 已由补丁 `315_icon_no_trim.py` 修成"整张画布等比铺满"，构图才真正生效。
- 排查顺序：**先确认改动有没有进包 / 有没有被脚本改掉，再怀疑启动器裁切**。

### 验证方法
1. 本地模拟裁切：对 `tools/app-icon.png` 裁掉四边各 16.7%（取中间 66.7%）→ 套 22% 圆角 → 就是桌面效果
2. 真机：装包后看桌面/应用详情里的图标，**注意系统图标缓存**（重启或清缓存才刷新）

### 历史沿革（别再绕回头路）
- 曾误判为"启动器裁切导致"，反复调留白/下移十几次都无变化
- 真正原因是最上面的 `getbbox()`，与启动器无关
