from __future__ import annotations

import math
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "dc": "http://www.omg.org/spec/DD/20100524/DC",
    "di": "http://www.omg.org/spec/DD/20100524/DI",
}


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/timesbd.ttf" if bold else "C:/Windows/Fonts/times.ttf",
        "C:/Windows/Fonts/calibri.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def wrap_lines(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.replace("\n", " \n ").split()
    lines: list[str] = []
    current = ""
    for word in words:
        if word == "\n":
            if current:
                lines.append(current)
                current = ""
            continue
        candidate = word if not current else f"{current} {word}"
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        if draw.textbbox((0, 0), word, font=font)[2] <= max_width:
            current = word
            continue
        pieces = textwrap.wrap(word, width=max(4, int(len(word) * max_width / max(draw.textbbox((0, 0), word, font=font)[2], 1))))
        lines.extend(pieces[:-1])
        current = pieces[-1] if pieces else ""
    if current:
        lines.append(current)
    return lines


def draw_multiline_centered(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: str = "#22242a",
    line_gap: int = 4,
) -> None:
    x0, y0, x1, y1 = box
    lines = wrap_lines(draw, text, font, max(20, x1 - x0 - 20))
    if not lines:
        return
    heights = [draw.textbbox((0, 0), line, font=font)[3] for line in lines]
    total_height = sum(heights) + line_gap * (len(lines) - 1)
    y = y0 + max(0, (y1 - y0 - total_height) // 2)
    for line, height in zip(lines, heights):
        bbox = draw.textbbox((0, 0), line, font=font)
        width = bbox[2] - bbox[0]
        draw.text((x0 + (x1 - x0 - width) / 2, y), line, font=font, fill=fill)
        y += height + line_gap


def draw_rotated_lane_label(
    base: Image.Image,
    box: tuple[int, int, int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: str = "#22242a",
) -> None:
    x0, y0, x1, y1 = box
    tmp = Image.new("RGBA", (y1 - y0, x1 - x0), (255, 255, 255, 0))
    tmp_draw = ImageDraw.Draw(tmp)
    draw_multiline_centered(tmp_draw, (0, 0, tmp.width, tmp.height), text, font, fill=fill, line_gap=2)
    rotated = tmp.rotate(90, expand=True)
    base.alpha_composite(rotated, dest=(x0, y0 + max(0, (y1 - y0 - rotated.height) // 2)))


def draw_arrow_head(draw: ImageDraw.ImageDraw, p1: tuple[float, float], p2: tuple[float, float], fill: str) -> None:
    angle = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    length = 16
    spread = math.pi / 7
    left = (p2[0] - length * math.cos(angle - spread), p2[1] - length * math.sin(angle - spread))
    right = (p2[0] - length * math.cos(angle + spread), p2[1] - length * math.sin(angle + spread))
    draw.polygon([p2, left, right], fill=fill)


def scale_bounds(bounds: dict[str, float], margin: int, x_scale: float, y_scale: float) -> tuple[int, int, int, int]:
    x = int(bounds["x"] * x_scale) + margin
    y = int(bounds["y"] * y_scale) + margin
    w = int(bounds["width"] * x_scale)
    h = int(bounds["height"] * y_scale)
    return x, y, x + w, y + h


def render_bpmn(xml_path: Path, output_path: Path) -> None:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    process = root.find("bpmn:process", NS)
    if process is None:
        raise RuntimeError("BPMN process not found")

    nodes = {}
    for tag in ("startEvent", "endEvent", "intermediateCatchEvent", "userTask", "serviceTask", "exclusiveGateway"):
        for node in process.findall(f"bpmn:{tag}", NS):
            nodes[node.attrib["id"]] = {
                "type": tag,
                "name": node.attrib.get("name", ""),
            }

    plane = root.find(".//bpmndi:BPMNPlane", NS)
    if plane is None:
        raise RuntimeError("BPMN plane not found")

    shapes = {}
    edges = []
    canvas_w = 0.0
    canvas_h = 0.0

    for shape in plane.findall("bpmndi:BPMNShape", NS):
        element_id = shape.attrib["bpmnElement"]
        bounds = shape.find("dc:Bounds", NS)
        if bounds is None:
            continue
        rect = {
            "x": float(bounds.attrib["x"]),
            "y": float(bounds.attrib["y"]),
            "width": float(bounds.attrib["width"]),
            "height": float(bounds.attrib["height"]),
        }
        canvas_w = max(canvas_w, rect["x"] + rect["width"])
        canvas_h = max(canvas_h, rect["y"] + rect["height"])
        shapes[element_id] = rect

    for edge in plane.findall("bpmndi:BPMNEdge", NS):
        points = []
        for waypoint in edge.findall("di:waypoint", NS):
            x = float(waypoint.attrib["x"])
            y = float(waypoint.attrib["y"])
            points.append((x, y))
            canvas_w = max(canvas_w, x)
            canvas_h = max(canvas_h, y)
        if points:
            edges.append((edge.attrib["bpmnElement"], points))

    x_scale = 1.0
    y_scale = 1.8
    margin = 36
    width = int(canvas_w * x_scale) + margin * 2
    height = int(canvas_h * y_scale) + margin * 2

    img = Image.new("RGBA", (width, height), "white")
    draw = ImageDraw.Draw(img)

    title_font = load_font(28, bold=True)
    lane_font = load_font(18)
    node_font = load_font(19)
    label_font = load_font(17)

    title = process.attrib.get("name", "")
    draw.text((width / 2, 18), title, font=title_font, fill="#111", anchor="ma")

    lane_set = process.find("bpmn:laneSet", NS)
    if lane_set is not None:
        for lane in lane_set.findall("bpmn:lane", NS):
            lane_id = lane.attrib["id"]
            rect = shapes.get(lane_id)
            if not rect:
                continue
            x0, y0, x1, y1 = scale_bounds(rect, margin, x_scale, y_scale)
            draw.rectangle((x0, y0, x1, y1), outline="#22242a", width=2, fill="#ffffff")
            label_strip = (x0, y0, x0 + int(34 * x_scale), y1)
            draw.rectangle(label_strip, outline="#22242a", width=2, fill="#f8f8f8")
            draw_rotated_lane_label(img, label_strip, lane.attrib.get("name", ""), lane_font)

    for element_id, rect in shapes.items():
        if element_id.startswith("Lane_"):
            continue
        node = nodes.get(element_id)
        if not node:
            continue
        x0, y0, x1, y1 = scale_bounds(rect, margin, x_scale, y_scale)
        shape_type = node["type"]
        if shape_type in {"userTask", "serviceTask"}:
            draw.rounded_rectangle((x0, y0, x1, y1), radius=14, outline="#22242a", width=3, fill="#fcfcfc")
            draw_multiline_centered(draw, (x0 + 10, y0 + 10, x1 - 10, y1 - 10), node["name"], node_font)
        elif shape_type == "exclusiveGateway":
            cx = (x0 + x1) / 2
            cy = (y0 + y1) / 2
            diamond = [(cx, y0), (x1, cy), (cx, y1), (x0, cy)]
            draw.polygon(diamond, outline="#22242a", width=3, fill="white")
            draw.text((cx, cy - 6), "X", font=load_font(34, bold=True), fill="#22242a", anchor="mm")
            draw_multiline_centered(draw, (x0 - 30, y1 + 8, x1 + 30, y1 + 78), node["name"], label_font)
        else:
            cx = (x0 + x1) / 2
            cy = (y0 + y1) / 2
            r = min(x1 - x0, y1 - y0) / 2
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline="#22242a", width=3, fill="white")
            if shape_type == "intermediateCatchEvent":
                inner = r - 6
                draw.ellipse((cx - inner, cy - inner, cx + inner, cy + inner), outline="#22242a", width=2, fill=None)
            draw_multiline_centered(draw, (x0 - 90, y1 + 8, x1 + 90, y1 + 72), node["name"], label_font)

    for edge_id, points in edges:
        scaled = [(x * x_scale + margin, y * y_scale + margin) for x, y in points]
        draw.line(scaled, fill="#22242a", width=3)
        if len(scaled) >= 2:
            draw_arrow_head(draw, scaled[-2], scaled[-1], "#22242a")
        label = ""
        flow = process.find(f"bpmn:sequenceFlow[@id='{edge_id}']", NS)
        if flow is not None:
            label = flow.attrib.get("name", "")
        if label and len(scaled) >= 2:
            mx = (scaled[0][0] + scaled[-1][0]) / 2
            my = (scaled[0][1] + scaled[-1][1]) / 2 - 18
            draw.text((mx, my), label, font=label_font, fill="#22242a", anchor="mm")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(output_path, dpi=(220, 220))


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    render_bpmn(here / "a.xml", here.parent / "images" / "process_diagram_bpmn.png")
