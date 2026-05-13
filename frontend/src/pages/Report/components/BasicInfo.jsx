const RISK_LABEL = { high: '고위험', medium: '주의', low: '안정', normal: '안정' };
const RISK_COLOR = {
  high:   { color: '#f87171', bg: 'rgba(248,113,113,0.12)' },
  medium: { color: '#fb923c', bg: 'rgba(251,146,60,0.12)'  },
  low:    { color: '#4ade80', bg: 'rgba(74,222,128,0.12)'  },
  normal: { color: '#4ade80', bg: 'rgba(74,222,128,0.12)'  },
};

export default function BasicInfo({ reportData }) {
  const info     = reportData?.company_info ?? {};
  const summary  = reportData?.summary ?? {};
  const riskLevel = summary.overall_risk_level ?? 'normal';
  const riskStyle = RISK_COLOR[riskLevel] ?? RISK_COLOR.normal;

  const rows = [
    { label: '기업명',   value: info.company_name  ?? '-' },
    { label: '종목코드', value: info.stock_code     ?? '-', highlight: true },
    { label: '분석연도', value: reportData?.analysis_year ? `${reportData.analysis_year}년` : '-' },
    { label: '기준연도', value: reportData?.base_year     ? `${reportData.base_year}년`     : '-' },
    { label: '주요발견', value: `${(summary.key_findings ?? []).length}건` },
  ];

  return (
    <div className="na-card bi-wrap">
      <div className="bi-title-row">
        <p className="na-card-title">기본 정보</p>
        {riskLevel && (
          <span
            className="bi-risk-badge"
            style={{ color: riskStyle.color, background: riskStyle.bg }}
          >
            {RISK_LABEL[riskLevel] ?? riskLevel}
          </span>
        )}
      </div>
      <div className="bi-row">
        {rows.map(({ label, value, highlight }) => (
          <div className="bi-item" key={label}>
            <span className="bi-label">{label}</span>
            <span className={highlight ? 'bi-value bi-ticker' : 'bi-value'}>{value}</span>
          </div>
        ))}
      </div>
      {summary.one_line_summary && (
        <p className="bi-summary">{summary.one_line_summary}</p>
      )}
    </div>
  );
}
