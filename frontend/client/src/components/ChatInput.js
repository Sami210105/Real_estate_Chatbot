import React, { useState } from "react";
import InputGroup from "react-bootstrap/InputGroup";
import FormControl from "react-bootstrap/FormControl";
import Button from "react-bootstrap/Button";

export default function ChatInput({ onQuery, loading }) {
  const [value, setValue] = useState("");
  
  const submit = () => {
    const q = value.trim();
    if (!q) return;
    if (onQuery) onQuery(q);
    setValue("");
  };
  
  return (
    <InputGroup size="lg">
      <FormControl
        placeholder="Ask anything... (e.g., 'Compare Wakad and Akurdi' or 'Show Hinjewadi price growth')"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && submit()}
        disabled={loading}
        style={{ fontSize: '1rem' }}
      />
      <Button 
        onClick={submit} 
        disabled={loading || !value.trim()}
        variant="primary"
        style={{ minWidth: '120px' }}
      >
        {loading ? (
          <>
            <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            Analyzing...
          </>
        ) : (
          <>Analyze</>
        )}
      </Button>
    </InputGroup>
  );
}