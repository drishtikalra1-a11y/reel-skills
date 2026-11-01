#!/usr/bin/env python3
"""
history-explainer renderer: archival photos + Ken Burns + Hindi/English text -> MP4.

Usage:
  python3 render.py storyboard.json out.mp4 [--preview]

Storyboard (JSON):
{
  "size": "16:9" | "9:16" | "1:1",          # default 16:9 (1920x1080)
  "fps": 30,
  "lang_font": "devanagari",                 # devanagari | latin   (title font family)
  "voiceover": "vo.mp3",                     # optional; video is padded/trimmed to it if "fit_to_voice": true
  "fit_to_voice": false,
  "music": "music.mp3",                      # optional, ducked under the voice
  "music_db": -22,
  "look": "archival",                        # archival (warm, vignette) | clean | dark
  "brand": {"handle": "@yourhandle", "series": "विश्व इतिहास · UPSC"},
  "scenes": [
    {"type": "title", "text": "बंगाल का अकाल", "sub": "1770", "duration": 3},
    {"type": "photo", "src": "assets/famine.jpg", "duration": 6, "move": "zoom_in",
     "title": "1770", "caption": "एक करोड़ लोग मारे गए", "credit": "Wellcome Collection, public domain",
     "focus": [0.5, 0.4]},
    {"type": "map", "src": "assets/india_1770.png", "duration": 5, "move": "zoom_in", "focus": [0.72, 0.35],
     "pins": [{"x": 0.72, "y": 0.35, "label": "बंगाल"}], "caption": "कंपनी का राज, 1765 से"},
    {"type": "timeline", "duration": 5, "active": 1, "title": "भारत के बड़े अकाल",
     "events": [{"year": "1770", "label": "बंगाल"}, {"year": "1876", "label": "दक्कन"}, {"year": "1943", "label": "बंगाल"}]},
    {"type": "compare", "left": "assets/a.jpg", "right": "assets/b.jpg", "left_label": "पहले", "right_label": "बाद", "duration": 5},
    {"type": "quote", "text": "“...”", "by": "— Warren Hastings, 1772", "duration": 4},
    {"type": "card", "title": "3 कारण", "bullets": ["सूखा", "लगान", "निर्यात"], "duration": 5}
  ]
}
Scene keys: "move" = zoom_in | zoom_out | pan_left | pan_right | still; "focus" = [x, y] in 0..1 where the zoom ends;
"start" (seconds) pins a scene to the voiceover; otherwise scenes run back to back. "transition": "dissolve" (default) | "cut".
"""
import json, math, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "assets", "fonts")
SIZES = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080)}
DISSOLVE = 0.4  # seconds


def font(kind, px, lang="devanagari"):
    """kind: title | body | display. Devanagari-capable Noto for titles/body, Oswald for dates/numbers."""
    paths = {
        "title": "NotoSansDevanagari.ttf" if lang == "devanagari" else "NotoSans.ttf",
        "body": "NotoSansDevanagari.ttf" if lang == "devanagari" else "NotoSans.ttf",
        "display": "Oswald.ttf",
    }
    f = ImageFont.truetype(os.path.join(FONTS, paths[kind]), px)
    try:
        f.set_variation_by_name("Bold" if kind != "body" else "Regular")
    except Exception:
        pass
    return f


def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * min(max(t, 0), 1))


def load_cover(path, W, H):
    im = Image.open(path).convert("RGB")
    im = ImageOps.exif_transpose(im)
    return im


def look_filter(im, look):
    if look == "archival":
        sep = ImageOps.colorize(ImageOps.grayscale(im), black=(28, 18, 10), white=(255, 244, 222))
        im = Image.blend(im, sep, 0.35)
    elif look == "dark":
        im = ImageOps.autocontrast(im)
    return im


def vignette(W, H, strength=0.55):
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    d.ellipse([-W * 0.25, -H * 0.25, W * 1.25, H * 1.25], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(min(W, H) * 0.18))
    m = m.point(lambda v: int(255 - (255 - v) * strength))
    return m


