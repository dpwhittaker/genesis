"""Draw the Session 11 map of the peoples of Genesis 10.

    ~/ml-env/bin/python build_map.py   ->  ../../sessions/11-babel/table-of-nations.svg
                                            ../../sessions/11-babel/canaan.svg
                                            ../../sessions/11-babel/wet-millennia.svg
    (needs numpy, scipy, matplotlib and Pillow)

Coastlines, lakes and rivers: Natural Earth (public domain), modern. Green land:
not desert in today's climate (Köppen-Geiger, Beck et al. 2023, CC BY 4.0), plus
the river valleys that farm the desert (see basemap.watered). Places and
peoples: labels.json (identifications and sources on the Session 11 sheet
"The table of nations"). Each label carries its own offset so nothing collides;
the layout was checked by eye in a browser.
"""
import json, os
from basemap import Albers, Frame, load, polygons, polylines, watered

HERE = os.path.dirname(os.path.abspath(__file__))

COLOR = {'Japheth': '#2f5d8a', 'Ham': '#9a4a14', 'Shem': '#2f6d3a', 'other': '#6b6b6b'}
SEA, LAND, SHORE, RIVER, WATER_TEXT = '#dce7ee', '#f5f0e4', '#9fb0ba', '#8fb0c4', '#5d7d92'
GREEN = '#dfe9c9'
# Hatches for the schematic "before" map: grassland that has since gone, and
# water at the head of the Gulf.
PATTERNS = {
    'grass': ('#8aad62', 1.8, None),
    'marsh': ('#6f98b3', 1.2, '#dce7ee'),
}

def pattern_defs():
    out = ''
    for pid, (col, w, bg) in PATTERNS.items():
        out += (f'<pattern id="{pid}" width="5" height="5" patternUnits="userSpaceOnUse" '
                f'patternTransform="rotate(45)">'
                + (f'<rect width="5" height="5" fill="{bg}" fill-opacity="0.7"/>' if bg else '')
                + f'<line x1="0" y1="0" x2="0" y2="5" stroke="{col}" stroke-width="{w}"/></pattern>')
    return out

def area_path(frame, pts, step=0.25):
    """A lon/lat polygon, its edges densified so they bend with the projection."""
    out = []
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        m = max(1, int(max(abs(x2 - x1), abs(y2 - y1)) / step))
        out += [frame(x1 + (x2 - x1) * t / m, y1 + (y2 - y1) * t / m) for t in range(m)]
    return 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in out) + 'Z'
SERIF = "Georgia, 'Times New Roman', serif"

ANCIENT_LAKES = {'Dead Sea', 'Sea of Galilee', 'Lake Van', 'Lake Urmia', 'Lake Tuz',
                 'Lake Tana', 'Lake Sevan', 'Great Bitter Lake'}
RIVERS = {'Nile', 'El Bahr el Abyad', 'El Bahr el Azraq', 'Atbara', 'Rosetta Branch',
          'Damietta Branch', 'Euphrates', 'Firat', 'Al Furat', 'Tigris', 'Dicle', 'Jordan',
          'Kiz?lirmak', 'Shatt al Arab', 'Karkheh', 'Aras', 'Kura', 'Abay', 'Tekeze',
          'Murat', 'Ceyhan', 'Qezel Owzan', 'Sakarya', 'Byk Menderes', 'Danube',
          'Bratul Sfintu Gheorghe', 'Bratul Chillia', 'Bratul Sulina', 'Don', 'Dnipro',
          'Kuban', 'Orontes', 'Asi'}

def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def basemap(frame, box, extra=14, tol=0.45):
    clip = (box[0] - extra, box[1] - 6, box[2] + extra, box[3] + 4)
    land = polygons(load('ne_10m_land'), frame, clip, tol=tol, minarea=1.0)
    lakes = polygons(load('ne_10m_lakes'), frame, clip, tol=tol, minarea=0.3,
                     want=lambda p: p.get('name') in ANCIENT_LAKES)
    rivers = polylines(load('ne_10m_rivers_lake_centerlines'), frame, clip, tol=tol,
                       want=lambda p: p.get('name') in RIVERS and
                       (p.get('featurecla') == 'River' or p.get('name') == 'Nile'))
    return land, lakes, rivers

