"""
Deterministic HTML renderer for pitch deck content.

Takes a ``PitchDeckContent`` instance and produces a self-contained HTML
presentation with:
- HLS.js video backgrounds
- Liquid glass aesthetic (glassmorphism, dark theme)
- Keyboard navigation (Arrow keys / Space)
- Progress dots and slide counter
- Smooth CSS transitions
"""

from __future__ import annotations

import html as html_mod
from app.schemas.deck_content import PitchDeckContent


def _e(text: str | None) -> str:
    """HTML-escape helper."""
    return html_mod.escape(text or "")


def _render_cover(slide) -> str:
    return f"""
    <section class="slide" data-slide="0">
      <video class="bg-video" muted loop autoplay playsinline></video>
      <div class="slide-overlay"></div>
      <div class="slide-content cover-content">
        <h1 class="cover-title">{_e(slide.headline)}</h1>
        <p class="cover-subtitle">{_e(slide.subheadline)}</p>
        <div class="cover-prompt">Press &rarr; to begin</div>
      </div>
    </section>"""


def _render_standard(slide, index: int, slide_class: str = "") -> str:
    accent = ""
    if slide.accent_metric:
        label = f'<span class="accent-label">{_e(slide.accent_label)}</span>' if slide.accent_label else ""
        accent = f'<div class="accent-block"><span class="accent-metric">{_e(slide.accent_metric)}</span>{label}</div>'

    points = "\n".join(f'<li>{_e(p)}</li>' for p in slide.body_points)

    return f"""
    <section class="slide {slide_class}" data-slide="{index}">
      <video class="bg-video" muted loop autoplay playsinline></video>
      <div class="slide-overlay"></div>
      <div class="slide-content">
        {accent}
        <h2 class="slide-headline">{_e(slide.headline)}</h2>
        <p class="slide-sub">{_e(slide.subheadline)}</p>
        <ul class="slide-points">{points}</ul>
      </div>
    </section>"""


def _render_market(slide, index: int) -> str:
    metrics = []
    for label, value in [("TAM", slide.tam), ("SAM", slide.sam), ("SOM", slide.som)]:
        if value:
            metrics.append(f'<div class="market-metric"><span class="market-value">{_e(value)}</span><span class="market-label">{label}</span></div>')
    metrics_html = f'<div class="market-metrics">{"".join(metrics)}</div>' if metrics else ""

    points = "\n".join(f'<li>{_e(p)}</li>' for p in slide.body_points)

    return f"""
    <section class="slide slide-market" data-slide="{index}">
      <video class="bg-video" muted loop autoplay playsinline></video>
      <div class="slide-overlay"></div>
      <div class="slide-content">
        <h2 class="slide-headline">{_e(slide.headline)}</h2>
        <p class="slide-sub">{_e(slide.subheadline)}</p>
        {metrics_html}
        <ul class="slide-points">{points}</ul>
      </div>
    </section>"""


def _render_team(slide, index: int) -> str:
    members_html = ""
    if slide.team_members:
        cards = []
        for m in slide.team_members:
            name = _e(m.get("name", ""))
            role = _e(m.get("role", ""))
            bio = _e(m.get("bio", ""))
            cards.append(f'<div class="team-card"><div class="team-avatar">{_e(name[:1])}</div><div class="team-name">{name}</div><div class="team-role">{role}</div><div class="team-bio">{bio}</div></div>')
        members_html = f'<div class="team-grid">{"".join(cards)}</div>'

    points = "\n".join(f'<li>{_e(p)}</li>' for p in slide.body_points)

    return f"""
    <section class="slide slide-team" data-slide="{index}">
      <video class="bg-video" muted loop autoplay playsinline></video>
      <div class="slide-overlay"></div>
      <div class="slide-content">
        <h2 class="slide-headline">{_e(slide.headline)}</h2>
        <p class="slide-sub">{_e(slide.subheadline)}</p>
        {members_html}
        <ul class="slide-points">{points}</ul>
      </div>
    </section>"""


