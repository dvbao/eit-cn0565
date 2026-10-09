from __future__ import annotations

import argparse
import copy
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
from xml.etree import ElementTree as ET


A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
P14 = "http://schemas.microsoft.com/office/powerpoint/2010/main"
A16 = "http://schemas.microsoft.com/office/drawing/2014/main"
MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"

for prefix, uri in (("a", A), ("p", P), ("r", R), ("p14", P14), ("a16", A16), ("mc", MC)):
    ET.register_namespace(prefix, uri)

# OPC requires [Content_Types].xml to use the content-types namespace as the
# default namespace. Registering it explicitly prevents ElementTree from
# rewriting the document as <ns0:Types><ns0:Override .../>, which PowerPoint
# often accepts but strict package validators correctly reject.
ET.register_namespace("", CT)


def q(uri: str, tag: str) -> str:
    return f"{{{uri}}}{tag}"


def xml_bytes(root: ET.Element) -> bytes:
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def shape_name(element: ET.Element) -> str | None:
    cnv = element.find(f".//{q(P, 'cNvPr')}")
    return cnv.attrib.get("name") if cnv is not None else None


def find_shape(root: ET.Element, name: str) -> ET.Element:
    for element in root.findall(f".//{q(P, 'sp')}"):
        if shape_name(element) == name:
            return element
    raise KeyError(name)


def first_title(root: ET.Element) -> ET.Element:
    for sp in root.findall(f".//{q(P, 'sp')}"):
        ph = sp.find(f"{q(P, 'nvSpPr')}/{q(P, 'nvPr')}/{q(P, 'ph')}")
        if ph is not None and ph.attrib.get("type") in ("title", "ctrTitle"):
            return sp
    for name in ("Title 1", "Title 2"):
        try:
            return find_shape(root, name)
        except KeyError:
            pass
    raise KeyError("title")


def set_existing_text(shape: ET.Element, text: str) -> None:
    texts = list(shape.iter(q(A, "t")))
    if not texts:
        raise ValueError(f"Shape {shape_name(shape)} has no text")
    texts[0].text = text
    for extra in texts[1:]:
        extra.text = ""


def set_title(root: ET.Element, text: str) -> None:
    set_existing_text(first_title(root), text)


def sp_tree(root: ET.Element) -> ET.Element:
    return root.find(f"{q(P, 'cSld')}/{q(P, 'spTree')}")


def clear_slide(root: ET.Element, keep_shape_names=(), keep_picture_ids=(), keep_table=False) -> None:
    tree = sp_tree(root)
    keep_names = set(keep_shape_names)
    keep_pic_ids = set(str(x) for x in keep_picture_ids)
    for child in list(tree):
        if child.tag in (q(P, "nvGrpSpPr"), q(P, "grpSpPr")):
            continue
        if child.tag == q(P, "sp") and shape_name(child) in keep_names:
            continue
        if child.tag == q(P, "pic"):
            cnv = child.find(f"{q(P, 'nvPicPr')}/{q(P, 'cNvPr')}")
            if cnv is not None and cnv.attrib.get("id") in keep_pic_ids:
                continue
        if child.tag == q(P, "graphicFrame") and keep_table:
            continue
        tree.remove(child)


def max_shape_id(root: ET.Element) -> int:
    values = []
    for cnv in root.findall(f".//{q(P, 'cNvPr')}"):
        try:
            values.append(int(cnv.attrib.get("id", "0")))
        except ValueError:
            pass
    return max(values, default=1)