def layer(land, lakes, rivers, green=(), sw=1.0, under=(), over=()):
    # One land path, used three times: fill, clip for the green, then the shore
    # line on top so the green does not cover half of it. Hatched areas go under
    # the green (land that was green once) or over it (water at the Gulf head).
    out = (f'<defs>{pattern_defs()}<path id="land" fill-rule="evenodd" clip-rule="evenodd" d="{"".join(land)}"/>'
           '<clipPath id="landclip"><use href="#land"/></clipPath></defs>'
           f'<use href="#land" fill="{LAND}"/>')
    hatch = lambda areas: ''.join(f'<path d="{d}" fill="url(#{pid})"/>' for d, pid in areas)
    if under:
        out += f'<g clip-path="url(#landclip)">{hatch(under)}</g>'
    if green:
        out += (f'<g clip-path="url(#landclip)" fill="{GREEN}" fill-rule="evenodd">'
                + ''.join(f'<path d="{d}"/>' for d in green) + '</g>')
    if over:
        out += f'<g clip-path="url(#landclip)">{hatch(over)}</g>'
    return (out + f'<use href="#land" fill="none" stroke="{SHORE}" stroke-width="{0.6*sw}"/>'
            + f'<g fill="{SEA}" stroke="{SHORE}" stroke-width="{0.5*sw}">'
            + ''.join(f'<path d="{d}"/>' for d in lakes) + '</g>'
            + f'<g fill="none" stroke="{RIVER}" stroke-width="{0.9*sw}" stroke-linejoin="round">'
            + ''.join(f'<path d="{d}"/>' for d in rivers) + '</g>')

def text(x, y, s, size, color, anchor='start', italic=False, weight='normal',
         spacing=0, halo=True, caps=False, rotate=0):
    st = 'italic' if italic else 'normal'
    tr = f' transform="rotate({rotate} {x:.1f} {y:.1f})"' if rotate else ''
    attrs = (f'x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" '
             f'font-style="{st}" font-weight="{weight}" letter-spacing="{spacing}"{tr}')
    if caps: s = s.upper()
    out = ''
    if halo:
        out += (f'<text {attrs} fill="none" stroke="#fffdf6" stroke-width="3.2" '
                f'stroke-linejoin="round" stroke-opacity="0.92">{esc(s)}</text>')
    return out + f'<text {attrs} fill="{color}">{esc(s)}</text>'

def labels(frame, items, scale=1.0):
    """items: dicts with name, lon, lat, line, kind ('people'|'city'|'water'|'note'),
    conf, dx, dy, anchor, optional size/rotate/sub (a second, smaller line)."""
    out = []
    for it in items:
        x, y = frame(it['lon'], it['lat'])
        color = COLOR.get(it.get('line', 'other'), COLOR['other'])
        kind = it.get('kind', 'people')
        uncertain = it.get('conf') == 'uncertain'
        name = it['name'] + ('†' if it.get('dagger') else '') + ('?' if uncertain else '')
        dx, dy = it.get('dx', 0) * scale, it.get('dy', 0) * scale
        anchor = it.get('anchor', 'middle' if kind in ('people', 'water') else 'start')
        if kind == 'city':
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{2.6*scale:.1f}" fill="{color}" '
                       f'stroke="#fffdf6" stroke-width="{0.9*scale:.1f}"/>')
            out.append(text(x + dx, y + dy, name, it.get('size', 11.5) * scale, color, anchor,
                            italic=uncertain))
        elif kind == 'water':
            out.append(text(x + dx, y + dy, it['name'], it.get('size', 12) * scale, WATER_TEXT,
                            anchor, italic=True, halo=False, spacing=it.get('spacing', 0.5),
                            rotate=it.get('rotate', 0)))
        elif kind in ('route', 'note'):
            out.append(text(x + dx, y + dy, it['name'], it.get('size', 10.5) * scale, '#555',
                            anchor, italic=True))
        else:
            size = it.get('size', 13) * scale
            out.append(text(x + dx, y + dy, name, size, color, anchor, italic=uncertain,
                            weight='bold' if not uncertain else 'normal',
                            spacing=it.get('spacing', 0.6), caps=True,
                            rotate=it.get('rotate', 0)))
        if it.get('sub'):
            sc = COLOR.get(it.get('sub_color', ''), '#555')
            out.append(text(x + dx, y + dy + it.get('size', 13) * scale * 1.05, it['sub'],
                            9.5 * scale, sc, anchor, italic=True))
    return ''.join(out)

def route(frame, pts, scale=1.0):
    d = 'M' + ' L'.join('%.1f,%.1f' % frame(lon, lat) for lon, lat in pts)
    return (f'<path d="{d}" fill="none" stroke="#6b6b6b" stroke-width="{1.4*scale:.1f}" '
            f'stroke-dasharray="{5*scale:.1f} {3.5*scale:.1f}" stroke-linecap="round"/>')

