# PRD — King Signal Member Dashboard

> **Product**: Member dashboard analisa trading dari king-signal-dashboard
> **Owner**: Fizz (@Fizzdn)
> **Created**: 2026-06-05
> **Status**: Planning
> **Deploy**: VPS Tencent (129.226.205.71)

---

## 1. Objective

Build **member-only dashboard** yang menampilkan analisa trading dari king-signal-dashboard dalam format profesional (TradingView-style) — supaya member bisa lihat detail analisa, trade plan, dan performa bot secara real-time.

**Goal utama:**
- Member bisa lihat analisa per-pair secara detail (chart, entry, SL, TP, RR)
- Dashboard terasa premium dan profesional
- Data bersumber 100% dari king-signal-dashboard (signals.sqlite3)
- Akses hanya untuk member (gate via Telegram login / invite link)

---

## 2. Target Users

| Segment | Need |
|---------|------|
| **Pro/VIP subscribers** | Lihat detail analisa sebelum eksekusi trade |
| **New members** | Pahami bagaimana bot membaca market |
| **Potential buyers** | Preview kualitas analisa sebelum subscribe |

---

## 3. Dashboard Sections

### 3.1 Market Overview (Home)
- **Top bar**: Pair selector (BTC, ETH, BNB, SOL) + timeframe filter
- **Market bias indicator**: Bullish / Bearish / Neutral per pair
- **Active signals count**: Berapa sinyal aktif sekarang
- **Quick stats**: Win rate hari ini, PnL hari ini, total signals

### 3.2 Signal Analysis View (per pair)
Mirip screenshot yang dikasih Fizz:

```
┌─────────────────────────────────────────────────────────┐
│ SOLUSDT · 1H                                            │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │           CHART AREA (TradingView widget)         │  │
│  │   Price action + EMA + SAR + Entry/SL/TP zones    │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  AI Pre-Trade Analysis                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                │
│  │ Rating   │ │ Confid.  │ │ Bias     │                │
│  │ B+       │ │ 72%      │ │ Bullish  │                │
│  └──────────┘ └──────────┘ └──────────┘                │
│                                                         │
│  Trade Plan                                             │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Direction  │ Entry     │ Stop Loss │ Take Profit │   │
│  │ LONG       │ 74.90     │ 71.80     │ 87.70       │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Leverage │ Position  │ Risk    │ RR Ratio       │   │
│  │ 10x      │ 500 USDT  │ $15.51  │ 2.19           │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Confluence Factors                                     │
│  ✓ BoS detected  ✓ Golden zone  ✓ FVG present          │
│  ✓ Volume spike  ✓ Orderbook bias                       │
│                                                         │
│  Structure JSON (expandable)                            │
│  { bos_level, choch_level, ob_zone, fib_levels... }     │
└─────────────────────────────────────────────────────────┘
```

### 3.3 Trade History
- Table: semua closed trades dengan detail
- Filter: pair, timeframe, date range, result (win/loss)
- Sort: newest, best PnL, worst PnL
- Export: CSV download

### 3.4 Performance Analytics
- Equity curve (cumulative PnL)
- Win rate pie chart (win/loss/breakeven)
- Per-pair breakdown bar chart
- Best/worst trade highlights
- Streak tracker (current win/loss streak)
- Monthly/weekly PnL summary

### 3.5 Signal Feed (Real-time)
- Live feed sinyal baru (auto-refresh)
- Card format: pair, direction, entry zone, confidence, timestamp
- Push notification via Telegram saat sinyal baru masuk

---

## 4. Data Model

### From signals.sqlite3:

**signals table:**
```
id, pair, timeframe, direction, entry_zone, stop_loss, tp1, tp2,
confluence_score, structure_json, fib_json, created_at
```

**paper_trades table:**
```
id, pair, direction, timeframe, entry_price, stop_loss, tp1, tp2,
position_size, leverage, status, exit_price, exit_reason,
pnl_usd, pnl_pct, opened_at, closed_at
```

### Derived data (API computes):
```
- rating: A/B/C/D based on confluence_score
- confidence: 0-100% based on confluence factors
- bias: BULLISH/BEARISH/NEUTRAL from direction + HTF analysis
- risk_reward: (tp1 - entry) / (entry - sl)
- confluence_flags: {bos, ob, fvg, volume, orderbook}
```

---

## 5. Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MEMBER DASHBOARD                          │
│               (HTML + Tailwind + Alpine.js)                  │
│                                                              │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │ Pair     │  │ Signal       │  │ Performance           │  │
│  │ Selector │  │ Analysis     │  │ Dashboard             │  │
│  └──────────┘  │ (chart+plan) │  │ (charts+stats)        │  │
│                └──────────────┘  └───────────────────────┘  │
│                                                              │
└──────────────────────────┬──────────────────────────────────┘
                           │ API calls
                ┌──────────▼──────────┐
                │  Dashboard API      │
                │  (FastAPI)          │
                │                     │
                │  GET /api/overview  │
                │  GET /api/signals   │
                │  GET /api/signal/:id│
                │  GET /api/history   │
                │  GET /api/stats     │
                │  GET /api/equity    │
                └──────────┬──────────┘
                           │
                ┌──────────▼──────────┐
                │  SQLite (WAL)       │
                │  signals.sqlite3    │
                │  (king-signal-dashboard)   │
                └─────────────────────┘