def add_textbox(
    root: ET.Element,
    name: str,
    left: int,
    top: int,
    width: int,
    height: int,
    paragraphs: list[dict],
    *,
    margin: int = 50000,
    vertical_anchor: str = "t",
) -> ET.Element:
    tree = sp_tree(root)
    shape_id = max_shape_id(root) + 1
    sp = ET.SubElement(tree, q(P, "sp"))
    nv = ET.SubElement(sp, q(P, "nvSpPr"))
    ET.SubElement(nv, q(P, "cNvPr"), {"id": str(shape_id), "name": name})
    ET.SubElement(nv, q(P, "cNvSpPr"), {"txBox": "1"})
    ET.SubElement(nv, q(P, "nvPr"))
    sppr = ET.SubElement(sp, q(P, "spPr"))
    xfrm = ET.SubElement(sppr, q(A, "xfrm"))
    ET.SubElement(xfrm, q(A, "off"), {"x": str(left), "y": str(top)})
    ET.SubElement(xfrm, q(A, "ext"), {"cx": str(width), "cy": str(height)})
    geom = ET.SubElement(sppr, q(A, "prstGeom"), {"prst": "rect"})
    ET.SubElement(geom, q(A, "avLst"))
    ET.SubElement(sppr, q(A, "noFill"))
    line = ET.SubElement(sppr, q(A, "ln"))
    ET.SubElement(line, q(A, "noFill"))
    body = ET.SubElement(sp, q(P, "txBody"))
    ET.SubElement(
        body,
        q(A, "bodyPr"),
        {
            "wrap": "square",
            "anchor": vertical_anchor,
            "lIns": str(margin),
            "rIns": str(margin),
            "tIns": str(margin),
            "bIns": str(margin),
        },
    )
    ET.SubElement(body, q(A, "lstStyle"))
    for item in paragraphs:
        p = ET.SubElement(body, q(A, "p"))
        ppr = ET.SubElement(p, q(A, "pPr"), {"algn": item.get("align", "l")})
        if item.get("space_after"):
            spc = ET.SubElement(ppr, q(A, "spcAft"))
            ET.SubElement(spc, q(A, "spcPts"), {"val": str(item["space_after"])})
        run = ET.SubElement(p, q(A, "r"))
        rpr = ET.SubElement(
            run,
            q(A, "rPr"),
            {
                "lang": "en-US",
                "sz": str(item.get("size", 1800)),
                "b": "1" if item.get("bold", False) else "0",
            },
        )
        fill = ET.SubElement(rpr, q(A, "solidFill"))
        ET.SubElement(fill, q(A, "srgbClr"), {"val": item.get("color", "222222")})
        ET.SubElement(rpr, q(A, "latin"), {"typeface": item.get("font", "Arial")})
        ET.SubElement(run, q(A, "t")).text = item["text"]
    return sp


def add_round_rect(root, name, text, left, top, width, height, *, fill="6F263D"):
    tree = sp_tree(root)
    shape_id = max_shape_id(root) + 1
    sp = ET.SubElement(tree, q(P, "sp"))
    nv = ET.SubElement(sp, q(P, "nvSpPr"))
    ET.SubElement(nv, q(P, "cNvPr"), {"id": str(shape_id), "name": name})
    ET.SubElement(nv, q(P, "cNvSpPr"))
    ET.SubElement(nv, q(P, "nvPr"))
    sppr = ET.SubElement(sp, q(P, "spPr"))
    xfrm = ET.SubElement(sppr, q(A, "xfrm"))
    ET.SubElement(xfrm, q(A, "off"), {"x": str(left), "y": str(top)})
    ET.SubElement(xfrm, q(A, "ext"), {"cx": str(width), "cy": str(height)})
    # DrawingML requires geometry before fill and line properties.
    geom = ET.SubElement(sppr, q(A, "prstGeom"), {"prst": "roundRect"})
    ET.SubElement(geom, q(A, "avLst"))
    sf = ET.SubElement(sppr, q(A, "solidFill"))
    ET.SubElement(sf, q(A, "srgbClr"), {"val": fill})
    ln = ET.SubElement(sppr, q(A, "ln"), {"w": "19050"})
    lnf = ET.SubElement(ln, q(A, "solidFill"))
    ET.SubElement(lnf, q(A, "srgbClr"), {"val": "53182D"})
    body = ET.SubElement(sp, q(P, "txBody"))
    ET.SubElement(body, q(A, "bodyPr"), {"anchor": "ctr", "wrap": "square"})
    ET.SubElement(body, q(A, "lstStyle"))
    p = ET.SubElement(body, q(A, "p"))
    ET.SubElement(p, q(A, "pPr"), {"algn": "ctr"})
    run = ET.SubElement(p, q(A, "r"))
    rpr = ET.SubElement(run, q(A, "rPr"), {"lang": "en-US", "sz": "1650", "b": "1"})
    rf = ET.SubElement(rpr, q(A, "solidFill"))
    ET.SubElement(rf, q(A, "srgbClr"), {"val": "FFFFFF"})
    ET.SubElement(rpr, q(A, "latin"), {"typeface": "Arial"})
    ET.SubElement(run, q(A, "t")).text = text
    return sp