def render(spec_file, out_file):
    spec = json.load(open(os.path.join(HERE, spec_file)))
    proj = Albers(36, 28, 18, 42)
    box = tuple(spec['box'])
    W = spec.get('width', 1000)
    k = spec.get('font_scale', 1.0)
    lon_c, lat_c = spec.get('center', [36, 30])
    fr = Frame(box, W, proj, lon_c, lat_c)
    H = fr.height
    extra, tol = spec.get('clip_extra', 14), spec.get('tol', 0.45)
    land, lakes, rivers = basemap(fr, box, extra=extra, tol=tol)
    green = []
    if spec.get('watered'):
        wt = spec['watered']
        clip = (box[0] - extra, box[1] - 6, box[2] + extra, box[3] + 4)
        green = watered(fr, clip, wt['step'], wt['sigma'], tol, valleys=wt.get('valleys', True))

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
             f'font-family="{SERIF}" role="img" aria-labelledby="t d">',
             f'<title id="t">{esc(spec["title"])}</title><desc id="d">{esc(spec["desc"])}</desc>',
             f'<clipPath id="frame"><rect width="{W:.0f}" height="{H:.0f}"/></clipPath>',
             '<g clip-path="url(#frame)">',
             f'<rect width="{W:.0f}" height="{H:.0f}" fill="{SEA}"/>',
             layer(land, lakes, rivers, green, sw=spec.get('stroke_scale', 1.0),
                   under=[(area_path(fr, a['points']), a['pattern']) for a in spec.get('areas', [])
                          if not a.get('over')],
                   over=[(area_path(fr, a['points']), a['pattern']) for a in spec.get('areas', [])
                         if a.get('over')])]
    for r in spec.get('routes', []):
        parts.append(route(fr, r['points'], k))
    for b in spec.get('outlines', []):
        corners = [(b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3])]
        pts = ' '.join('%.1f,%.1f' % fr(*c) for c in corners)
        parts.append(f'<polygon points="{pts}" fill="none" stroke="#444" stroke-width="1" '
                     f'stroke-dasharray="3 2"/>')
    parts.append(labels(fr, spec['labels'], k))

    for box_ in spec.get('boxes', []):
        # A framed text box (title, legend, or a list), lines drawn in order.
        bx, by, bw = box_['x'], box_['y'], box_['w']
        rows = box_['rows']
        h = 12 + sum(r.get('h', 16) for r in rows) * k + 6
        g = [f'<g transform="translate({bx} {by})">',
             f'<rect width="{bw}" height="{h:.0f}" rx="3" fill="#fffdf6" fill-opacity="0.95" '
             f'stroke="#888" stroke-width="0.8"/>']
        y = 6
        for r in rows:
            y += r.get('h', 16) * k
            size = r.get('size', 12) * k
            x = 12
            if r.get('swatch'):
                sw_ = r['swatch']
                col = (GREEN if sw_ == 'watered' else f'url(#{sw_})' if sw_ in PATTERNS
                       else COLOR[sw_])
                edge = (f' stroke="{SHORE}" stroke-width="0.8"'
                        if sw_ == 'watered' or sw_ in PATTERNS else '')
                g.append(f'<rect x="12" y="{y - size*0.85:.1f}" width="{size*0.9:.1f}" '
                         f'height="{size*0.9:.1f}" fill="{col}"{edge}/>')
                x = 12 + size * 1.5
            if r.get('dot'):
                g.append(f'<circle cx="{12 + size*0.45:.1f}" cy="{y - size*0.33:.1f}" r="{2.8*k:.1f}" fill="#444"/>')
                x = 12 + size * 1.5
            if r.get('dash'):
                g.append(f'<path d="M12,{y - size*0.33:.1f} L{12 + size*1.1:.1f},{y - size*0.33:.1f}" '
                         f'stroke="#6b6b6b" stroke-width="{1.4*k:.1f}" stroke-dasharray="5 3.5"/>')
                x = 12 + size * 1.5
            color = COLOR.get(r.get('color', ''), r.get('color', '#222'))
            g.append(text(x, y, r['text'], size, color, italic=r.get('italic', False),
                          weight='bold' if r.get('bold') else 'normal', halo=False))
        g.append('</g>')
        parts.append(''.join(g))
    parts.append(f'<rect width="{W:.0f}" height="{H:.0f}" fill="none" stroke="#555" stroke-width="1.5"/>')
    parts.append('</g></svg>')
    svg = '\n'.join(parts)
    out = os.path.join(HERE, '..', '..', 'sessions', '11-babel', out_file)
    open(out, 'w').write(svg)
    print(f'wrote {os.path.normpath(out)}: {W:.0f}x{H:.0f}, {len(svg)//1024} KB')

if __name__ == '__main__':
    render('labels.json', 'table-of-nations.svg')
    render('canaan.json', 'canaan.svg')
    render('then.json', 'wet-millennia.svg')
