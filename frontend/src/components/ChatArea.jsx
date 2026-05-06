import React, { useState } from 'react';

export function ChatArea({ onSendMessage }) {
  const [inputMessage, setInputMessage] = useState('');
  const [chatLog, setChatLog] = useState([]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputMessage.trim() === '') return;

    // 대화 로그에 사용자 메시지 추가
    const newLog = [...chatLog, { sender: 'user', text: inputMessage }];
    setChatLog(newLog);
    setInputMessage('');

    // 부모 컴포넌트에 메시지 전달
    if (onSendMessage) {
      onSendMessage(inputMessage);
    }
  };

  return (
    <div
      style={{
        border: '1px solid #dcdcdc',
        borderRadius: '8px',
        padding: '20px',
        backgroundColor: '#fff',
      }}
    >
      {/* <h3 style={{ marginTop: 0, color: '#333' }}></h3> */}
      
      {/* 대화 기록 표시창 */}
      <div
        style={{
          maxHeight: '150px',
          overflowY: 'auto',
          padding: '10px',
          backgroundColor: '#f9f9f9',
          borderRadius: '4px',
          marginBottom: '15px',
        }}
      >
        {chatLog.length === 0 ? (
          <p style={{ color: '#999', fontSize: '0.9rem' }}>대화 기록이 없습니다. 질문을 입력해보세요!</p>
        ) : (
          chatLog.map((chat, idx) => (
            <div key={idx} style={{ marginBottom: '8px' }}>
              <strong>{chat.sender === 'user' ? '사용자' : '시스템'}:</strong> {chat.text}
            </div>
          ))
        )}
      </div>

      {/* 메시지 입력 폼 */}
      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '10px' }}>
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="추가로 궁금한 내용을 입력하세요"
          style={{
            flex: 1,
            padding: '8px',
            borderRadius: '4px',
            border: '1px solid #ccc',
          }}
        />
        <button
          type="submit"
          style={{
            padding: '8px 16px',
            borderRadius: '4px',
            backgroundColor: '#28a745',
            color: '#fff',
            border: 'none',
            cursor: 'pointer',
          }}
        >
          전송
        </button>
      </form>
    </div>
  );
}

export default ChatArea;