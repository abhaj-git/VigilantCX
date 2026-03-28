# Abha — consultation page

Static one-page site (`index.html`). No build step.

## Vedic chart workbench (optional)

Python + Streamlit app: date, time, place → Lahiri sidereal grahas + **Lagna**, **D1–D10** signs, **D1 vs D9** and **D1 vs D10** comparison blurbs, **nakshatra/pada** + short notes.

```bash
cd /path/to/VigilantCX
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run vedic_chart/app.py
```

Uses **Swiss Ephemeris** (bundled with `pyswisseph`), **geopy** + **timezonefinder** for place → lat/lon/time zone. Divisional logic is **Parashari-style**; cross-check important charts with your usual software.

## Put it on your own domain

**GitHub (code + free hosting)**

- Your HTML/CSS **stays in the GitHub repo**. That is normal: the repo is the source; visitors load the published copy.
- **GitHub Pages** (static sites): **no extra charge** for typical use on a **free** account with a **public** repo. You pay GitHub only if you use a **paid plan** or add-ons (Copilot, Actions overages, etc.)—not because a small HTML file is stored there.
- **Custom domain**: You buy the domain from a registrar (often about **$10–15/year**). In the repo’s **Pages** settings you add the domain; at the registrar you add the DNS records GitHub shows. **GitHub does not sell the domain.**

**Summary:** Domain ≈ yearly fee to a registrar. Hosting the static page on **GitHub Pages** is **free** on the free tier (public repo). Private repo Pages may require a paid GitHub plan—check current GitHub docs.

**Enable Pages:** Repository **Settings → Pages → Build and deployment → Source**: Deploy from branch **main**, folder **/** (root). Your `index.html` at the repo root will be the homepage.

**Other hosts (also fine):** Netlify, Cloudflare Pages, and Vercel have free tiers for static sites; you can upload `index.html` or connect the same GitHub repo.
