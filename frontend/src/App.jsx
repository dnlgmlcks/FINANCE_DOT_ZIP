import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import SearchBox from './components/SearchBox';
import MainContent from './components/MainContent';
import Footer from './components/Footer';

import { BeatLoader } from "react-spinners";  // 로딩 스피너 라이브러리

import { gfn_transaction } from './util/common-util';

function App() {
  const [loading, setLoading] = useState(false);        // 로딩바 여부
  const [reportData, setReportData] = useState(null);   // 레포트 데이터 (API 응답 결과)
  const [allCompanies, setAllCompanies] = useState([]); // 전체 원본 데이터
  const [filteredData, setFilteredData] = useState([]); // 화면에 보여줄 필터링된 데이터

  // 페이지 로드 시 딱 한 번 실행
  useEffect(() => {
    // 기본 정보 조회(기업 데이터)
    const fetchInitialData = async () => {
      const options = {
        svcId: 'initData',
        strUrl: '/api/initData', // 전체 데이터를 주는 백엔드 주소
        method: 'POST',
        pCall: (svcId, responseData, errCd, msgTp, msgCd, msgText) => {
          if (errCd === 0) {
              console.log('초기 데이터 로드 성공:', responseData.data);
              setAllCompanies(responseData.data); // 원본 저장
              // setFilteredData(responseData.data); // 처음엔 전체 다 보여줌
          } else {
            alert('통신 실패: ' + msgText);
          }
          // setLoading(false);
        },

      };
      await gfn_transaction(options);
    };

    fetchInitialData();
  }, []);

  // 조회 함수
  const handleSearch = async (keyword) => {
    
    if(keyword === "" || keyword === undefined ){
      alert('검색어를 입력해주세요.');
      return false;
    }
    
    // 로딩바 세팅
    setLoading(true);

    // 조회 API 옵션
    const options = {
      svcId: 'searchCompany',
      strUrl: '/api/searchCompany',
      param: { keyword: keyword },
      method: 'POST',
      inDs: {},
      pCall: (svcId, responseData, errCd, msgTp, msgCd, msgText) => {
        if (errCd === 0) {
          alert('통신 성공: ' + responseData.data.length + '개의 결과가 반환되었습니다.');
          // setReportData({
          //   title: `[분석 결과] ${keyword}`,
          //   content: `${keyword}에 대한 기업 DART 및 뉴스 종합 분석이 완료되었습니다. (차트 및 상세 데이터가 포함될 수 있습니다.)`,
          // });
        } else {
          alert('통신 실패: ' + msgText);
        }
        setLoading(false);
      },
    };

    try {
      await gfn_transaction(options);
    } catch (error) {
      console.error('API 통신 중 예외 발생', error);
      setLoading(false);
    }
  };

  const handleSendMessage = (messageText) => {
    console.log('대화 메시지 전송:', messageText);
  };

  // searchbox에서 사용자가 타이핑할 때마다 실행될 함수
const handleKeyIn = (keyword) => {
  console.log("handleKeyIn 실행, 입력값:", keyword);
  if (!keyword) {
    setFilteredData([]); // 입력값이 없으면 리스트를 비움
    return;
  }

  // 메모리에 저장된 전체 데이터에서 필터링
  const filtered = allCompanies.filter(company => 
    company.CORP_NAME.includes(keyword) || (company.CORP_CODE && company.CORP_CODE.includes(keyword))
  );
  
  setFilteredData(filtered);
};

  return (
    <div style={{ maxWidth: '1200px', margin: '40px auto', padding: '0 20px', fontFamily: 'sans-serif' }}>
      <Header title="Finance.zip" />
      <SearchBox onSearch={handleSearch} onKeyIn={handleKeyIn} searchResults={filteredData}/>
   
      {/* loading이 true일 때만 로딩 바를 보여줌 */}
      {loading && 
        <div style={{ textAlign: 'center' }}>
          <BeatLoader color="#0070f3" />
        </div>}

      {/* loading이 아닐 때만 결과 화면을 보여줌 */}
      {!loading && <MainContent data={reportData} />}
      
      <Footer />
    </div>
  );
}

export default App;