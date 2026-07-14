#!/usr/bin/env python3
"""Generate Glowforge-ready SVGs for the DaysSince case (see dims.py).

    python3 generate.py          # writes ./output/

Output:
  output/piece-*.svg        one file per piece, mm-true, red strokes = cut
  output/sheet-*.svg        pieces shelf-packed onto Glowforge bed sheets
  output/preview-*.svg      assembly views with dashed ghosts + labels —
                            NEVER send previews to the laser

Kerf: circles/holes/slots are drawn at target - KERF so the finished hole
hits target. Outer plate profiles are drawn at target + KERF. Wall strip
polygons are drawn at target (they come out ~KERF small = looser, fine for
locate-only walls).

Back-of-case pieces (back plate, magnet layer, magnet cover) are emitted
MIRRORED so that, once flipped over during assembly, their features line up
with the front-view coordinates everything is designed in.
"""
from __future__ import annotations

import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dims as D

CUT = "#ff0000"
GHOST = "#0088ff"
KEEPOUT = "#00aa44"
LABEL = "#666666"

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


# ----------------------------------------------------------- svg helpers
def _f(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return s if s else "0"


def circle(cx, cy, dia, color=CUT, dash=False):
    d = f' stroke-dasharray="1.5,1.5"' if dash else ""
    return (f'<circle cx="{_f(cx)}" cy="{_f(cy)}" r="{_f(dia / 2)}" '
            f'fill="none" stroke="{color}" stroke-width="0.15"{d}/>')


def rect(x, y, w, h, color=CUT, rx=0.0, dash=False):
    r = f' rx="{_f(rx)}"' if rx else ""
    d = f' stroke-dasharray="1.5,1.5"' if dash else ""
    return (f'<rect x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" height="{_f(h)}"'
            f'{r} fill="none" stroke="{color}" stroke-width="0.15"{d}/>')


def poly(points, color=CUT):
    pts = " ".join(f"{_f(x)},{_f(y)}" for x, y in points)
    return (f'<polygon points="{pts}" fill="none" stroke="{color}" '
            f'stroke-width="0.15"/>')


def text(x, y, s, size=3.5, color=LABEL, anchor="middle"):
    return (f'<text x="{_f(x)}" y="{_f(y)}" font-size="{_f(size)}" '
            f'font-family="sans-serif" fill="{color}" '
            f'text-anchor="{anchor}">{s}</text>')


def svg_doc(w, h, elems):
    body = "\n".join(elems)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{_f(w)}mm" '
            f'height="{_f(h)}mm" viewBox="0 0 {_f(w)} {_f(h)}">\n'
            f"{body}\n</svg>\n")


# kerf-compensated primitives
def hole(cx, cy, dia):
    return circle(cx, cy, dia - D.KERF)


def cut_slot(x, y, w, h, rx=0.0):
    k = D.KERF
    return rect(x + k / 2, y + k / 2, w - k, h - k, rx=max(0.0, rx - k / 2))


def outer_rrect(w, h, rx):
    k = D.KERF
    return rect(-k / 2, -k / 2, w + k, h + k, rx=rx + k / 2)


class Piece:
    def __init__(self, name, w, h, mirrored=False):
        self.name, self.w, self.h, self.mirrored = name, w, h, mirrored
        self.elems: list[str] = []

    def add(self, *frags):
        self.elems.extend(frags)

    def group(self, extra_transform=""):
        t = f'translate({_f(self.w)},0) scale(-1,1)' if self.mirrored else ""
        t = f"{extra_transform} {t}".strip()
        attr = f' transform="{t}"' if t else ""
        return f"<g{attr}>\n" + "\n".join(self.elems) + "\n</g>"

    def write(self):
        path = os.path.join(OUT, f"piece-{self.name}.svg")
        with open(path, "w") as f:
            f.write(svg_doc(self.w, self.h, [self.group()]))
        return path


