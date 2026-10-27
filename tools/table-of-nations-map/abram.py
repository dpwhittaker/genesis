"""Draw the Session 12 map: Abram's road, Ur to the Negev (Genesis 11:31-12:9).

    ~/ml-env/bin/python abram.py   ->  ../../sessions/12-call-of-abram/abrams-road.svg

One printed page, two panels: the whole road on top; the land (12:6-9) below,
with the key beside it. The thread the map carries is the handout's: God says
"I will show you" at Haran (12:1) and "appeared" at Shechem (12:7), and the
road between them is the gap. Same base layers and style as the Session 11
maps (build_map.py, basemap.py): Natural Earth coastlines and rivers, and
Koppen-Geiger green. Places and their sources: the Session 12 sheet
"Abram's road on the ground".
"""
import math, os
from basemap import Albers, Frame, load, lines, simplify, watered
from build_map import basemap, layer, text, SEA, SERIF, WATER_TEXT

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '..', 'sessions', '12-call-of-abram', 'abrams-road.svg')

ROAD, TERAH, SPEAK, LATER, INK, GREY = '#9a3412', '#7c7c7c', '#b7791f', '#2f5d8a', '#222', '#555'
W = 860                      # page width in SVG units (7.5 in on paper)

# --- places (lon, lat), from Pleiades; identifications and sources on the sheet --
UR, HARRAN = (46.1054, 30.9613), (39.0307, 36.8636)
RAQQA = (39.0472, 35.9581)              # Tuttul, at the mouth of the Balikh
SHECHEM, BETHEL, AI = (35.2821, 32.2135), (35.2383, 31.9283), (35.2616, 31.9167)
JERUSALEM, HEBRON, BEERSHEBA = (35.2350, 31.7772), (35.1022, 31.5248), (34.8408, 31.2452)
TIRZAH, BETHSHEAN = (35.3379, 32.2872), (35.5031, 32.5037)

def euphrates_up(start, end):
    """The Euphrates centerline (Natural Earth), from the point nearest `start`
    upstream to the point nearest `end`."""
    segs = {}
    for f in load('ne_10m_rivers_lake_centerlines')['features']:
        if f['properties'].get('name') in ('Euphrates', 'Al Furat'):
            for ln in lines(f['geometry']):
                segs[(round(ln[0][0], 2), round(ln[0][1], 2))] = ln
    pts, key = [], (38.56, 35.86)        # chain downstream from the Tabqa lake outlet
    while key in segs:
        ln = segs.pop(key)
        pts += ln if not pts else ln[1:]
        key = (round(ln[-1][0], 2), round(ln[-1][1], 2))
    near = lambda p: min(range(len(pts)), key=lambda i: (pts[i][0]-p[0])**2 + (pts[i][1]-p[1])**2)
    a, b = near(start), near(end)
    return [tuple(p) for p in pts[b:a + 1][::-1]]

# Terah's road is drawn along the (modern) river; its length is measured along
# the usual waypoints: Uruk, Babylon, Sippar, Hit, Anat, Mari, Terqa, the
# Zenobia bend, Tuttul.
TERAH_ROUTE = [UR] + euphrates_up(UR, RAQQA) + [(39.06, 36.25), (39.08, 36.55), HARRAN]
TERAH_WAYPOINTS = [UR, (45.6391, 31.3234), (44.4250, 32.5373), (44.2542, 33.0597),
                   (42.8215, 33.6436), (41.9727, 34.4620), (40.8886, 34.5503),
                   (40.5682, 34.9224), (39.8216, 35.6893), RAQQA, HARRAN]
# Haran to Shechem: Carchemish ford, Aleppo, Ebla, Hamath, Qatna, Damascus, Hazor,
# Beth-shean, Tirzah. Genesis names none of these, so the line is dashed.
ABRAM_ROUTE = [HARRAN, (38.0149, 36.8294), (37.1629, 36.1994), (36.7983, 35.7990),
               (36.7488, 35.1330), (36.8663, 34.8347), (36.3091, 33.5116),
               (35.5668, 33.0192), BETHSHEAN, TIRZAH, SHECHEM]
