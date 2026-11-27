# Automatic System for Detecting Trends in Fashion - React Frontend

A complete, modern, and responsive React frontend for the college capstone project **"Automatic System for Detecting Trends in Fashion"**.

The application analyzes fashion images (CLIP vision embeddings) and historical H&M customer sales logs to detect emergent clothing categories, patterns, and colour palettes. It interfaces with Gemini AI to generate trend explanations and strategic business recommendations, with an automated 3-day update scheduler (APScheduler).

---

## 🎨 Technology Stack

- **React 18** (Vite build system)
- **Tailwind CSS** (Custom palette: black, white, beige, subtle lavender/pastel accents)
- **Lucide React** (Clean, minimalist icons)
- **Recharts** (Interactive responsive Bar, Pie, Line, and Area charts)
- **Axios** (Reusable API service client for Flask backend)

---

## 🔌 Backend Connection

The frontend connects directly to your existing Flask backend running at:
```
http://127.0.0.1:5000
```

All requests route strictly through the designated endpoints:

| Endpoint | Method | Purpose |
| :--- | :---: | :--- |
| `/` | `GET` | Backend server status check |
| `/api/image-tags` | `GET` / `POST` | Retrieve and add fashion image tag records |
| `/api/fashionpedia` | `GET` | Fashionpedia dataset classification results |
| `/api/trends` | `GET` | Category and pattern fashion trend frequencies |
| `/api/combined-trends`| `GET` | Fused score (Vision % + H&M Sales %) |
| `/api/hm-sales` | `GET` | Raw and aggregated H&M historical sales data |
| `/api/hm-monthly-sales`| `GET` | Monthly sales turnover |
| `/api/hm-growth` | `GET` | Month-over-month growth velocity |
| `/api/hm-comparisons` | `GET` | Visual trends vs sales performance comparisons |
| `/api/hm-popularity` | `GET` | H&M garment popularity indices |
| `/api/ai-analysis` | `GET` | Gemini AI trend explanations and merchandising tips |

> **Note:** If your Flask backend runs on a different port or host in production, create a `.env` file with `VITE_BACKEND_URL=http://your-flask-host:port`.

---

## 📑 Application Pages & Sections

1. **Dashboard**
   - High-level project summary with college capstone hero section.
   - Dynamic record counters (Image tags, trends, combined metrics, H&M logs).
   - Overview table of the latest top-ranking trends and Gemini AI highlights.

2. **Fashion Trends**
   - Clothing category distribution bar chart.
   - Pattern distribution donut chart (floral, solid, striped, etc.).
   - Clothing colour distribution chart.

3. **Combined Trend Analysis**
   - Top 3 ranked fashion categories with podium cards.
   - Side-by-side comparison chart of Image Detection % vs H&M Sales %.
   - Full sortable interactive table (sorting by Image %, Sales %, and Combined Score).

4. **H&M Sales Analysis**
   - Monthly sales volume area chart (`/api/hm-monthly-sales`).
   - Monthly growth velocity bar chart (`/api/hm-growth`).
   - Category popularity horizontal ranking chart (`/api/hm-popularity`).
   - Summary statistics cards.

5. **AI Insights**
   - Real-time display of Gemini AI trend analysis (`/api/ai-analysis`).
   - Formatted executive summaries, trend dynamics, and actionable merchandising recommendations.
   - Integrated loading states and error notifications.

6. **Image Tags**
   - Interactive searchable table with image ID, clothing type, pattern, and color badge.
   - Quick-add form to create and post new records directly to `POST /api/image-tags`.

---

## 🚀 Setup & Execution Guide

### 1. Prerequisites
- **Node.js** (v18 or higher recommended)
- **Flask backend** running at `http://127.0.0.1:5000`

### 2. Install Dependencies
In the frontend project root folder, run:
```bash
npm install
```

### 3. Run the Development Server
```bash
npm run dev
```
Open your browser and navigate to `http://localhost:3000` (or the URL printed by Vite).

### 4. Build for Production
To create an optimized production bundle:
```bash
npm run build
```
The compiled assets will be placed in the `dist/` directory.

---

## 🛠️ Project Structure

```
fashion/
├── public/
│   └── favicon.svg
├── src/
│   ├── components/
│   │   ├── common/
│   │   │   └── FeedbackStates.jsx   # Loading, Error, Empty, and SectionHeader
│   │   └── layout/
│   │       ├── Header.jsx           # Topbar with backend connectivity indicator
│   │       └── Sidebar.jsx          # Left navigation bar with fashion chic styling
│   ├── context/
│   │   └── BackendContext.jsx       # Global status polling & connection state
│   ├── pages/
│   │   ├── Dashboard.jsx            # Project overview & high-level statistics
│   │   ├── FashionTrends.jsx        # Category, pattern, and color distributions
│   │   ├── CombinedTrendAnalysis.jsx# Fused multimodal visual & sales scores
│   │   ├── HmSalesAnalysis.jsx      # Historical sales, growth, and popularity
│   │   ├── AiInsights.jsx           # Gemini AI natural language explanations
│   │   └── ImageTags.jsx            # Dataset table & POST /api/image-tags form
│   ├── services/
│   │   └── api.js                   # Axios client for all 11 Flask endpoints
│   ├── App.jsx                      # Root container & view routing
│   ├── index.css                    # Tailwind CSS directives & theme scrollbar
│   └── main.jsx                     # Vite React entrypoint
├── index.html
├── package.json
├── tailwind.config.js
└── vite.config.js
```