# ------------------------------------------------------------- layout math
def build_layout() -> SimpleNamespace:
    L = SimpleNamespace()
    T = D.THICKNESS
    L.cavity_w = 2 * D.PANEL_PCB_W + D.PANEL_GAP + 2 * D.PANEL_MARGIN
    L.cavity_h = (D.PANEL_MARGIN + D.PANEL_PCB_H + D.ZONE_GAP
                  + D.STACK_ZONE_H + D.BOTTOM_MARGIN)
    L.w = L.cavity_w + 2 * T
    L.h = L.cavity_h + 2 * T
    L.cx0, L.cy0 = T, T  # cavity origin

    # panel PCB rects (x, y, w, h), left = tens, right = ones
    p1x = L.cx0 + D.PANEL_MARGIN
    py = L.cy0 + D.PANEL_MARGIN
    p2x = p1x + D.PANEL_PCB_W + D.PANEL_GAP
    L.panels = [(p1x, py, D.PANEL_PCB_W, D.PANEL_PCB_H),
                (p2x, py, D.PANEL_PCB_W, D.PANEL_PCB_H)]

    def corners(px, pyy):
        ix, iy = D.PANEL_HOLE_INSET_X, D.PANEL_HOLE_INSET_Y
        return [(px + ix, pyy + iy),
                (px + D.PANEL_PCB_W - ix, pyy + iy),
                (px + ix, pyy + D.PANEL_PCB_H - iy),
                (px + D.PANEL_PCB_W - ix, pyy + D.PANEL_PCB_H - iy)]

    L.m3 = corners(p1x, py) + corners(p2x, py)

    def centered(px, pyy, w, h, ox, oy):
        cx = px + D.PANEL_PCB_W / 2 + ox
        cy = pyy + D.PANEL_PCB_H / 2 + oy
        return (cx - w / 2, cy - h / 2, w, h)

    ww = D.ACTIVE_W + 2 * D.WINDOW_MARGIN
    wh = D.ACTIVE_H + 2 * D.WINDOW_MARGIN
    L.windows = [centered(px, pyy, ww, wh, D.ACTIVE_OFFSET_X, D.ACTIVE_OFFSET_Y)
                 for (px, pyy, _, _) in L.panels]
    L.glass = [centered(px, pyy, D.GLASS_W, D.GLASS_H,
                        D.GLASS_OFFSET_X, D.GLASS_OFFSET_Y)
               for (px, pyy, _, _) in L.panels]
    L.active = [centered(px, pyy, D.ACTIVE_W, D.ACTIVE_H,
                         D.ACTIVE_OFFSET_X, D.ACTIVE_OFFSET_Y)
                for (px, pyy, _, _) in L.panels]

    # stack zone
    L.zone_y = py + D.PANEL_PCB_H + D.ZONE_GAP
    L.zone_cy = L.zone_y + D.STACK_ZONE_H / 2
    pix = L.cx0 + L.cavity_w - D.PI_ZONE_RIGHT - D.PI_W
    piy = L.zone_cy - D.PI_H / 2
    L.pi = (pix, piy, D.PI_W, D.PI_H)
    L.pi_c = (pix + D.PI_W / 2, piy + D.PI_H / 2)
    gx, gy = D.PI_HOLE_GRID_W / 2, D.PI_HOLE_GRID_H / 2
    L.m25 = [(L.pi_c[0] + sx * gx, L.pi_c[1] + sy * gy)
             for sx in (-1, 1) for sy in (-1, 1)]

    L.button = (L.cx0 + D.BUTTON_FROM_LEFT, L.zone_cy)
    # bottom-wall features, case x (converted to wall-local in build_wall);
    # depths are stored back-plate-relative, walls are drawn front-relative
    L.usb_x = L.pi_c[0] + D.USB_OFFSET_X
    L.led_x = L.pi_c[0] + D.LED_OFFSET_X
    L.reset_x = L.pi_c[0] + D.RESET_OFFSET_X
    L.usb_d = D.INTERNAL_DEPTH - D.USB_FROM_BACK
    L.led_d = D.INTERNAL_DEPTH - D.LED_FROM_BACK
    L.reset_d = D.INTERNAL_DEPTH - D.RESET_FROM_BACK
    # battery pouch laid flat LEFT of the Pi (short JST lead only reaches
    # that way; only when BATTERY_BESIDE_STACK)
    L.battery = (L.pi[0] - D.BATTERY_GAP - D.BATTERY_W,
                 L.zone_cy - D.BATTERY_H / 2, D.BATTERY_W, D.BATTERY_H)

    # magnets: side pairs in the panel mid-band (corner placement collides
    # with the M3 screw-head pass-throughs; mid-band keeps them clear of the
    # heads AND of the PiSugar/battery zone)
    L.magnet_y_top = D.MAGNET_INSET_Y + 13.0
    L.magnet_y_bottom = L.zone_y - D.MAGNET_DIA / 2 - 4.0
    inb = D.MAGNET_INSET_X + 12.0  # bottom pair dodges panel bottom screws
    L.magnets = [(D.MAGNET_INSET_X, L.magnet_y_top),
                 (L.w - D.MAGNET_INSET_X, L.magnet_y_top),
                 (inb, L.magnet_y_bottom),
                 (L.w - inb, L.magnet_y_bottom)]

    # walls: top/bottom span full width; sides fit between them.
    # Tabs on the BACK edge only (front plates rest on the wall edges,
    # located + clamped by the M3 stacks — no tabs through the front face).
    def tab_centers(length, end_inset):
        usable0, usable1 = end_inset, length - end_inset
        span = usable1 - usable0
        n = max(2, round(span / 70))
        return [usable0 + (i + 0.5) * span / n for i in range(n)]

    L.walls = {
        "top": {"len": L.w, "tabs": tab_centers(L.w, T + 8)},
        "bottom": {"len": L.w, "tabs": tab_centers(L.w, T + 8)},
        "left": {"len": L.h - 2 * T, "tabs": tab_centers(L.h - 2 * T, 8)},
        "right": {"len": L.h - 2 * T, "tabs": tab_centers(L.h - 2 * T, 8)},
    }
    # back-plate slot rects (plate coords) per wall
    sw = D.TAB_W + D.TAB_SLOT_CLEAR
    st = T + D.TAB_SLOT_CLEAR
    L.slots = []
    for c in L.walls["top"]["tabs"]:
        L.slots.append((c - sw / 2, T / 2 - st / 2, sw, st))
    for c in L.walls["bottom"]["tabs"]:
        L.slots.append((c - sw / 2, L.h - T / 2 - st / 2, sw, st))
    for c in L.walls["left"]["tabs"]:
        L.slots.append((T / 2 - st / 2, T + c - sw / 2, st, sw))
    for c in L.walls["right"]["tabs"]:
        L.slots.append((L.w - T / 2 - st / 2, T + c - sw / 2, st, sw))

    return L


