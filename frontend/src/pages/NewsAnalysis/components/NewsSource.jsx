/* 뉴스 출처 / 링크 */

const MOCK_SOURCES = [
  { id: 1, outlet: '한국경제',  title: 'HBM3E 수율 개선…삼성, 엔비디아 공급 물량 확대', date: '2026.05.07' },
  { id: 2, outlet: '조선일보',  title: '미 정부, 삼성 텍사스 공장 보조금 공식 확정', date: '2026.05.06' },
  { id: 3, outlet: '연합뉴스',  title: '삼성전자, 정관 변경…AI 소프트웨어·로봇 사업 추가', date: '2026.05.05' },
  { id: 4, outlet: 'Bloomberg', title: 'Samsung eyes HBM4 mass production in H2 2026', date: '2026.05.04' },
];

const OUTLET_COLORS = {
  '한국경제': '#3b82f6',
  '조선일보': '#ef4444',
  '연합뉴스': '#f59e0b',
  'Bloomberg': '#6366f1',
};

export default function NewsSource() {
  return (
    <div className="na-card">
      <h3 className="na-card-title">뉴스 출처</h3>
      <ul className="nso-list">
        {MOCK_SOURCES.map((src) => (
          <li key={src.id} className="nso-item">
            <span
              className="nso-outlet"
              style={{ background: OUTLET_COLORS[src.outlet] ?? '#6b7280' }}
            >
              {src.outlet}
            </span>
            <span className="nso-title">{src.title}</span>
            <span className="nso-date">{src.date}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