def ken_burns_frame(src, W, H, t, move, focus):
    """Return a WxH crop of src at progress t (0..1)."""
    sw, sh = src.size
    scale_cover = max(W / sw, H / sh)
    # zoom factors relative to cover
    z0, z1 = {"zoom_in": (1.0, 1.22), "zoom_out": (1.22, 1.0), "pan_left": (1.15, 1.15),
              "pan_right": (1.15, 1.15), "still": (1.06, 1.06)}.get(move, (1.0, 1.2))
    z = z0 + (z1 - z0) * ease(t)
    cw, ch = W / (scale_cover * z), H / (scale_cover * z)  # crop size in source px
    fx, fy = focus if focus else (0.5, 0.5)
    if move == "pan_left":
        fx = 0.72 - 0.44 * ease(t)
    elif move == "pan_right":
        fx = 0.28 + 0.44 * ease(t)
    cx = fx * sw if move in ("pan_left", "pan_right") else (0.5 + (fx - 0.5) * ease(t)) * sw
    cy = (0.5 + (fy - 0.5) * ease(t)) * sh
    x0 = min(max(cx - cw / 2, 0), sw - cw)
    y0 = min(max(cy - ch / 2, 0), sh - ch)
    box = (x0, y0, x0 + cw, y0 + ch)
    return src.resize((W, H), Image.LANCZOS, box=box)


def wrap(draw, text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=f) <= maxw:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def text_block(img, text, f, xy, fill, maxw, anchor_bottom=False, shadow=True, line_gap=1.15, align="left"):
    d = ImageDraw.Draw(img)
    lines = wrap(d, text, f, maxw)
    lh = int(f.size * line_gap)
    x, y = xy
    if anchor_bottom:
        y = y - lh * len(lines)
    for ln in lines:
        lx = x
        if align == "center":
            lx = x - d.textlength(ln, font=f) / 2
        if shadow:
            d.text((lx + 3, y + 3), ln, font=f, fill=(0, 0, 0))
        d.text((lx, y), ln, font=f, fill=fill)
        y += lh
    return y


def lower_third(img, title, caption, W, H, lang, t):
    """Study-IQ style: yellow date/keyword tag + white caption bar, slides in."""
    if not (title or caption):
        return
    d = ImageDraw.Draw(img, "RGBA")
    slide = ease(min(t / 0.35, 1))
    pad = int(W * 0.045)
    base_y = int(H * 0.80) if H <= W else int(H * 0.70)
    ox = int((1 - slide) * -W * 0.3)
    if title:
        ft = font("display", int(H * 0.07))
        tw = d.textlength(title, font=ft)
        d.rectangle([pad + ox, base_y - int(H * 0.10), pad + ox + tw + pad, base_y - int(H * 0.015)], fill=(250, 204, 21, 255))
        d.text((pad + ox + pad / 2, base_y - int(H * 0.098)), title, font=ft, fill=(20, 16, 10))
    if caption:
        fc = font("title", int(H * 0.055), lang)
        lines = wrap(d, caption, fc, W - 2 * pad)
        lh = int(fc.size * 1.25)
        d.rectangle([0, base_y, W, base_y + lh * len(lines) + int(H * 0.03)], fill=(0, 0, 0, 165))
        y = base_y + int(H * 0.012)
        for ln in lines:
            d.text((pad + ox, y), ln, font=fc, fill=(255, 255, 255))
            y += lh


def credit_line(img, text, W, H):
    if not text:
        return
    d = ImageDraw.Draw(img, "RGBA")
    f = font("body", int(H * 0.02), "latin")
    tw = d.textlength(text, font=f)
    d.rectangle([W - tw - 24, H - int(H * 0.045), W, H], fill=(0, 0, 0, 120))
    d.text((W - tw - 12, H - int(H * 0.04)), text, font=f, fill=(220, 220, 220))


def brand(img, b, W, H, lang):
    if not b:
        return
    d = ImageDraw.Draw(img, "RGBA")
    if b.get("series"):
        f = font("title", int(H * 0.028), lang)
        d.text((int(W * 0.03), int(H * 0.03)), b["series"], font=f, fill=(250, 204, 21))
    if b.get("handle"):
        f = font("body", int(H * 0.024), "latin")
        tw = d.textlength(b["handle"], font=f)
        d.text((W - tw - int(W * 0.03), int(H * 0.03)), b["handle"], font=f, fill=(255, 255, 255, 200))


# ---------- scene renderers (each returns a PIL frame for local time t in seconds, duration dur) ----------

