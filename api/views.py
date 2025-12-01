# backend/api/views.py
import os
import traceback
from typing import List
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET

import pandas as pd

from .llm_helper import generate_custom_summary, generate_compare_summary, generate_fallback_summary

# DATA_PATH: adjust if your excel lives elsewhere
DATA_PATH = getattr(settings, "REAL_ESTATE_DATA_PATH", os.path.join(settings.BASE_DIR, "data", "realestate.xlsx"))

# Helper: safe read excel
def _safe_read_excel(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Excel file not found at: {path}")
    return pd.read_excel(path)


def _detect_price_column(df: pd.DataFrame):
    """
    Attempt to detect one or more price columns; returns list of candidate column names.
    Prefers '__price_computed__' if already present.
    """
    if "__price_computed__" in df.columns:
        return ["__price_computed__"]
    candidates = []
    lower = {c: c.lower() for c in df.columns}
    for c, lc in lower.items():
        if "price" in lc or "rate" in lc or "value" in lc:
            candidates.append(c)
    # fallback: numeric columns excluding year-like columns
    if not candidates:
        for c in df.select_dtypes(include=["number"]).columns:
            if "year" not in c.lower():
                candidates.append(c)
    return candidates


def _coerce_year(df: pd.DataFrame):
    # try to find year column
    possible = [c for c in df.columns if c.lower() in ("year", "Year", "yr", "YEAR")]
    if not possible:
        # find any column with integer-like values in a reasonable range
        for c in df.columns:
            try:
                s = pd.to_numeric(df[c], errors="coerce")
                if s.notna().sum() > 0 and s.dropna().between(1900, 2100).any():
                    return c
            except Exception:
                continue
        return None
    return possible[0]


@require_GET
def analyze(request):
    """
    GET /api/analyze/?prompt=<text> OR ?area=<areaName>
    Returns:
      - summary (backend fallback)
      - chart: [{ "year": 2020, "__price_computed__": 12345.0 }, ...]
      - table: sample rows
      - llm_summary: string (from Groq or fallback)
      - used_price_columns, found_columns
    """
    prompt = request.GET.get("prompt", "").strip()
    area_param = request.GET.get("area", "").strip()

    if not prompt and not area_param:
        return JsonResponse({"error": "please provide ?prompt=... or ?area=..."}, status=400)

    try:
        df = _safe_read_excel(DATA_PATH)
        cols = list(df.columns)

        # detect price columns and compute __price_computed__ if needed
        price_candidates = _detect_price_column(df)
        price_sources = price_candidates.copy()

        if "__price_computed__" not in df.columns:
            # create a computed price column by taking first valid candidate numeric column
            df["__price_computed__"] = None
            for pc in price_candidates:
                # coerce numeric values
                try:
                    numeric = pd.to_numeric(df[pc], errors="coerce")
                    mask = numeric.notna()
                    df.loc[mask, "__price_computed__"] = numeric[mask]
                except Exception:
                    continue

        # coerce year
        year_col = _coerce_year(df)
        if not year_col:
            # fallback: try common column
            year_col = "year" if "year" in df.columns else None

        # Filter by area if provided explicitly OR try to parse from prompt (simple heuristic)
        filtered = df.copy()
        if area_param:
            filtered = filtered[filtered.apply(lambda r: str(r).lower().find(area_param.lower()) >= 0 if True else False, axis=1)]
            # better: if you have a 'final location' column, use it
            if "final location" in df.columns:
                filtered = df[df["final location"].astype(str).str.contains(area_param, case=False, na=False)]
        else:
            # try to extract an area-like token from prompt — naive: split and check for exact matches in 'final location'
            # If prompt contains "of <area>", pick that
            import re
            m = re.search(r"of\s+([A-Za-z0-9\s-]+)", prompt, re.IGNORECASE)
            if m:
                possible_area = m.group(1).strip()
                if "final location" in df.columns:
                    filtered = df[df["final location"].astype(str).str.contains(possible_area, case=False, na=False)]
                else:
                    # try contains in any textual column
                    txt_cols = [c for c in df.columns if df[c].dtype == "object"]
                    cond = False
                    for c in txt_cols:
                        cond = cond | df[c].astype(str).str.contains(possible_area, case=False, na=False)
                    filtered = df[cond]
            else:
                # If no explicit area found, attempt to use the first word as area
                first_word = prompt.split()[0] if prompt else ""
                if first_word and "final location" in df.columns:
                    filtered = df[df["final location"].astype(str).str.contains(first_word, case=False, na=False)]

        # ensure year column in filtered is numeric and present in chart
        if year_col and year_col in filtered.columns:
            filtered[year_col] = pd.to_numeric(filtered[year_col], errors="coerce")
            filtered = filtered[filtered[year_col].notna()]

        # Rename year column to 'year' in output if it's something else
        if year_col and year_col != "year":
            filtered = filtered.rename(columns={year_col: "year"})

        # final sanity
        if filtered.empty:
            # attempt fallback: narrow df by any row where any textual column includes area_param
            if area_param and "final location" in df.columns:
                filtered = df[df["final location"].astype(str).str.contains(area_param, case=False, na=False)]
            if filtered.empty:
                # return empty but sensible response
                return JsonResponse({
                    "summary": f"No records found for query: '{prompt or area_param}'.",
                    "chart": [],
                    "table": [],
                    "llm_summary": f"No records found for query: '{prompt or area_param}'.",
                    "used_price_columns": price_sources,
                    "found_columns": cols
                })

        # prepare filtered_list
        filtered_list = filtered.to_dict(orient="records")

        # compute avg price summary
        try:
            prices = [float(r.get("__price_computed__")) for r in filtered_list if r.get("__price_computed__") is not None]
            avg_price = float(sum(prices)/len(prices)) if prices else None
        except Exception:
            avg_price = None

        summary_text = f"{(area_param or prompt)} — {len(filtered_list)} records found."
        if avg_price is not None:
            summary_text += f" Average price (computed): {avg_price:.2f}"

        # compute chart: group by year and average __price_computed__
        chart = []
        if "year" in filtered.columns and "__price_computed__" in filtered.columns:
            try:
                chart_df = filtered.groupby("year")["__price_computed__"].mean().reset_index().sort_values("year")
                # convert to simple dicts with consistent keys
                chart = [{"year": int(r["year"]), "__price_computed__": float(r["__price_computed__"])} for _, r in chart_df.iterrows()]
            except Exception:
                chart = []

        # call the LLM helper to get a nicer summary (custom if prompt provided)
        llm_summary = None
        try:
            if prompt:
                llm_summary = generate_custom_summary(prompt, filtered_list, user_prompt=prompt)
            else:
                # if user only supplied area_param, still generate
                llm_summary = generate_custom_summary(area_param, filtered_list, user_prompt=None)
        except Exception as e:
            # fallback to deterministic summary
            llm_summary = generate_fallback_summary(area_param or prompt, filtered_list)

        resp = {
            "summary": summary_text,
            "chart": chart,
            "table": filtered_list[:200],
            "llm_summary": llm_summary,
            "used_price_columns": price_sources,
            "found_columns": cols
        }
        return JsonResponse(resp)

    except Exception as e:
        tb = traceback.format_exc()
        return JsonResponse({"error": "analyze exception", "exception": str(e), "traceback": tb}, status=500)


@require_GET
def compare(request):
    """
    GET /api/compare/?areas=Area1,Area2&prompt=optional
    Returns combined data and an LLM comparison summary.
    """
    areas = request.GET.get("areas", "").strip()
    user_prompt = request.GET.get("prompt", "").strip()

    if not areas:
        return JsonResponse({"error": "please provide ?areas=area1,area2"}, status=400)

    try:
        df = _safe_read_excel(DATA_PATH)
        area_list = [a.strip() for a in areas.split(",") if a.strip()]
        consolidated = {}

        for a in area_list:
            if "final location" in df.columns:
                sel = df[df["final location"].astype(str).str.contains(a, case=False, na=False)]
            else:
                # fallback: any textual column contains area
                txt_cols = [c for c in df.columns if df[c].dtype == "object"]
                cond = False
                for c in txt_cols:
                    cond = cond | df[c].astype(str).str.contains(a, case=False, na=False)
                sel = df[cond]
            # coerce year if possible
            year_col = _coerce_year(sel)
            if year_col and year_col != "year":
                sel = sel.rename(columns={year_col: "year"})
            if "year" in sel.columns:
                sel["year"] = pd.to_numeric(sel["year"], errors="coerce")
                sel = sel[sel["year"].notna()]

            consolidated[a] = sel.to_dict(orient="records")

        # call LLM compare
        try:
            llm_text = generate_compare_summary(consolidated, user_prompt=user_prompt or None)
        except Exception:
            llm_text = None

        return JsonResponse({"areas": list(consolidated.keys()), "data": consolidated, "llm_summary": llm_text})

    except Exception as e:
        tb = traceback.format_exc()
        return JsonResponse({"error": "compare exception", "exception": str(e), "traceback": tb}, status=500)
