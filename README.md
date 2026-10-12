# Junction Traffic Volume dashboard

A fast, single-file HTML dashboard for junction traffic counts. This replaces the Looker Studio version.
Every Excel export in `data/raw/` is merged into one page with filters for junction, dates, day type, hours and detector.

## Update the data

1. Put each junction's Excel export (same columns as the Looker file) in `data/raw/`.
   Any number of files works, and a file can hold one or several junctions or weeks.
2. For each new junction, add an entry to `data/junctions.json` with its name and stage notes.
   Save its layout image as `data/layouts/<code>.png` (for example `A009.png`).
3. Build:

   ```
   pip install openpyxl
   python3 scripts/build_dashboard.py
   ```

   The script prints rows per file, flags duplicate rows (same junction, date, hour, detector and class),
   and writes `dist/traffic-dashboard.html`.

## Share it

`dist/traffic-dashboard.html` is a single file with the data and layout images inside it.

- **Email or Drive:** send the file. It opens in any browser, even offline (the chart library is
  built into the file; only the fonts need internet, and it falls back to system fonts without it).
- **Link with login:** host it on Cloudflare Pages and add Cloudflare Access (free for up to 50 users)
  so the client signs in with their email.
- **Public link (works on phones):** drag the `dist` folder onto https://app.netlify.com/drop.
  The build also writes `dist/index.html`, so the site opens at its plain link. Anyone with the link can see the data.
- Phones can't open the HTML as an email or WhatsApp attachment (previews don't run scripts), so send phone users a link.

## Files

| Path | What it is |
|---|---|
| `data/raw/` | Excel or CSV exports, one or more per junction |
| `data/junctions.json` | Junction names, stage notes and layout image paths |
| `data/layouts/` | Junction layout images |
| `dashboard/template.html` | Dashboard page (layout, styles, charts) |
| `dashboard/vendor/echarts.min.js` | Chart library (ECharts 5.5.1), embedded into the built page |
| `scripts/build_dashboard.py` | Merges the data and builds the page |
| `dist/traffic-dashboard.html` | The built dashboard to share |
