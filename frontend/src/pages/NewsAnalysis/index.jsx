import SignalList from './components/SignalList';
import NewsSummary from './components/NewsSummary';
import NewsSource from './components/NewsSource';
import './NewsAnalysis.css';

export default function NewsAnalysis() {
  return (
    <div>
      {/* 페이지 헤더 */}
      <div className="na-page-header">
        <div className="na-title-group">
          <h2 className="na-page-title">뉴스 기반 변동 사유 분석</h2>
          <span className="na-badge">LLM 베타</span>
        </div>
        <select className="na-model-select" defaultValue="3.0">
          <option value="3.0">3.0 버전</option>
          <option value="2.5">2.5 버전</option>
        </select>
      </div>

      {/* 최근 이슈 + 변동 사유 (2열) */}
      <SignalList />

      {/* 주요 경영 판단 요약 (Signal 태그 흐름) */}
      <NewsSummary />

      {/* 뉴스 출처 */}
      <NewsSource />
    </div>
  );
}
