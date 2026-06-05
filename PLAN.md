# Project Plan — King Signal Member Dashboard

> **Created**: 2026-06-05
> **Owner**: Fizz
> **Deploy**: VPS Tencent (129.226.205.71)
> **Repo**: king-signal-dashboard

---

## Phase 1: Foundation (Day 1)

### 1.1 Project Setup
- [ ] Init project structure on VPS Tencent
- [ ] Setup directory: `/var/www/king-signal-dashboard/`
- [ ] Copy signals.sqlite3 DB path reference
- [ ] Setup systemd service for dashboard API
- [ ] Setup nginx config for dashboard domain/path

### 1.2 Design System
- [ ] Reuse landing page color palette + typography
- [ ] Component library: signal cards, stat cards, trade rows, chart containers
- [ ] Mobile-first grid layout
- [ ] Bottom tab bar navigation (mobile)

---

## Phase 2: Dashboard API (Day 2-3)

### 2.1 Core API Endpoints
- [ ] `GET /api/overview` — market bias per pair, active signals count, today stats
- [ ] `GET /api/signals` — recent signals with full analysis (paginated)
- [ ] `GET /api/signal/:id` — single signal detail (structure_json, fib_json, confluence)
- [ ] `GET /api/history` — closed trades with filters (pair, tf, date, result)
- [ ] `GET /api/stats` — aggregated performance (win rate, PnL, sharpe, drawdown)
- [ ] `GET /api/equity` — cumulative PnL curve
- [ ] `GET /api/pairs` — per-pair breakdown
- [ ] `GET /api/feed` — real-time signal feed (last 24h)

### 2.2 Data Enrichment
- [ ] Compute `rating` (A/B/C/D) from confluence_score
- [ ] Compute `confidence` (0-100%) from confluence factors
- [ ] Compute `bias` (BULLISH/BEARISH/NEUTRAL) from direction
- [ ] Compute `risk_reward` from entry/SL/TP
- [ ] Parse `structure_json` → confluence flags (bos, ob, fvg, volume, orderbook)
- [ ] Parse `fib_json` → fib levels display

### 2.3 Binance OHLCV Integration
- [ ] Fetch OHLCV data from Binance API for chart
- [ ] Cache OHLCV in Redis or file (refresh every 5m)
- [ ] Endpoint: `GET /api/ohlcv?pair=SOLUSDT&interval=1h&limit=200`

---

## Phase 3: Market Overview (Day 3-4)

### 3.1 Overview Page
- [ ] Top bar: pair selector (BTC, ETH, BNB, SOL) + timeframe filter
- [ ] Market bias cards per pair (bullish/bearish/neutral + confidence)
- [ ] Active signals count badge
- [ ] Quick stats row: win rate today, PnL today, signals today
- [ ] Recent signals mini-cards (last 5)

### 3.2 Signal Feed
- [ ] Real-time feed component (auto-refresh every 30s)
- [ ] Signal card: pair badge, direction arrow, entry zone, confidence bar, timestamp
- [ ] Click → navigate to signal detail view
- [ ] New signal indicator (pulse animation)

---

## Phase 4: Signal Analysis View (Day 4-6)

### 4.1 Signal Detail Page
- [ ] Header: pair + timeframe + direction badge + timestamp
- [ ] Chart area: TradingView Lightweight Chart
  - Candlestick data from Binance OHLCV
  - Entry zone overlay (horizontal band)
  - Stop Loss line (red)
  - Take Profit lines (green, TP1 + TP2)
  - EMA overlay (20, 50, 200)
  - SAR dots
  - BoS/CHoCH markers
- [ ] AI Pre-Trade Analysis section
  - Rating badge (A/B/C/D with color)
  - Confidence bar (0-100%)
  - Bias indicator (bullish/bearish/neutral)
- [ ] Trade Plan table
  - Direction, Entry, Stop Loss, TP1, TP2
  - Leverage, Position Size, Risk Amount
  - Risk:Reward ratio
- [ ] Confluence Factors
  - Checklist: BoS ✓, OB ✓, FVG ✓, Volume ✓, Orderbook ✓
  - Each with detail on hover/click
- [ ] Structure JSON (expandable accordion)
  - Raw JSON view for advanced users
  - Pretty-printed with syntax highlighting

