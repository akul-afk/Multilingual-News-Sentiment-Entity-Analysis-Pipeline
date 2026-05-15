# UI Design & Aesthetics — Vintage Press

The **Global News Pulse** dashboard utilizes a unique **"Vintage Press"** design language. It is conceptualized as an archival intelligence terminal from the mid-20th century, combining the ruggedness of a field dossier with the typographical precision of a printing house.

---

## 🎨 Design Philosophy

The aesthetic is built on three core pillars:
1.  **Tactical Archival**: Interfaces should feel like "physical" documents — torn edges, ink bleeds, and parchment textures.
2.  **High-Density Intelligence**: Prioritize high-information density (ledgers, grids, and charts) over white space, evoking the feeling of a packed newspaper or a military briefing.
3.  **Digital Marginalia**: Use handwritten-style annotations and "blueprint" backgrounds to simulate human analysis on top of automated data.

---

## 🔑 Design Tokens

### Color Palette (Ink & Parchment)
| Token | Hex | Role |
|-------|-----|------|
| `--bg` | `#f4e9d9` | Primary parchment background |
| `--surface` | `#ede1cf` | Secondary paper surface |
| `--text` | `#2d1b0d` | Primary ink black |
| `--primary` | `#8b0000` | Oxide Red (Alerts, Highlights) |
| `--outline` | `#5a3c1e` | Sepia (Borders, Dividers) |
| `--positive`| `#1b4d3e` | Verdigris (Positive Sentiment) |

### Typography
*   **Headings**: `Old Standard TT` (Classic serif for high-authority titles)
*   **Body**: `IBM Plex Serif` (Legible, journalistic serif)
*   **Marginalia**: `Shadows Into Light` (Handwritten annotations)
*   **Data/Sketch**: `Inter` (Clean sans-serif for UI controls)

---

## 🧱 Component Architecture

The UI is built using **Vanilla JS Components** and **Modern CSS Clipping**.

### 1. The Torn Wrapper (`.torn-wrapper`)
The fundamental layout unit. It uses a `clip-path` polygon to simulate a rugged, hand-torn edge on the bottom of containers.
```css
clip-path: polygon(0% 0%, 100% 0%, 100% 98%, 98% 100%, 90% 99%, ...);
```

### 2. The KPI Snapshot (`.kpi`)
Used for top-level metrics. Features:
*   **Ink Bleed Filter**: A SVG Gaussian blur filter applied to large numbers to simulate ink spreading on cheap paper.
*   **Status Indicators**: "⊕" and "⊖" symbols for trend direction.

### 3. The Intelligence Ledger (`.table-vintage`)
High-density tables with dashed borders and hover-highlighting. Used extensively in the **Entity Explorer** and **Sentiment** screens.

### 4. The Dossier Panel (`.dossier-active`)
A specialized container in the Entity Explorer that acts as a "folder" for a selected actor, featuring a sentiment slider and connection tags.

---

## 🖥️ Screen Layouts

### 1. Executive Overview
The dashboard entry point. Displays 3 key KPIs, a 30-day sentiment trend, and the latest translated dispatches.

### 2. Narrative Sentiment
Focuses on the "Axis of Bias." Displays:
*   **Polarity by Dispatch**: A bar chart comparing regional sentiment.
*   **Source Deviation**: How much a specific language service diverges from the global mean.

### 3. Cross-Language Divergence
A comparative view showing current vs. historical sentiment per language, highlighting shifts in regional narratives.

### 4. Entity Explorer (Intelligence Ledger)
An interactive actor database. Users filter by type (Person, Org, GPE) and select rows to populate a detailed **Dossier** on the left.

### 5. Geographic Heatmap (Spatial Nodes)
A Leaflet-based world map utilizing a custom sepia filter. Mentions are represented as "Intelligence Nodes" that reveal metadata on hover.

### 6. Archival Reports
A deep-dive section (accessible via the Sidebar) that serves long-form, AI-generated executive summaries. These reports are formatted as full-page news briefings with:
*   "Intelligence Bulletins"
*   Regional breakdown tables
*   Thematic impact assessments

---

## 🛠️ Implementation Workflow

To add a new component while maintaining the Vintage Press aesthetic:
1.  Wrap the element in a `.torn-wrapper` to provide the base drop-shadow.
2.  Use `.torn-container` for the actual content area.
3.  Avoid rounded corners (`border-radius: 0`).
4.  Use `1px dashed var(--outline)` for internal dividers.
5.  Apply the `sepia()` filter to any external assets or maps.
