import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend
} from 'recharts';
import Card from 'react-bootstrap/Card';

export default function PriceChart({ data, queryType }) {
  if (!data || data.length === 0) return null;

  // Check if this is comparison data (has 'area' field)
  const isComparison = data.some(d => d.area);

  // shared styles for axes/grid to look good on dark background
  const axisTickStyle = { fill: '#e6f0ff', fontSize: 12 };
  const axisLineStyle = { stroke: 'rgba(255,255,255,0.06)' };
  const gridStroke = 'rgba(255,255,255,0.06)';

  // common Tooltip style overrides to remove default white box and keep it above
  const tooltipWrapperStyle = {
    backgroundColor: 'transparent',
    boxShadow: 'none',
    border: 'none',
    color: '#fff',
    zIndex: 9999, // ensure tooltip sits above everything
    pointerEvents: 'auto'
  };
  const tooltipContentStyle = {
    backgroundColor: 'rgba(255,255,255,0.03)',
    border: '1px solid rgba(255,255,255,0.06)',
    boxShadow: '0 6px 20px rgba(0,0,0,0.6)',
    color: '#fff',
    padding: '6px 8px'
  };
  const legendWrapperStyle = {
    paddingTop: 8,
    color: '#fff',
    fontSize: 13
  };

  if (isComparison) {
    // Group data by year for comparison chart
    const yearMap = {};
    data.forEach(d => {
      const year = d.year;
      if (!yearMap[year]) yearMap[year] = { year };
      yearMap[year][d.area] = d.__price_computed__;
    });

    const chartData = Object.values(yearMap).sort((a, b) => a.year - b.year);
    const areas = [...new Set(data.map(d => d.area))];
    const colors = ['#ffc658', '#82ca9d', '#8884d8', '#ff7c7c'];

    return (
      <Card className="shadow-sm glass-card" style={{ position: 'relative', zIndex: 1 }}>
        <Card.Body>
          <Card.Title>Price Comparison</Card.Title>

          {/* chart container forced above card via zIndex */}
          <div
            className="chart-container"
            style={{ width: '100%', height: 350, position: 'relative', zIndex: 10 }}
          >
            <ResponsiveContainer>
              <LineChart
                data={chartData}
                style={{ backgroundColor: 'transparent', position: 'relative', zIndex: 10 }}
              >
                <CartesianGrid stroke={gridStroke} strokeDasharray="3 3" />
                <XAxis
                  dataKey="year"
                  tick={axisTickStyle}
                  axisLine={axisLineStyle}
                  tickLine={false}
                />
                <YAxis
                  tick={axisTickStyle}
                  axisLine={axisLineStyle}
                  tickLine={false}
                />
                <Tooltip
                  formatter={(value) =>
                    value !== undefined ? `₹${value?.toLocaleString()}` : value
                  }
                  wrapperStyle={tooltipWrapperStyle}
                  contentStyle={tooltipContentStyle}
                  cursor={{ stroke: 'rgba(255,255,255,0.06)', strokeDasharray: '3 3' }}
                />
                <Legend wrapperStyle={legendWrapperStyle} />
                {areas.map((area, i) => (
                  <Line
                    key={area}
                    type="monotone"
                    dataKey={area}
                    stroke={colors[i % colors.length]}
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    activeDot={{ r: 5 }}
                    isAnimationActive={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card.Body>
      </Card>
    );
  }

  // Single area chart
  const chartData = data.map((d) => ({
    year: d.year,
    price:
      d.__price_computed__ !== undefined && d.__price_computed__ !== null
        ? d.__price_computed__
        : Object.values(d).find(v => typeof v === 'number' && v !== d.year)
  }));

  return (
    <Card className="shadow-sm glass-card" style={{ position: 'relative', zIndex: 1 }}>
      <Card.Body>
        <Card.Title>Price Trend Over Time</Card.Title>

        <div
          className="chart-container"
          style={{ width: '100%', height: 320, position: 'relative', zIndex: 100 }}
        >
          <ResponsiveContainer>
            <LineChart
              data={chartData}
              style={{ backgroundColor: 'transparent', position: 'relative', zIndex: 10 }}
            >
              <CartesianGrid stroke={gridStroke} strokeDasharray="3 3" />
              <XAxis
                dataKey="year"
                tick={axisTickStyle}
                axisLine={axisLineStyle}
                tickLine={false}
              />
              <YAxis
                tick={axisTickStyle}
                axisLine={axisLineStyle}
                tickLine={false}
              />
              <Tooltip
                formatter={(value) =>
                  value !== undefined ? `₹${value?.toLocaleString()}` : value
                }
                wrapperStyle={tooltipWrapperStyle}
                contentStyle={tooltipContentStyle}
                cursor={{ stroke: 'rgba(255,255,255,0.06)', strokeDasharray: '3 3' }}
              />
              <Line
                type="monotone"
                dataKey="price"
                stroke="#1f77b4"
                strokeWidth={2}
                dot={{ r: 4 }}
                activeDot={{ r: 5 }}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card.Body>
    </Card>
  );
}