def scene_photo(sc, W, H, lang, look, cache):
    src = cache.get(sc["src"]) or cache.setdefault(sc["src"], look_filter(load_cover(sc["src"], W, H), look if sc.get("type") == "photo" else "clean"))
    vig = cache.get("_vig") or cache.setdefault("_vig", vignette(W, H))
    dur = sc["duration"]

    def frame(t):
        im = ken_burns_frame(src, W, H, t / dur, sc.get("move", "zoom_in"), sc.get("focus"))
        if look == "archival" and sc.get("type") == "photo":
            im = Image.composite(im, Image.new("RGB", (W, H), (0, 0, 0)), vig)
        for pin in sc.get("pins", []):
            pulse = 0.5 + 0.5 * math.sin(t * 4)
            px, py = pin["x"] * W, pin["y"] * H
            d = ImageDraw.Draw(im, "RGBA")
            r = int(H * 0.012 + H * 0.01 * pulse)
            d.ellipse([px - r * 2.2, py - r * 2.2, px + r * 2.2, py + r * 2.2], fill=(220, 38, 38, 70))
            d.ellipse([px - r, py - r, px + r, py + r], fill=(220, 38, 38, 255), outline=(255, 255, 255), width=3)
            if pin.get("label"):
                f = font("title", int(H * 0.04), lang)
                d.text((px + r * 2.6 + 2, py - f.size / 2 + 2), pin["label"], font=f, fill=(0, 0, 0))
                d.text((px + r * 2.6, py - f.size / 2), pin["label"], font=f, fill=(255, 255, 255))
        lower_third(im, sc.get("title"), sc.get("caption"), W, H, lang, t)
        credit_line(im, sc.get("credit"), W, H)
        return im
    return frame


def scene_title(sc, W, H, lang, look, cache):
    bg = None
    if sc.get("src"):
        bg = cache.get(sc["src"]) or cache.setdefault(sc["src"], look_filter(load_cover(sc["src"], W, H), look))

    def frame(t):
        if bg is not None:
            im = ken_burns_frame(bg, W, H, t / sc["duration"], "zoom_in", sc.get("focus"))
            im = Image.blend(im, Image.new("RGB", (W, H), (0, 0, 0)), 0.55)
        else:
            im = Image.new("RGB", (W, H), (16, 14, 12))
        a = ease(min(t / 0.5, 1))
        f = font("title", int(H * 0.12), lang)
        y = H * 0.40 + (1 - a) * 40
        text_block(im, sc["text"], f, (W / 2, y), (255, 255, 255), W * 0.85, align="center")
        if sc.get("sub"):
            fs = font("display", int(H * 0.07))
            d = ImageDraw.Draw(im)
            tw = d.textlength(sc["sub"], font=fs)
            d.rectangle([W / 2 - tw / 2 - 24, H * 0.58, W / 2 + tw / 2 + 24, H * 0.58 + fs.size * 1.3], fill=(220, 38, 38))
            d.text((W / 2 - tw / 2, H * 0.58 + fs.size * 0.1), sc["sub"], font=fs, fill=(255, 255, 255))
        return im
    return frame


def scene_timeline(sc, W, H, lang, look, cache):
    ev = sc["events"]
    active = sc.get("active", 0)

    def frame(t):
        im = Image.new("RGB", (W, H), (20, 18, 16))
        d = ImageDraw.Draw(im, "RGBA")
        if sc.get("title"):
            text_block(im, sc["title"], font("title", int(H * 0.07), lang), (W / 2, H * 0.12), (250, 204, 21), W * 0.9, align="center", shadow=False)
        y = H * 0.55
        x0, x1 = W * 0.1, W * 0.9
        prog = ease(min(t / 1.2, 1))
        d.line([(x0, y), (x0 + (x1 - x0) * prog, y)], fill=(255, 255, 255), width=6)
        n = len(ev)
        for i, e in enumerate(ev):
            x = x0 + (x1 - x0) * (i / max(n - 1, 1))
            if x > x0 + (x1 - x0) * prog + 1:
                continue
            r = int(H * 0.018)
            col = (220, 38, 38) if i == active else (255, 255, 255)
            if i == active:
                pulse = int(r * (1.6 + 0.4 * math.sin(t * 5)))
                d.ellipse([x - pulse, y - pulse, x + pulse, y + pulse], fill=(220, 38, 38, 80))
            d.ellipse([x - r, y - r, x + r, y + r], fill=col)
            fy = font("display", int(H * (0.065 if i == active else 0.045)))
            yt = y - fy.size - H * 0.03
            tw = d.textlength(e["year"], font=fy)
            d.text((x - tw / 2, yt), e["year"], font=fy, fill=(250, 204, 21) if i == active else (255, 255, 255))
            fl = font("title", int(H * (0.04 if i == active else 0.03)), lang)
            tw = d.textlength(e["label"], font=fl)
            d.text((x - tw / 2, y + H * 0.035), e["label"], font=fl, fill=(255, 255, 255))
        if sc.get("caption"):
            text_block(im, sc["caption"], font("title", int(H * 0.045), lang), (W / 2, H * 0.78), (255, 255, 255), W * 0.85, align="center", shadow=False)
        return im
    return frame


