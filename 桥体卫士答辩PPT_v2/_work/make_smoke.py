# -*- coding: utf-8 -*-
"""冒烟测试：用最小样例喂给 build_deck.py，验证渲染管线可用。"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

D = pathlib.Path(__file__).resolve().parent / "smoke"
D.mkdir(parents=True, exist_ok=True)

content = {
    "deck": {"title": "smoke", "slides_total": 15, "duration_seconds": 720,
             "speaker": "单人主讲", "hardware_on_stage": False},
    "slides": [
        {"slide_id": "s01_cover", "chrome": "none", "section": None, "title": "桥体卫士",
         "seconds": 30,
         "elements": [
             {"id": "t1", "type": "text", "x": 685800, "y": 2743200, "w": 6096000, "h": 914400,
              "text": "桥体卫士", "font": "display", "bold": True, "color": "ink"},
             {"id": "t2", "type": "text", "x": 685800, "y": 3657600, "w": 6096000, "h": 457200,
              "text": "桥梁结构健康监测缩尺原型", "font": "h2", "color": "slate"},
         ],
         "notes": "这是一段测试讲稿，用于验证 notes 写入。"},
        {"slide_id": "s06_video", "chrome": "standard", "section": "现场演示",
         "title": "软件全链路演示", "seconds": 60,
         "elements": [
             {"id": "t1", "type": "text", "x": 685800, "y": 1188720, "w": 4572000, "h": 457200,
              "text": "一分钟看完整链路", "font": "h2", "color": "ink"},
         ],
         "notes": "测试。"},
    ],
}

figs = {"figures": [
    {"fig_id": "cover_geo", "for_slide": "s01_cover",
     "canvas": {"x": 0, "y": 0, "w": 12192000, "h": 6858000},
     "elements": [
         {"id": "g1", "type": "rect", "x": 8229600, "y": 0, "w": 3962400, "h": 6858000, "fill": "navy"},
         {"id": "g2", "type": "line", "points": [[8229600, 0], [8229600, 6858000]],
          "line_color": "teal", "line_width": 2},
     ]},
    {"fig_id": "video_slots", "for_slide": "s06_video",
     "canvas": {"x": 685800, "y": 1188720, "w": 10820400, "h": 4846320},
     "elements": [
         {"id": "v1", "type": "rect", "x": 1188720, "y": 1330000, "w": 7528560, "h": 4000000,
          "fill": "ink", "line_color": "blue", "line_width": 1.5, "radius": 0.02},
         {"id": "v2", "type": "rect", "x": 4754880, "y": 3130000, "w": 685800, "h": 381000,
          "fill": "teal", "line_color": "none", "radius": 0.5},
         {"id": "v3", "type": "text", "x": 1188720, "y": 5500000, "w": 7528560, "h": 228600,
          "text": "占位框内插入演示录屏（1 分钟，16:9，无硬件实物）", "font": "small",
          "color": "slate_light", "align": "center"},
         {"id": "v4", "type": "text", "x": 1188720, "y": 5760000, "w": 7528560, "h": 228600,
          "text": "模拟数据源 → 分级报警 → 确认处置 → 历史追溯 → 如实离线", "font": "small",
          "color": "slate", "align": "center"},
     ]},
    {"fig_id": "chart_demo", "for_slide": "s01_cover",
     "canvas": {"x": 0, "y": 0, "w": 12192000, "h": 6858000},
     "elements": [
         {"id": "c1", "type": "chart", "x": 6400800, "y": 2743200, "w": 4572000, "h": 2286000,
          "chart_type": "line",
          "categories": ["1", "2", "3", "4", "5", "6", "7", "8"],
          "series": [{"name": "相对应变", "values": [40, 60, 95, 130, 150, 142, 120, 90],
                      "color": "teal"}],
          "y_min": 0, "y_max": 200,
          "ref_lines": [{"value": 120, "color": "red", "label": "阈值 120", "dash": True}],
          "bands": [{"from": 0, "to": 120, "color": "green"}],
          "x_label": "采样点（1s）", "y_label": "相对应变指标", "font_size": 11},
     ]},
]}

(D / "SPEC_content.json").write_text(json.dumps(content, ensure_ascii=False, indent=1), encoding="utf-8")
(D / "SPEC_diagrams.json").write_text(json.dumps(figs, ensure_ascii=False, indent=1), encoding="utf-8")
print("smoke specs written to", D)
