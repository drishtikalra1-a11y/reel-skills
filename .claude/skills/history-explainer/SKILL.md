---
name: history-explainer
description: "Make Study IQ / Aadesh Singh style history and polity explainer videos from REAL archival images: public-domain paintings, engravings, photographs and old maps with slow Ken Burns moves, pulsing map pins, a dated timeline strip, before/after compares, quote cards and bullet cards, Hindi or Hinglish lower-thirds in Devanagari, a voiceover (the creator's own or TTS) with a ducked music bed, in 16:9 for YouTube or 9:16 for Reels. Use when the user says 'Study IQ style', 'Aadesh Singh style', 'history explainer', 'documentary style video with real images', 'animate these photos', 'chronology video', 'UPSC / UGC NET history video', 'famine / revolution / dynasty video', or hands over a script about a historical topic and wants a video, not a talking head. Not for hand-drawn cartoons (animation-studio), paper-collage looks (melvynx-vox, vox-explainer) or product promos."
---

# history-explainer

Documentary explainers the way Study IQ's history channel does them: a narrator over **real pictures**
that move slowly, every date and name stamped on screen, a map whenever a place is named, a timeline
whenever a sequence is named. Nothing is AI-generated imagery; everything is a sourced archival asset with a credit.

## Workflow

1. **Script first.** Get or write the narration in the creator's language (Hindi, Hinglish or English).
   Split it into beats of 5 to 9 seconds, one idea each. For each beat note what the viewer should SEE:
   a portrait, an event picture, a map, a number, a comparison, a quote, a list. Mark the 4 to 6 facts
   that deserve a stamp (dates, numbers, names).
2. **Source real images** with `scripts/fetch_commons.py` (Wikimedia Commons, public domain or CC only;
   credits.json is written next to the files). Search in English with the period and the medium:
   "Bengal famine 1770 engraving", "Warren Hastings portrait", "Rennell map Bengal 1776",
   "Dandi march 1930 photograph". Other good open sources to fetch by URL: Wellcome Collection,
   British Library Flickr, Library of Congress, Rijksmuseum, Met Open Access, NYPL Digital Collections.
   Reject anything with a watermark, a modern reconstruction, or an unclear licence. Open each image and
   LOOK at it before using it; pick a `focus` point (face, crowd, place on the map) for the zoom to end on.
3. **Voiceover.** Prefer the creator's own recording (gives the channel its voice). Otherwise:
   `edge-tts --voice hi-IN-MadhurNeural` (male) / `hi-IN-SwaraNeural` (female), `en-IN-PrabhatNeural`
   for Indian English, rate `-5%` for teaching pace. If edge-tts cannot connect (corporate proxy), use
   `gTTS(text, lang='hi')`. Transcribe the final voice with whisper to get word times if captions are wanted.
4. **Storyboard JSON** (schema in `scripts/render.py` docstring). Pin each scene to the voice with
   `"start"` seconds taken from the narration timing, or let scenes run back to back and set
   `"fit_to_voice": true`. Rules of the look are below.
5. **Render.** `python3 scripts/render.py storyboard.json out.mp4 --preview` first (half size, 15 fps,
   fast), make a contact sheet and LOOK at it, fix, then render full. For Reels add `"size": "9:16"`
   and shorten to one idea under 60 s, or run `reel-export` on the 16:9 master.
6. **Verify** with ffprobe (duration, 1920x1080 or 1080x1920, yuv420p, audio present), watch the
   first 10 s and the last 10 s, check every Devanagari string rendered (no boxes), check every image
   has its credit, check no text sits in the Reels UI zone (bottom 20 %, right 10 %) for 9:16.

## The look (what makes it read as Study IQ, not a slideshow)

- **Every image moves.** Slow zoom in to the subject (`zoom_in` + `focus`) is the default; `zoom_out`
  to reveal a scene; `pan_left`/`pan_right` across a wide engraving or map. Never static, never fast.
  Vary the move from scene to scene; two zoom-ins in a row is fine, three is not.
- **One stamp per beat.** The yellow date/keyword tag (`title`) plus one caption line (`caption`) that
  restates the key fact in the script's words. Short: a caption is one sentence, under 10 words in Hindi.
- **Map whenever a place is named.** A `map` scene with `pins` at the place, zooming toward it. Old maps
  (Rennell, Survey of India, Tallis) look right for the period; a modern outline map is fine for clarity.
- **Timeline whenever a sequence is named.** `timeline` scene with 3 to 6 events, `active` on the one
  being discussed; reuse the same timeline across the video with a different `active` each time.
- **Numbers as numbers.** A big figure goes in the `title` tag ("1 करोड़") or a `card` bullet, never only
  in the voice.
- **Compare** for change over time or two sides (before/after, Company vs Nawab, 1770 vs 1943).
- **Quote** for a primary source, with the speaker and year in `by`.
- **Archival look** (`"look": "archival"`): a light warm tone and vignette unify engravings, paintings
  and photos. Use `"clean"` when the images are already consistent or when the topic is modern.
- **Rhythm.** 5 to 9 s per picture, 3 s title, 4 to 6 s for timeline and card. Dissolves between
  pictures (default), hard cuts into title and card scenes (`"transition": "cut"`) for emphasis.
- **Sound.** Voice normalised to -16 LUFS, music 20 to 24 dB under and ducked (the renderer does both).
  Choose a quiet instrumental, documentary strings or tanpura drone, never a beat-heavy track.
- **Brand.** `brand.series` top-left (e.g. "विश्व इतिहास · UPSC"), `brand.handle` top-right.
  Thumbnail: the strongest archival image, darkened on one side, Hindi title in yellow and white,
  English keyword on a red strip (see the creator's earlier thumbnails for the exact pattern).

## Scripts

- `scripts/fetch_commons.py "query" -n 6 -o assets/topic` : search and download licensed archival
  images with `credits.json`.
- `scripts/render.py storyboard.json out.mp4 [--preview]` : render. Pure Pillow + ffmpeg, no other
  dependencies. Fonts ship in `assets/fonts` (Noto Sans Devanagari, Noto Sans, Mukta, Oswald).

## Facts and credits

Every date, number and name in the script must be checked against a reliable source before it is
stamped on screen; a wrong stamp is worse than no stamp. Put the credit on screen for each image
(the `credit` field) and list all credits with links in the video description. Public domain still
deserves attribution; CC BY requires it.
