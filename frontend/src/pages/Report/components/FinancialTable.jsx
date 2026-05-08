/**
 * FinancialTable.jsx
 * 재무제표 / 주요 지표(비율) 테이블 (하단 전체)
 * - 탭: 재무제표 | 주요 지표(비율)
 * - props: financialData, ratioData (optional)
 */
import { useState } from 'react';

/* ── 재무제표 mock ─────────────────────────────── */
const MOCK_FINANCIAL = {
  years: ['2020', '2021', '2022', '2023', '2024'],
  rows: [
    { label: '매출액(억)',    values: ['2,368', '2,796', '3,022', '2,589', '3,009'], dir: [0,0,0,0,0] },
    { label: '영업이익(억)',  values: ['359',   '516',   '433',   '65',    '327' ],  dir: [0,1,0,-1,1] },
    { label: '당기순이익(억)',values: ['264',   '399',   '555',   '154',   '344' ],  dir: [0,1,1,-1,1] },
    { label: '영업이익률(%)', values: ['6.87',  '7.355', '8,033', '3,355', '3,078'], dir: [0,1,1,-1,0] },
    { label: '내러티브(억)',  values: ['23,98', '—',     '—',     '3,236', '1,075'], dir: [0,0,0,0,0] },
  ],
};

/* ── 주요 지표 mock ────────────────────────────── */
const MOCK_RATIO = {
  years: ['2020', '2021', '2022', '2023', '2024'],
  rows: [
    { label: 'PER',      values: ['21.3', '13.8', '9.4',  '38.2', '11.7'], dir: [0,0,0,-1,1] },
    { label: 'PBR',      values: ['1.88', '1.76', '1.22', '1.45', '1.09'], dir: [0,0,0,0,0]  },
    { label: 'ROE(%)',   values: ['9.2',  '13.9', '14.1', '3.9',  '10.2'], dir: [0,1,1,-1,1] },
    { label: 'ROA(%)',   values: ['5.4',  '8.3',  '9.0',  '2.2',  '6.1'],  dir: [0,1,1,-1,1] },
    { label: '부채비율', values: ['39.6', '42.3', '37.8', '41.2', '38.5'], dir: [0,0,0,0,0]  },
    { label: 'EPS(원)',  values: ['3,841','5,777','8,057','2,131','4,872'], dir: [0,1,1,-1,1] },
  ],
};

const TABS = [
  { id: 'financial', label: '재무제표' },
  { id: 'ratio',     label: '주요 지표(비율)' },
];

function dirClass(d) {
  if (d > 0) return 'ft-val-up';
  if (d < 0) return 'ft-val-down';
  return '';
}

export default function FinancialTable({
  financialData = MOCK_FINANCIAL,
  ratioData     = MOCK_RATIO,
}) {
  const [activeTab, setActiveTab] = useState('financial');
  const data = activeTab === 'financial' ? financialData : ratioData;

  return (
    <div className="r-card ft-wrap">
      <div className="ft-header">
        <span className="ft-title">
          {activeTab === 'financial' ? '재무제표' : '주요 지표 (비율)'}
        </span>
        <div className="ft-tabs">
          {TABS.map(({ id, label }) => (
            <button
              key={id}
              className={`ft-tab-btn ${activeTab === id ? 'active' : ''}`}
              onClick={() => setActiveTab(id)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <table className="ft-table">
        <thead>
          <tr>
            <th>항목</th>
            {data.years.map((y) => <th key={y}>{y}</th>)}
          </tr>
        </thead>
        <tbody>
          {data.rows.map(({ label, values, dir }) => (
            <tr key={label}>
              <td>{label}</td>
              {values.map((v, i) => (
                <td key={i} className={dirClass(dir[i])}>{v}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
