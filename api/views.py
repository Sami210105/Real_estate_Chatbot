# api/views.py
from django.http import JsonResponse
import pandas as pd
import os
from django.conf import settings
from .llm_helper import generate_summary, generate_custom_summary, generate_compare_summary
import re

# Load Excel file once at startup
EXCEL_PATH = os.path.join(settings.BASE_DIR, 'backend', 'data', 'realestate.xlsx')
df = pd.read_excel(EXCEL_PATH)

def extract_areas_from_query(query):
    """
    Extract area names from user query.
    Returns list of potential area names.
    """
    # Common keywords to filter out
    stop_words = ['give', 'me', 'analysis', 'of', 'compare', 'and', 'show', 'price', 
                  'growth', 'for', 'over', 'last', 'years', 'year', 'demand', 'trends',
                  'the', 'a', 'an', 'in', 'on', 'at', 'to']
    
    # Remove numbers and common words
    words = re.findall(r'\b[A-Za-z]+\b', query)
    areas = [w.strip().title() for w in words if w.lower() not in stop_words and len(w) > 2]
    
    return areas

def filter_by_area(df, area):
    """Filter dataframe by area name (case-insensitive)."""
    location_cols = [col for col in df.columns 
                     if 'location' in col.lower() or 'area' in col.lower() or 'city' in col.lower()]
    
    mask = pd.Series([False] * len(df))
    for col in location_cols:
        mask |= df[col].astype(str).str.contains(area, case=False, na=False)
    
    return df[mask].copy()

def compute_prices(filtered):
    """Add computed price column to filtered data."""
    price_cols = [col for col in filtered.columns 
                 if any(kw in col.lower() for kw in ['price', 'cost', 'rate', 'value'])]
    
    if price_cols:
        filtered['__price_computed__'] = filtered[price_cols].apply(
            lambda row: pd.to_numeric(row, errors='coerce').mean(), axis=1
        )
    else:
        filtered['__price_computed__'] = 0
    
    return filtered, price_cols

def analyze_view(request):
    """
    API endpoint to analyze real estate data based on user query.
    Handles:
    - Simple area queries: "Wakad"
    - Analysis requests: "Give me analysis of Wakad"
    - Comparisons: "Compare Ambegaon Budruk and Aundh"
    - Time-based: "Show price growth for Akurdi over 3 years"
    """
    query = request.GET.get('area', '').strip()
    
    if not query:
        return JsonResponse({'error': 'No query provided'}, status=400)
    
    try:
        query_lower = query.lower()
        
        # Detect query type
        is_comparison = any(word in query_lower for word in ['compare', 'vs', 'versus', 'between'])
        is_time_based = any(word in query_lower for word in ['growth', 'trend', 'over', 'last', 'years'])
        
        # Extract area names from query
        areas = extract_areas_from_query(query)
        
        if not areas:
            return JsonResponse({
                'summary': 'Please specify an area name in your query (e.g., Wakad, Akurdi, Hinjewadi).',
                'chart': [],
                'table': [],
                'used_price_columns': []
            })
        
        # Handle COMPARISON queries
        if is_comparison and len(areas) >= 2:
            area_to_rows = {}
            all_chart_data = []
            all_table_data = []
            all_price_cols = set()
            
            for area in areas[:3]:  # Limit to 3 areas
                filtered = filter_by_area(df, area)
                if not filtered.empty:
                    filtered, price_cols = compute_prices(filtered)
                    area_to_rows[area] = filtered.to_dict('records')
                    all_price_cols.update(price_cols)
                    
                    # Add to table
                    all_table_data.extend(filtered.head(10).fillna('').to_dict('records'))
                    
                    # Add to chart with area label
                    if 'year' in filtered.columns:
                        area_chart = (
                            filtered.groupby('year')['__price_computed__']
                            .mean()
                            .reset_index()
                        )
                        for _, row in area_chart.iterrows():
                            all_chart_data.append({
                                'year': row['year'],
                                'area': area,
                                '__price_computed__': row['__price_computed__']
                            })
            
            if not area_to_rows:
                return JsonResponse({
                    'summary': f'No data found for areas: {", ".join(areas)}',
                    'chart': [],
                    'table': [],
                    'used_price_columns': []
                })
            
            # Generate comparison summary using LLM
            summary = generate_compare_summary(area_to_rows, user_prompt=query)
            
            return JsonResponse({
                'summary': summary,
                'chart': all_chart_data,
                'table': all_table_data[:30],  # Limit table rows
                'used_price_columns': list(all_price_cols),
                'query_type': 'comparison',
                'areas': list(area_to_rows.keys())
            })
        
        # Handle SINGLE AREA queries (analysis or time-based)
        else:
            area = areas[0]
            filtered = filter_by_area(df, area)
            
            if filtered.empty:
                return JsonResponse({
                    'summary': f'No data found for "{area}". Try another location like Wakad, Akurdi, or Hinjewadi.',
                    'chart': [],
                    'table': [],
                    'used_price_columns': []
                })
            
            filtered, price_cols = compute_prices(filtered)
            
            # Filter by years if time-based query
            if is_time_based:
                years_match = re.search(r'(\d+)\s*years?', query_lower)
                if years_match:
                    num_years = int(years_match.group(1))
                    if 'year' in filtered.columns:
                        max_year = filtered['year'].max()
                        filtered = filtered[filtered['year'] >= (max_year - num_years)]
            
            # Generate chart data
            if 'year' in filtered.columns:
                chart_data = (
                    filtered.groupby('year')['__price_computed__']
                    .mean()
                    .reset_index()
                    .to_dict('records')
                )
            else:
                chart_data = []
            
            # Prepare table data
            table_data = filtered.head(20).fillna('').to_dict('records')
            
            # Generate AI summary based on query complexity
            if len(query.split()) > 2:  # Complex query
                summary = generate_custom_summary(area, filtered.to_dict('records'), user_prompt=query)
            else:  # Simple area name
                summary = generate_summary(area, filtered.to_dict('records'))
            
            return JsonResponse({
                'summary': summary,
                'chart': chart_data,
                'table': table_data,
                'used_price_columns': price_cols,
                'query_type': 'analysis',
                'area': area
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)