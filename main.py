"""One-picture summary of the world's news of Monday 23 November 2026.

Draws a newspaper front page in pure Python (standard library only):
a masthead naming the day, a lead story on the US-Iran Gulf tanker
standoff, and panels on the COP31 collapse, the Ukrainian drone strike
on a Russian warship off Libya, Jensen Huang's return as Nvidia CEO,
and BepiColombo reaching Mercury, plus a footer of the day's other
news. Writes the picture to entry.png and verifies it is a whole,
valid PNG within the competition's limits.
"""

import math
import os
import struct
import zlib

# ---------------------------------------------------------------- font --
# A 5x7 bitmap font, written here by hand. Each glyph is 7 rows of 5
# bits, '#' on, '.' off. Only capitals, digits and common punctuation
# are needed: every label in the picture is set in capitals.

FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "|": ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
}

# -------------------------------------------------------------- canvas --
# A plain RGB canvas backed by one bytearray. All drawing is done with
# row slices and scanlines, so a 1024x1024 picture renders in seconds.

PAPER = (250, 248, 240)
INK = (22, 22, 22)
NAVY = (18, 48, 84)
RED = (178, 34, 34)
SEA = (38, 110, 160)
SKY = (186, 220, 238)
SAND = (232, 214, 170)
GREEN = (34, 139, 34)
DARKGREEN = (16, 90, 40)
ORANGE = (230, 120, 20)
YELLOW = (245, 200, 40)
GREY = (120, 120, 120)
DARKGREY = (70, 70, 70)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GOLD = (212, 175, 55)