def _render_ask(slide, index: int) -> str:
    amount_html = ""
    if slide.funding_amount:
        amount_html = f'<div class="ask-amount">{_e(slide.funding_amount)}</div>'

    funds_html = ""
    if slide.use_of_funds:
        items = []
        for f in slide.use_of_funds:
            cat = _e(f.get("category", f.get("area", "")))
            pct = _e(str(f.get("percentage", f.get("amount", ""))))
            items.append(f'<div class="fund-item"><span class="fund-cat">{cat}</span><span class="fund-pct">{pct}</span></div>')
        funds_html = f'<div class="funds-grid">{"".join(items)}</div>'

    points = "\n".join(f'<li>{_e(p)}</li>' for p in slide.body_points)

    return f"""
    <section class="slide slide-ask" data-slide="{index}">
      <video class="bg-video" muted loop autoplay playsinline></video>
      <div class="slide-overlay"></div>
      <div class="slide-content">
        <h2 class="slide-headline">{_e(slide.headline)}</h2>
        {amount_html}
        <p class="slide-sub">{_e(slide.subheadline)}</p>
        {funds_html}
        <ul class="slide-points">{points}</ul>
      </div>
    </section>"""


def _render_vision(slide, index: int) -> str:
    points = "\n".join(f'<li>{_e(p)}</li>' for p in slide.body_points)
    return f"""
    <section class="slide slide-vision" data-slide="{index}">
      <video class="bg-video" muted loop autoplay playsinline></video>
      <div class="slide-overlay"></div>
      <div class="slide-content cover-content">
        <h2 class="vision-headline">{_e(slide.headline)}</h2>
        <p class="slide-sub">{_e(slide.subheadline)}</p>
        <ul class="slide-points">{points}</ul>
      </div>
    </section>"""


def render_pitch_deck(content: PitchDeckContent, project_name: str) -> str:
    """Render a PitchDeckContent into a self-contained HTML presentation."""

    slides_html = []
    slides_html.append(_render_cover(content.cover))
    slides_html.append(_render_standard(content.problem, 1))
    slides_html.append(_render_standard(content.solution, 2))
    slides_html.append(_render_market(content.market, 3))
    slides_html.append(_render_standard(content.traction, 4, "slide-traction"))
    slides_html.append(_render_standard(content.business_model, 5))
    slides_html.append(_render_team(content.team, 6))
    slides_html.append(_render_ask(content.ask, 7))
    slides_html.append(_render_vision(content.vision, 8))

    total_slides = 9
    dots = "".join(
        f'<span class="dot{" active" if i == 0 else ""}" data-dot="{i}"></span>'
        for i in range(total_slides)
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_e(project_name)} — Pitch Deck</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

html, body {{
  width: 100%; height: 100%; overflow: hidden;
  font-family: 'Plus Jakarta Sans', sans-serif;
  background: #000; color: #fff;
}}

/* --- Slide system --- */
.deck {{ position: relative; width: 100vw; height: 100vh; overflow: hidden; }}

.slide {{
  position: absolute; inset: 0;
  width: 100vw; height: 100vh;
  display: flex; align-items: center; justify-content: center;
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 0.7s cubic-bezier(.4,0,.2,1), transform 0.7s cubic-bezier(.4,0,.2,1);
  pointer-events: none;
  z-index: 0;
}}
.slide.active {{
  opacity: 1; transform: translateY(0);
  pointer-events: auto; z-index: 1;
}}

/* --- Video background --- */
.bg-video {{
  position: absolute; inset: 0;
  width: 100%; height: 100%;
  object-fit: cover;
  opacity: 0.15;
  z-index: 0;
}}
.slide-overlay {{
  position: absolute; inset: 0;
  background: radial-gradient(ellipse at 30% 20%, rgba(99,102,241,0.12) 0%, transparent 60%),
              radial-gradient(ellipse at 70% 80%, rgba(168,85,247,0.08) 0%, transparent 60%),
              linear-gradient(180deg, rgba(0,0,0,0.3) 0%, rgba(0,0,0,0.6) 100%);
  z-index: 1;
}}

/* --- Content --- */
.slide-content {{
  position: relative; z-index: 2;
  max-width: min(90vw, 900px);
  padding: clamp(24px, 4vw, 60px);
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: clamp(16px, 2vw, 28px);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  box-shadow: 0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.06);
}}

