import { useState, useEffect } from 'react';
import Header from './components/Header';
import SearchBox from './components/SearchBox';
import MainLayout from './layouts/MainLayout';
import Report from './pages/Report';
import NewsAnalysis from './pages/NewsAnalysis';
import Disclosure from './pages/Disclosure';
import { BeatLoader } from 'react-spinners';
import { gfn_transaction } from './util/common-util';
import './index.css';
import './App.css';
import {SAMPLE_NORMAL_AI_INPUT, MOCK} from './mock_data';

const PAGE_MAP = {
  report:      <Report />,
  news:        <NewsAnalysis />,
  disclosure:  <Disclosure />,
};

function App() {
  const [activeTab, setActiveTab]           = useState('report');
  const [loading, setLoading]               = useState(false);
  const [allCompanies, setAllCompanies]     = useState([]);
  const [filteredData, setFilteredData]     = useState([]);
  const [searchCollapsed, setSearchCollapsed] = useState(false);
  const [searchResult, setSearchResult]     = useState(false);

  useEffect(() => {
    const fetchInitialData = async () => {
      const options = {
        svcId:  'initData',
        strUrl: '/api/initData',
        method: 'POST',
        pCall:  (svcId, responseData, errCd) => {
          if (errCd === 0) setAllCompanies(responseData.data);
        },
      };
      await gfn_transaction(options);
    };
    fetchInitialData();
  }, []);

  const handleSearch = async (keyword) => {
    if (!keyword) { alert('검색어를 입력해주세요.'); return; }

    // 내용 초기화 
    setSearchResult(null);
    // 로딩바
    setLoading(true);

    // 전송 파라미터
    const options = {
      svcId:  'searchCompany',
      strUrl: '/api/searchCompany',
      param:  { keyword },
      method: 'POST',
      pCall:  (svcId, responseData, errCd, msgTp, msgCd, msgText) => {

        // 데이터 체크
        const { reportData, newsData, disclosureData } = responseData ?? {};

        // setTimeout(function() {
        //   console.log('TEST!');
        // }, 3000);

        if (!reportData || !newsData || !disclosureData) {
            alert('일부 데이터가 누락되었습니다.');
            
        } else {
            setSearchResult(responseData);
        }

        setLoading(false);
      },
    };

    try {
      // 조회
      await gfn_transaction(options);
    } catch {
      setLoading(false);
    }
  };

  const renderPage = () => {

    // searchResult 없으면 렌더링 X -> 이건 백엔드가 다 붙지 않은 상황에서 잠시 주석처리
    // if (!searchResult) return null;

    const commonProps = { reportData: SAMPLE_NORMAL_AI_INPUT , disclosureData: MOCK };

    switch (activeTab) {
      case 'report':     return <Report {...commonProps} />;
      case 'news':       return <NewsAnalysis />;
      case 'disclosure': return <Disclosure {...commonProps} />;
    }
  };

  const handleKeyIn = (keyword) => {
    if (!keyword) { setFilteredData([]); return; }
    setFilteredData(
      allCompanies.filter(
        (c) => c.CORP_NAME.includes(keyword) || c.CORP_CODE?.includes(keyword)
      )
    );
  };

  return (
    <>
      <Header onToggleSearch={() => setSearchCollapsed(v => !v)} searchCollapsed={searchCollapsed} />
      <div className={`app-search-bar${searchCollapsed ? ' collapsed' : ''}`}>
        <SearchBox
          onSearch={handleSearch}
          onKeyIn={handleKeyIn}
          searchResults={filteredData}
        />
      </div>
      {loading && (
        <div className="app-loader">
          <BeatLoader color="#c084fc" size={10} />
        </div>
      )}
      <MainLayout activeTab={activeTab} onTabChange={setActiveTab}>
        {renderPage()}
      </MainLayout>
    </>
  );
}

export default App;
