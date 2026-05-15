/* 주요 경영 판단 요약 — Signal 흐름 (카테고리 → 태그들) */
import { useState, useMemo } from 'react';
import SignalDetail from './SignalDetail';

// const MOCK_SIGNALS = [
//   {
//     id: 1,
//     category: '반도체 영역 경기',
//     tags: [
//       {
//         tag: 'HBM 시장 점유 확대',
//         tagColor: '#c084fc',
//         tagBg: 'rgba(192,132,252,0.15)',
//         description: 'HBM3E 생산 수율이 전분기 대비 12%p 개선되며 엔비디아·AMD 향 공급 물량이 크게 확대됐습니다. AI 서버 수요 증가와 맞물려 평균 판가도 상승 추세입니다.',
//         keywords: ['HBM3E', '수율 개선', 'AI 서버', '엔비디아'],
//       },
//       {
//         tag: '경쟁사 대비 시장 현황',
//         tagColor: '#7b9fff',
//         tagBg: 'rgba(123,159,255,0.15)',
//         description: 'SK하이닉스의 HBM 점유율이 확대되는 가운데, 삼성전자는 2026년 하반기 HBM4 양산을 목표로 격차 축소에 나서고 있습니다.',
//         keywords: ['SK하이닉스', 'HBM4', '시장점유율'],
//       },
//     ],
//   },
//   {
//     id: 2,
//     category: '실리 투자 계획',
//     tags: [
//       {
//         tag: '환경 관련 사유',
//         tagColor: '#4ade80',
//         tagBg: 'rgba(74,222,128,0.12)',
//         description: '텍사스 테일러 파운드리 공장 착공이 예정대로 진행되며 미국 정부 보조금 440억 달러 수령이 공식 확정됐습니다. 장기 수주 확보에 긍정적 영향이 기대됩니다.',
//         keywords: ['테일러 공장', '미국 보조금', '파운드리'],
//       },
//     ],
//   },
//   {
//     id: 3,
//     category: '신규 사업 특목 추가 배경',
//     tags: [
//       {
//         tag: '신규 사업 특목 추가 방법',
//         tagColor: '#fb923c',
//         tagBg: 'rgba(251,146,60,0.12)',
//         description: '정관 목적 변경을 통해 AI 소프트웨어 및 로봇 관련 사업이 추가됐습니다. 가우스 LLM 상용화 일정 가속화와 연계된 포석으로 분석됩니다.',
//         keywords: ['정관 변경', '가우스 LLM', '로봇', 'AI 소프트웨어'],
//       },
//     ],
//   },
// ];

const COLOR_MAP = {
  increase: { tagColor: '#4ade80', tagBg: 'rgba(74,222,128,0.15)' },
  decrease_high:   { tagColor: '#f87171', tagBg: 'rgba(248,113,113,0.15)' },
  decrease_medium: { tagColor: '#fb923c', tagBg: 'rgba(251,146,60,0.15)' },
  decrease_low:    { tagColor: '#fbbf24', tagBg: 'rgba(251,191,36,0.12)' },
  neutral: { tagColor: '#94a3b8', tagBg: 'rgba(148,163,184,0.12)' },
};

function getTagColors(direction, severity) {
  if (direction === 'increase') return COLOR_MAP.increase;
  if (direction === 'decrease') {
    if (severity === 'high')   return COLOR_MAP.decrease_high;
    if (severity === 'medium') return COLOR_MAP.decrease_medium;
    if (severity === 'low')    return COLOR_MAP.decrease_low;
    return COLOR_MAP.decrease_high;
  }
  return COLOR_MAP.neutral;
}

function buildSignals(detectedChanges) {
  const groupMap = new Map();
  detectedChanges.forEach((change) => {
    const category = change.metric_label ?? '기타';
    if (!groupMap.has(category)) groupMap.set(category, { category, tags: [], tagLabels: new Set() });
    const group = groupMap.get(category);
    const tagLabel = change.source_signal || `${category} ${change.change_type || '변화'}`;
    if (group.tagLabels.has(tagLabel)) return;
    group.tagLabels.add(tagLabel);
    const { tagColor, tagBg } = getTagColors(change.direction, change.severity);
    group.tags.push({
      tag: tagLabel,
      tagColor,
      tagBg,
      description: change.description ?? '',
      keywords: change.search_keywords ?? [],
    });
  });
  return Array.from(groupMap.values()).map(({ tagLabels, ...row }, i) => ({ id: i + 1, ...row }));
}

export default function NewsSummary({ detectedChanges }) {
  const [activeSignal, setActiveSignal] = useState(null);

  const signals = useMemo(() => {
     if (!detectedChanges?.length) return [];
    return buildSignals(detectedChanges);
  }, [detectedChanges]);

  const handleTagClick = (rowId, tagIndex, tagData) => {
    if (activeSignal?.rowId === rowId && activeSignal?.tagIndex === tagIndex) {
      setActiveSignal(null);
    } else {
      setActiveSignal({ rowId, tagIndex, ...tagData });
    }
  };

  return (
    <div className="na-card">
      <h3 className="na-card-title">주요 경영 판단 요약</h3>
      <p className="na-card-hint">Signal 태그를 클릭하면 상세 내용을 확인할 수 있습니다.</p>

      {signals.length === 0 && (
        <p className="na-empty-msg">경영 판단 데이터를 불러오지 못했습니다.</p>
      )}

      <div className="ns-list">
        {signals.map((row) => (
          <div key={row.id} className="ns-row">
            {/* 카테고리 */}
            <div className="ns-flow">
              <span className="ns-category">{row.category}</span>
              <span className="ns-arrow">→</span>
              <div className="ns-tags">
                {row.tags.map((tag, i) => (
                  <button
                    key={i}
                    className={`ns-tag ${activeSignal?.rowId === row.id && activeSignal?.tagIndex === i ? 'active' : ''}`}
                    style={{
                      '--tag-color': tag.tagColor,
                      '--tag-bg': tag.tagBg,
                    }}
                    onClick={() => handleTagClick(row.id, i, tag)}
                  >
                    {tag.tag}
                  </button>
                ))}
              </div>
            </div>

            {/* 인라인 상세 패널 */}
            {activeSignal?.rowId === row.id && (
              <SignalDetail
                signal={activeSignal}
                onClose={() => setActiveSignal(null)}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