# In the land: the ridge road, Shechem, Shiloh, the camp between Bethel and Ai,
# Jerusalem, Bethlehem, Hebron, Beersheba, and on south.
CAMP = (35.250, 31.922)
LAND_ROUTE = [SHECHEM, (35.2983, 32.0538), CAMP, JERUSALEM, (35.2032, 31.7070), HEBRON,
              BEERSHEBA, (34.80, 31.03)]

def gc_miles(pts):
    R, tot = 3958.8, 0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        p1, p2, dl = math.radians(y1), math.radians(y2), math.radians(x2 - x1)
        tot += R * math.acos(min(1, math.sin(p1)*math.sin(p2) + math.cos(p1)*math.cos(p2)*math.cos(dl)))
    return tot

def walked(pts, tol=0.1):
    """Miles along a route with the river's small meanders cut off (~10 km)."""
    c = lambda y: math.cos(math.radians(y))
    s = simplify([(x * c(y), y) for x, y in pts], tol)
    return gc_miles([(x / c(y), y) for x, y in s])

r50 = lambda m: 50 * round(m / 50)
MILES = {'ur': r50(gc_miles(TERAH_WAYPOINTS)), 'haran': r50(gc_miles(ABRAM_ROUTE)),
         'bethel': round(gc_miles(LAND_ROUTE[:3]), -1), 'negev': round(gc_miles(LAND_ROUTE[2:]), -1)}

# --- drawing helpers ------------------------------------------------------------
def poly(fr, pts):
    return 'M' + ' L'.join('%.1f,%.1f' % fr(*p) for p in pts)

def star(x, y, r, color=SPEAK):
    """A four-pointed star: where God speaks."""
    pts = []
    for i in range(8):
        a = math.pi / 4 * i - math.pi / 2
        rr = r if i % 2 == 0 else r * 0.38
        pts.append(f'{x + rr*math.cos(a):.1f},{y + rr*math.sin(a):.1f}')
    return f'<polygon points="{" ".join(pts)}" fill="{color}" stroke="#fffdf6" stroke-width="1"/>'

def altar(x, y, s, color=ROAD):
    """A small stepped stone altar."""
    return (f'<g fill="{color}" stroke="#fffdf6" stroke-width="0.8">'
            f'<rect x="{x - s:.1f}" y="{y - s*0.55:.1f}" width="{2*s:.1f}" height="{s*1.1:.1f}"/>'
            f'<rect x="{x - s*1.35:.1f}" y="{y + s*0.55:.1f}" width="{2.7*s:.1f}" height="{s*0.6:.1f}"/></g>')

def tent(x, y, s, color=ROAD):
    return (f'<path d="M{x - s*1.3:.1f},{y + s:.1f} L{x:.1f},{y - s:.1f} L{x + s*1.3:.1f},{y + s:.1f} Z" '
            f'fill="{color}" stroke="#fffdf6" stroke-width="0.8"/>')

def dot(x, y, r, color):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{color}" stroke="#fffdf6" stroke-width="1"/>'

def stack(x, y, rows, anchor='start', lh=1.2):
    """rows: (string, size, color, italic, bold), stacked downward from y."""
    out = ''
    for s, size, color, italic, bold in rows:
        out += text(x, y, s, size, color, anchor, italic=italic, weight='bold' if bold else 'normal')
        y += size * lh
    return out

def arrows(fr, pts, every, color, size):
    """Chevrons along a route, pointing the way it runs."""
    px = [fr(*p) for p in pts]
    out, acc, nxt = '', 0.0, every * 0.5
    for (x1, y1), (x2, y2) in zip(px, px[1:]):
        L = math.hypot(x2 - x1, y2 - y1)
        while L and acc + L >= nxt:
            t = (nxt - acc) / L
            x, y = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
            ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
            out += (f'<path d="M{-size:.1f},{-size*0.8:.1f} L{size*0.6:.1f},0 L{-size:.1f},{size*0.8:.1f}" '
                    f'fill="none" stroke="{color}" stroke-width="{size*0.45:.1f}" stroke-linejoin="round" '
                    f'transform="translate({x:.1f} {y:.1f}) rotate({ang:.1f})"/>')
            nxt += every
        acc += L
    return out

