# 字体说明与开源许可

本仓库默认内置开源字体 **思源黑体 CN（Source Han Sans CN VF）**（见 `SourceHanSansCN/SourceHanSansCN-VF.otf` 与 [LICENSE.txt](SourceHanSansCN/LICENSE.txt)），遵循 **SIL Open Font License 1.1**，可随仓库免费克隆使用，确保在 Windows / macOS / Linux 下开箱即用。

## 优先启用 MiSans Global（本地自装，不随仓再分发）

为遵守小米 MiSans 字体许可协议（不得擅自修改或单独随第三方仓库再分发字体文件），本仓库 **不打包 MiSans 字体文件**。

如果你希望渲染统一脚标、预览图及文字修复贴片时优先使用 **MiSans Global**：
1. 请自行前往小米官方字体页下载正版 MiSans Global：<https://hyperos.mi.com/font/download>
2. 将官方包中的 `MiSans-Medium.ttf`、`MiSans-Bold.ttf` 或 `MiSans VF.ttf` 放入本机以下任意位置之一（或直接安装到系统字体）：
   - `assets/fonts/MiSans_Global/`（已在 `.gitignore` 中忽略，不会被意外提交到 GitHub）
   - 本机系统字体目录，或通过环境变量 `XHS_FONT_DIR` 指定自定义字体目录。

`scripts/postprocess.py` 会按 **MiSans（本地自装） → 思源黑体 CN（随仓开源）** 的顺序自动检测；**绝不静默回退到未授权或风格不匹配的系统默认字体**，并在输出报告中如实打印实际使用的字体路径。