# ------------------------------------------------------------ piece builds
def fastener_holes(piece, L, m3=True, m25=False, dia_override=None):
    if m3:
        for cx, cy in L.m3:
            piece.add(hole(cx, cy, dia_override or D.M3_CLEAR))
    if m25:
        for cx, cy in L.m25:
            piece.add(hole(cx, cy, dia_override or D.M25_CLEAR))


def build_mask_plate(L):
    p = Piece("front-mask", L.w, L.h)
    p.add(outer_rrect(L.w, L.h, D.CORNER_RADIUS))
    for x, y, w, h in L.windows:
        p.add(cut_slot(x, y, w, h, rx=1.0))
    fastener_holes(p, L)
    p.add(hole(*L.button, D.BUTTON_HOLE))
    return p


def build_cover_plate(L):
    p = Piece("front-cover", L.w, L.h)
    p.add(outer_rrect(L.w, L.h, D.CORNER_RADIUS))
    fastener_holes(p, L)
    d = D.BUTTON_HOLE if D.BUTTON_SPANS_BOTH_LAYERS else D.BUTTON_COVER_CLEAR
    p.add(hole(*L.button, d))
    return p


def build_back_plate(L):
    p = Piece("back-plate", L.w, L.h, mirrored=True)
    p.add(outer_rrect(L.w, L.h, D.CORNER_RADIUS))
    fastener_holes(p, L, m25=True)
    for x, y, w, h in L.slots:
        p.add(cut_slot(x, y, w, h))
    return p


def build_magnet_layer(L):
    p = Piece("magnet-layer", L.w, L.h, mirrored=True)
    p.add(outer_rrect(L.w, L.h, D.CORNER_RADIUS))
    for cx, cy in L.magnets:
        p.add(hole(cx, cy, D.MAGNET_DIA + D.MAGNET_POCKET_SLIP))
    # screw-head pass-throughs so back screws can live under this layer
    for cx, cy in L.m3 + L.m25:
        p.add(hole(cx, cy, D.SCREW_HEAD_CLEAR))
    return p


