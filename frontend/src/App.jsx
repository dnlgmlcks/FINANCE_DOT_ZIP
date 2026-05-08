import { useState, useEffect } from 'react';
import Header from './components/Header';
import SearchBox from './components/SearchBox';
import MainLayout from './layouts/MainLayout';
import NewsAnalysis from './pages/NewsAnalysis';
import Report from './pages/Report';
import Disclosure from './pages/Disclosure';
import { BeatLoader } from 'react-spinners';
import { gfn_transaction } from './util/common-util';
import './index.css';
import './App.css';

const PAGE_MAP = {
  report:      <Report />,
  news:        <NewsAnalysis />,
  disclosure:  <Disclosure />,
};

function App() {
  const [activeTab, setActiveTab]       = useState('news');
  const [loading, setLoading]           = useState(false);
  const [allCompanies, setAllCompanies] = useState([]);
  const [filteredData, setFilteredData] = useState([]);

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
    setLoading(true);
    const options = {
      svcId:  'searchCompany',
      strUrl: '/api/searchCompany',
      param:  { keyword },
      method: 'POST',
      pCall:  (svcId, responseData, errCd, msgTp, msgCd, msgText) => {
        if (errCd !== 0) alert('통신 실패: ' + msgText);
        setLoading(false);
      },
    };
    try {
      await gfn_transaction(options);
    } catch {
      setLoading(false);
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
    <div className="container">
      <Header />
      <div className="app-search-bar">
        <SearchBox
          onSearch={handleSearch}
          onKeyIn={handleKeyIn}
          searchResults={filteredData}
        />
      </div>
      {loading && (
        <div className="loading-overlay">
          <BeatLoader color="#c084fc" size={10} />
        </div>
      )}
      <div className={`content-wrapper ${loading ? 'is-loading' : ''}`}>
        <MainLayout activeTab={activeTab} onTabChange={setActiveTab}>
          {PAGE_MAP[activeTab]}
        </MainLayout>
      </div>
    </div>
  );
}

export default App;