def set_picture_geometry(root, picture_id: str, left: int, top: int, width: int, height: int, descr: str):
    for pic in root.findall(f".//{q(P, 'pic')}"):
        cnv = pic.find(f"{q(P, 'nvPicPr')}/{q(P, 'cNvPr')}")
        if cnv is not None and cnv.attrib.get("id") == str(picture_id):
            cnv.attrib["descr"] = descr
            xfrm = pic.find(f"{q(P, 'spPr')}/{q(A, 'xfrm')}")
            off = xfrm.find(q(A, "off"))
            ext = xfrm.find(q(A, "ext"))
            off.attrib.update({"x": str(left), "y": str(top)})
            ext.attrib.update({"cx": str(width), "cy": str(height)})
            return
    raise KeyError(f"picture {picture_id}")


def set_table(root, headers, rows, widths, left, top, width, height, font_size):
    frame = root.find(f".//{q(P, 'graphicFrame')}")
    if frame is None:
        raise ValueError("No graphic frame")
    xfrm = frame.find(q(P, "xfrm"))
    off = xfrm.find(q(A, "off"))
    ext = xfrm.find(q(A, "ext"))
    off.attrib.update({"x": str(left), "y": str(top)})
    ext.attrib.update({"cx": str(width), "cy": str(height)})
    table = frame.find(f".//{q(A, 'tbl')}")
    old_rows = table.findall(q(A, "tr"))
    header_template = old_rows[0]
    body_templates = old_rows[1:3] if len(old_rows) >= 3 else [old_rows[-1]]
    for row in old_rows:
        table.remove(row)
    all_values = [headers] + rows
    row_height = height // len(all_values)
    for row_index, values in enumerate(all_values):
        template = header_template if row_index == 0 else body_templates[(row_index - 1) % len(body_templates)]
        new_row = copy.deepcopy(template)
        new_row.attrib["h"] = str(row_height)
        cells = new_row.findall(q(A, "tc"))
        if len(cells) != len(values):
            raise ValueError(f"Expected {len(values)} table cells, found {len(cells)}")
        for cell, value in zip(cells, values):
            texts = list(cell.iter(q(A, "t")))
            if not texts:
                raise ValueError("Table cell has no text run")
            texts[0].text = value
            for extra in texts[1:]:
                extra.text = ""
            for rpr in cell.iter(q(A, "rPr")):
                rpr.attrib["sz"] = str(font_size)
        table.append(new_row)
    grid = table.find(q(A, "tblGrid"))
    for col, col_width in zip(grid.findall(q(A, "gridCol")), widths):
        col.attrib["w"] = str(col_width)


def set_notes(root: ET.Element, paragraphs: list[str], slide_number: int):
    body_shape = None
    for sp in root.findall(f".//{q(P, 'sp')}"):
        ph = sp.find(f"{q(P, 'nvSpPr')}/{q(P, 'nvPr')}/{q(P, 'ph')}")
        if ph is not None and ph.attrib.get("type") == "body":
            body_shape = sp
            break
    if body_shape is None:
        raise ValueError("Notes body placeholder not found")
    tx = body_shape.find(q(P, "txBody"))
    for p in list(tx.findall(q(A, "p"))):
        tx.remove(p)
    for text in paragraphs:
        p = ET.SubElement(tx, q(A, "p"))
        run = ET.SubElement(p, q(A, "r"))
        rpr = ET.SubElement(run, q(A, "rPr"), {"lang": "en-US", "sz": "1200"})
        ET.SubElement(rpr, q(A, "latin"), {"typeface": "Arial"})
        ET.SubElement(run, q(A, "t")).text = text
    for fld in root.findall(f".//{q(A, 'fld')}"):
        if fld.attrib.get("type") == "slidenum":
            t = fld.find(q(A, "t"))
            if t is not None:
                t.text = str(slide_number)