### 4.2 Chart Features
- [ ] Timeframe switcher (5m, 15m, 30m, 1h, 4h)
- [ ] Crosshair with price/time display
- [ ] Zoom/pan
- [ ] Responsive: full-width on mobile, pinch-to-zoom
- [ ] Dark theme matching dashboard

---

## Phase 5: Trade History & Analytics (Day 6-7)

### 5.1 History Table
- [ ] Columns: Time, Pair, TF, Direction, Entry, Exit, PnL, Result
- [ ] Filters: pair, timeframe, date range, result (win/loss)
- [ ] Sort: newest, best PnL, worst PnL
- [ ] Pagination (20 per page)
- [ ] CSV export button
- [ ] Color-coded PnL (green profit, red loss)

### 5.2 Analytics Dashboard
- [ ] Equity curve chart (cumulative PnL)
- [ ] Win rate donut chart (win/loss/breakeven)
- [ ] Per-pair PnL bar chart
- [ ] Best/worst trade highlight cards
- [ ] Streak tracker (current win/loss streak, max streak)
- [ ] Monthly/weekly PnL summary table
- [ ] Sharpe ratio, max drawdown, profit factor

---

## Phase 6: Auth & Access Control (Day 7-8)

### 6.1 Telegram Login Widget
- [ ] Integrate Telegram Login Widget
- [ ] Backend: verify Telegram auth hash
- [ ] Check user against allowed list (DB or config)
- [ ] Session management (cookie-based)
- [ ] Login page with Telegram button

### 6.2 Access Tiers
- [ ] Free: limited signals (delayed 15m), basic stats
- [ ] Pro: all signals real-time, full analytics
- [ ] VIP: everything + orderbook data + risk regime
- [ ] Gate features based on tier

### 6.3 Token-based Access (alternative)
- [ ] Generate unique token per member
- [ ] URL: `dashboard.kingsignal.com/?token=xxx`
- [ ] Token validation middleware
- [ ] Token expiry management

---

## Phase 7: Deploy (Day 8-9)

### 7.1 Infrastructure
- [ ] Nginx config: `dashboard.kingsignal.com` or `/dashboard` path
- [ ] SSL cert (Certbot)
- [ ] Systemd service for dashboard API
- [ ] CORS config for landing page domain

### 7.2 Performance
- [ ] Gzip compression
- [ ] Static asset caching (30d)
- [ ] API response caching (60s for stats)
- [ ] Lazy load charts
- [ ] Lighthouse score target: 90+

---

## Phase 8: Polish & Launch (Day 9-11)

### 8.1 QA
- [ ] Mobile testing (iOS Safari, Android Chrome)
- [ ] Desktop testing (Chrome, Firefox, Edge)
- [ ] API load testing
- [ ] Auth flow testing
- [ ] Edge cases: no data, API down, empty states

### 8.2 Content
- [ ] Onboarding tooltip (first-time user)
- [ ] Empty state illustrations
- [ ] Error state messages
- [ ] Loading skeletons

### 8.3 Launch
- [ ] Push to production
- [ ] Announce to members via Telegram
- [ ] Add dashboard link to landing page
- [ ] Monitor analytics

---

## File Structure

```
king-signal-dashboard/
├── PRD.md
├── PLAN.md
├── README.md
├── .gitignore
├── dashboard/
│   ├── index.html          # Main dashboard SPA
│   ├── login.html          # Telegram login page
│   ├── css/
│   │   └── dashboard.css   # Custom styles
│   ├── js/
│   │   ├── app.js          # Alpine.js app logic
│   │   ├── charts.js       # TradingView chart setup
│   │   ├── api.js          # API fetch wrapper
│   │   └── auth.js         # Telegram login handler
│   └── assets/
│       └── img/
├── api/
│   ├── main.py             # FastAPI app
│   ├── routes/
│   │   ├── overview.py
│   │   ├── signals.py
│   │   ├── history.py
│   │   └── stats.py
│   ├── models.py           # Data models
│   ├── enrichments.py      # Rating, confidence, bias computation
│   ├── binance.py          # OHLCV fetcher
│   └── requirements.txt
├── nginx/
│   └── kingsignal-dashboard.conf
└── systemd/
    └── kingsignal-dashboard.service
```

---

## Dependencies

```
fastapi>=0.109.0
uvicorn>=0.27.0
aiosqlite>=0.19.0
httpx>=0.26.0        # Binance API calls
python-telegram-bot>=20.0  # Telegram auth verification
```

---

*Plan v1.0 — Siap eksekusi ke VPS Tencent*
