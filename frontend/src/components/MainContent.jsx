import { useState } from 'react';
import Report from './Report';
import ChatArea from './ChatArea';

function MainContent() {
  const [message, setMessage] = useState('오늘저녁 뭐먹지. 굶을까, Finance.zip');
  const [loading, setLoading] = useState(false);
  const [reportData, setReportData] = useState(null);
  
  // 우측 채팅창의 확장/축소 상태를 관리하는 State
  const [isChatExpanded, setIsChatExpanded] = useState(true);

  const handleSearch = async (keyword) => {
    setLoading(true);

    const options = {
      svcId: 'fetchAnalysis',
      strUrl: '/api/v1/search',
      param: { keyword: keyword },
      inDs: {},
      pCall: (svcId, responseData, errCd, msgTp, msgCd, msgText) => {
        if (errCd === 0) {
          setReportData({
            title: `[분석 결과] ${keyword}`,
            content: `${keyword}에 대한 기업 DART 및 뉴스 종합 분석이 완료되었습니다. (차트 및 상세 데이터가 포함될 수 있습니다.)`,
          });
        } else {
          alert('통신 실패: ' + msgText);
        }
        setLoading(false);
      },
    };

    // try {
    //   await gfn_transaction(options);
    // } catch (error) {
    //   console.error('API 통신 중 예외 발생', error);
    //   setLoading(false);
    // }
  };

  const handleSendMessage = (messageText) => {
    console.log('대화 메시지 전송:', messageText);
  };


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

        {/* 우측: 대화 영역 (isChatExpanded 상태에 따라 보이기/숨기기 처리) */}
        {(
          <div style={{ flex: '0 0 33%', position: 'sticky', top: '20px', transition: 'all 0.3s ease' }}>
            <ChatArea onSendMessage={handleSendMessage} />
          </div>
        )}
        
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