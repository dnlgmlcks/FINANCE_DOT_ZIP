/* 최근 주요 이슈 요약 + 뉴스 기반 변동 사유 */

const MOCK_RECENT_ISSUES = [
  { id: 1, date: '2026.05.07', headline: 'HBM3E 생산 수율 개선으로 엔비디아 공급 확대 기대감' },
  { id: 2, date: '2026.05.06', headline: '중국 반도체 수출 규제 완화 논의… 삼성·SK 수혜 주목' },
  { id: 3, date: '2026.05.05', headline: '파운드리 부문 적자 지속, 2분기 턴어라운드 가능성은?' },
];

const MOCK_CHANGE_REASONS = [
  { id: 1, signal: 'positive', label: '▲ +2.3%', reason: 'HBM 공급 증가 기대감이 주가 반등 주요 요인으로 작용' },
  { id: 2, signal: 'negative', label: '▼ -0.8%', reason: '파운드리 적자 지속 우려가 상승폭을 제한' },
  { id: 3, signal: 'neutral',  label: '→ 0.0%', reason: '미 연준 금리 동결 결정으로 시장 관망세 유지' },
];

const SIGNAL_COLOR = {
  positive: { color: '#4ade80', bg: 'rgba(74,222,128,0.12)' },
  negative: { color: '#f87171', bg: 'rgba(248,113,113,0.12)' },
  neutral:  { color: '#94a3b8', bg: 'rgba(148,163,184,0.12)' },
};

export default function SignalList() {
  return (
    <div className="na-section-row">
      {/* 최근 주요 이슈 요약 */}
      <div className="na-card na-card-half">
        <h3 className="na-card-title">최근 주요 이슈 요약</h3>
        <ul className="na-issue-list">
          {MOCK_RECENT_ISSUES.map((item) => (
            <li key={item.id} className="na-issue-item">
              <span className="na-issue-date">{item.date}</span>
              <span className="na-issue-text">{item.headline}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* 뉴스 기반 변동 사유 */}
      <div className="na-card na-card-half">
        <h3 className="na-card-title">뉴스 기반 변동 사유</h3>
        <ul className="na-change-list">
          {MOCK_CHANGE_REASONS.map((item) => {
            const style = SIGNAL_COLOR[item.signal];
            return (
              <li key={item.id} className="na-change-item">
                <span
                  className="na-change-badge"
                  style={{ color: style.color, background: style.bg }}
                >
                  {item.label}
                </span>
                <span className="na-change-reason">{item.reason}</span>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
