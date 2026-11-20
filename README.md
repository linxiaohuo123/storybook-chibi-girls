# 童话 Q 版少女（storybook-chibi-girls）

用于设计、生成和修改白底 2D 童话幻想少女的 Skill，支持多组接单规划、穿搭与配色设计、独立图片生成、局部返工和系列续做。

## 默认成图规范

- 单一女性角色、完整全身、1:1 纯白不透明背景、约 2～2.5 头身。
- 头发均匀平涂，无高光、渐变、塑形暗面；无贴纸白边、投影、接地阴影。
- 梦幻设定通过角色、服装、主道具和动作表现，不依赖背景或光效。
- 配色有主辅层级，服装能解释层次、固定点和持物关系；细节丰富但有主次。
- 每张独立生成，系列变化身份、发型、衣服轮廓、动作与正向表情。

## 工作方式

1. 提炼本单要求，区分已确认条件、参考建议与未知项。
2. 先规划所有组的主题世界、服装语言和配色关系，再展开角色卡。
3. 为角色写出幻想规则、可见证据、穿搭逻辑、细节层级和部位配色。
4. 按组选择代表样张，实际看图检查后逐批扩展；按用户要求决定是否等待确认。
5. 定向修改，分别记录生成状态、自检状态、客户状态和修订版本。

可选服装方向包括精细童话礼装、折页礼装、梦绒奇装、潮汐珍藏、游艺机关、云纹奇谭。它们是创作起点，不是已获客户认可的成品或固定套路。

## 使用示例

**先规划：**

> 使用 $storybook-chibi-girls 规划 18 个梦幻少女，分 3 组，每组 6 个，样式不同，避免日常职业装。先给角色方案和每组一个提示词，不出图。

**独立出图：**

> 按已确认的折页礼装方向生成 6 张独立白底少女图。统一比例、线条和平涂，各自改变发型、服装结构、主道具、动作和表情。先检查代表样张，再继续完成本组。

**定向返工：**

> 只修改这张图的披风和裙身配色，保留人物、服装剪裁、道具、动作及画幅。其他部位不变。

## 文件

- [SKILL.md](SKILL.md)：工作流入口与默认硬约束。
- [多组生产](references/production-workflow.md)：简报、分组、版本、反馈与续做。
- [幻想设计](references/fantasy-design.md)、[服装方向](references/style-profiles.md)、[穿搭结构](references/wardrobe-design.md)：创意与服装设计。
- [角色卡](references/character-design.md)、[配色](references/palette-design.md)、[提示词](references/prompt-templates.md)：可直接使用的设计结构。
- [质量检查](references/quality-control.md)、[工具适配](references/backends.md)：检查范围和执行边界。
- `scripts/`：只读的图片文件检查与角色字段差异检查。
- `tests/`：脚本回归测试。
- `assets/references/`：四张原始分辨率参考文件，以及保留用于兼容旧链接的 WebP 缩略图。

## 验证

使用 Python 3；图片检查依赖 Pillow。

```bash
python3 -B -m unittest discover -s tests -v
python3 scripts/check_image.py /path/to/output.png --require-exact-white-border
python3 scripts/check_diversity.py --plan /path/to/plan.json
python3 scripts/check_diversity.py --plan /path/to/plan.json --history /path/to/history.jsonl
```

严格白边带检查只确认采样边带的 RGB 值，不证明整片背景、头发、手部或服饰合格。角色检查比较规范化字符串，不能证明真实图片互不相似。零次比较不算已证明去重；客户接受只能来自真实反馈。

图像修改遵守当前环境的图像工具规则；不再提供自动抹白背景脚本，避免误改浅色服装。Skill 本身不含图像模型。根据当前工具 schema 调用，不固定某个函数名或弃用参数。私有 New API / ima 2.6 接口未完成联调。

## 参考素材

- [系列变化参考](assets/references/series-variety.png)
- [主题变化参考](assets/references/theme-variety.png)
- [苹果主题服装参考](assets/references/apple-detail-reference.jpeg)
- [深色配色反例](assets/references/dark-palette-counterexample.png)

参考图的使用范围见 [style-and-references.md](references/style-and-references.md)。不要把配色反例当作默认正向参考。原图存在的光影、边框、文字或杂线不代表本技能允许继承。

本仓库公开；参考素材公开可见不代表取得第三方再授权，未附加统一开源许可证。客户原始聊天、订单附件、生产历史和未公开项目图片不放入此公共仓库。
