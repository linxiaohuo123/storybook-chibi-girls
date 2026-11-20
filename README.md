# 童话 Q 版少女（storybook-chibi-girls）

用于生成与修改 1:1 白底、2D 童话风格 Q 版少女角色图的 ChatGPT Skill。

## 默认规范

- 单名女性角色、完整全身、纯白不透明背景、约 2～2.5 头身。
- 头发纯色平涂，禁止高光、渐变和立体塑形。
- 发型、服装、道具和动作体现独立主题，表情保持积极并避免雷同。
- 配色协调有层次；线条干净，不要杂线、白色贴纸描边或脚下阴影。

## 文件

- `SKILL.md` — 工作流入口。
- `references/` — 主题、配色、提示词、质量检查与后端说明。
- `agents/` — Skill 元信息。
- `scripts/` — 格式、白底与角色差异检查工具。
- `tests/` — 回归测试。
- `assets/references/` — 用户提供的风格参考素材（如已上传）。

## 验证

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_image.py /path/to/output.png
python3 scripts/check_diversity.py --plan /path/to/plan.json
```

图片脚本检查格式和有限的颜色统计，不替代实际视觉审查。使用 Python 3；图片处理脚本依赖 Pillow。

## 使用方式

在支持 Skills 的客户端加载包含 `SKILL.md` 的目录，使用当前环境可用的图像生成能力。Skill 不包含独立生图模型。私有 New API / ima 2.6 接口未完成联调。

## 公共仓库与素材

本仓库是公开的。任何用户提供的参考图片，仅用作风格研究；文件公开可见不代表已获得第三方版权、再分发或商业使用许可。未附加统一开源许可证。
