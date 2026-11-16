# xiaohongshu-ip-skill · 个人 IP 小红书/抖音图文全链路 Skill

> **给一张真人照或一个选题，完成「个人 IP 定型 → 14 张品牌视觉全案 → GIF 动效 → 爆款暖米彩铅知识图文轮播」整套工程化交付。**

本 Skill 融合了两部分能力：
1. **工程纪律与爆款钩子骨架**（承袭并致谢 [cy-carousel](https://github.com/chengyi-ai/cy-carousel) MIT 开源规范）：PyMuPDF 一手原文定位、事实核查边界、高转化反差钩子结构、独立文稿契约、自动化交付检查、绝不自动发布；
2. **AI 个人 IP 孵化 + 暖米彩铅视觉生产流**：三段式 IP 角色设计与全案规范 + 暖米白彩铅手绘视觉系统（`#F5F1E8` + `#253B38` + `#27877B` + `#E5A45B` + `#D96B5B`）+ IP 主角陪读融入 + `1440×1920` 统一后处理 + Windows UTF-8 BOM 零乱码导出。

---

## 成品样张一览

### 样板 01 · 无 IP 基础科普风（《高性价比人生指南》第 1 章 1–2 节）
![01-安全带与戴头盔全套预览](examples/01-安全带与戴头盔/全套预览.jpg)

### 样板 02 · 「阿乐」个人 IP 陪读风（《高性价比人生指南》第 1 章 3–4 节）
![02-报警器与燃气安全全套预览](examples/02-报警器与燃气安全/全套预览.jpg)

---

## 四阶段工作流总览

```text
[前置分流]
  ├── 有照片无 IP ──▶ 阶段一：分析照片结构特征 → 6 款 IP 候选方案
  ├── 已有定稿 IP ──▶ 阶段二：14 张 IP 品牌视觉全案（三视图 / 9表情 / 透明LOGO / 6封面）
  ├── 需动图表情  ──▶ 阶段三：透明 / 纯白背景可播放 GIF 制作
  └── 已有 IP/直出图文 ──▶ 阶段四：PDF 查证 → 钩子分镜 → AI 生图 → 自检修错 → 后处理打包
```

---

## 目录结构

```text
xiaohongshu-ip-skill/
├── SKILL.md                       # Skill 主控说明（触发词、路由、四阶段主流程与红线）
├── CLAUDE.md                      # 仓库维护与开发规范
├── LICENSE                        # MIT + SIL OFL 1.1 声明
├── requirements.txt               # pillow, pymupdf, numpy
├── references/                    # 四阶段详细 Prompt 与美学/查证规则
│   ├── 01_ip_design_candidates.md
│   ├── 02_ip_brand_case.md
│   ├── 03_ip_animated_gif.md
│   ├── 04_carousel_visual_spec.md
│   └── 05_hooks_and_factcheck.md
├── assets/
│   ├── fonts/                     # 内置 SIL OFL 1.1 思源黑体 CN（本地自装 MiSans 时自动优先启用）
│   └── ip_examples/ale/           # 示例 IP「阿乐」特征图、三视图、表情表、透明LOGO与角色规范
├── scripts/
│   ├── extract_pdf.py             # PyMuPDF 一手书籍/论文查证定位
│   ├── postprocess.py             # 1440×1920 统一缩放、双角标叠加、全套预览.jpg、UTF-8 BOM 导出
│   ├── gif_compose.py             # 逐帧 PNG 转透明/纯白 GIF 合成工具
│   └── check_delivery.py          # 交付质检（尺寸、SHA256清单、BOM编码、禁用草稿/TODO词拦截）
├── examples/                      # 两套真实跑通的成片预览、标题、正文、置顶评论与来源清单
├── tools/validate_repo.py         # 上架/提交前仓库自检（隐私词与绝对路径防泄露检查）
└── tests/test_skill.py            # unittest 自动化测试
```

---

## 安装与使用

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 安装到 Antigravity / Codex / Claude Code
将本目录直接复制到你的全局或项目 Skills 目录：
- **Antigravity 全局**：`~/.gemini/config/skills/xiaohongshu-ip-skill/`
- **Codex 全局**：`~/.codex/skills/xiaohongshu-ip-skill/`
- **Claude Code**：`~/.claude/skills/xiaohongshu-ip-skill/`
- **项目级工作区**：`<项目根目录>/.agents/skills/xiaohongshu-ip-skill/`

### 3. 字体说明（优先 MiSans，兜底思源黑体 CN）
仓库已随附开源字体 **思源黑体 CN（SIL OFL 1.1）** 保证零依赖可用。若需获得最佳现代苹果简体视觉效果，请自行前往 [小米字体官网](https://hyperos.mi.com/font/download) 下载 **MiSans Global** 放入 `assets/fonts/MiSans_Global/` 或安装到系统字体，`scripts/postprocess.py` 会自动优先识别。

### 4. 脚本常用命令
```bash
# 1) 提取 PDF 原文与页码核对
python scripts/extract_pdf.py "书稿.pdf" --pages 13-16 --query "安全带"

# 2) 后处理生图目录：统一 1440×1920、加统一脚标、生成预览图与 BOM 文案校验
python scripts/postprocess.py --raw-dir ./raw --out-dir ./output --book "《高性价比人生指南》" --section "第1章第3-4节读书笔记"

# 3) 交付红线检查
python scripts/check_delivery.py --out-dir ./output

# 4) 仓库开发自检与单元测试
python tools/validate_repo.py
python -m unittest discover -s tests
```

---

## 致谢与许可

- 本项目在事实可回溯、勾子分镜节奏、独立文稿契约与自动化交付门禁理念上参考并衍生自 [chengyi-ai/cy-carousel](https://github.com/chengyi-ai/cy-carousel)（MIT License）。
- 代码与文档采用 **MIT License**；内置字体采用 **SIL Open Font License 1.1**。
