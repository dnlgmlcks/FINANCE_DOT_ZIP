import { useState } from 'react';

function MainContent() {
  const [message, setMessage] = useState('오늘저녁 뭐먹지. 굶을까, Finance.zip');

  return (
    <main className="main-content">
      <section className="hero-section">
        <h2>{message}</h2>
        <p>졸려 집갈래</p>
      </section>
      <section className="action-area">
        <button className="main-button" onClick={() => setMessage('아이셔도 맛있어')}>
          빼빼로 맛있겠다
        </button>
      </section>
    </main>
  );
}
export default MainContent;