def scene_compare(sc, W, H, lang, look, cache):
    L = cache.get(sc["left"]) or cache.setdefault(sc["left"], look_filter(load_cover(sc["left"], W, H), look))
    R = cache.get(sc["right"]) or cache.setdefault(sc["right"], look_filter(load_cover(sc["right"], W, H), look))
    vertical = H > W

    def frame(t):
        im = Image.new("RGB", (W, H), (0, 0, 0))
        if vertical:
            a = ken_burns_frame(L, W, H // 2, t / sc["duration"], "still", None)
            b = ken_burns_frame(R, W, H // 2, t / sc["duration"], "still", None)
            im.paste(a, (0, 0)); im.paste(b, (0, H // 2))
            la, lb = (W / 2, H * 0.42), (W / 2, H * 0.92)
        else:
            a = ken_burns_frame(L, W // 2 - 4, H, t / sc["duration"], "still", None)
            b = ken_burns_frame(R, W // 2 - 4, H, t / sc["duration"], "still", None)
            im.paste(a, (0, 0)); im.paste(b, (W // 2 + 4, 0))
            la, lb = (W * 0.25, H * 0.86), (W * 0.75, H * 0.86)
        f = font("title", int(H * 0.055), lang)
        d = ImageDraw.Draw(im, "RGBA")
        for (x, y), txt in ((la, sc.get("left_label")), (lb, sc.get("right_label"))):
            if not txt:
                continue
            tw = d.textlength(txt, font=f)
            d.rectangle([x - tw / 2 - 20, y - 10, x + tw / 2 + 20, y + f.size * 1.2], fill=(250, 204, 21))
            d.text((x - tw / 2, y), txt, font=f, fill=(20, 16, 10))
        if sc.get("caption"):
            lower_third(im, None, sc["caption"], W, H, lang, t)
        return im
    return frame


def scene_quote(sc, W, H, lang, look, cache):
    bg = cache.get(sc.get("src")) if sc.get("src") else None
    if sc.get("src") and bg is None:
        bg = cache.setdefault(sc["src"], look_filter(load_cover(sc["src"], W, H), look))

    def frame(t):
        if bg is not None:
            im = ken_burns_frame(bg, W, H, t / sc["duration"], "still", None).filter(ImageFilter.GaussianBlur(6))
            im = Image.blend(im, Image.new("RGB", (W, H), (0, 0, 0)), 0.6)
        else:
            im = Image.new("RGB", (W, H), (24, 20, 16))
        f = font("title", int(H * 0.06), lang)
        d = ImageDraw.Draw(im)
        d.rectangle([W * 0.08, H * 0.25, W * 0.08 + 10, H * 0.72], fill=(250, 204, 21))
        y = text_block(im, sc["text"], f, (W * 0.12, H * 0.27), (255, 255, 255), W * 0.78, shadow=False, line_gap=1.3)
        if sc.get("by"):
            text_block(im, sc["by"], font("body", int(H * 0.035), lang), (W * 0.12, y + H * 0.03), (250, 204, 21), W * 0.78, shadow=False)
        return im
    return frame


def scene_card(sc, W, H, lang, look, cache):
    def frame(t):
        im = Image.new("RGB", (W, H), (250, 246, 236))
        d = ImageDraw.Draw(im)
        for gx in range(0, W, 60):
            d.line([(gx, 0), (gx, H)], fill=(232, 226, 212), width=1)
        for gy in range(0, H, 60):
            d.line([(0, gy), (W, gy)], fill=(232, 226, 212), width=1)
        text_block(im, sc["title"], font("title", int(H * 0.085), lang), (W * 0.08, H * 0.12), (20, 16, 10), W * 0.84, shadow=False)
        y = H * 0.32
        for i, b in enumerate(sc.get("bullets", [])):
            if t < 0.6 + i * 0.6:
                break
            a = ease((t - (0.6 + i * 0.6)) / 0.3)
            fx = W * 0.10 + (1 - a) * -40
            d.rectangle([fx, y + H * 0.02, fx + 14, y + H * 0.065], fill=(220, 38, 38))
            text_block(im, b, font("title", int(H * 0.06), lang), (fx + 40, y), (20, 16, 10), W * 0.8, shadow=False)
            y += H * 0.12
        return im
    return frame


RENDERERS = {"photo": scene_photo, "map": scene_photo, "title": scene_title, "timeline": scene_timeline,
             "compare": scene_compare, "quote": scene_quote, "card": scene_card}


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    sb = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    preview = "--preview" in sys.argv
    W, H = SIZES[sb.get("size", "16:9")]
    fps = sb.get("fps", 30)
    if preview:
        W, H, fps = W // 2, H // 2, 15
    lang = sb.get("lang_font", "devanagari")
    look = sb.get("look", "archival")
    scenes = sb["scenes"]
    # timing
    tcur = 0.0
    for sc in scenes:
        if "start" in sc:
            tcur = float(sc["start"])
        sc["_start"] = tcur
        tcur += float(sc["duration"])
    total = tcur
    cache = {}
    frames_fn = [(sc, RENDERERS[sc["type"]](sc, W, H, lang, look, cache)) for sc in scenes]
    nframes = int(round(total * fps))

    tmpdir = tempfile.mkdtemp()
    silent = os.path.join(tmpdir, "silent.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
           "-c:v", "libx264", "-preset", "veryfast" if preview else "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", silent]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    last = None
    for i in range(nframes):
        T = i / fps
        cur = [s for s in frames_fn if s[0]["_start"] <= T < s[0]["_start"] + s[0]["duration"]]
        if not cur:
            im = last or Image.new("RGB", (W, H), (0, 0, 0))
        else:
            sc, fn = cur[-1]
            im = fn(T - sc["_start"])
            # dissolve from previous scene
            k = scenes.index(sc)
            if k > 0 and sc.get("transition", "dissolve") == "dissolve" and T - sc["_start"] < DISSOLVE:
                psc, pfn = frames_fn[k - 1]
                prev = pfn(min(psc["duration"] - 1 / fps, T - psc["_start"]))
                im = Image.blend(prev, im, ease((T - sc["_start"]) / DISSOLVE))
            brand(im, sb.get("brand"), W, H, lang)
        last = im
        p.stdin.write(im.tobytes())
        if i % (fps * 5) == 0:
            print(f"  frame {i}/{nframes}  t={T:.1f}s", flush=True)
    p.stdin.close(); p.wait()

    # audio
    vo, music = sb.get("voiceover"), sb.get("music")
    if not vo and not music:
        os.replace(silent, out)
    else:
        inputs, fc = ["-i", silent], []
        idx = 1
        if vo:
            inputs += ["-i", vo]; vo_i = idx; idx += 1
        if music:
            inputs += ["-i", music]; mu_i = idx; idx += 1
        mdb = sb.get("music_db", -22)
        if vo and music:
            fc.append(f"[{mu_i}:a]aloop=loop=-1:size=2e9,volume={mdb}dB,atrim=0:{total}[m];"
                      f"[{vo_i}:a]aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.5:LRA=11,apad,atrim=0:{total}[v];"
                      f"[m][v]sidechaincompress=threshold=0.03:ratio=8:attack=50:release=600[md];"
                      f"[md][v]amix=inputs=2:duration=first:dropout_transition=0,alimiter=limit=0.95[a]")
        elif vo:
            fc.append(f"[{vo_i}:a]aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.5:LRA=11,apad,atrim=0:{total}[a]")
        else:
            fc.append(f"[{mu_i}:a]aloop=loop=-1:size=2e9,volume={mdb + 8}dB,atrim=0:{total},afade=t=out:st={max(total - 2, 0)}:d=2[a]")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + inputs + ["-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[a]",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", out], check=True)
    print(f"done: {out}  ({total:.1f}s, {W}x{H}@{fps})")


if __name__ == "__main__":
    main()
