import base64
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parent
ASSETS = ("cover", "loop", "warp", "software", "science", "physical", "control", "city")
TEXT = "{http://schemas.openxmlformats.org/drawingml/2006/main}t"


def read_notes(deck):
    with ZipFile(deck) as pptx:
        for number in range(1, 14):
            xml = ET.fromstring(pptx.read(f"ppt/notesSlides/notesSlide{number}.xml"))
            body = []
            sources = []
            for node in xml.iter(TEXT):
                value = node.text or ""
                match = re.fullmatch(r"参考来源\s+(.+) (https://\S+)", value)
                if match:
                    sources.append({"title": match[1].rstrip("."), "url": match[2]})
                elif value:
                    body.append(value)
            assert body, f"Missing speaker notes on slide {number}"
            yield {"body": "\n".join(body), "sources": sources}


folder = ROOT.parent / "演示文稿"
speaker_data = json.dumps(list(read_notes(folder / "智能爆炸.pptx")), ensure_ascii=False)
css = (ROOT / "web.css").read_text(encoding="utf-8")
script = (ROOT / "web.js").read_text(encoding="utf-8")
assets = []
for name in ASSETS:
    image_data = base64.b64encode((ROOT / f"{name}.jpg").read_bytes()).decode("ascii")
    assets.append(f'--{name}:url("data:image/jpeg;base64,{image_data}");')
template = (ROOT / "web.html").read_text(encoding="utf-8")
output = (
    template.replace("/* INLINE STYLES */", css + "\n:root{" + "".join(assets) + "}")
    .replace("/* INLINE SCRIPT */", script)
    .replace("SPEAKER_DATA", speaker_data.replace("</", "<\\/"))
)
(folder / "智能爆炸 · 互动演示.html").write_text(output, encoding="utf-8")
