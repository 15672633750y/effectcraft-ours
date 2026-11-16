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
- 汉化 5 批 + 混合模式/纯色设置（约 465 行已进翻译表）

## 未完成
1. **汉化**：界面文字已收口，剩效果参数名长尾
   - 进度（2026-11-17 07:00，已推 1–11 批）：`ui.rs` 表 1074 → 2310 行；`prop.rs` 196 → 672 臂；
     `tr()` 字面量 606/606；tooltip 100%；裸画英文 0；**参数名还剩 ~321 条**
   - 做法：中文行加到 `crates/ui-egui/src/i18n/ui.rs` 的 `SIMPLIFIED_CHINESE` 表
   - 插入锚点：`];\n/// EFFECTCRAFT_OURS_ZH_BLEND_SOLID_V1`（把新行插在 `];` 之前）
   - **参数名也走这张表**：`zzzzzzzzzzzzzzzzz_zh_prop_fallback.py` 把 `i18n/prop.rs` 的兜底改成查表
   - 裸画文字的坑：控件若直接 `painter.text(...)`，表里有中文也不显示 → 见 `zzzzzzzzzzzzzzzz_zh_draw_routes.py`
   - 文件名就是执行顺序（`3xx` < `70_` < `9x` < `1xx` < `zz_`）；改 `prop.rs` 的补丁必须排在 `70_property_names_zh.py` 之后
2. 文字动画器导入（inbox/奇峰自由文字出场.ffx 的“蒸发”）
3. S_射线 / S_辉光 / S_阴影 / S_TextureFlux 真实实现（现在是空壳）
4. RSMB 运动模糊、MB Looks（用户说先放着）
5. 字体缺失提示

## 环境坑
- 本机**没有 Rust 工具链**，编译错误只能等 CI；所以 precheck 是唯一防线
- 补丁编号字典序：`2xx` < `5xx`，要晚于某补丁生效就起名 `zz_`/`99_`
- 构建并发组已改成 per-run，不会互相取消
