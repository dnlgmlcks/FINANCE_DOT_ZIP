import React, { useState } from 'react';

export function SearchBox({ onSearch, onKeyIn, searchResults }) {
  const [keyword, setKeyword] = useState('');

  const handleInputChange = (e) => {
    const value = e.target.value;
    setKeyword(value);    // 화면에 타이핑한 글자 반영
    onKeyIn(value);       // 부모(App.jsx)에게 전달해서 리스트 필터링
  };

  const handleItemClick = (company) => {
    // 클릭한 회사의 이름을 검색창에 반영
    setKeyword(company.CORP_NAME);
    
    // 리스트 닫기.
    onKeyIn(""); 
  };

  return (
    <div style={{ position: 'relative', width: '100%', marginBottom: '20px' }}>
      <div style={{ display: 'flex', gap: '10px' }}>
        <input 
          type="text" 
          value={keyword}
          placeholder="기업명을 입력하세요"
          onChange={handleInputChange}
          style={{ flex: 1, padding: '10px', borderRadius: '4px', border: '1px solid #ccc' }}
        />
        {/* 검색 결과가 있을 때만 ul 표시 */}
        {searchResults && searchResults.length > 0 && (
          <ul style={{ 
            position: 'absolute', // 아래 컨텐츠를 밀어내지 않음
            top: '45px', 
            left: 0, 
            right: 0, 
            backgroundColor: 'white', 
            border: '1px solid #ddd', 
            borderRadius: '4px',
            zIndex: 100, // 최상단에 위치
            maxHeight: '200px',
            overflowY: 'auto',
            listStyle: 'none',
            padding: 0,
            margin: 0,
            boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
          }}>
          {searchResults.map((company, index) => (
            <li 
              key={index} 
              onClick={() => handleItemClick(company)}
              style={{ 
                padding: '10px', 
                cursor: 'pointer', 
                borderBottom: '1px solid #eee' 
              }}
              onMouseOver={(e) => e.target.style.backgroundColor = '#f0f0f0'}
              onMouseOut={(e) => e.target.style.backgroundColor = 'transparent'}
            >
              <strong>{company.CORP_NAME}</strong> <small style={{ color: '#888' }}>{company.CORP_CODE}</small>
            </li>
          ))}
        </ul>
      )}
        <button onClick={() => onSearch()} style={{ padding: '10px 20px' }}>분석</button>
      </div>

      
    </div>
    
  );
}

export default SearchBox;