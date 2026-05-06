import React from 'react';

export function Header({ title }) {
  return (
    <header style={{ padding: '16px 0', borderBottom: '1px solid #eee', marginBottom: '20px' }}>
      <h1 style={{ margin: 0, fontSize: '1.5rem', color: '#333' }}>{title}</h1>
    </header>
  );
}

export default Header;