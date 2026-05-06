import React from 'react';

export function Report({ data }) {
  if (!data) return null;

  return (
    <div
      style={{
        border: '1px solid #eaeaea',
        borderRadius: '8px',
        padding: '20px',
        backgroundColor: '#fafafa',
        boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
        marginBottom: '20px',
      }}
    >
      <h2 style={{ color: '#0070f3', marginTop: 0 }}>{data.title}</h2>
      <div style={{ lineHeight: '1.6', color: '#555' }}>
        <p>{data.content}</p>
      </div>
    </div>
  );
}

export default Report;