def build_magnet_cover(L):
    p = Piece("magnet-cover", L.w, L.h, mirrored=True)
    p.add(outer_rrect(L.w, L.h, D.CORNER_RADIUS))
    # plain clearance holes: leaves both options open at assembly — short
    # screws stopping at the back plate (heads hidden under this cover) or
    # long screws all the way through
    fastener_holes(p, L, m25=True)
    return p


def build_battery_rails(L):
    """Three strips glued to the back plate boxing the battery pouch (top,
    bottom, far side); open toward the Pi for the JST leads. Outer profiles
    drawn at target + kerf like plate outlines."""
    k = D.KERF
    long_l = D.BATTERY_W + 2 * D.CORRAL_SLACK
    short_l = D.BATTERY_H + 2 * D.CORRAL_SLACK
    sw = D.CORRAL_STRIP_W
    p = Piece("battery-rails", long_l + k, 3 * sw + 4 + k)
    for i, w in enumerate((long_l, long_l, short_l)):
        y = i * (sw + 2)
        p.add(rect(-k / 2, y - k / 2, w + k, sw + k))
    return p


def build_wall(L, name):
    T = D.THICKNESS
    length = L.walls[name]["len"]
    tabs = L.walls[name]["tabs"]
    depth = D.INTERNAL_DEPTH
    p = Piece(f"wall-{name}", length, depth + T)
    pts = [(0, 0), (length, 0), (length, depth)]
    for c in sorted(tabs, reverse=True):
        x_r, x_l = c + D.TAB_W / 2, c - D.TAB_W / 2
        pts += [(x_r, depth), (x_r, depth + T), (x_l, depth + T), (x_l, depth)]
    pts.append((0, depth))
    p.add(poly(pts))
    if name == "bottom":
        # the PiSugar's USB/button/LED edge faces this wall; local x == case
        # x (bottom wall spans full width), local y: 0 = front face of cavity
        p.add(cut_slot(L.usb_x - D.USB_CUT_W / 2,
                       L.usb_d - D.USB_CUT_H / 2,
                       D.USB_CUT_W, D.USB_CUT_H, rx=1.5))
        p.add(cut_slot(L.led_x - D.LED_SLOT_W / 2,
                       L.led_d - D.LED_SLOT_H / 2,
                       D.LED_SLOT_W, D.LED_SLOT_H, rx=D.LED_SLOT_H / 2))
        p.add(hole(L.reset_x, L.reset_d, D.RESET_PINHOLE_DIA))
    return p


# ---------------------------------------------------------------- preview
def build_preview(L, mask):
    e = list(mask.elems)
    for x, y, w, h in L.panels:
        e.append(rect(x, y, w, h, GHOST, dash=True))
    for x, y, w, h in L.glass:
        e.append(rect(x, y, w, h, GHOST, dash=True))
    for x, y, w, h in L.active:
        e.append(rect(x, y, w, h, KEEPOUT, dash=True))
    e.append(rect(*L.pi, GHOST, dash=True))
    for cx, cy in L.m25:
        e.append(circle(cx, cy, D.M25_CLEAR, GHOST, dash=True))
    e.append(circle(*L.button, D.BUTTON_BODY_DIA, KEEPOUT, dash=True))
    for cx, cy in L.magnets:
        e.append(circle(cx, cy, D.MAGNET_DIA, KEEPOUT, dash=True))
    # bottom-wall features, projected onto the wall band
    e.append(rect(L.usb_x - D.USB_CUT_W / 2, L.h - D.THICKNESS,
                  D.USB_CUT_W, D.THICKNESS, KEEPOUT, dash=True))
    e.append(rect(L.led_x - D.LED_SLOT_W / 2, L.h - D.THICKNESS,
                  D.LED_SLOT_W, D.THICKNESS, KEEPOUT, dash=True))
    e.append(circle(L.reset_x, L.h - D.THICKNESS / 2,
                    D.RESET_PINHOLE_DIA, KEEPOUT, dash=True))
    if D.BATTERY_BESIDE_STACK:
        e.append(rect(*L.battery, KEEPOUT, dash=True))
    stack_label = ("pi + pisugar" if D.BATTERY_BESIDE_STACK
                   else "pi + pisugar + battery")
    labels = [
        (L.panels[0][0] + D.PANEL_PCB_W / 2, L.panels[0][1] - 1, "tens"),
        (L.panels[1][0] + D.PANEL_PCB_W / 2, L.panels[1][1] - 1, "ones"),
        (L.pi_c[0], L.pi[1] + D.PI_H + 5, stack_label),
        (L.button[0], L.button[1] + 15, "button"),
        (L.led_x, L.h + 4, "leds"),
        (L.usb_x, L.h + 8, "usb-c"),
        (L.reset_x + 8, L.h + 4, "rst"),
    ]
    if D.BATTERY_BESIDE_STACK:
        labels.append((L.battery[0] + L.battery[2] / 2,
                       L.battery[1] + L.battery[3] / 2, "battery"))
    e += [text(x, y, s) for x, y, s in labels]
    pad = 8
    doc = (f'<g transform="translate({pad},{pad})">' + "\n".join(e) + "</g>")
    with open(os.path.join(OUT, "preview-assembly.svg"), "w") as f:
        f.write(svg_doc(L.w + 2 * pad, L.h + 2 * pad, [doc]))


