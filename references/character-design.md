# 角色卡与跨组差异

## 保持画风，改变设计

新角色固定项目级比例、五官语言、线条、2D 平涂、背景与构图。变化身份和子主题、发型、服装结构、道具功能、动作与正向表情。

七个基础比较字段：`theme`、`hair_style`、`hair_color`、`outfit_silhouette`、`signature_prop`、`pose`、`expression`。默认每两名至少四项不同，且发型轮廓、服装轮廓或姿态至少一项有实质区别。这是设计提醒，不是图像质量定律。

先统一术语：例如“齐颈波波头”和“短波波头”若实际同形，视为相同；“微笑捧盒”和“含笑托匣”若手臂与物件轮廓相同，也视为相近。不能故意写不同词让脚本通过。

- 单组：共享幻想规则，使用不同子功能、衣服组合与动作。
- 多组：先区别世界规则和服装语言，再安排组内角色；不能每组都套同款披肩蓬裙。
- 跨组复核幻想机制，不让纸、贝壳、云朵三个组最终都只做同一种台阶装置。复核“主道具功能＋手臂动作＋表情”的组合；同样举扇并眨眼不能仅因衣服换色就忽略相似性。
- 同一个角色换装：保留用户指定身份特征，按 `edit` 的身份保持要求规划，不强制四轴全变。
- 仅改色／清线：不执行新角色多样性；新版本不计入新增角色数量。

## 结构化计划

完整角色卡用于批量、提示词和续做；简单单张可在上下文内部保留，无需为形式创建文件。生成前状态仍是未检查。

```json
{
  "mode": "new_character",
  "delivery": "plan_only",
  "project_id": "fantasy-collection",
  "characters": [
    {
      "id": "g01-c01",
      "series_id": "g01",
      "style_profile": "paper_court",
      "theme": "折门钥匙少女",
      "fantasy_rule": "厚纸钥匙可以沿折页展开成掌心大小的拱门",
      "visual_evidence": "一手托住展开的纸门底，一手扶折叠侧边；拱门与折叠连接清楚",
      "story": "展示刚打开的折页门",
      "hair_style": "齐刘海内扣短波波头",
      "hair_color": "暖栗棕",
      "outfit_silhouette": "角形短披肩搭双层前片A字裙",
      "signature_prop": "展开为拱门的折页钥匙",
      "pose": "侧身一手托底另一手扶侧边，肘部离开腰线",
      "expression": "睁眼抬眉、闭嘴自信浅笑",
      "palette_id": "terracotta-jade",
      "palette_roles": {
        "hair": "#94634F 均匀平涂",
        "main_outfit": "#BD6C60 陶红裙身",
        "secondary": "#78A59C 青绿短披肩",
        "buffer": "#F5E6CF 浅象牙内搭",
        "prop": "浅象牙纸门配陶红拱边",
        "accent": "#C9A15E 小面积金赭扣件",
        "line": "#765348 暖棕细线"
      },
      "wardrobe_logic": {
        "inner": "圆领收口袖内搭",
        "main": "收腰A字裙，折页前片连接裙腰",
        "outer": "短披肩以领前扣固定",
        "attachments": "拱形腰扣固定于腰带，头饰固定在发夹底座",
        "footwear": "浅袜配陶红圆头系带鞋",
        "hand_prop_contact": "左手托底，右手扶侧边；收口袖不遮手"
      },
      "detail_hierarchy": {
        "primary": "纸门道具与折页前裙片",
        "echoes": ["拱形腰扣", "小折角发饰"],
        "quiet_areas": ["披肩中部", "裙侧"]
      },
      "generation_status": "planned",
      "quality_status": "not_reviewed",
      "client_status": "pending"
    }
  ]
}
```

去重脚本只验证基础比较字段与状态，不自动验证幻想规则、服装逻辑或审美；新增字段要由设计和实际看图落实。不要把 JSON 完整复制进生图指令，只提取能画出来的关键事实。

## 检查计划与真实历史

运行 `python3 scripts/check_diversity.py --plan /absolute/path/plan.json`。可用历史存在时再加 `--history /absolute/path/history.jsonl`。

- `edit` 计划至少提供 `mode` 与非空 `characters`，每项一个 `id`；编辑范围可另加字段。脚本跳过新角色差异和历史比较。
- 没有提供历史时只能报告本批次覆盖；显式提供不存在或损坏的文件是错误，不视为空历史。
- 历史只有明确通过全部已记录质量状态的条目才进入视觉历史比较；字符串与对象状态矛盾会排除。
- 自检通过且客户未确认／拒绝的设计可用于避免重复提出，但不能用作客户已接受的风格锚点。客户状态单独读取，不从自检推断。
- 零次比较没有“去重通过”的证据；脚本返回空覆盖，不能宣称全库不重复。
- `palette_id` 不计入结构差异。之后仍需实际并排看发型、肩腰裙形、手臂位置、眼嘴特征和主要色块。

只记录真实可访问的历史；当前对话以外数据不可用时说明范围。不声称永久记得旧订单，不覆盖旧记录。历史状态与修订方法见 [production-workflow.md](production-workflow.md)。