def line(fr, pts, color, width, dash=None, opacity=1):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return (f'<path d="{poly(fr, pts)}" fill="none" stroke="{color}" stroke-width="{width}"{d} '
            f'stroke-linecap="round" stroke-linejoin="round" opacity="{opacity}"/>')

def panel(box, width, center, extra, tol, sw, step, sigma, valleys, uid):
    """A frame and its base layers. Both panels share one SVG, so each gets its
    own clip ids."""
    proj = Albers(center[0], center[1] - 4, center[1] - 4, center[1] + 4)
    fr = Frame(box, width, proj, *center)
    land, lakes, rivers = basemap(fr, box, extra=extra, tol=tol)
    clip = (box[0] - extra, box[1] - 6, box[2] + extra, box[3] + 4)
    green = watered(fr, clip, step, sigma, tol, valleys=valleys)
    svg = layer(land, lakes, rivers, green, sw=sw)
    for a, b in (('id="land"', f'id="land{uid}"'), ('href="#land"', f'href="#land{uid}"'),
                 ('id="landclip"', f'id="landclip{uid}"'), ('url(#landclip)', f'url(#landclip{uid})')):
        svg = svg.replace(a, b)
    return fr, f'<rect width="{width}" height="{fr.height:.0f}" fill="{SEA}"/>' + svg

def nest(x, y, w, h, body):
    return (f'<svg x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}">'
            f'{body}<rect x="0.75" y="0.75" width="{w-1.5:.1f}" height="{h-1.5:.1f}" fill="none" '
            f'stroke="#555" stroke-width="1.5"/></svg>')

# --- panel A: the whole road -----------------------------------------------------
LAND_BOX = (34.3, 30.95, 36.0, 32.42)