```

---

## 6. API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /api/overview` | GET | Market overview: bias per pair, active signals, today stats |
| `GET /api/signals` | GET | Recent signals with full analysis data |
| `GET /api/signal/:id` | GET | Single signal detail (structure, fib, confluence) |
| `GET /api/history` | GET | Closed trades with filters (pair, tf, date, result) |
| `GET /api/stats` | GET | Aggregated performance stats |
| `GET /api/equity` | GET | Cumulative PnL curve data |
| `GET /api/pairs` | GET | Per-pair breakdown |
| `GET /api/feed` | GET | Real-time signal feed (last 24h) |

---

## 7. Chart Integration

### TradingView Lightweight Charts
- Library: `lightweight-charts` (TradingView open-source)
- Data: OHLCV from Binance API (real-time or cached)
- Overlays: Entry zone (horizontal lines), SL/TP levels, EMA, SAR
- Markers: Signal entry point, BoS/CHoCH events

### Alternative: Chart.js
- Simpler, already used on landing page
- Line/candle chart with annotations
- Less features but smaller bundle

**Recommendation**: TradingView Lightweight Charts — lebih profesional, cocok untuk audience trader.

---

## 8. Access Control

### Option A: Telegram Login Widget (recommended)
- User login via Telegram OAuth
- Check if user is in allowed list / has active subscription
- Session cookie after login
- Pro: familiar for Telegram users, no password needed

### Option B: Token-based
- Unique invite link per member: `dashboard.kingsignal.com/?token=xxx`
- Token generated on subscription activation
- Pro: no login needed, easy to share

### Option C: Simple password
- Single shared password for all members
- Pro: simplest to implement
- Con: less secure, can't track individual access

**Recommendation**: Option A (Telegram Login) untuk Pro/VIP, Option B (token link) untuk Free tier.

---

## 9. Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | HTML + Tailwind CSS + Alpine.js | Same as landing page, zero build |
| Charts | TradingView Lightweight Charts | Professional, trading-focused |
| API | FastAPI (Python) | Same stack, async, fast |
| Database | SQLite (existing king-signal-dashboard DB) | Already populated |
| Auth | Telegram Login Widget | Familiar, no password |
| Server | Nginx + Certbot | Existing VPS pattern |
| Process | systemd | Durable, auto-restart |

---

## 10. UI Design System

### Color Palette (same as landing page)
```
bg:      #06080d  (background)
surface: #0b0f17  (card bg)
card:    #111827  (elevated card)
border:  #1e293b  (borders)
neon:    #00ff9c  (positive/bullish)
acid:    #b6ff3c  (accent)
pink:    #ff3ea5  (negative/bearish)
muted:   #64748b  (secondary text)
```

### Typography
- Headings: Inter 700/800
- Body: Inter 400/500
- Numbers/prices: JetBrains Mono
- Price change: green (up) / red (down)

### Components
- Signal card: pair badge + direction + entry + confidence bar
- Stat card: icon + label + value + change indicator
- Trade row: pair + direction + entry/exit + PnL + time
- Chart container: dark bg + neon grid + price line

---

## 11. Mobile Responsiveness

- **Mobile-first** design (target: TikTok users = mostly mobile)
- Chart: full-width, pinch-to-zoom
- Signal cards: stacked layout
- Navigation: bottom tab bar (Overview / Signals / History / Profile)
- Trade table: horizontal scroll on mobile

---

## 12. Milestones

| Phase | Deliverable | Est. Duration |
|-------|-------------|---------------|
| **Phase 1** | PRD + Design mockup | 1 day |
| **Phase 2** | Dashboard API (FastAPI) | 1-2 days |
| **Phase 3** | Frontend: Market Overview + Signal View | 2-3 days |
| **Phase 4** | Frontend: History + Analytics | 1-2 days |
| **Phase 5** | TradingView chart integration | 1 day |
| **Phase 6** | Auth (Telegram Login) | 1 day |
| **Phase 7** | Deploy + SSL + domain | 0.5 day |
| **Phase 8** | Testing + polish | 1 day |

**Total estimate: 8-11 days to launch**

---

## 13. Success Metrics

| Metric | Target (30 days) |
|--------|------------------|
| Member dashboard visits | 500+ |
| Avg session duration | > 3 min |
| Signal views per session | 5+ |
| Member retention (weekly active) | 60%+ |
| Conversion: dashboard visitor → paid | 5%+ |

---

## 14. Open Questions

- [ ] Domain untuk dashboard? (e.g., dashboard.kingsignal.com atau subpath /dashboard)
- [ ] TradingView chart: pakai widget embed atau lightweight-charts library?
- [ ] Auth method final: Telegram Login vs token link vs both?
- [ ] Real-time update: polling vs WebSocket vs SSE?
- [ ] Binance OHLCV data: fetch live atau cache di server?

---

*PRD v1.0 — King Signal Member Dashboard*
