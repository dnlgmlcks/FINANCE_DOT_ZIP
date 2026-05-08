import BasicInfo from './components/BasicInfo';
import PriceSignal from './components/PriceSignal';
import RevenueChart from './components/RevenueChart';
import FinancialTable from './components/FinancialTable';
import './Report.css';

export default function Report() {
  return (
    <div>
      {/* 페이지 헤더 */}
      <div className="na-page-header">
        <div className="na-title-group">
          <h2 className="na-page-title">기업 분석 기본 정보</h2>
          <span className="na-badge">LLM 베타</span>
        </div>
        <select className="na-model-select" defaultValue="3.0">
          <option value="3.0">3.0 버전</option>
          <option value="2.5">2.5 버전</option>
        </select>
      </div>
    
      <div className="report-wrap">
        {/* 페이지 헤더 */}
        
        {/* 상단: 기본정보 + 차트 */}
        <div className="report-top">
          <div className="report-left-col">
            <BasicInfo />
            <PriceSignal />
          </div>
          <div className="report-right-col">
            <RevenueChart />
          </div>
        </div>

        {/* 하단: 재무제표 + 주요지표 */}
        <div className="report-bottom">
          <FinancialTable />
        </div>
      </div>
    </div>
  );
}
