/* 
    Disclosure

    Author        - jyhong
    Created At    - 2026-05-09
    Description   - 공시보고서 기반 분석 보고서 페이지 
    Features      - 
      1. LLM 연동을 통한 자동 분석 결과 제공 (향후 업데이트 예정)
*/
export default function CompDisclosure({ reportData }) {
  const d = reportData;

  if (!d || !d.sections) {
    return (
      <div className="dc-report r-card">
        <p style={{ color: 'var(--text-muted, #888)', textAlign: 'center', padding: '40px 0' }}>
          공시 데이터가 없습니다.
        </p>
      </div>
    );
  }

  return (
    <div className="dc-report r-card">
      <div className="dc-report-header">
        <span className="dc-report-corp">{d.title}</span>
        <span className="dc-report-date">{d.date}</span>
      </div>

      {d.sections.map(sec => (
        <div key={sec.id} className="dc-section">
          <h3 className="dc-section-title">
            <span className="dc-section-num">{sec.id}.</span>
            {sec.title}
          </h3>
          <ul className="dc-section-list">
            {sec.items.map((item, i) => (
              <li key={i} className="dc-section-item">{item}</li>
            ))}
          </ul>
        </div>
      ))}

      {/* TODO: 위험 관련 데이터가 있을 때 별도로 기재가 필요한가..?  */}
      {d.warnings && d.warnings.length > 0 && (
        <div className="dc-warnings">
          <h3 className="dc-section-title dc-warnings-title">
            위험 경보(Warning Signals) 감지
          </h3>
          <div className="dc-warnings-list">
            {d.warnings.map((w, i) => (
              <div key={i} className={`dc-warning-item dc-warning-${w.level}`}>
                <span className="dc-warning-dot" />
                <span className="dc-warning-text">{w.text}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
