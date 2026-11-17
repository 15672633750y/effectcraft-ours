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