class Canvas:
    def __init__(self, width, height, background):
        self.w = width
        self.h = height
        self.buf = bytearray(bytes(background) * (width * height))

    def _idx(self, x, y):
        return (y * self.w + x) * 3

    def pixel(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = self._idx(x, y)
            self.buf[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = self._idx(x0, yy)
            self.buf[i:i + len(row)] = row

    def hline(self, x, y, w, color, thick=1):
        self.rect(x, y - thick // 2, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.rect(x - thick // 2, y, thick, h, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        # Bresenham, with a small disc stamped at each step for thickness.
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        r = max(1, thick // 2)
        while True:
            self.disc(x0, y0, r, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, color):
        if r <= 0:
            self.pixel(cx, cy, color)
            return
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(r * r - dy * dy))
            self.rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)

    def circle(self, cx, cy, r, color, thick=3):
        # Outline circle: stamp discs along the circumference.
        steps = max(24, int(2 * math.pi * r))
        for i in range(steps):
            a = 2 * math.pi * i / steps
            self.disc(int(cx + r * math.cos(a)), int(cy + r * math.sin(a)),
                      max(1, thick // 2), color)

    def polygon(self, points, color):
        # Even-odd scanline fill.
        if len(points) < 3:
            return
        ys = [p[1] for p in points]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                xa = max(0, int(math.ceil(xs[i])))
                xb = min(self.w - 1, int(math.floor(xs[i + 1])))
                if xb >= xa:
                    self.rect(xa, y, xb - xa + 1, 1, color)

    def starburst(self, cx, cy, r_out, r_in, spikes, color):
        pts = []
        for i in range(spikes * 2):
            a = math.pi * i / spikes - math.pi / 2
            r = r_out if i % 2 == 0 else r_in
            pts.append((int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
        self.polygon(pts, color)

    # ------------------------------------------------------------ text --
    def text_width(self, s, scale):
        return len(s) * 6 * scale - scale

    def draw_text(self, x, y, s, scale, color):
        s = s.upper()
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx

    def text_centered(self, y, s, scale, color, cx=None, width=None):
        if cx is None:
            cx = self.w // 2
        if width is None:
            width = self.w
        w = self.text_width(s, scale)
        self.draw_text(cx - w // 2, y, s, scale, color)

    def wrap(self, s, max_width, scale):
        words = s.split(" ")
        lines = []
        cur = ""
        for word in words:
            trial = (cur + " " + word).strip()
            if self.text_width(trial, scale) <= max_width or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines


def encode_png(canvas):
    """Encode the canvas as a deterministic PNG (no ancillary chunks)."""
    w, h = canvas.w, canvas.h
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)  # filter: None
        raw += canvas.buf[y * stride:(y + 1) * stride]
    compressed = zlib.compress(bytes(raw), 9)

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", compressed)
    png += chunk(b"IEND", b"")
    return png


def check_png(data):
    """Fail loudly unless data is one whole valid PNG within the limits."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    if len(data) > 1048576:
        raise ValueError("PNG over 1 MiB: %d bytes" % len(data))
    pos = 8
    saw_iend = False
    width = height = None
    while pos < len(data):
        if pos + 8 > len(data):
            raise ValueError("truncated PNG chunk header")
        size = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        if pos + 12 + size > len(data):
            raise ValueError("truncated PNG chunk %r" % kind)
        body = data[pos + 8:pos + 8 + size]
        crc = struct.unpack(">I", data[pos + 8 + size:pos + 12 + size])[0]
        if zlib.crc32(kind + body) & 0xFFFFFFFF != crc:
            raise ValueError("bad CRC in PNG chunk %r" % kind)
        if kind == b"IHDR":
            width, height = struct.unpack(">II", body[:8])
            if width > 1024 or height > 1024:
                raise ValueError("PNG over 1024x1024: %dx%d" % (width, height))
        if kind == b"IEND":
            saw_iend = True
            pos += 12 + size
            break
        pos += 12 + size
    if not saw_iend:
        raise ValueError("PNG has no IEND")
    if pos != len(data):
        raise ValueError("trailing bytes after PNG IEND")
    return width, height


# -------------------------------------------------------------- scenes --
# Each scene is drawn flat and bold: the judge sees the picture at
# about 300 pixels across, so big shapes and short labels win over
# fine detail. Every scene is drawn from scratch here.

def scene_tanker(c, x, y, w, h):
    """Lead story: a tanker on the sea under a burst of fire."""
    c.rect(x, y, w, h, SKY)
    c.rect(x, y + h * 3 // 5, w, h * 2 // 5, SEA)
    # Sun glint on the water.
    c.rect(x + w // 8, y + h * 3 // 5 + 8, w // 4, 3, WHITE)
    c.rect(x + w // 2, y + h * 3 // 5 + 22, w // 5, 3, WHITE)
    # Warship silhouette, far right.
    wx, wy = x + w - 150, y + h * 3 // 5 - 6
    c.polygon([(wx, wy + 26), (wx + 130, wy + 26), (wx + 118, wy + 6),
               (wx + 92, wy + 6), (wx + 88, wy - 18), (wx + 78, wy - 18),
               (wx + 74, wy + 6), (wx + 20, wy + 6), (wx + 8, wy + 26)],
              DARKGREY)
    c.rect(wx + 40, wy - 30, 6, 14, DARKGREY)
    # The tanker, centre-left.
    tx, ty = x + 40, y + h * 3 // 5 - 34
    c.rect(tx, ty, 330, 34, (30, 30, 30))          # hull
    c.rect(tx, ty + 26, 330, 8, RED)               # waterline stripe
    c.rect(tx + 30, ty - 34, 70, 34, WHITE)        # superstructure
    c.rect(tx + 44, ty - 26, 42, 8, INK)
    c.rect(tx + 240, ty - 24, 26, 24, (200, 60, 40))  # funnel
    c.rect(tx + 240, ty - 30, 26, 6, INK)
    # Explosion above the tanker.
    c.starburst(tx + 200, ty - 50, 46, 22, 10, ORANGE)
    c.starburst(tx + 200, ty - 50, 30, 14, 10, YELLOW)
    c.disc(tx + 200, ty - 50, 11, WHITE)
    # Smoke.
    c.disc(tx + 130, ty - 66, 15, GREY)
    c.disc(tx + 155, ty - 74, 18, GREY)
    c.disc(tx + 185, ty - 68, 13, GREY)


def scene_globe(c, x, y, w, h):
    """COP31: a globe with a crack through it."""
    c.rect(x, y, w, h, (214, 232, 216))
    cx, cy, r = x + w // 2, y + h // 2 - 6, 78
    c.disc(cx, cy, r, (120, 190, 230))
    c.circle(cx, cy, r, NAVY, 5)
    # Land masses: rough green blobs.
    c.disc(cx - 34, cy - 26, 22, GREEN)
    c.disc(cx - 14, cy - 34, 16, GREEN)
    c.disc(cx + 30, cy + 6, 24, GREEN)
    c.disc(cx + 44, cy + 26, 14, GREEN)
    c.disc(cx - 40, cy + 30, 14, GREEN)
    # The crack: a red zigzag splitting the globe.
    c.line(cx - 52, cy - 62, cx - 18, cy - 14, RED, 7)
    c.line(cx - 18, cy - 14, cx + 8, cy + 18, RED, 7)
    c.line(cx + 8, cy + 18, cx + 40, cy + 62, RED, 7)
    # A fallen leaf at the base.
    c.polygon([(cx - 8, y + h - 26), (cx + 8, y + h - 26),
               (cx + 2, y + h - 6), (cx - 14, y + h - 6)], DARKGREEN)


def scene_drone_ship(c, x, y, w, h):
    """Ukraine: a drone above a stricken ship at night."""
    c.rect(x, y, w, h, (24, 32, 54))
    # Stars.
    for sx, sy in [(30, 20), (90, 44), (160, 16), (230, 36), (290, 18),
                   (60, 70), (200, 64), (270, 76)]:
        c.disc(x + sx, y + sy, 2, WHITE)
    c.rect(x, y + h * 2 // 3, w, h // 3, (16, 44, 66))
    # The ship, burning.
    sx, sy = x + 40, y + h * 2 // 3 - 8
    c.polygon([(sx, sy + 24), (sx + 210, sy + 24), (sx + 196, sy + 4),
               (sx + 150, sy + 4), (sx + 146, sy - 16), (sx + 136, sy - 16),
               (sx + 132, sy + 4), (sx + 30, sy + 4), (sx + 14, sy + 24)],
              DARKGREY)
    c.starburst(sx + 120, sy - 30, 40, 18, 9, ORANGE)
    c.starburst(sx + 120, sy - 30, 26, 12, 9, YELLOW)
    c.disc(sx + 60, sy - 44, 12, GREY)
    c.disc(sx + 80, sy - 56, 16, GREY)
    # The drone, top right: light body so it reads against the night.
    dx, dy = x + w - 90, y + 44
    c.rect(dx - 22, dy - 8, 44, 16, (190, 190, 190))
    c.disc(dx - 30, dy - 12, 10, GREY)
    c.disc(dx + 30, dy - 12, 10, GREY)
    c.line(dx - 30, dy - 12, dx - 22, dy - 6, (190, 190, 190), 3)
    c.line(dx + 30, dy - 12, dx + 22, dy - 6, (190, 190, 190), 3)
    c.disc(dx, dy + 4, 4, RED)


def scene_chip(c, x, y, w, h):
    """Nvidia: a chip on the left, a rising arrow on the right."""
    c.rect(x, y, w, h, (226, 240, 224))
    # The chip, left of centre: sized to fit the 150px scene.
    cx, cy = x + 36, y + 14
    c.rect(cx - 34, cy, 116, 116, DARKGREEN)
    # Pins: short bars around the chip's edges, outside its body.
    for px in range(5):
        c.rect(cx + 2 + px * 22, cy - 12, 8, 12, GOLD)
        c.rect(cx + 2 + px * 22, cy + 116, 8, 12, GOLD)
    for py in range(5):
        c.rect(cx - 12, cy + 2 + py * 22, 12, 8, GOLD)
        c.rect(cx + 116, cy + 2 + py * 22, 12, 8, GOLD)
    c.rect(cx - 22, cy + 12, 92, 92, GREEN)
    c.draw_text(cx + 6, cy + 44, "NVDA", 2, WHITE)
    # The rising arrow: a thick diagonal shaft and a triangle head.
    ax0, ay0 = x + w - 128, y + h - 34
    ax1, ay1 = x + w - 30, y + 30
    c.line(ax0, ay0, ax1, ay1, GREEN, 14)
    c.polygon([(ax1 - 34, ay1 - 2), (ax1 + 6, ay1 - 34),
               (ax1 + 22, ay1 + 6)], GREEN)


def scene_mercury(c, x, y, w, h):
    """BepiColombo: a cratered planet and its probe."""
    c.rect(x, y, w, h, BLACK)
    for sx, sy in [(24, 18), (70, 52), (150, 14), (230, 40), (290, 22),
                   (40, 96), (120, 84), (200, 100), (260, 92),
                   (16, 140), (300, 140)]:
        c.disc(x + sx, y + sy, 2, WHITE)
    cx, cy, r = x + w // 2, y + h // 2 + 8, 74
    c.disc(cx, cy, r, (150, 140, 130))
    c.circle(cx, cy, r, (110, 100, 90), 4)
    for ox, oy, orr in [(-30, -20, 12), (18, -34, 9), (34, 10, 14),
                        (-6, 26, 10), (-44, 18, 7), (8, -6, 6)]:
        c.disc(cx + ox, cy + oy, orr, (120, 110, 100))
        c.disc(cx + ox - 2, cy + oy - 2, max(2, orr - 3), (165, 155, 145))
    # The probe, top right.
    px, py = x + w - 96, y + 34
    c.rect(px, py, 34, 20, (200, 200, 200))
    c.rect(px - 26, py + 4, 22, 12, (90, 120, 200))
    c.rect(px + 38, py + 4, 22, 12, (90, 120, 200))
    c.line(px + 6, py + 20, px + 14, py + 40, (200, 200, 200), 3)


# -------------------------------------------------------------- layout --
def panel(c, x, y, w, h, kicker, headline, sub, scene=None):
    c.rect(x, y, w, h, PAPER)
    c.rect(x, y, w, 3, INK)
    c.rect(x, y, 3, h, INK)
    c.rect(x + w - 3, y, 3, h, INK)
    c.rect(x, y + h - 3, w, 3, INK)
    inner_x = x + 14
    inner_w = w - 28
    cy = y + 12
    c.draw_text(inner_x, cy, kicker, 2, RED)
    cy += 24
    if scene is not None:
        sh = 150 if h < 400 else 190
        scene(c, inner_x, cy, inner_w, sh)
        cy += sh + 12
    else:
        cy += 4
    for line in c.wrap(headline, inner_w, 3):
        if cy + 21 > y + h - 8:
            break
        c.draw_text(inner_x, cy, line, 3, INK)
        cy += 30
    cy += 4
    for line in c.wrap(sub, inner_w, 2):
        if cy + 14 > y + h - 8:
            break
        c.draw_text(inner_x, cy, line, 2, INK)
        cy += 16


def build():
    c = Canvas(1024, 1024, PAPER)
    # Masthead.
    c.rect(0, 0, 1024, 122, NAVY)
    c.text_centered(14, "THE WORLD IN ONE PICTURE", 2, WHITE)
    c.text_centered(44, "MONDAY 23 NOVEMBER 2026", 6, WHITE)
    c.rect(0, 122, 1024, 6, RED)
    c.text_centered(136, "FIVE STORIES THAT DEFINED THE DAY", 2, INK)

    # Lead story: the Gulf tanker standoff.
    panel(c, 16, 164, 612, 330, "LEAD STORY",
          "U.S. STRIKES IRANIAN OIL TANKER",
          "Trump warns Tehran: any vessel testing the blockade "
          "will be sunk. 31 tankers already past Hormuz.",
          scene_tanker)
    # COP31.
    panel(c, 644, 164, 364, 330, "CLIMATE",
          "CLIMATE TALKS END WITH NO DEAL",
          "COP31 in Antalya collapses after record overtime. "
          "No fossil-fuel phase-out agreed.",
          scene_globe)

    # Second row: Ukraine, Nvidia, Mercury.
    panel(c, 16, 510, 328, 348, "WAR IN UKRAINE",
          "DRONE HITS RUSSIAN SHIP OFF LIBYA",
          "Zelensky confirms the strike. 15 killed near Kyiv.",
          scene_drone_ship)
    panel(c, 356, 510, 328, 348, "TECH",
          "HUANG BACK AS NVIDIA CHIEF",
          "Shares jump 31% as Jensen Huang is reinstated "
          "as chief executive.",
          scene_chip)
    panel(c, 696, 510, 312, 348, "SPACE",
          "PROBE REACHES MERCURY AFTER 8 YEARS",
          "BepiColombo enters orbit after 8 years.",
          scene_mercury)

    # Footer: the rest of the day.
    c.rect(16, 874, 992, 3, INK)
    c.draw_text(16, 890, "ALSO TODAY", 2, RED)
    footer = ("AI 'PROVES' THE RIEMANN HYPOTHESIS  |  DEADLY FIRE AT "
              "INDONESIAN SWEETS FACTORY, DOZENS MISSING  |  DRONES HIT "
              "HOMES AND A UN BUILDING IN KHARTOUM  |  DEMOCRATS TAKE "
              "BIGGEST HOUSE MAJORITY SINCE 1992")
    cy = 916
    for line in c.wrap(footer, 992, 2):
        c.draw_text(16, cy, line, 2, INK)
        cy += 16
    return c


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    data = encode_png(build())
    with open(path, "wb") as f:
        f.write(data)
    os.chmod(path, 0o644)
    # Read it back: a broken image must fail loudly here, not sail
    # through to judging with the wrong contents.
    with open(path, "rb") as f:
        written = f.read()
    if written != data:
        raise ValueError("entry.png read back differs from what was written")
    width, height = check_png(written)
    print("entry.png: %dx%d, %d bytes" % (width, height, len(written)))


if __name__ == "__main__":
    main()