def road_panel():
    box = (33.2, 30.3, 48.6, 37.65)
    fr, out = panel(box, W, (40.9, 34.1), 10, 0.45, 1.1, 0.05, 1.0, True, 'A')
    out = [out]
    P = lambda p: fr(*p)
    out.append(line(fr, TERAH_ROUTE, TERAH, 2.4, '7 4'))
    out.append(arrows(fr, TERAH_ROUTE, 125, TERAH, 4.4))
    out.append(line(fr, ABRAM_ROUTE, ROAD, 3.2, '9 5'))
    out.append(line(fr, LAND_ROUTE, ROAD, 3.2))
    out.append(arrows(fr, ABRAM_ROUTE, 95, ROAD, 4.8))
    out.append(line(fr, [LAND_ROUTE[-1], (34.3, 30.9), (33.6, 30.86), (32.367, 30.8496)], ROAD,
                    1.8, '2 4', 0.85))
    # the land panel's outline
    corners = [(LAND_BOX[0], LAND_BOX[1]), (LAND_BOX[2], LAND_BOX[1]),
               (LAND_BOX[2], LAND_BOX[3]), (LAND_BOX[0], LAND_BOX[3])]
    out.append(f'<polygon points="{" ".join("%.1f,%.1f" % P(c) for c in corners)}" fill="none" '
               f'stroke="#444" stroke-width="1" stroke-dasharray="3 2"/>')

    for name, p, dx, dy, anchor in [('Babylon', (44.4250, 32.5373), 8, 15, 'start'),
                                    ('Mari', (40.8886, 34.5503), 6, 17, 'start'),
                                    ('Aleppo', (37.1629, 36.1994), -8, 5, 'end'),
                                    ('Hamath', (36.7488, 35.1330), -8, 5, 'end'),
                                    ('Damascus', (36.3091, 33.5116), 9, 5, 'start')]:
        x, y = P(p)
        out.append(dot(x, y, 3.4, '#6b6b6b'))
        out.append(text(x + dx, y + dy, name, 14, GREY, anchor))

    out.append(text(*fr(34.15, 33.6), 'THE GREAT SEA', 15, WATER_TEXT, 'middle', italic=True,
                    halo=False, spacing=1.5, rotate=-80))
    out.append(text(W - 10, fr.height - 12, 'THE GULF', 13, WATER_TEXT, 'end', italic=True,
                    halo=False, spacing=1))
    out.append(text(*fr(41.7, 34.05), 'Euphrates', 14, WATER_TEXT, 'middle', italic=True,
                    halo=False, rotate=-12))
    out.append(text(*fr(44.25, 34.95), 'Tigris', 14, WATER_TEXT, 'middle', italic=True,
                    halo=False, rotate=-52))
    out.append(text(*fr(39.6, 32.0), 'SYRIAN DESERT', 14, '#a39a86', 'middle', italic=True,
                    halo=False, spacing=3))

    # Ur, and Terah's leg
    x, y = P(UR)
    out.append(dot(x, y, 5.5, INK))
    out.append(stack(x + 10, y - 30, [('Ur', 19, INK, False, True),
                                       ('of the Chaldeans', 13, INK, True, False),
                                       ('a city of the', 12, GREY, True, False),
                                       ('moon god', 12, GREY, True, False)]))
    x, y = fr(44.75, 33.75)
    out.append(stack(x, y, [('They set out “to go to the', 13, '#444', True, False),
                            ('land of Canaan. When they', 13, '#444', True, False),
                            ('came to Haran, they settled', 13, '#444', True, False),
                            ('there” (11:31)', 13, '#444', True, False),
                            (f'about {MILES["ur"]:.0f} miles', 13, GREY, False, True)]))
    # Haran
    x, y = P(HARRAN)
    out.append(dot(x, y, 5.5, INK))
    out.append(star(x + 14, y - 13, 10))
    out.append(stack(x + 30, y - 18, [('Haran', 19, INK, False, True),
                                       ('also a city of the moon god', 12, GREY, True, False)]))
    out.append(stack(x + 12, y + 30, [('“Go… to the land that', 15, INK, True, True),
                                       ('I will show you” (12:1)', 15, INK, True, True)]))
    # the gap
    x, y = fr(37.45, 34.75)
    out.append(stack(x, y, [(f'about {MILES["haran"]:.0f} miles', 16, ROAD, False, True),
                            ('between “I will show you”', 14, ROAD, True, False),
                            ('and “the LORD appeared”', 14, ROAD, True, False)]))
    # Shechem
    x, y = P(SHECHEM)
    out.append(dot(x, y, 5.5, INK))
    out.append(star(x - 14, y - 13, 10))
    out.append(text(x - 30, y - 18, 'Shechem', 19, INK, 'end', weight='bold'))
    out.append(stack(x + 14, y + 24, [('“The LORD', 15, INK, True, True),
                                       ('appeared” (12:7)', 15, INK, True, True)]))
    x, y = fr(35.55, 30.85)
    out.append(text(x, y, 'NEGEV', 13, ROAD, 'start', weight='bold', spacing=1.5))
    x, y = fr(33.62, 31.12)
    out.append(stack(x, y, [('to Egypt', 12, GREY, True, False), ('(12:10)', 12, GREY, True, False)]))
    return fr.height, ''.join(out)

