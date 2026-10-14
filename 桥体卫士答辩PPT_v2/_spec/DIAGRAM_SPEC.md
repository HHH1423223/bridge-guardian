# DIAGRAM_SPEC —— 矢量图形几何规范（图形负责人 B 必读）

> 目标：**零位图**。所有图形用 PPT 原生形状 / 文本框 / 表格 / 折线拼出来。构建脚本已实现下列能力，你只出坐标与文本。

## 1. 你能用的元素类型（只有这几种）

| type | 可画出的东西 | 关键字段 |
|---|---|---|
| `rect` | 矩形 / 圆角矩形（卡片、底板、条带、节点、进度条）/ 圆形（`shape:"oval"`）/ 菱形（`shape:"diamond"`） | `x y w h fill line_color line_width radius shape` |
| `line` | 直线段（含斜线）、正交折线（多段 `points`）、箭头（`arrow:true`）、虚线（`dash:true`） | `points`（≥2 点，EMU）、`line_color`、`line_width`、`arrow`、`dash` |
| `text` | 纯文本（可混排 `runs`） | `text`/`runs`、`font`、`color`、`align`、`valign`、`line_spacing` |
| `table` | 表格（矩阵、对比、清单） | `rows`、`col_widths`、`header_fill`、`font_size` |
| `chart` | 折线/柱/面积图（坐标轴与刻度由脚本自动推导） | `chart_type`、`categories`、`series`、`y_min`、`y_max`、`ref_lines`、`bands`、`x_label`、`y_label` |

**没有的能力（不要写进规格）**：曲线/贝塞尔/任意多边形、图片、图标字体、SVG 导入、渐变填充、阴影、SmartArt、动画。

## 2. 坐标系（EMU，整数）

- 画布 12192000 × 6858000。
- **正文可用区**：x ∈ [685800, 11506200]，y ∈ [1188720, 6035040]。**图形必须完全落在此区间内。**
- 图形内文字最小 11pt；最小可读矩形高 = 228600（0.25in）；最小圆角矩形高 = 320000。
- 中文宽度估算：`(中文字数 + 0.5×非中文字数) × 字号pt × 12700 ≤ w × 0.95`；单行高 ≥ `字号pt × 1.55 × 12700`。
- **元素之间不得重叠**（同一位置放底卡 + 上层文字是允许的，但底卡必须更大且先绘制，即 `z` 更小）。

## 3. 颜色名（只能用这些）

`ink` `navy` `navy_deep` `blue` `blue_soft` `teal` `teal_soft` `amber` `orange` `red` `green` `slate` `slate_light` `line` `white` `bg`
（HEX 见 `BUILD_SPEC.md` §2；语义固定：green=安全、amber=预警、orange=报警、red=严重、teal=强调数据）

## 4. 字号名

`display 66` `hero 40` `h1 27` `h2 18` `h3 15` `body 13` `small 11` `tiny 9` `kpi 32` `kpi_sm 22`

## 5. 输出格式

- 每个图一个 JSON 文件：`_spec/diagrams/<fig_id>.json`
- 一个 JSON **只画一个图**（不要跨页复用坐标系）。
- 顶层结构：

```jsonc
{
  "fig_id": "arch6",
  "for_slide": "s03_arch",
  "canvas": {"x": 685800, "y": 1188720, "w": 10820400, "h": 4846320},
  "elements": [ /* 见上表 schema，字段名与 BUILD_SPEC.md §5 完全一致 */ ]
}
```

- 允许在 JSON 外用 `_note` 字段写意图说明（不会渲染）。
- **不要**写页面标题、页眉、页脚、页码：这些由构建脚本统一生成。
- 图内如需标题，用 `text`，`font: h3`，`color: ink`。

## 6. 关键几何坐标（供参考，可直接用）

| 名称 | 值 |
|---|---|
| 页面宽 / 高 | 12192000 / 6858000 |
| 内容左 / 右 | 685800 / 11506200 |
| 内容上 / 下 | 1188720 / 6035040 |
| 内容宽 / 高 | 10820400 / 4846320 |
| 水平三分点 | 685800 → 4293000 → 7898400 → 11506200 |
| 水平两半分界 | 6096000 |
| 垂直三分点 | 1188720 → 2804400 → 4420080 → 6035040 |