def ensure_notes_relationship(slide_rels: ET.Element, notes_number: int):
    for rel in slide_rels.findall(q(REL, "Relationship")):
        if rel.attrib.get("Type", "").endswith("/notesSlide"):
            rel.attrib["Target"] = f"../notesSlides/notesSlide{notes_number}.xml"
            return
    used = {rel.attrib.get("Id") for rel in slide_rels.findall(q(REL, "Relationship"))}
    idx = 1
    while f"rId{idx}" in used:
        idx += 1
    ET.SubElement(
        slide_rels,
        q(REL, "Relationship"),
        {
            "Id": f"rId{idx}",
            "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide",
            "Target": f"../notesSlides/notesSlide{notes_number}.xml",
        },
    )


def notes_rels(slide_file_number: int) -> ET.Element:
    root = ET.Element(q(REL, "Relationships"))
    ET.SubElement(
        root,
        q(REL, "Relationship"),
        {
            "Id": "rId1",
            "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesMaster",
            "Target": "../notesMasters/notesMaster1.xml",
        },
    )
    ET.SubElement(
        root,
        q(REL, "Relationship"),
        {
            "Id": "rId2",
            "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide",
            "Target": f"../slides/slide{slide_file_number}.xml",
        },
    )
    return root


def replace_reference_slide(root: ET.Element):
    set_title(root, "References")
    body = find_shape(root, "Text Placeholder 3")
    tx = body.find(q(P, "txBody"))
    for p in list(tx.findall(q(A, "p"))):
        tx.remove(p)
    refs = [
        '[1] B. Liu et al., "pyEIT: A Python Based Framework for Electrical Impedance Tomography," SoftwareX 7 (2018), 304–308.',
        '[2] Analog Devices, "CN0565: Electrical Impedance Tomography Measurement System," Rev. A, 2024.',
        '[3] A. Adler et al., "GREIT: A Unified Approach to 2D Linear EIT Reconstruction of Lung Images," Physiological Measurement 30 (2009), S35–S55.',
    ]
    for ref in refs:
        p = ET.SubElement(tx, q(A, "p"))
        ppr = ET.SubElement(p, q(A, "pPr"))
        spc = ET.SubElement(ppr, q(A, "spcAft"))
        ET.SubElement(spc, q(A, "spcPts"), {"val": "1000"})
        run = ET.SubElement(p, q(A, "r"))
        rpr = ET.SubElement(run, q(A, "rPr"), {"lang": "en-US", "sz": "1700"})
        ET.SubElement(rpr, q(A, "latin"), {"typeface": "Arial"})
        ET.SubElement(run, q(A, "t")).text = ref


