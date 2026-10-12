# Junction Traffic Volume dashboard

A fast, single-file HTML dashboard for junction traffic counts. This replaces the Looker Studio version.
Every Excel export in `data/raw/` is merged into one page with filters for junction, dates, day type, hours and detector.

## Update the data

1. Put each junction's Excel export in `data/raw/`. The file needs a sheet with the columns
   `Date, Hour, Detector, Stage, Class, Vehicles, Junction` (extra columns and extra sheets, such as
   summaries, are ignored; `Day_Type` and `Detector_Sort` are filled in when missing).
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

## Clickable detectors on the layout image

Each junction's detectors can appear as clickable pins on its layout image. Positions are set once per junction:

1. Build the dashboard, then open `dist/traffic-dashboard.html` in Chrome or Edge.
2. Add `#place` to the end of the address (for example `...traffic-dashboard.html#place`) and press Enter.
3. Choose the junction, then click the image where each detector is, in the order shown (D1, D2, ...).
   Use **Skip** for detectors you don't want on the map and **Undo** to redo the last click.
4. Click **Copy text** and paste it into that junction's entry in `data/junctions.json`, after its `"stages"` block:

   ```json
   "A009": {
     "name": "...",
     "layout_image": "layouts/A009.png",
     "stages": { ... },
     "detector_positions": {
       "D1": [20.5, 31.2],
       "D2": [28.1, 31.0]
     }
   }
   ```

   Remember the comma after the `"stages"` block's closing `}`.
5. Rebuild. Pins are coloured by stage, and clicking one filters every chart to that detector.

## Downloads

- **PNG** button on each chart: saves the chart with its title, junction, dates and active filters.
- **Download Excel** in the filter bar: saves an .xlsx of the current view, with a Summary sheet
  (totals, detectors, vehicle classes, hourly averages) and a Data sheet (every row, with filter arrows).

Downloads work in the shared file and on a hosted link.

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
| `data/logo.png` | Company logo shown top right (optional; remove it to hide the logo) |
| `dashboard/template.html` | Dashboard page (layout, styles, charts) |
| `dashboard/vendor/echarts.min.js` | Chart library (ECharts 5.5.1), embedded into the built page |
| `scripts/build_dashboard.py` | Merges the data and builds the page |
| `dist/traffic-dashboard.html` | The built dashboard to share |
