import React, { useState } from 'react';
import Header from './components/Header';
import SearchBox from './components/SearchBox';
import MainContent from './components/MainContent';
import Footer from './components/Footer';

// import { gfn_transaction } from './api/apiService';

function App() {
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
    <div style={{ maxWidth: '1200px', margin: '40px auto', padding: '0 20px', fontFamily: 'sans-serif' }}>
      <Header title="기업 분석 대시보드" />
      <SearchBox onSearch={handleSearch} />
      <MainContent />
      <Footer />
    </div>
  );
}

export default App;