#!/usr/bin/env python3
"""
Find and download real archival images from Wikimedia Commons, with licence and credit saved alongside.

Usage:
  python3 fetch_commons.py "Bengal famine 1770" -n 6 -o assets/famine
  python3 fetch_commons.py "Warren Hastings portrait" -n 3 -o assets/hastings --min-width 1200

Writes assets/<dir>/NN_<title>.jpg and assets/<dir>/credits.json  ({file, title, author, license, url}).
Only keeps files whose licence is public domain or Creative Commons (CC0 / CC BY / CC BY-SA).
Always put the credit on screen (the renderer's "credit" field) and in the description.
"""
import argparse, json, os, re, sys, time, urllib.parse, urllib.request

API = "https://commons.wikimedia.org/w/api.php"
UA = "history-explainer-skill/1.0 (educational video research; contact via GitHub)"


def fetch(url, tries=5):
    """GET with polite backoff; Commons answers 429 when thumbnails are requested too fast."""
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and i < tries - 1:
                time.sleep(2 * (i + 1) + 1)
                continue
            raise


def get(params):
    params = dict(params, format="json")
    return json.loads(fetch(API + "?" + urllib.parse.urlencode(params)))


def search(q, n):
    j = get({"action": "query", "list": "search", "srsearch": q, "srnamespace": 6, "srlimit": n * 3})
    return [h["title"] for h in j["query"]["search"]]


def info(titles):
    out = []
    for i in range(0, len(titles), 20):
        j = get({"action": "query", "titles": "|".join(titles[i:i + 20]), "prop": "imageinfo",
                 "iiprop": "url|size|extmetadata|mime", "iiurlwidth": 2000})
        for p in j["query"]["pages"].values():
            ii = (p.get("imageinfo") or [None])[0]
            if not ii:
                continue
            em = ii.get("extmetadata", {})
            out.append({
                "title": p["title"].replace("File:", ""),
                "url": ii.get("thumburl") or ii["url"],
                "page": ii.get("descriptionurl"),
                "width": ii.get("width", 0), "height": ii.get("height", 0), "mime": ii.get("mime", ""),
                "license": em.get("LicenseShortName", {}).get("value", ""),
                "author": re.sub("<[^>]+>", "", em.get("Artist", {}).get("value", "")).strip(),
                "date": em.get("DateTimeOriginal", {}).get("value", ""),
            })
    return out


def ok_license(l):
    l = l.lower()
    return "public domain" in l or l.startswith("pd") or l.startswith("cc0") or l.startswith("cc by") or l.startswith("cc-by")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query"); ap.add_argument("-n", type=int, default=6); ap.add_argument("-o", default="assets")
    ap.add_argument("--min-width", type=int, default=800)
    a = ap.parse_args()
    os.makedirs(a.o, exist_ok=True)
    cands = [c for c in info(search(a.query, a.n)) if c["mime"].startswith("image/") and c["mime"] != "image/svg+xml"
             and c["width"] >= a.min_width and ok_license(c["license"])]
    cands.sort(key=lambda c: -c["width"])
    credits = []
    for i, c in enumerate(cands[:a.n], 1):
        ext = ".png" if c["mime"] == "image/png" else ".jpg"
        safe = re.sub(r"[^A-Za-z0-9]+", "_", c["title"])[:60].strip("_")
        fn = os.path.join(a.o, f"{i:02d}_{safe}{ext}")
        with open(fn, "wb") as f:
            f.write(fetch(c["url"]))
        time.sleep(1.2)
        credit = f"{c['author'] or 'Unknown'} · {c['license']} · Wikimedia Commons"
        credits.append({"file": fn, "title": c["title"], "author": c["author"], "license": c["license"], "date": c["date"], "url": c["page"], "credit": credit})
        print(f"{fn}  [{c['width']}x{c['height']}]  {c['license']}  {c['title']}")
    json.dump(credits, open(os.path.join(a.o, "credits.json"), "w"), indent=2, ensure_ascii=False)
    print(f"{len(credits)} files, credits in {a.o}/credits.json")
    if not credits:
        print("Nothing usable. Try other words (English, the period, 'engraving', 'map', 'portrait'), or lower --min-width.", file=sys.stderr)


if __name__ == "__main__":
    main()
