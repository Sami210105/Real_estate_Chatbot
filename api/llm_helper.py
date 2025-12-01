# backend/api/llm_helper.py
import json
import math
import statistics
from typing import List, Dict, Optional, Any

from django.conf import settings

try:
    from groq import Groq
except Exception:
    Groq = None  # graceful degradation in environments without groq installed


def _safe_number(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            if math.isfinite(v):
                return float(v)
            return None
        # sometimes numbers come as strings with commas
        if isinstance(v, str):
            v2 = v.replace(",", "").strip()
            return float(v2) if v2 not in ("", "NA", "N/A", "-") else None
    except Exception:
        return None
    return None


def _condense_for_llm(filtered_list: List[Dict], top_n_years: int = 6) -> List[Dict]:
    """
    Build a compact yearly average summary and small sample rows for sending to LLM.
    Returns a list of {"year": <int>, "avg_price": <float>} sorted by year.
    Limits to last `top_n_years` years.
    """
    years = {}
    for r in filtered_list:
        # try common year keys
        y = r.get("year") or r.get("Year") or r.get("YEAR")
        try:
            y = int(y)
        except Exception:
            continue

        # find price-like value
        price = None
        if "__price_computed__" in r:
            price = _safe_number(r.get("__price_computed__"))
        else:
            # look for columns that contain 'price' or numeric fields
            for k, v in r.items():
                if k and isinstance(k, str) and "price" in k.lower():
                    price = _safe_number(v)
                    if price is not None:
                        break
            if price is None:
                # fallback: first numeric-looking value
                for v in r.values():
                    pn = _safe_number(v)
                    if pn is not None:
                        price = pn
                        break

        if price is None:
            continue

        years.setdefault(y, []).append(price)

    summary = []
    for y, vals in years.items():
        if vals:
            summary.append({"year": int(y), "avg_price": float(sum(vals) / len(vals))})

    summary = sorted(summary, key=lambda x: x["year"])
    if len(summary) > top_n_years:
        summary = summary[-top_n_years:]
    return summary


def _format_inr(x: float) -> str:
    try:
        return f"₹{x:,.2f}"
    except Exception:
        return str(x)

# Fallback deterministic summary
def generate_fallback_summary(area: str, filtered_data: List[Dict]) -> str:
    """
    Deterministic fallback summary using basic stats (no LLM).
    """
    if not filtered_data:
        return f"No data available for {area}."

    prices = [_safe_number(r.get("__price_computed__")) for r in filtered_data]
    prices = [p for p in prices if p is not None]

    years = []
    for r in filtered_data:
        y = r.get("year") or r.get("Year") or r.get("YEAR")
        try:
            years.append(int(y))
        except Exception:
            continue

    if prices and years:
        avg_price = statistics.mean(prices)
        min_price = min(prices)
        max_price = max(prices)
        yr_min = min(years)
        yr_max = max(years)
        return (
            f"Found {len(filtered_data)} records for {area} from {yr_min} to {yr_max}. "
            f"Average price: {_format_inr(avg_price)}. "
            f"Price range: {_format_inr(min_price)} to {_format_inr(max_price)}."
        )
    else:
        return f"Found {len(filtered_data)} records for {area}. Insufficient numeric data to compute price statistics."


# Low-level Groq call wrapper
def _call_groq(prompt_text: str, model: str = "llama-3.3-70b-versatile", max_tokens: int = 300, temperature: float = 0.6) -> str:
    """
    Wrap Groq client call. Returns the text answer or raises.
    """
    if Groq is None:
        raise RuntimeError("Groq client library not available in this environment.")

    api_key = getattr(settings, "GROQ_API_KEY", None)
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set in Django settings.")

    client = Groq(api_key=api_key) 
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a professional real estate market analyst."},
            {"role": "user", "content": prompt_text}
        ],
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )
    # try to extract response
    try:
        # chat_completion may be a dict-like object
        choices = getattr(chat_completion, "choices", None) or chat_completion.get("choices") if isinstance(chat_completion, dict) else None
        if choices and len(choices) > 0:
            # many SDKs put the text at choices[0].message.content or choices[0].text
            first = choices[0]
            if isinstance(first, dict):
                msg = first.get("message") or first.get("text") or {}
                if isinstance(msg, dict):
                    return msg.get("content", "").strip()
                return str(msg).strip()
            else:
                # try attribute access
                msg = getattr(first, "message", None)
                if msg:
                    return getattr(msg, "content", str(msg)).strip()
                return str(first).strip()
        # fallback: attempt to string-convert
        return str(chat_completion).strip()
    except Exception:
        return str(chat_completion).strip()

