/**
 * BasicInfo.jsx
 * 기본 정보 카드 (상단 좌측)
 * - 종목명, 업종, 종목코드, 결산월, 날짜 등 표시
 * - props: stockData (optional) — 없으면 mock 데이터 사용
 */

const MOCK = {
  name: '삼성전자',
  nameEn: 'Samsung Electronics',
  exchange: 'KOSPI',
  sector: '반도체 및 전자부품 제조',
  industry: 'IT / 반도체',
  code: 'C4671',
  fiscalMonth: '12월',
  listedDate: '1969.01.13',
};

export default function BasicInfo({ stockData = MOCK }) {
  const {
    name, nameEn, exchange, sector,
    industry, code, fiscalMonth, listedDate,
  } = stockData;

  const rows = [
    { label: '기업명',   value: name },
    { label: 'English', value: nameEn },
    { label: '거래소',   value: exchange },
    { label: '업종',     value: sector },
    { label: '산업',     value: industry },
    { label: '종목코드', value: code,        highlight: true },
    { label: '결산월',   value: fiscalMonth },
    { label: '상장일',   value: listedDate },
  ];

  return (
    <div className="r-card bi-wrap">
      <p className="r-card-title">기본 정보</p>
      <div className="bi-row">
        {rows.map(({ label, value, highlight }) => (
          <div className="bi-item" key={label}>
            <span className="bi-label">{label}</span>
            <span className={highlight ? 'bi-value bi-ticker' : 'bi-value'}>
              {value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