# --- panel B: the land, 12:6-9 ---------------------------------------------------
def land_panel(width):
    fr, out = panel(LAND_BOX, width, (35.15, 31.7), 2.5, 0.3, 1.3, 1/120, 1.5, False, 'B')
    out = [out]
    P = lambda p: fr(*p)
    out.append(line(fr, [(35.62, 32.62), BETHSHEAN, TIRZAH, SHECHEM], ROAD, 3.6, '10 6'))
    out.append(line(fr, LAND_ROUTE, ROAD, 3.6))
    out.append(arrows(fr, LAND_ROUTE, 72, ROAD, 5.2))

    for name, p, dx, dy, anchor in [('Jerusalem', JERUSALEM, 9, 5, 'start'),
                                    ('Hebron', HEBRON, 9, 5, 'start'),
                                    ('Beersheba', BEERSHEBA, -9, 5, 'end')]:
        x, y = P(p)
        out.append(dot(x, y, 3.4, '#6b6b6b'))
        out.append(text(x + dx, y + dy, name, 14, GREY, anchor))

    x, y = P(SHECHEM)
    out.append(dot(x, y, 5.5, INK))
    out.append(star(x + 15, y - 9, 10))
    out.append(altar(x + 15, y + 13, 6))
    out.append(stack(x - 11, y - 12, [('Shechem', 19, INK, False, True),
                                       ('the oak of Moreh', 14, INK, True, False)], anchor='end'))
    out.append(stack(x + 30, y - 4, [('“The LORD appeared”;', 14, INK, True, False),
                                      ('an altar (12:6–7)', 14, INK, True, False)]))
    out.append(stack(x - 11, y + 24, [('later: Jacob’s altar (33:20),', 13, LATER, True, False),
                                       ('Joshua’s covenant (Josh 24),', 13, LATER, True, False),
                                       ('Joseph’s grave (Josh 24:32)', 13, LATER, True, False)],
                     anchor='end'))
    xb, yb = P(BETHEL); xa, ya = P(AI)
    out.append(dot(xb, yb, 4.5, INK)); out.append(dot(xa, ya, 4.5, INK))
    out.append(tent((xb + xa) / 2 + 4, yb - 15, 6.5))
    out.append(altar((xb + xa) / 2 + 21, yb - 14, 6))
    out.append(text(xb - 9, yb + 3, 'Bethel', 17, INK, 'end', weight='bold'))
    out.append(text(xa + 10, ya + 16, 'Ai', 17, INK, 'start', weight='bold'))
    out.append(stack(xa + 36, ya - 16, [('a tent and an altar;', 14, INK, True, False),
                                         ('he “called on the name', 14, INK, True, False),
                                         ('of the LORD” (12:8)', 14, INK, True, False)]))
    out.append(stack(xb - 9, yb + 22, [('later: Jacob’s dream', 13, LATER, True, False),
                                        ('at Bethel (28:19);', 13, LATER, True, False),
                                        ('Joshua at Ai (Josh 7–8)', 13, LATER, True, False)], anchor='end'))
    x, y = fr(34.9, 31.16)
    out.append(stack(x, y, [('THE NEGEV', 15, ROAD, False, True),
                            ('he “journeyed by stages”', 13.5, INK, True, False),
                            ('toward it (12:9)', 13.5, INK, True, False)]))
    out.append(text(*fr(34.55, 31.9), 'THE GREAT SEA', 13, WATER_TEXT, 'middle', italic=True,
                    halo=False, spacing=1.2, rotate=-66))
    out.append(text(*fr(35.62, 31.47), 'Dead Sea', 12.5, WATER_TEXT, 'middle', italic=True,
                    halo=False, rotate=-80))
    return fr.height, ''.join(out)

