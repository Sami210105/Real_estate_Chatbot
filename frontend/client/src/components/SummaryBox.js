import React from 'react';
import Card from 'react-bootstrap/Card';
import Badge from 'react-bootstrap/Badge';

export default function SummaryBox({ summary, meta }) {
  return (
    <Card className="shadow-sm">
      <Card.Body>
        <div className="d-flex justify-content-between align-items-center mb-3">
          <Card.Title className="mb-0">
            AI Analysis
          </Card.Title>
          <div>
            <Badge bg="success" pill className="me-1">Groq AI</Badge>
            {meta?.query_type && (
              <Badge bg="info" pill>{meta.query_type}</Badge>
            )}
          </div>
        </div>
        
        <Card.Text style={{ 
          whiteSpace: 'pre-wrap', 
          fontSize: '1.05rem',
          lineHeight: '1.6',
          color: '#2c3e50'
        }}>
          {summary}
        </Card.Text>
        
        {meta?.used_price_columns && meta.used_price_columns.length > 0 && (
          <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid #dee2e6' }}>
            <small className="mb-2 d-block">
              <strong>Data sources:</strong>{' '}
            </small>
            {meta.used_price_columns.map((c) => (
              <Badge key={c} bg="secondary" className="me-1" style={{ fontSize: '0.75rem' }}>{c}</Badge>
            ))}
            {meta?.areas && (
              <>
                <br />
                <small className="mt-2 d-block">
                  <strong>Areas analyzed:</strong> {meta.areas.join(', ')}
                </small>
              </>
            )}
          </div>
        )}
      </Card.Body>
    </Card>
  );
}