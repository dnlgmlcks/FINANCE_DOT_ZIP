import { useState } from 'react';
import Report from './Report';
import AIChatPanel from "./ChatArea/AIchatpanel";

function MainContent() {
  const [message, setMessage] = useState('오늘저녁 뭐먹지. 굶을까, Finance.zip');
  const [loading, setLoading] = useState(false);
  const [reportData, setReportData] = useState(null);
  
  // 우측 채팅창의 확장/축소 상태를 관리하는 State
  const [isChatExpanded, setIsChatExpanded] = useState(true);

  return (
    <main className="main-content">
      {/* 좌우 분할 레이아웃 컨테이너 */}
      <div style={{ display: 'flex', gap: '24px', alignItems: 'flex-start', position: 'relative' }}>
        
        {/* 좌측: 레포트 영역 (확장 상태에 따라 65% 또는 100% 너비 변경) */}
        <div style={{ flex: `0 0 '65%'}`, transition: 'flex 0.3s ease' }}>
          {loading ? (
            <p style={{ textAlign: 'center', margin: '40px 0' }}>데이터를 분석하는 중입니다...</p>
          ) : (
            <Report data={reportData} />
          )}
        </div>

        {/* 우측: 대화 영역 */}
        <div style={{ flex: '0 0 33%', position: 'sticky', top: '20px', transition: 'all 0.3s ease' }}>
          <AIChatPanel />
        </div>
        
        {/* 토글(Expander) 버튼: 화면 우측 상단이나 분할 영역 사이에 위치 */}
        {reportData && (
          <button
            // onClick={() => setIsChatExpanded(!isChatExpanded)}
            style={{
              position: 'absolute',
              top: '-45px',
              right: '0',
              padding: '8px 16px',
              backgroundColor: '#0070f3',
              color: '#fff',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: 'bold',
            }}
          >
            {/* {isChatExpanded ? '대화창 접기' : '대화창 펼치기'} */}
          </button>
        )}

      </div>
    </main>
  );
}
export default MainContent;