# --- the key ----------------------------------------------------------------------------
def key(w):
    rows = [('title', 'Abram’s road'), ('sub', 'Genesis 11:31–12:9'), ('gap', ''),
            ('terah', 'Terah’s family, Ur to Haran (11:31)'),
            ('abramd', 'Abram, Haran to Shechem (12:4–6)'),
            ('abram', 'Abram in the land (12:6–9)'),
            ('star', 'God speaks (12:1, 7)'), ('altar', 'an altar (12:7, 8)'), ('tent', 'a tent (12:8)'),
            ('later', 'later on the same ground'),
            ('green', 'fertile land, watered by rain or river'), ('gap', ''),
            ('head', 'On foot, roughly'),
            ('leg', f'Ur to Haran|about {MILES["ur"]:.0f} miles'),
            ('leg', f'Haran to Shechem|about {MILES["haran"]:.0f} miles'),
            ('leg', f'Shechem to Bethel and Ai|about {MILES["bethel"]:.0f} miles'),
            ('leg', f'Bethel to the Negev|about {MILES["negev"]:.0f} miles'), ('gap', ''),
            ('note', 'Genesis names no stop between Haran and Shechem;'),
            ('note', 'the dashed road follows the main route. Places:'),
            ('note', 'Pleiades (CC BY); climate zones: Beck et al. 2023'),
            ('note', '(CC BY 4.0); coastlines and rivers are modern.')]
    g, y = [], 4
    for kind, s in rows:
        y += {'gap': 8, 'note': 18, 'sub': 20, 'leg': 21, 'head': 22}.get(kind, 24)
        if kind == 'title':
            g.append(text(14, y + 4, s, 24, INK, weight='bold', halo=False)); y += 6
        elif kind == 'sub':
            g.append(text(14, y, s, 15, '#444', italic=True, halo=False))
        elif kind == 'head':
            g.append(text(14, y, s, 15, INK, weight='bold', halo=False))
        elif kind == 'leg':
            a_, b_ = s.split('|')
            g.append(text(14, y, a_, 14.5, INK, halo=False))
            g.append(text(w - 14, y, b_, 14.5, INK, 'end', halo=False))
        elif kind == 'note':
            g.append(text(14, y, s, 13, GREY, italic=True, halo=False))
        elif kind != 'gap':
            sx, sy = 27, y - 5
            g.append({'terah': f'<path d="M12,{sy} L42,{sy}" stroke="{TERAH}" stroke-width="2.4" stroke-dasharray="7 4"/>',
                      'abram': f'<path d="M12,{sy} L42,{sy}" stroke="{ROAD}" stroke-width="3.2"/>',
                      'abramd': f'<path d="M12,{sy} L42,{sy}" stroke="{ROAD}" stroke-width="3.2" stroke-dasharray="9 5"/>',
                      'star': star(sx, sy, 9), 'altar': altar(sx, sy, 6), 'tent': tent(sx, sy, 6.5),
                      'later': text(sx, sy + 5, 'Aa', 14, LATER, 'middle', italic=True, halo=False),
                      'green': f'<rect x="18" y="{sy - 8}" width="18" height="15" fill="#dfe9c9" '
                               f'stroke="#9fb0ba" stroke-width="0.8"/>'}[kind])
            g.append(text(54, y, s, 15, INK, halo=False))
    return f'<rect width="{w}" height="{y + 16}" fill="#fffdf6"/>' + ''.join(g), y + 16

def render():
    ha, a = road_panel()
    bw = 455
    hb, b = land_panel(bw)
    gap = 12
    k, hk = key(W - bw - gap)
    H = ha + gap + max(hb, hk)
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H:.0f}" font-family="{SERIF}" '
           f'role="img" aria-labelledby="t d">',
           '<title id="t">Abram’s road: Ur to the Negev (Genesis 11:31–12:9)</title>',
           '<desc id="d">Two maps. Above: the Fertile Crescent, from Ur in southern Mesopotamia up the '
           'Euphrates to Haran, then south through Aleppo and Damascus to Shechem and on toward the Negev. '
           'Below: the land of Canaan from Shechem through Bethel and Ai to the Negev. Stars mark where God '
           'speaks: at Haran, “Go… to the land that I will show you” (12:1), and at Shechem, “The LORD '
           'appeared” (12:7). Altars stand at Shechem and between Bethel and Ai, with a tent. Green marks land '
           'watered by rain or river (today’s climate: Köppen-Geiger, Beck et al. 2023, CC BY 4.0).</desc>',
           f'<rect width="{W}" height="{H:.0f}" fill="#fffdf6"/>',
           nest(0, 0, W, ha, a), nest(0, ha + gap, bw, hb, b),
           f'<g transform="translate({bw + gap} {ha + gap})">{k}</g>',
           '</svg>']
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    s = '\n'.join(svg)
    open(OUT, 'w').write(s)
    print(f'wrote {os.path.normpath(OUT)}: {W}x{H:.0f} (road {ha:.0f}, land {bw}x{hb:.0f}, key {hk:.0f}), '
          f'{len(s)//1024} KB; miles {MILES}')

if __name__ == '__main__':
    render()
