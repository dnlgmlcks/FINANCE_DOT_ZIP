import { useState, useEffect } from 'react';
import { LucideProvider } from 'lucide-react';
import Header from './components/Header';
import SearchBox from './components/SearchBox';
import MainLayout from './layouts/MainLayout';
import Report from './pages/Report';
import NewsAnalysis from './pages/NewsAnalysis';
import Disclosure from './pages/Disclosure';
import HomePage from './pages/Home';
import { BeatLoader } from 'react-spinners';
import { gfn_transaction } from './util/common-util';
import './index.css';
import './App.css';
import { MOCK } from './mock_data';

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
  const [searchResult, setSearchResult]     = useState(null);
  const [companyName, setCompanyName]       = useState(null);

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
    setCompanyName(null);
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
        const { reportData, newsData, disclosureData } = responseData?.data ?? {};

        // setTimeout(function() {
        //   console.log('TEST!');
        // }, 3000);

        // if (!reportData || !newsData || !disclosureData) {
        //     alert('일부 데이터가 누락되었습니다.');
            
        // } else {
            setSearchResult(responseData.data);
            setCompanyName(responseData.data.reportData?.company_name ?? keyword);
        // }

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
    if (!searchResult) return <HomePage />;

    const reportData     = searchResult.reportData;
    const newsData       = searchResult.newsData;
    const disclosureData = searchResult.disclosureData ?? MOCK;

    switch (activeTab) {
      case 'report':     return <Report reportData={reportData} disclosureData={disclosureData} />;
      case 'news':       return <NewsAnalysis newsData={newsData} />;
      case 'disclosure': return <Disclosure reportData={reportData} disclosureData={disclosureData} />;
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
    <LucideProvider>
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
      <MainLayout activeTab={activeTab} onTabChange={setActiveTab} companyName={companyName}>
        {renderPage()}
      </MainLayout>
    </LucideProvider>
  );
}

export default App;
