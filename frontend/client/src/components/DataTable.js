import React from 'react';
import Table from 'react-bootstrap/Table';
import Card from 'react-bootstrap/Card';

export default function DataTable({ rows }) {
  if (!rows || rows.length === 0) return null;

  const keys = ['final location', 'year', 'city', '__price_computed__']
    .filter(k => k in rows[0]);

  return (
    <Card className="glass-card shadow-sm" style={{ marginTop: 20 }}>
      <Card.Body>
        <Card.Title style={{ color: "#ffffffd2", marginBottom: "12px" }}>
          Filtered Table
        </Card.Title>

        <div className="glass-table-wrapper">
          <Table bordered responsive size="sm" className="glass-table">
            <thead>
              <tr>
                {keys.map(k => (
                  <th key={k} className="glass-th">
                    {k.replace(/__/g, '').replace(/_/g, ' ').toUpperCase()}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {rows.map((row, i) => (
                <tr key={i} className="glass-row">
                  {keys.map(k => (
                    <td key={k} className="glass-td">
                      {String(row[k] ?? '')}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      </Card.Body>
    </Card>
  );
}