def generate_summary(area: str, filtered_data: List[Dict]) -> str:
    """
    Generate a natural language summary using Groq.
    This is the simpler convenience function for area-specific summaries.
    """
    try:
        if not filtered_data:
            return f"No data found for {area}."

        years_condensed = _condense_for_llm(filtered_data)
        prices = [_safe_number(r.get("__price_computed__")) for r in filtered_data]
        prices = [p for p in prices if p is not None]

        stats = {
            "area": area,
            "total_records": len(filtered_data),
            "year_range": f"{years_condensed[0]['year']} to {years_condensed[-1]['year']}" if years_condensed else "N/A",
            "avg_price": float(statistics.mean(prices)) if prices else 0.0,
            "min_price": float(min(prices)) if prices else 0.0,
            "max_price": float(max(prices)) if prices else 0.0,
            "condensed_yearly": years_condensed,
        }

        prompt = (
            f"You are a real estate analyst. Provide a concise 3-4 sentence data-driven summary using the stats and the compact yearly data below.\n\n"
            f"Area: {stats['area']}\n"
            f"Total Records: {stats['total_records']}\n"
            f"Year Range: {stats['year_range']}\n"
            f"Average Price: {_format_inr(stats['avg_price'])}\n"
            f"Price Range: {_format_inr(stats['min_price'])} to {_format_inr(stats['max_price'])}\n\n"
            f"Compact Yearly Averages (most recent first): {json.dumps(stats['condensed_yearly'], default=str)}\n\n"
            "Write 3-4 sentences covering: an overview of the market, notable price trends, and 1-2 key insights or cautions. Keep it professional and concise."
        )

        # limit tokens slightly for safety (adjust as needed)
        return _call_groq(prompt, max_tokens=220, temperature=0.5)
    except Exception as e:
        # log minimal info to stdout; don't crash the app
        print(f"generate_summary error: {str(e)}")
        return generate_fallback_summary(area, filtered_data)


def generate_custom_summary(area_or_prompt: str, filtered_data: List[Dict], user_prompt: Optional[str] = None) -> str:
    """
    Generate a summary using a free-form user prompt combined with a condensed JSON context.
    - area_or_prompt: string identifying area or the user's textual request.
    - filtered_data: list of dict rows (already filtered).
    - user_prompt: if provided, this is used as the explicit question; otherwise area_or_prompt is used.
    """
    try:
        if not filtered_data:
            # If there's no filtered data, still pass a helpful prompt to the LLM
            base_prompt = user_prompt or area_or_prompt
            empty_prompt = f"{base_prompt}\n\nNote: No rows are available for this query."
            return _call_groq(empty_prompt, max_tokens=180, temperature=0.6)

        condensed = _condense_for_llm(filtered_data, top_n_years=8)
        sample_rows = filtered_data[:5]  # small sample for context

        context = {
            "description": "Condensed yearly averages and a small sample of rows for the user's query.",
            "condensed_yearly": condensed,
            "sample_rows": sample_rows
        }

        base_question = user_prompt or area_or_prompt
        prompt_parts = [
            "You are a professional real estate market analyst. Use the JSON context to answer the user's question precisely and concisely.",
            f"User question: {base_question}",
            "Context JSON:",
            json.dumps(context, default=str)
        ]
        full_prompt = "\n\n".join(prompt_parts)

        # Provide the LLM slightly more tokens for descriptive prompts
        return _call_groq(full_prompt, max_tokens=350, temperature=0.6)
    except Exception as e:
        print(f"generate_custom_summary error: {str(e)}")
        return generate_fallback_summary(area_or_prompt, filtered_data)


def generate_compare_summary(area_to_rows: Dict[str, List[Dict]], user_prompt: Optional[str] = None) -> str:
    """
    Compare multiple areas.
    - area_to_rows: mapping from area name -> list of rows
    - user_prompt: optional specific instruction for comparison
    Returns: LLM-generated comparison text or fallback.
    """
    try:
        if not area_to_rows:
            return "No area data provided for comparison."

        # Condense each area's data
        condensed_map = {}
        for area, rows in area_to_rows.items():
            condensed_map[area] = _condense_for_llm(rows, top_n_years=6)

        # Build compact combined context
        context = {
            "description": "Yearly averages for each area (compact).",
            "areas": condensed_map
        }

        prompt_intro = user_prompt or "Compare the listed areas in terms of recent price trends, relative growth, and notable differences. Provide a concise comparison and highlight any area with exceptional behavior."
        full_prompt = "\n\n".join([
            "You are a professional real estate market analyst.",
            f"Task: {prompt_intro}",
            "Context JSON:",
            json.dumps(context, default=str)
        ])

        return _call_groq(full_prompt, max_tokens=400, temperature=0.6)
    except Exception as e:
        print(f"generate_compare_summary error: {str(e)}")
        # fallback: produce a small deterministic textual comparison
        lines = []
        for area, rows in area_to_rows.items():
            rows_count = len(rows or [])
            condensed = _condense_for_llm(rows or [], top_n_years=3)
            latest = condensed[-1]["avg_price"] if condensed else None
            lines.append(f"{area}: {rows_count} records. Latest avg: {_format_inr(latest)}" if latest else f"{area}: {rows_count} records.")
        return " | ".join(lines)
