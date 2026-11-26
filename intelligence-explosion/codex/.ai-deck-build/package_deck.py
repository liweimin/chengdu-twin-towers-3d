import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parent
TRANSITIONS = [
    ("slow", '<p:fade thruBlk="1"/>'),
    ("fast", '<p:cut thruBlk="1"/>'),
    ("med", "<p:fade/>"),
    ("fast", "<p:fade/>"),
    ("fast", '<p:wipe dir="l"/>'),
    ("fast", '<p:zoom dir="in"/>'),
    ("fast", '<p:push dir="l"/>'),
    ("fast", '<p:push dir="l"/>'),
    ("med", '<p:fade thruBlk="1"/>'),
    ("fast", "<p:cut/>"),
    ("med", "<p:fade/>"),
    ("fast", "<p:cut/>"),
    ("slow", '<p:fade thruBlk="1"/>'),
]

with ZipFile(ROOT / "draft.pptx") as source, ZipFile(ROOT / "candidate.pptx", "w", ZIP_DEFLATED) as output:
    count = 0
    for entry in source.infolist():
        data = source.read(entry)
        match = re.fullmatch(r"ppt/slides/slide(\d+)\.xml", entry.filename)
        if match:
            slide_xml = data.decode("utf-8")
            speed, effect = TRANSITIONS[int(match.group(1)) - 1]
            transition = f'<p:transition spd="{speed}" advClick="1">{effect}</p:transition>'
            boundary = re.search(r"</p:clrMapOvr>|</p:cSld>", slide_xml)
            override_end = slide_xml.find("</p:clrMapOvr>")
            assert boundary is not None and "<p:transition" not in slide_xml
            at = override_end + len("</p:clrMapOvr>") if override_end >= 0 else boundary.end()
            slide_xml = slide_xml[:at] + transition + slide_xml[at:]
            data = slide_xml.encode("utf-8")
            count += 1
        output.writestr(entry, data)
    assert count == len(TRANSITIONS)