def build(source: Path, assets: Path, output: Path):
    with ZipFile(source) as zin:
        original = {name: zin.read(name) for name in zin.namelist()}
        infos = {info.filename: info for info in zin.infolist()}

    replacements: dict[str, bytes] = {}

    # Slide 18 in presentation order: section divider (slide12.xml).
    root = ET.fromstring(original["ppt/slides/slide12.xml"])
    set_title(root, "3. Active Sensing – Simulation Study")
    set_existing_text(find_shape(root, "Text Placeholder 6"), "BP, JAC, and GREIT: a controlled comparison")
    replacements["ppt/slides/slide12.xml"] = xml_bytes(root)

    # Slide 19: rationale and process.
    root = ET.fromstring(original["ppt/slides/slide13.xml"])
    clear_slide(root, keep_shape_names=("Title 2", "Slide Number Placeholder 21"))
    set_title(root, "Simulation Rationale")
    add_textbox(root, "Research Question", 520000, 720000, 8100000, 500000, [
        {"text": "How do BP, JAC, and GREIT reconstruct the same known conductivity change?", "size": 2200, "bold": True, "color": "222222", "align": "c"}
    ], vertical_anchor="ctr")
    box_y, box_w, box_h, gap, start = 1650000, 1650000, 720000, 420000, 470000
    labels = ["Known conductivity map", "Forward simulation", "208 voltage changes", "BP, JAC, GREIT"]
    captions = ["Ground truth", "Synthetic measurement", "Shared input", "Three estimates"]
    for i, (label, caption) in enumerate(zip(labels, captions)):
        x = start + i * (box_w + gap)
        add_round_rect(root, f"Process {i+1}", label, x, box_y, box_w, box_h)
        add_textbox(root, f"Caption {i+1}", x, box_y + box_h + 90000, box_w, 330000, [
            {"text": caption, "size": 1300, "color": "555555", "align": "c"}
        ], vertical_anchor="ctr")
        if i < 3:
            add_textbox(root, f"Chevron {i+1}", x + box_w, box_y + 80000, gap, 520000, [
                {"text": "›", "size": 3000, "bold": True, "color": "6F263D", "align": "c"}
            ], vertical_anchor="ctr")
    add_textbox(root, "Rationale", 900000, 3300000, 7300000, 820000, [
        {"text": "The simulation provides an answer key. Each algorithm receives the same data, so differences in the images come from the reconstruction method and its settings.", "size": 1850, "color": "222222", "align": "c"}
    ], vertical_anchor="ctr")
    replacements["ppt/slides/slide13.xml"] = xml_bytes(root)

    # Slide 20: ground truth.
    root = ET.fromstring(original["ppt/slides/slide14.xml"])
    clear_slide(root, keep_shape_names=("Title 2", "Slide Number Placeholder 21"), keep_picture_ids=(4,))
    set_title(root, "Known Conductivity Map")
    set_picture_geometry(root, "4", 340000, 690000, 5100000, 3860000, "Ground-truth relative conductivity map used in the simulation")
    add_textbox(root, "Model Definition", 5660000, 820000, 2900000, 430000, [
        {"text": "Model definition", "size": 1950, "bold": True, "color": "6F263D"}
    ])
    add_textbox(root, "Model Values", 5660000, 1260000, 2900000, 2100000, [
        {"text": "2D circular domain", "size": 1700, "bold": True, "space_after": 500},
        {"text": "16 boundary electrodes", "size": 1700, "space_after": 500},
        {"text": "Background σrel = 1", "size": 1700, "space_after": 500},
        {"text": "Target radius = 0.12R", "size": 1700, "space_after": 500},
        {"text": "Target ratios: 0.1×, 10×, 5×, 0.1×", "size": 1700},
    ])
    add_textbox(root, "Normalization Note", 5660000, 3530000, 2900000, 760000, [
        {"text": "The value 1 is a normalized reference. It does not identify the physical material or imply 1 S/m.", "size": 1350, "color": "555555"}
    ])
    replacements["ppt/slides/slide14.xml"] = xml_bytes(root)
    replacements["ppt/media/image8.png"] = (assets / "ground_truth.png").read_bytes()

    # Slide 21: mesh.
    root = ET.fromstring(original["ppt/slides/slide15.xml"])
    clear_slide(root, keep_shape_names=("Title 2", "Slide Number Placeholder 21"), keep_picture_ids=(14,))
    set_title(root, "Finite-Element Representation")
    set_picture_geometry(root, "14", 360000, 690000, 5100000, 3860000, "Triangular finite-element mesh with 16 boundary electrodes")
    add_textbox(root, "Mesh Numbers", 5680000, 900000, 2850000, 2700000, [
        {"text": "583 nodes", "size": 2050, "bold": True, "color": "6F263D", "space_after": 250},
        {"text": "Calculation points for electric potential", "size": 1450, "color": "333333", "space_after": 700},
        {"text": "1083 elements", "size": 2050, "bold": True, "color": "6F263D", "space_after": 250},
        {"text": "Triangular regions that store conductivity", "size": 1450, "color": "333333", "space_after": 700},
        {"text": "16 electrodes", "size": 2050, "bold": True, "color": "6F263D", "space_after": 250},
        {"text": "Boundary locations for the measurement protocol", "size": 1450, "color": "333333"},
    ])
    add_textbox(root, "Mesh Note", 5680000, 3820000, 2850000, 500000, [
        {"text": "h0 = 0.08 controls the approximate triangle size. The mesher determines the final node and element counts.", "size": 1250, "color": "555555"}
    ])
    replacements["ppt/slides/slide15.xml"] = xml_bytes(root)
    replacements["ppt/media/image9.png"] = (assets / "mesh.png").read_bytes()

    # Slide 22: synthetic voltage data.
    root = ET.fromstring(original["ppt/slides/slide16.xml"])
    clear_slide(root, keep_shape_names=("Title 2", "Slide Number Placeholder 21"), keep_picture_ids=(26,))
    set_title(root, "Synthetic Boundary-Voltage Data")
    set_picture_geometry(root, "26", 330000, 980000, 6050000, 3000000, "Reference, target, and difference voltage vectors from the forward solver")
    add_textbox(root, "Frame Definitions", 6580000, 1050000, 2050000, 2400000, [
        {"text": "v₀", "size": 2200, "bold": True, "color": "6F263D", "space_after": 150},
        {"text": "Reference frame", "size": 1450, "space_after": 700},
        {"text": "v₁", "size": 2200, "bold": True, "color": "6F263D", "space_after": 150},
        {"text": "Target frame", "size": 1450, "space_after": 700},
        {"text": "Δv = v₁ − v₀", "size": 1900, "bold": True, "color": "6F263D"},
    ])
    add_textbox(root, "Measurement Count", 6580000, 3290000, 2050000, 660000, [
        {"text": "16 drive pairs × 13 sense pairs = 208 voltage differences per frame", "size": 1300, "bold": True, "align": "c"}
    ], vertical_anchor="ctr")
    add_textbox(root, "Model Assumptions", 480000, 4140000, 7900000, 330000, [
        {"text": "Forward-model data only: ideal 2D geometry, point electrodes, normalized current, and zero added noise", "size": 1150, "color": "666666", "align": "c"}
    ], vertical_anchor="ctr")
    replacements["ppt/slides/slide16.xml"] = xml_bytes(root)
    replacements["ppt/media/image11.png"] = (assets / "voltage_frames.png").read_bytes()

    # Slide 23: algorithm comparison table.
    root = ET.fromstring(original["ppt/slides/slide17.xml"])
    clear_slide(root, keep_shape_names=("Title 2", "Slide Number Placeholder 21"), keep_table=True)
    set_title(root, "Same Data, Three Reconstruction Methods")
    set_table(
        root,
        ["Algorithm", "Core idea", "Output space", "What to look for"],
        [
            ["BP", "Direct back-projection of voltage changes", "Mesh nodes", "Fast, broad response"],
            ["JAC", "Jacobian sensitivity with regularization", "Mesh elements", "Detail versus stability"],
            ["GREIT", "Sensitivity-based linear map to a regular grid", "32 × 32 grid", "Smooth, standardized output"],
        ],
        [900000, 3150000, 1500000, 2800000],
        370000,
        1120000,
        8400000,
        2900000,
        1250,
    )
    add_textbox(root, "Shared Input", 800000, 4210000, 7550000, 370000, [
        {"text": "Shared input: the same mesh, electrode protocol, v₀, and v₁. The algorithms do not receive the ground-truth target locations.", "size": 1250, "color": "555555", "align": "c"}
    ], vertical_anchor="ctr")
    replacements["ppt/slides/slide17.xml"] = xml_bytes(root)

    # Slide 24: reconstruction result.
    root = ET.fromstring(original["ppt/slides/slide18.xml"])
    clear_slide(root, keep_shape_names=("Title 2", "Slide Number Placeholder 21"), keep_picture_ids=(5,))
    set_title(root, "Reconstruction of the Same Simulated Object")
    set_picture_geometry(root, "5", 330000, 770000, 8460000, 2470000, "Normalized qualitative comparison of ground truth, BP, JAC, and GREIT")
    add_textbox(root, "Result Observations", 570000, 3420000, 8000000, 780000, [
        {"text": "BP: broad, diffuse regions", "size": 1550, "bold": True, "color": "6F263D", "align": "c", "space_after": 250},
        {"text": "JAC: concentrated peaks with mesh-related artifacts", "size": 1550, "bold": True, "color": "6F263D", "align": "c", "space_after": 250},
        {"text": "GREIT: smooth output on a regular pixel grid", "size": 1550, "bold": True, "color": "6F263D", "align": "c"},
    ], vertical_anchor="ctr")
    add_textbox(root, "Result Scope", 800000, 4280000, 7550000, 270000, [
        {"text": "Noise = 0. These observations describe this parameter set and do not establish a universal ranking.", "size": 1120, "color": "666666", "align": "c"}
    ], vertical_anchor="ctr")
    replacements["ppt/slides/slide18.xml"] = xml_bytes(root)
    replacements["ppt/media/image12.png"] = (assets / "reconstruction_comparison.png").read_bytes()

    # Slide 25: controlled comparison plan.
    root = ET.fromstring(original["ppt/slides/slide19.xml"])
    clear_slide(root, keep_shape_names=("Title 1",), keep_table=True)
    set_title(root, "Controlled Comparison Plan")
    set_table(
        root,
        ["Test", "Question answered"],
        [
            ["Position", "Does localization change from the center to the boundary?"],
            ["Size", "Does reconstructed target size follow the simulated radius?"],
            ["Contrast", "Does the output remain linear as the conductivity ratio changes?"],
            ["Noise", "Which method amplifies measurement noise?"],
            ["Separation", "Can the method distinguish two nearby targets?"],
        ],
        [1800000, 6400000],
        470000,
        1050000,
        8200000,
        3100000,
        1500,
    )
    add_textbox(root, "Test Rule", 800000, 4260000, 7550000, 360000, [
        {"text": "Change one variable at a time while keeping the mesh, protocol, and algorithm settings fixed.", "size": 1350, "bold": True, "color": "6F263D", "align": "c"}
    ], vertical_anchor="ctr")
    replacements["ppt/slides/slide19.xml"] = xml_bytes(root)

    # Slide 26: scope and next step.
    root = ET.fromstring(original["ppt/slides/slide20.xml"])
    clear_slide(root, keep_shape_names=("Title 1",), keep_table=True)
    set_title(root, "Scope of the Simulation")
    set_table(
        root,
        ["The simulation evaluates", "It does not yet evaluate"],
        [
            ["The reconstruction pipeline", "CN0565 measurement accuracy"],
            ["Algorithm behavior", "Electrode contact and cable noise"],
            ["Controlled target changes", "Mismatch in a physical medium"],
            ["Response to synthetic noise", "Human-subject performance"],
            ["Comparison with known ground truth", "Clinical validity"],
        ],
        [4100000, 4100000],
        470000,
        1050000,
        8200000,
        3100000,
        1450,
    )
    add_textbox(root, "Next Step", 700000, 4230000, 7750000, 470000, [
        {"text": "Next validation sequence: electrical load, homogeneous saline tank, then known inclusions at controlled locations", "size": 1350, "bold": True, "color": "6F263D", "align": "c"}
    ], vertical_anchor="ctr")
    replacements["ppt/slides/slide20.xml"] = xml_bytes(root)

    # Slide 27: references.
    root = ET.fromstring(original["ppt/slides/slide21.xml"])
    replace_reference_slide(root)
    replacements["ppt/slides/slide21.xml"] = xml_bytes(root)

    # Speaker notes for presentation slides 18 through 26.
    note_text = {
        18: [
            "I will now focus on the computational model used to compare three EIT reconstruction methods: BP, JAC, and GREIT.",
            "The goal is to understand the software behavior before introducing hardware variability.",
        ],
        19: [
            "Simulation gives me a known answer. I define the internal conductivity map, generate synthetic boundary data with a forward model, and ask three algorithms to reconstruct the hidden change.",
            "All three methods receive exactly the same input. This isolates the effect of the reconstruction method and its parameters.",
        ],
        20: [
            "The domain is a two-dimensional unit circle with sixteen boundary electrodes. The background conductivity is normalized to one.",
            "The four circular targets are defined by position, radius, and conductivity ratio. A value of ten means ten times the background conductivity. A value of 0.1 means one tenth.",
            "This is a conceptual reproduction of the four-target CN0565 Figure 14 workflow. The circuit note does not publish the exact simulation parameters, so I do not claim a pixel-level reproduction.",
            "Source: Analog Devices, CN0565 Rev. A, Figure 14.",
        ],
        21: [
            "The computer represents the continuous domain with a finite triangular mesh. This mesh contains 583 nodes and 1083 elements.",
            "Nodes are calculation points for electric potential. Each triangular element stores one conductivity value. The sixteen red boundary points represent the electrodes.",
            "These counts describe the computational model. They are not measurement counts. The mesh generator obtains them from h0 equals 0.08.",
        ],
        22: [
            "The forward solver acts as a virtual measurement system. It calculates a reference frame v0 for the homogeneous background and a target frame v1 after adding the four anomalies.",
            "Each frame contains 208 voltage differences. The count comes from sixteen adjacent drive pairs and thirteen valid sensing pairs per drive.",
            "The reconstruction input is the change vector v1 minus v0. No CN0565 hardware data are used at this stage.",
        ],
        23: [
            "BP directly back-projects voltage changes into the domain and provides a fast baseline result.",
            "JAC uses the Jacobian sensitivity matrix with regularization. Its settings control the balance between spatial detail and stability.",
            "The pyEIT GREIT implementation applies a sensitivity-based linear reconstruction matrix and maps the result to a regular output grid.",
            "The grid size changes the displayed sampling. It does not add new measurement information.",
            "Sources: Liu et al., SoftwareX 2018; Adler et al., Physiological Measurement 2009; pyEIT 1.2.4 implementation.",
        ],
        24: [
            "This figure uses the same ground truth and the same two voltage frames for all three reconstruction methods.",
            "Red indicates a positive conductivity change and blue indicates a negative change. All three methods recover the four general target locations and their signs in this noise-free test.",
            "BP is broad and diffuse. JAC produces concentrated peaks but also shows mesh-related artifacts. GREIT gives a smooth image on a regular grid.",
            "Each reconstructed output is normalized independently here. I compare location, sign, spatial spread, and artifacts rather than raw amplitude.",
            "Figure generated from scripts/eit_sim_playground.py.",
        ],
        25: [
            "A visual comparison is only the first step. I will change one simulation variable at a time and keep all other settings fixed.",
            "The planned tests examine target position, target size, conductivity contrast, measurement noise, and the separation between two targets.",
            "The comparison will use localization error, spatial spread, sign recovery, artifacts, and noise sensitivity.",
        ],
        26: [
            "The simulation verifies the computational workflow and supports a controlled algorithm comparison.",
            "It does not validate the CN0565 hardware because the forward model generated the voltage data.",
            "The hardware validation sequence should begin with an electrical load, continue with a homogeneous saline tank, and then use known inclusions at controlled locations.",
        ],
    }
    slide_file_for_order = {18: 12, 19: 13, 20: 14, 21: 15, 22: 16, 23: 17, 24: 18, 25: 19, 26: 20}
    note_file_for_order = {18: 10, 19: 11, 20: 12, 21: 13, 22: 14, 23: 15, 24: 16, 25: 17, 26: 18}
    note_template = ET.fromstring(original["ppt/notesSlides/notesSlide16.xml"])
    for order in range(18, 27):
        note_no = note_file_for_order[order]
        slide_file_no = slide_file_for_order[order]
        if note_no <= 16:
            note_root = ET.fromstring(original[f"ppt/notesSlides/notesSlide{note_no}.xml"])
        else:
            note_root = copy.deepcopy(note_template)
        set_notes(note_root, note_text[order], order)
        replacements[f"ppt/notesSlides/notesSlide{note_no}.xml"] = xml_bytes(note_root)
        if note_no >= 17:
            replacements[f"ppt/notesSlides/_rels/notesSlide{note_no}.xml.rels"] = xml_bytes(notes_rels(slide_file_no))
            slide_rels_name = f"ppt/slides/_rels/slide{slide_file_no}.xml.rels"
            slide_rels_root = ET.fromstring(original[slide_rels_name])
            ensure_notes_relationship(slide_rels_root, note_no)
            replacements[slide_rels_name] = xml_bytes(slide_rels_root)

    # Add content-type declarations for the two new notes slides.
    ct_root = ET.fromstring(original["[Content_Types].xml"])
    existing_parts = {el.attrib.get("PartName") for el in ct_root.findall(q(CT, "Override"))}
    for note_no in (17, 18):
        part = f"/ppt/notesSlides/notesSlide{note_no}.xml"
        if part not in existing_parts:
            ET.SubElement(
                ct_root,
                q(CT, "Override"),
                {
                    "PartName": part,
                    "ContentType": "application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml",
                },
            )
    replacements["[Content_Types].xml"] = xml_bytes(ct_root)

    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as zout:
        for name, data in original.items():
            if name in replacements:
                data = replacements.pop(name)
            info = infos[name]
            new_info = ZipInfo(name, date_time=info.date_time)
            new_info.compress_type = ZIP_DEFLATED
            new_info.external_attr = info.external_attr
            zout.writestr(new_info, data)
        for name, data in replacements.items():
            zout.writestr(name, data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.source, args.assets, args.output)
    print(f"Created {args.output}")


if __name__ == "__main__":
    main()
