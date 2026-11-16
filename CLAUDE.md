# CLAUDE.md

本仓库是 Agent Skill `xiaohongshu-ip-skill`：将 **个人 IP 孵化与视觉全案生成（三段式角色工作流）** 与 **严谨的知识核查、爆款钩子分镜及工程化图文后处理（承袭 `cy-carousel` 工程纪律 + 暖米彩铅视觉体系）** 融合为一体的全流程图文生产力工具。

## 目录分工

- `SKILL.md`：Skill 主入口，定义触发条件、前置路由、4 阶段主流程与红线。
- `references/`：各阶段详细提示词与方法论规范：
  - `01_ip_design_candidates.md`：照片分析与 6 款 IP 方案生成规范。
  - `02_ip_brand_case.md`：14 张 IP 品牌视觉全案生成规范。
  - `03_ip_animated_gif.md`：IP 角色透明/纯白可播放 GIF 生成规范。
  - `04_carousel_visual_spec.md`：暖米彩铅小红书/抖音视觉系统、MiSans/思源黑体规范与 IP 融入规范。
  - `05_hooks_and_factcheck.md`：承自 `cy-carousel` 的事实查证表、钩子文案节奏与禁止事项红线。
- `scripts/`：可复用本地 Python 工程脚本：
  - `extract_pdf.py`：PyMuPDF 原书/PDF 查证定位脚本。
  - `postprocess.py`：1440×1920 规格统一、双角标叠加、`全套预览.jpg` 生成、Windows UTF-8 BOM + CRLF 文稿导出。
  - `gif_compose.py`：在无直接图转 GIF 工具的环境下将多帧 PNG 合成为透明或纯白 GIF。
  - `check_delivery.py`：工程化红线与技术质检脚本（尺寸、清单 SHA256、BOM 编码、禁用草稿/TODO 词检查）。
- `tools/validate_repo.py`：开源仓上架/提交自检（敏感词与绝对路径防泄露检查、相对链接与字体许可检查）。
- `tests/test_skill.py`：`unittest` 自动化测试。

## 不可妥协的红线

1. **事实可回溯**：重要数据与法条必须核对原书/PDF/论文（写入 `research/事实表.md`），标明边界与统计口径，禁止将「TODO / 待核实」等草稿提示印上正式图片或正文中。
2. **工具与模型诚实**：严禁虚构生图模型、动画工具或核查结果；规定模型不可用时必须向用户如实说明。
3. **自检后再交付**：每生成一张图必须目检汉字、数字、人物特征（尤其是固定服装与非对称腕表左右位置）；发现瑕疵当场重修再交，禁止把错字带入成品。
4. **字体与隐私合规**：仓库内仅打包开放许可字体（思源黑体 CN / SIL OFL 1.1），严禁在公开仓库随附专有字体或私人真名/本机绝对路径。
5. **只出文件不发布**：所有脚本只生成本地成品包，不执行自动发布。

## 开发与提交前验证

```bash
python tools/validate_repo.py
python -m unittest discover -s tests
```