# ------------------------------------------------------------ sheet packer
def pack_sheets(pieces, spacing=5.0, prefix="sheet"):
    sheets, cur, shelf_y, shelf_h, x = [], [], 0.0, 0.0, 0.0
    for p in sorted(pieces, key=lambda p: -p.h):
        w, h = p.w + spacing, p.h + spacing
        if x + w > D.SHEET_W:  # new shelf
            shelf_y += shelf_h
            x, shelf_h = 0.0, 0.0
        if shelf_y + h > D.SHEET_H:  # new sheet
            sheets.append(cur)
            cur, shelf_y, shelf_h, x = [], 0.0, 0.0, 0.0
        cur.append((p, x, shelf_y))
        x += w
        shelf_h = max(shelf_h, h)
    if cur:
        sheets.append(cur)
    import glob
    for old in glob.glob(os.path.join(OUT, f"{prefix}-*.svg")):
        os.remove(old)
    paths = []
    for i, placed in enumerate(sheets, 1):
        elems = [p.group(f"translate({_f(x)},{_f(y)})") for p, x, y in placed]
        path = os.path.join(OUT, f"{prefix}-{i}.svg")
        with open(path, "w") as f:
            f.write(svg_doc(D.SHEET_W, D.SHEET_H, elems))
        paths.append((path, [p.name for p, _, _ in placed]))
    return paths


