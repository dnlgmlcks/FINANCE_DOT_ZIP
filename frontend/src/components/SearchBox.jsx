import React, { useState } from 'react';

export function SearchBox({ onSearch }) {
  const [keyword, setKeyword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault(); // 기본 새로고침 방지
    if (keyword.trim() === '') return;
    onSearch(keyword); // 부모 컴포넌트에서 받은 함수 실행
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
      <input
        type="text"
        value={keyword}
        onChange={(e) => setKeyword(e.target.value)}
        placeholder="조회할 기업명이나 검색어를 입력하세요"
        style={{
          flex: 1,
          padding: '10px',
          borderRadius: '4px',
          border: '1px solid #ccc',
          fontSize: '1rem',
        }}
      />
      <button
        type="submit"
        style={{
          padding: '10px 20px',
          borderRadius: '4px',
          backgroundColor: '#0070f3',
          color: '#fff',
          border: 'none',
          cursor: 'pointer',
          fontWeight: 'bold',
        }}
      >
        조회하기
      </button>
    </form>
  );
}

export default SearchBox;