/* --- Cover --- */
.cover-content {{ text-align: center; }}
.cover-title {{
  font-size: clamp(36px, 6vw, 80px);
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.1;
  background: linear-gradient(135deg, #fff 0%, rgba(167,139,250,0.9) 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}}
.cover-subtitle {{
  margin-top: clamp(12px, 2vw, 24px);
  font-size: clamp(16px, 2.2vw, 26px);
  font-weight: 300;
  color: rgba(255,255,255,0.7);
}}
.cover-prompt {{
  margin-top: clamp(32px, 4vw, 60px);
  font-size: clamp(11px, 1.2vw, 14px);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  color: rgba(255,255,255,0.35);
  animation: pulse-fade 2s ease-in-out infinite;
}}
@keyframes pulse-fade {{
  0%, 100% {{ opacity: 0.35; }}
  50% {{ opacity: 0.7; }}
}}

/* --- Standard slides --- */
.slide-headline {{
  font-size: clamp(26px, 4vw, 52px);
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.15;
  margin-bottom: clamp(8px, 1vw, 16px);
}}
.slide-sub {{
  font-size: clamp(14px, 1.6vw, 20px);
  font-weight: 300;
  color: rgba(255,255,255,0.6);
  margin-bottom: clamp(16px, 2vw, 32px);
}}
.slide-points {{
  list-style: none;
  display: flex; flex-direction: column;
  gap: clamp(8px, 1vw, 14px);
}}
.slide-points li {{
  font-size: clamp(13px, 1.4vw, 18px);
  font-weight: 400;
  color: rgba(255,255,255,0.8);
  padding-left: 20px;
  position: relative;
}}
.slide-points li::before {{
  content: '';
  position: absolute; left: 0; top: 50%;
  width: 6px; height: 6px;
  border-radius: 50%;
  background: rgba(167,139,250,0.7);
  transform: translateY(-50%);
}}

/* --- Accent metric --- */
.accent-block {{ margin-bottom: clamp(16px, 2vw, 28px); }}
.accent-metric {{
  font-size: clamp(40px, 6vw, 72px);
  font-weight: 800;
  background: linear-gradient(135deg, #a78bfa 0%, #818cf8 50%, #6366f1 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}}
.accent-label {{
  display: block;
  font-size: clamp(11px, 1.2vw, 14px);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: rgba(255,255,255,0.4);
  margin-top: 4px;
}}

/* --- Market metrics --- */
.market-metrics {{
  display: flex; gap: clamp(16px, 3vw, 40px);
  margin-bottom: clamp(16px, 2vw, 32px);
  flex-wrap: wrap;
}}
.market-metric {{
  flex: 1; min-width: 120px;
  padding: clamp(16px, 2vw, 28px);
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: clamp(10px, 1.2vw, 16px);
  text-align: center;
}}
.market-value {{
  display: block;
  font-size: clamp(24px, 3.5vw, 44px);
  font-weight: 800;
  background: linear-gradient(135deg, #a78bfa, #6366f1);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}}
.market-label {{
  display: block;
  font-size: clamp(10px, 1vw, 13px);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  color: rgba(255,255,255,0.4);
  margin-top: 6px;
}}

/* --- Team --- */
.team-grid {{
  display: flex; gap: clamp(12px, 1.5vw, 20px);
  flex-wrap: wrap;
  margin-bottom: clamp(16px, 2vw, 28px);
}}
.team-card {{
  flex: 1; min-width: 140px;
  padding: clamp(16px, 2vw, 24px);
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: clamp(10px, 1.2vw, 16px);
  text-align: center;
}}
.team-avatar {{
  width: clamp(40px, 4vw, 56px); height: clamp(40px, 4vw, 56px);
  border-radius: 50%;
  background: linear-gradient(135deg, #a78bfa, #6366f1);
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto clamp(8px, 1vw, 14px);
  font-size: clamp(16px, 2vw, 22px);
  font-weight: 700;
}}
.team-name {{ font-size: clamp(13px, 1.4vw, 16px); font-weight: 600; }}
.team-role {{ font-size: clamp(11px, 1.1vw, 13px); color: rgba(167,139,250,0.8); margin-top: 2px; }}
.team-bio {{ font-size: clamp(11px, 1vw, 13px); color: rgba(255,255,255,0.5); margin-top: 6px; }}

/* --- Ask --- */
.ask-amount {{
  font-size: clamp(40px, 6vw, 72px);
  font-weight: 800;
  background: linear-gradient(135deg, #a78bfa 0%, #818cf8 50%, #6366f1 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: clamp(8px, 1vw, 16px);
}}
.funds-grid {{
  display: flex; flex-wrap: wrap; gap: clamp(8px, 1vw, 14px);
  margin-bottom: clamp(16px, 2vw, 28px);
}}
.fund-item {{
  flex: 1; min-width: 120px;
  padding: clamp(12px, 1.5vw, 20px);
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: clamp(8px, 1vw, 12px);
  display: flex; flex-direction: column; align-items: center; gap: 4px;
}}
.fund-cat {{ font-size: clamp(11px, 1.1vw, 14px); color: rgba(255,255,255,0.6); }}
.fund-pct {{ font-size: clamp(16px, 2vw, 22px); font-weight: 700; color: #a78bfa; }}

/* --- Vision --- */
.vision-headline {{
  font-size: clamp(30px, 5vw, 60px);
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.1;
  background: linear-gradient(135deg, #fff 0%, rgba(167,139,250,0.9) 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: clamp(12px, 2vw, 24px);
}}

/* --- Progress dots --- */
.progress {{
  position: fixed; bottom: clamp(16px, 2vw, 32px);
  left: 50%; transform: translateX(-50%);
  display: flex; gap: 8px; z-index: 100;
}}
.dot {{
  width: 8px; height: 8px;
  border-radius: 50%;
  background: rgba(255,255,255,0.2);
  transition: background 0.3s, transform 0.3s;
  cursor: pointer;
}}
.dot.active {{
  background: #a78bfa;
  transform: scale(1.3);
}}

/* --- Slide counter --- */
.slide-counter {{
  position: fixed; top: clamp(16px, 2vw, 28px); right: clamp(16px, 2vw, 28px);
  font-size: clamp(11px, 1vw, 13px);
  font-weight: 600;
  color: rgba(255,255,255,0.3);
  letter-spacing: 0.08em;
  z-index: 100;
}}
</style>
</head>
<body>
<div class="deck">
  {"".join(slides_html)}
</div>

<div class="progress">{dots}</div>
<div class="slide-counter"><span id="current">1</span> / {total_slides}</div>

<script>
(function() {{
  const TOTAL = {total_slides};
  let current = 0;
  const slides = document.querySelectorAll('.slide');
  const dots = document.querySelectorAll('.dot');
  const counter = document.getElementById('current');

  function goTo(n) {{
    if (n < 0 || n >= TOTAL) return;
    slides[current].classList.remove('active');
    dots[current].classList.remove('active');
    current = n;
    slides[current].classList.add('active');
    dots[current].classList.add('active');
    counter.textContent = current + 1;
  }}

  // Init first slide
  slides[0].classList.add('active');

  // Keyboard navigation
  document.addEventListener('keydown', function(e) {{
    if (e.key === 'ArrowRight' || e.key === ' ') {{ e.preventDefault(); goTo(current + 1); }}
    if (e.key === 'ArrowLeft') {{ e.preventDefault(); goTo(current - 1); }}
  }});

  // Dot click navigation
  dots.forEach(function(dot, i) {{
    dot.addEventListener('click', function() {{ goTo(i); }});
  }});

  // HLS video backgrounds
  const VIDEO_URL = 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8';
  document.querySelectorAll('.bg-video').forEach(function(video) {{
    if (Hls.isSupported()) {{
      var hls = new Hls({{ enableWorker: false }});
      hls.loadSource(VIDEO_URL);
      hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, function() {{ video.play().catch(function(){{}}); }});
    }} else if (video.canPlayType('application/vnd.apple.mpegurl')) {{
      video.src = VIDEO_URL;
      video.addEventListener('loadedmetadata', function() {{ video.play().catch(function(){{}}); }});
    }}
  }});
}})();
</script>
</body>
</html>"""
