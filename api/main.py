"""
King Signal — Member Dashboard API
Serves trading analysis data from fib-signal-bot signals.sqlite3
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="King Signal Dashboard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

DB_PATH = os.getenv("SIGNALS_DB", "signals.sqlite3")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ─── Enrichment Helpers ───────────────────────────────────

def compute_rating(confluence_score: int) -> str:
    if confluence_score >= 80:
        return "A+"
    elif confluence_score >= 65:
        return "A"
    elif confluence_score >= 50:
        return "B+"
    elif confluence_score >= 35:
        return "B"
    elif confluence_score >= 20:
        return "C"
    return "D"


def compute_confidence(confluence_score: int) -> int:
    return min(100, max(0, confluence_score))


def compute_rr(entry: float, sl: float, tp1: float) -> float:
    risk = abs(entry - sl)
    reward = abs(tp1 - entry)
    if risk == 0:
        return 0
    return round(reward / risk, 2)


def parse_confluence(structure_json: str) -> dict:
    flags = {"bos": False, "choch": False, "ob": False, "fvg": False, "volume": False, "orderbook": False}
    if not structure_json:
        return flags
    try:
        s = json.loads(structure_json) if isinstance(structure_json, str) else structure_json
        flags["bos"] = bool(s.get("bos"))
        flags["choch"] = bool(s.get("choch"))
        flags["ob"] = bool(s.get("ob"))
        flags["fvg"] = bool(s.get("fvg"))
        flags["volume"] = bool(s.get("volume_spike") or s.get("volume"))
        flags["orderbook"] = bool(s.get("orderbook_bias") or s.get("orderbook"))
    except (json.JSONDecodeError, TypeError):
        pass
    return flags



def generate_analysis_text(pair: str, timeframe: str, direction: str, confluence_flags: dict,
                           entry_zone: dict, stop_loss: float, tp1: float, tp2: float,
                           fib_levels: dict, structure_json: str, confluence_score: int) -> str:
    """Generate human-readable analysis explanation from signal data."""
    parts = []
    bias_text = "bullish" if direction == "LONG" else "bearish"
    pair_clean = pair.replace("USDT", "")

    # Intro
    active_conf = [k for k, v in confluence_flags.items() if v]
    if len(active_conf) >= 5:
        parts.append(f"Setup {pair_clean} pada {timeframe} menunjukkan konfluensi yang sangat kuat dengan {len(active_conf)} faktor yang saling mengkonfirmasi.")
    elif len(active_conf) >= 4:
        parts.append(f"Setup {pair_clean} pada {timeframe} memiliki konfluensi yang solid dengan {len(active_conf)} faktor pendukung.")
    elif len(active_conf) >= 2:
        parts.append(f"Setup {pair_clean} pada {timeframe} menunjukkan beberapa sinyal, namun konfluensi masih terbatas ({len(active_conf)} faktor).")
    else:
        parts.append(f"Setup {pair_clean} pada {timeframe} memiliki konfluensi rendah ({len(active_conf)} faktor). Hati-hati dengan sinyal ini.")

    # Structure analysis
    struct_notes = []
    if confluence_flags.get("bos"):
        struct_notes.append("Break of Structure (BoS) terdeteksi — struktur market telah berubah, mengkonfirmasi perubahan tren.")
    if confluence_flags.get("choch"):
        struct_notes.append("Change of Character (CHoCH) teridentifikasi — pembalikan arah sudah terkonfirmasi.")
    if confluence_flags.get("ob"):
        struct_notes.append("Order Block terdeteksi di zona entry — area di mana smart money kemungkinan besar melakukan akumulasi.")
    if confluence_flags.get("fvg"):
        struct_notes.append("Fair Value Gap (FVG) hadir di sekitar entry — harga cenderung tertarik ke area ini untuk mengisi ketidakseimbangan.")
    if confluence_flags.get("volume"):
        struct_notes.append("Volume spike terdeteksi — ada peningkatkan aktivitas yang mendukung arah trade.")
    if confluence_flags.get("orderbook"):
        struct_notes.append("Analisa orderbook menunjukkan bias yang searah — likuiditas mendukung posisi ini.")
    parts.extend(struct_notes)

    # Fib analysis
    if fib_levels:
        golden = []
        for lv in ["61.8", "78.6"]:
            if lv in fib_levels:
                golden.append(f"{lv}% ({fib_levels[lv]["price"]:.2f})")
        if golden:
            parts.append(f"Golden zone Fibonacci berada di level {" dan ".join(golden)} — entry berada di area retrace ideal.")

    # Entry zone
    if entry_zone and isinstance(entry_zone, dict):
        low = entry_zone.get("low", 0)
        high = entry_zone.get("high", 0)
        if low and high:
            parts.append(f"Zona entry: {low:.2f} - {high:.2f}.")

    # Risk assessment
    risk = abs(entry_zone.get("mid", entry_zone.get("price", 0)) - stop_loss) if isinstance(entry_zone, dict) else 0
    reward = abs(tp1 - entry_zone.get("mid", entry_zone.get("price", 0))) if isinstance(entry_zone, dict) else 0
    if risk > 0 and reward > 0:
        rr = reward / risk
        if rr >= 3:
            parts.append(f"Risk:Reward sangat menguntungkan (1:{rr:.1f}) — potensi profit jauh lebih besar dari risiko.")
        elif rr >= 2:
            parts.append(f"Risk:Reward solid (1:{rr:.1f}) — rasio yang layak untuk dieksekusi.")
        else:
            parts.append(f"Risk:Reward cukup ketat (1:{rr:.1f}) — pertimbangkan position sizing yang hati-hati.")

    # Conclusion
    if len(active_conf) >= 4:
        parts.append("Kesimpulan: Setup ini layak dipertimbangkan untuk entry dengan manajemen risiko yang ketat.")
    else:
        parts.append("Kesimpulan: Konfluensi belum cukup kuat. Disarankan menunggu konfirmasi tambahan sebelum entry.")

    return " ".join(parts)

def format_signal(row: dict) -> dict:
    confluence_score = row.get("confluence_score", 0)
    entry = row.get("entry_price") or (json.loads(row["entry_zone"]).get("mid", 0) if row.get("entry_zone") else 0)
    
    # Parse entry zone
    entry_zone = {}
    if row.get("entry_zone"):
        try:
            entry_zone = json.loads(row["entry_zone"])
        except (json.JSONDecodeError, TypeError):
            entry_zone = {"mid": entry}
    
    # Parse fib levels
    fib = {}
    if row.get("fib_json"):
        try:
            fib = json.loads(row["fib_json"])
        except (json.JSONDecodeError, TypeError):
            pass

    flags = parse_confluence(row.get("structure_json"))
    active_count = sum(1 for v in flags.values() if v)
    show_plan = active_count >= 4

    return {
        "id": row["id"],
        "pair": row["pair"],
        "timeframe": row["timeframe"],
        "direction": row["direction"],
        "entry_zone": entry_zone,
        "entry_price": row.get("entry_price") or entry,
        "stop_loss": row["stop_loss"],
        "tp1": row["tp1"],
        "tp2": row.get("tp2"),
        "rating": compute_rating(confluence_score),
        "confidence": compute_confidence(confluence_score),
        "bias": "BULLISH" if row["direction"] == "LONG" else "BEARISH",
        "risk_reward": compute_rr(entry, row["stop_loss"], row["tp1"]),
        "confluence_score": confluence_score,
        "confluence_count": active_count,
        "show_trade_plan": show_plan,
        "confluence_flags": flags,
        "analysis_text": generate_analysis_text(
            row["pair"], row["timeframe"], row["direction"], flags,
            entry_zone, row["stop_loss"], row["tp1"], row.get("tp2"),
            fib, row.get("structure_json"), confluence_score
        ),
        "structure": row.get("structure_json"),
        "fib_levels": fib,
        "created_at": row["created_at"],
    }


def format_trade(row: dict) -> dict:
    return {
        "id": row["id"],
        "pair": row["pair"],
        "timeframe": row["timeframe"],
        "direction": row["direction"],
        "entry_price": row["entry_price"],
        "stop_loss": row["stop_loss"],
        "tp1": row["tp1"],
        "tp2": row.get("tp2"),
        "exit_price": row.get("exit_price"),
        "exit_reason": row.get("exit_reason"),
        "pnl_usd": round(row.get("pnl_usd", 0), 2),
        "pnl_pct": round(row.get("pnl_pct", 0), 2),
        "leverage": row.get("leverage", 1),
        "position_size": row.get("position_size", 0),
        "status": row["status"],
        "opened_at": row["opened_at"],
        "closed_at": row.get("closed_at"),
        "result": "WIN" if (row.get("pnl_usd") or 0) > 0 else ("LOSS" if (row.get("pnl_usd") or 0) < 0 else "BREAKEVEN"),
    }


# ─── Endpoints ─────────────────────────────────────────────

@app.get("/api/overview")
def get_overview():
    """Market overview: bias per pair, active signals, today stats."""
    try:
        db = get_db()

        # Active signals (last 24h)
        cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        active = db.execute(
            "SELECT * FROM signals WHERE created_at > ? ORDER BY created_at DESC",
            (cutoff,)
        ).fetchall()

        # Per-pair latest signal
        pairs = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]
        pair_bias = {}
        for p in pairs:
            latest = db.execute(
                "SELECT direction FROM signals WHERE pair = ? ORDER BY created_at DESC LIMIT 1",
                (p,)
            ).fetchone()
            pair_bias[p] = latest["direction"] if latest else "NEUTRAL"

        # Today stats
        today = datetime.utcnow().strftime("%Y-%m-%d")
        today_trades = db.execute(
            "SELECT COUNT(*) as n, COALESCE(SUM(pnl_usd), 0) as pnl "
            "FROM paper_trades WHERE status='closed' AND DATE(closed_at) = ?",
            (today,)
        ).fetchone()
        today_wins = db.execute(
            "SELECT COUNT(*) as n FROM paper_trades WHERE status='closed' AND pnl_usd > 0 AND DATE(closed_at) = ?",
            (today,)
        ).fetchone()

        # Open positions
        open_pos = db.execute(
            "SELECT COUNT(*) as n FROM paper_trades WHERE status='open'"
        ).fetchone()

        # Today signals count
        today_signals = db.execute(
            "SELECT COUNT(*) as n FROM signals WHERE DATE(created_at) = ?",
            (today,)
        ).fetchone()

        db.close()

        today_win_rate = (today_wins["n"] / today_trades["n"] * 100) if today_trades["n"] > 0 else 0

        return {
            "pair_bias": pair_bias,
            "active_signals_count": len(active),
            "today": {
                "win_rate": round(today_win_rate, 1),
                "pnl": round(today_trades["pnl"], 2),
                "trades": today_trades["n"],
                "signals": today_signals["n"],
            },
            "open_positions": open_pos["n"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/signals")
def get_signals(
    pair: Optional[str] = None,
    timeframe: Optional[str] = None,
    limit: int = Query(20, le=100),
):
    """Recent signals with full analysis data."""
    try:
        db = get_db()
        query = "SELECT * FROM signals WHERE 1=1"
        params = []
        if pair:
            query += " AND pair = ?"
            params.append(pair)
        if timeframe:
            query += " AND timeframe = ?"
            params.append(timeframe)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        rows = db.execute(query, params).fetchall()
        db.close()

        return [format_signal(dict(r)) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/signal/{signal_id}")
def get_signal_detail(signal_id: int):
    """Single signal detail."""
    try:
        db = get_db()
        row = db.execute("SELECT * FROM signals WHERE id = ?", (signal_id,)).fetchone()
        db.close()

        if not row:
            raise HTTPException(status_code=404, detail="Signal not found")

        return format_signal(dict(row))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history")
def get_history(
    pair: Optional[str] = None,
    timeframe: Optional[str] = None,
    result: Optional[str] = None,
    days: int = Query(30, le=365),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
):
    """Closed trades with filters."""
    try:
        db = get_db()
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

        query = "SELECT * FROM paper_trades WHERE status = 'closed' AND closed_at > ?"
        params = [cutoff]

        if pair:
            query += " AND pair = ?"
            params.append(pair)
        if timeframe:
            query += " AND timeframe = ?"
            params.append(timeframe)
        if result == "win":
            query += " AND pnl_usd > 0"
        elif result == "loss":
            query += " AND pnl_usd < 0"

        query += " ORDER BY closed_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = db.execute(query, params).fetchall()

        # Total count
        count_query = "SELECT COUNT(*) as n FROM paper_trades WHERE status = 'closed' AND closed_at > ?"
        count_params = [cutoff]
        if pair:
            count_query += " AND pair = ?"
            count_params.append(pair)
        if timeframe:
            count_query += " AND timeframe = ?"
            count_params.append(timeframe)
        if result == "win":
            count_query += " AND pnl_usd > 0"
        elif result == "loss":
            count_query += " AND pnl_usd < 0"

        total = db.execute(count_query, count_params).fetchone()["n"]
        db.close()

        return {
            "trades": [format_trade(dict(r)) for r in rows],
            "total": total,
            "offset": offset,
            "limit": limit,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
def get_stats():
    """Aggregated performance stats."""
    try:
        db = get_db()

        total = db.execute("SELECT COUNT(*) as n FROM paper_trades WHERE status='closed'").fetchone()["n"]
        wins = db.execute("SELECT COUNT(*) as n FROM paper_trades WHERE status='closed' AND pnl_usd > 0").fetchone()["n"]
        losses = db.execute("SELECT COUNT(*) as n FROM paper_trades WHERE status='closed' AND pnl_usd < 0").fetchone()["n"]
        win_rate = (wins / total * 100) if total > 0 else 0

        total_pnl = db.execute("SELECT COALESCE(SUM(pnl_usd), 0) as s FROM paper_trades WHERE status='closed'").fetchone()["s"]
        best = db.execute("SELECT MAX(pnl_usd) as v FROM paper_trades WHERE status='closed'").fetchone()["v"] or 0
        worst = db.execute("SELECT MIN(pnl_usd) as v FROM paper_trades WHERE status='closed'").fetchone()["v"] or 0

        # Sharpe
        daily = db.execute("""
            SELECT DATE(closed_at) as d, SUM(pnl_usd) as daily_pnl
            FROM paper_trades WHERE status='closed'
            GROUP BY DATE(closed_at)
        """).fetchall()
        sharpe = 0
        if len(daily) > 1:
            pnls = [r["daily_pnl"] for r in daily]
            mean_pnl = sum(pnls) / len(pnls)
            std_pnl = (sum((p - mean_pnl)**2 for p in pnls) / (len(pnls) - 1)) ** 0.5
            sharpe = (mean_pnl / std_pnl) * (252 ** 0.5) if std_pnl > 0 else 0

        # Max drawdown
        cum_pnl = 0
        peak = 0
        max_dd = 0
        for r in db.execute("SELECT pnl_usd FROM paper_trades WHERE status='closed' ORDER BY closed_at").fetchall():
            cum_pnl += r["pnl_usd"]
            peak = max(peak, cum_pnl)
            dd = (peak - cum_pnl) / peak * 100 if peak > 0 else 0
            max_dd = max(max_dd, dd)

        # Current streak
        recent = db.execute(
            "SELECT pnl_usd FROM paper_trades WHERE status='closed' ORDER BY closed_at DESC LIMIT 20"
        ).fetchall()
        streak = 0
        streak_type = None
        for r in recent:
            if streak_type is None:
                streak_type = "WIN" if r["pnl_usd"] > 0 else "LOSS"
                streak = 1
            elif (streak_type == "WIN" and r["pnl_usd"] > 0) or (streak_type == "LOSS" and r["pnl_usd"] < 0):
                streak += 1
            else:
                break

        # Profit factor
        gross_profit = db.execute(
            "SELECT COALESCE(SUM(pnl_usd), 0) as s FROM paper_trades WHERE status='closed' AND pnl_usd > 0"
        ).fetchone()["s"]
        gross_loss = abs(db.execute(
            "SELECT COALESCE(SUM(pnl_usd), 0) as s FROM paper_trades WHERE status='closed' AND pnl_usd < 0"
        ).fetchone()["s"])
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else 0

        # Per-pair
        pair_rows = db.execute("""
            SELECT pair, SUM(pnl_usd) as pnl, COUNT(*) as trades,
                   SUM(CASE WHEN pnl_usd > 0 THEN 1 ELSE 0 END) as wins
            FROM paper_trades WHERE status='closed'
            GROUP BY pair
        """).fetchall()

        db.close()

        return {
            "total_trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 1),
            "total_pnl": round(total_pnl, 2),
            "best_trade": round(best, 2),
            "worst_trade": round(worst, 2),
            "sharpe": round(sharpe, 2),
            "max_drawdown": round(max_dd, 1),
            "profit_factor": profit_factor,
            "current_streak": streak,
            "streak_type": streak_type,
            "gross_profit": round(gross_profit, 2),
            "gross_loss": round(gross_loss, 2),
            "pairs": {
                r["pair"]: {
                    "pnl": round(r["pnl"], 2),
                    "trades": r["trades"],
                    "wins": r["wins"],
                    "win_rate": round(r["wins"] / r["trades"] * 100, 1) if r["trades"] > 0 else 0,
                } for r in pair_rows
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/equity")
def get_equity():
    """Cumulative PnL curve data."""
    try:
        db = get_db()
        rows = db.execute("""
            SELECT DATE(closed_at) as d, SUM(pnl_usd) as daily_pnl
            FROM paper_trades WHERE status='closed'
            GROUP BY DATE(closed_at)
            ORDER BY d
        """).fetchall()
        db.close()

        cum = 0
        labels = []
        values = []
        for r in rows:
            cum += r["daily_pnl"]
            labels.append(r["d"])
            values.append(round(cum, 2))

        return {"labels": labels, "values": values}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pairs")
def get_pairs():
    """Per-pair breakdown."""
    try:
        db = get_db()
        rows = db.execute("""
            SELECT pair, SUM(pnl_usd) as total_pnl, COUNT(*) as trades,
                   SUM(CASE WHEN pnl_usd > 0 THEN 1 ELSE 0 END) as wins
            FROM paper_trades WHERE status='closed'
            GROUP BY pair ORDER BY total_pnl DESC
        """).fetchall()
        db.close()

        return {
            "labels": [r["pair"] for r in rows],
            "values": [round(r["total_pnl"], 2) for r in rows],
            "trades": [r["trades"] for r in rows],
            "win_rates": [round(r["wins"] / r["trades"] * 100, 1) if r["trades"] > 0 else 0 for r in rows],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/feed")
def get_feed(hours: int = Query(24, le=72)):
    """Real-time signal feed (last N hours)."""
    try:
        db = get_db()
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        rows = db.execute(
            "SELECT * FROM signals WHERE created_at > ? ORDER BY created_at DESC LIMIT 50",
            (cutoff,)
        ).fetchall()
        db.close()

        return [format_signal(dict(r)) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8503)
