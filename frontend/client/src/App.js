import React, { useState } from 'react';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Navbar from 'react-bootstrap/Navbar';
import Nav from 'react-bootstrap/Nav';
import ChatInput from './components/ChatInput';
import SummaryBox from './components/SummaryBox';
import PriceChart from './components/PriceChart';
import DataTable from './components/DataTable';
import Alert from 'react-bootstrap/Alert';
import Spinner from 'react-bootstrap/Spinner';
import './App.css';

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleQuery = async (area) => {
    setError(null);
    setLoading(true);
    setData(null);
    
    try {
      const res = await fetch(`/api/analyze/?area=${encodeURIComponent(area)}`);
      const json = await res.json();
      
      if (!res.ok) {
        setError(json.error || 'API error');
      } else {
        setData(json);
      }
    } catch (err) {
      setError(err.message || 'Network error');
    } finally {
      setLoading(false);
    }
  };

  const handleHomeClick = (e) => {
    e.preventDefault();
    setData(null);
    setError(null);
    setLoading(false);
  };

  return (
    <div className="app-wrapper">
      {/* Navbar */}
      <Navbar className="glass-navbar" variant="dark" sticky="top">
        <Container>
          <Navbar.Brand href="#home" onClick={handleHomeClick} className="d-flex align-items-center" style={{ cursor: 'pointer' }}>
            <span className="brand-icon">
              <svg xmlns="http://www.w3.org/2000/svg" x="0px" y="0px" width={35} height={35} viewBox="0 0 40 40">
              <path fill="#dbf2ff" d="M3.5,38.5V13.3L20,3.6l16.5,9.7v25.2H3.5z"></path><path fill="#b5ddf5" d="M4,34h32.3v4H4V34z"></path><path fill="#7496c4" d="M20,4.2l16,9.4V38H4V13.6L20,4.2 M20,3L3,13v26h34V13L20,3L20,3z"></path><path fill="#f78f8f" d="M20,4.6L1.5,16v-3.1L20,1.6l18.5,11.3V16L20,4.6z"></path><path fill="#c74343" d="M20,2.2l18,11v1.9L20.5,4.4L20,4.1l-0.5,0.3L2,15.1v-1.9L20,2.2 M20,1L1,12.6v4.2L20,5.2l19,11.6v-4.2L20,1	L20,1z"></path><path fill="#ffc49c" d="M14.5,21.5h11v17h-11V21.5z"></path><path fill="#a16a4a" d="M25,22v16H15V22H25 M26,21H14v18h12V21L26,21z"></path><path fill="#a16a4a" d="M23,30c-0.6,0-1,0.4-1,1s0.4,1,1,1s1-0.4,1-1S23.6,30,23,30z"></path>
              </svg>
            </span>
            <span className="brand-text">RealEstate AI</span>
          </Navbar.Brand>
          <Nav className="ms-auto">
            <Nav.Link href="#home" onClick={handleHomeClick}>Home</Nav.Link>
            <Nav.Link href="#features">Features</Nav.Link>
            <Nav.Link href="#about">About</Nav.Link>
            <Nav.Link href="#contact">Contact</Nav.Link>
          </Nav>
        </Container>
      </Navbar>

      {/* Hero Section */}
      <div className="hero-section">
        <Container>
          <Row className="justify-content-center text-center mb-5">
            <Col lg={8}>
              <div className="hero-content">
                <span className="hero-icon">
                  <img src="/bot.png" alt="bot" width={50} height={50}/>
                </span>
                <h1 className="hero-title">Real Estate AI Assistant</h1>
                <p className="hero-subtitle">
                  Powered by Groq AI • Analyze property trends across Pune with intelligent insights
                </p>
              </div>
            </Col>
          </Row>

          {/* Floating Chat Box */}
          <Row className="justify-content-center mb-4">
            <Col lg={10} xl={8}>
              <div className="glass-card chat-box">
                <ChatInput onQuery={handleQuery} loading={loading} />
              </div>
            </Col>
          </Row>

          {/* Example Queries */}
          {!data && !loading && !error && (
            <Row className="justify-content-center mb-4">
              <Col lg={10} xl={8}>
                <div className="example-queries">
                  <p className="example-label">
                    <span className="icon"></span> Try these examples:
                  </p>
                  <div className="example-buttons">
                    {[
                      { text: "Wakad" },
                      { text: "Compare Wakad and Akurdi"},
                      { text: "Show Aundh growth over 3 years"}
                    ].map((example, i) => (
                      <button
                        key={i}
                        className="example-btn"
                        onClick={() => handleQuery(example.text)}
                      >
                        <span className="btn-icon">{example.icon}</span>
                        {example.text}
                      </button>
                    ))}
                  </div>
                </div>
              </Col>
            </Row>
          )}
        </Container>
      </div>

      {/* Results Section */}
      <Container className="results-container">
        {loading && (
          <Row className="justify-content-center mb-4">
            <Col lg={10} xl={8}>
              <div className="glass-card text-center loading-box">
                <Spinner animation="border" variant="light" />
                <p className="loading-text">
                  <span className="icon">🔍</span>
                  Analyzing data with AI...
                </p>
              </div>
            </Col>
          </Row>
        )}

        {error && (
          <Row className="justify-content-center mb-4">
            <Col lg={10} xl={8}>
              <Alert variant="danger" className="glass-card error-alert">
                <span className="icon">⚠️</span> {error}
              </Alert>
            </Col>
          </Row>
        )}

        {data && !loading && (
          <>
            <Row className="justify-content-center mb-4">
              <Col lg={10} xl={8}>
                <SummaryBox 
                  summary={data.summary} 
                  meta={{ 
                    used_price_columns: data.used_price_columns,
                    query_type: data.query_type,
                    areas: data.areas,
                    area: data.area
                  }} 
                />
              </Col>
            </Row>

            {data.chart && data.chart.length > 0 && (
              <Row className="justify-content-center mb-4">
                <Col lg={10} xl={8}>
                  <PriceChart data={data.chart} queryType={data.query_type} />
                </Col>
              </Row>
            )}

            {data.table && data.table.length > 0 && (
              <Row className="justify-content-center mb-4">
                <Col lg={10} xl={8}>
                  <DataTable rows={data.table} />
                </Col>
              </Row>
            )}
          </>
        )}
      </Container>

      {/* Footer */}
      <footer className="glass-footer">
        <Container>
          <Row className="align-items-center">
            <Col md={4} className="text-center text-md-start mb-3 mb-md-0">
              <div className="footer-brand">
                <span className="icon"></span> RealEstate AI
              </div>
            </Col>
            <Col md={4} className="text-center mb-3 mb-md-0">
              <p className="footer-text mb-0">
                © 2024 RealEstate AI • Built with Django & React
              </p>
            </Col>
            <Col md={4} className="text-center text-md-end">
              <div className="footer-links">
                <a href="#privacy" className="footer-link">Privacy</a>
                <span className="separator">•</span>
                <a href="#terms" className="footer-link">Terms</a>
                <span className="separator">•</span>
                <a href="#support" className="footer-link">Support</a>
              </div>
            </Col>
          </Row>
        </Container>
      </footer>
    </div>
  );
}

export default App;