# ---------------------------------------------------------------- checks
def run_checks(L):
    def inside(inner, outer, margin):
        ix, iy, iw, ih = inner
        ox, oy, ow, oh = outer
        return (ix >= ox + margin and iy >= oy + margin
                and ix + iw <= ox + ow - margin and iy + ih <= oy + oh - margin)

    errs = []
    for i in range(2):
        if not inside(L.windows[i], L.glass[i], 0.5):
            errs.append(f"window {i} not ≥0.5mm inside glass outline")
        if not inside(L.glass[i], L.panels[i], 0):
            errs.append(f"glass {i} overflows PCB outline")

    bx, by = L.button
    r_body = D.BUTTON_BODY_DIA / 2
    rects = [("panel0", L.panels[0]), ("panel1", L.panels[1]),
             ("pi stack", L.pi)]
    if D.BATTERY_BESIDE_STACK:
        rects.append(("battery", L.battery))
        bx0, by0, bw, bh = L.battery
        if (bx0 + bw > L.cx0 + L.cavity_w - 1 or by0 < L.zone_y + 1
                or by0 + bh > L.zone_y + D.STACK_ZONE_H - 1):
            errs.append("battery pouch leaves the stack zone")
    for name, (x, y, w, h) in rects:
        ncx = min(max(bx, x), x + w)
        ncy = min(max(by, y), y + h)
        if (bx - ncx) ** 2 + (by - ncy) ** 2 < (r_body + 1.0) ** 2:
            errs.append(f"button body keep-out hits {name}")
    if not (L.cx0 + r_body <= bx <= L.cx0 + L.cavity_w - r_body):
        errs.append("button body leaves the cavity")

    mag_r = (D.MAGNET_DIA + D.MAGNET_POCKET_SLIP) / 2
    head_r = D.SCREW_HEAD_CLEAR / 2
    for mx, my in L.magnets:
        for cx, cy in L.m3 + L.m25:
            if (mx - cx) ** 2 + (my - cy) ** 2 < (mag_r + head_r + 1.5) ** 2:
                errs.append(f"magnet at ({mx:.0f},{my:.0f}) too close to "
                            f"screw head at ({cx:.0f},{cy:.0f})")
        if not (mag_r + 2 <= mx <= L.w - mag_r - 2
                and mag_r + 2 <= my <= L.h - mag_r - 2):
            errs.append(f"magnet at ({mx:.0f},{my:.0f}) too close to edge")
        if my + mag_r > L.zone_y - 1.0:
            errs.append(f"magnet at ({mx:.0f},{my:.0f}) intrudes on the "
                        f"PiSugar/battery zone")

    # bottom-wall features must land on the strip, clear of the side walls
    T = D.THICKNESS
    for name, x, half_w, depth, half_h in [
            ("usb", L.usb_x, D.USB_CUT_W / 2, L.usb_d,
             D.USB_CUT_H / 2),
            ("led slot", L.led_x, D.LED_SLOT_W / 2, L.led_d,
             D.LED_SLOT_H / 2),
            ("reset", L.reset_x, D.RESET_PINHOLE_DIA / 2,
             L.reset_d, D.RESET_PINHOLE_DIA / 2)]:
        if not (T + 1 <= x - half_w and x + half_w <= L.w - T - 1):
            errs.append(f"bottom-wall {name} runs into a side wall")
        if not (1 <= depth - half_h and depth + half_h
                <= D.INTERNAL_DEPTH - 1):
            errs.append(f"bottom-wall {name} exceeds the strip depth")
    return errs


def main():
    os.makedirs(OUT, exist_ok=True)
    L = build_layout()
    errs = run_checks(L)
    if errs:
        for e in errs:
            print(f"CHECK FAILED: {e}", file=sys.stderr)
        sys.exit(1)

    mask = build_mask_plate(L)
    pieces = [mask, build_cover_plate(L), build_back_plate(L),
              build_magnet_layer(L), build_magnet_cover(L)]
    pieces += [build_wall(L, n) for n in ("top", "bottom", "left", "right")]
    if D.BATTERY_BESIDE_STACK:
        pieces.append(build_battery_rails(L))
    for p in pieces:
        p.write()
    build_preview(L, mask)
    # Optional piece names as CLI args pack only those onto sheet-custom-*
    # (all piece files are still written): e.g.
    #   python3 generate.py front-mask back-plate wall-{top,bottom,left,right} battery-rails
    names = set(sys.argv[1:])
    if names:
        known = {p.name for p in pieces}
        if names - known:
            print(f"unknown piece(s): {', '.join(sorted(names - known))}\n"
                  f"available: {', '.join(sorted(known))}", file=sys.stderr)
            sys.exit(1)
        sheets = pack_sheets([p for p in pieces if p.name in names],
                             prefix="sheet-custom")
    else:
        sheets = pack_sheets(pieces)

    print(f"case outline: {L.w:.1f} x {L.h:.1f} mm, "
          f"internal depth {D.INTERNAL_DEPTH:.1f} mm "
          f"(+{2 if D.FRONT_LAYERS == 2 else 1}x{D.THICKNESS} front, "
          f"+{D.THICKNESS} back, +{2 * D.THICKNESS} magnet layers)")
    print(f"windows: {L.windows[0][2]:.1f} x {L.windows[0][3]:.1f} mm each, "
          f"bezel between panels: "
          f"{L.windows[1][0] - (L.windows[0][0] + L.windows[0][2]):.1f} mm")
    print(f"pieces: {len(pieces)}  |  all checks passed")
    for path, names in sheets:
        print(f"  {os.path.basename(path)}: {', '.join(names)}")


if __name__ == "__main__":
    main()
