/* 뉴스 출처 / 링크 */
import { useMemo } from 'react';

// const MOCK_SOURCES = [
//   { id: 1, outlet: '한국경제',  title: 'HBM3E 수율 개선…삼성, 엔비디아 공급 물량 확대', date: '2026.05.07', url: null },
//   { id: 2, outlet: '조선일보',  title: '미 정부, 삼성 텍사스 공장 보조금 공식 확정', date: '2026.05.06', url: null },
//   { id: 3, outlet: '연합뉴스',  title: '삼성전자, 정관 변경…AI 소프트웨어·로봇 사업 추가', date: '2026.05.05', url: null },
//   { id: 4, outlet: 'Bloomberg', title: 'Samsung eyes HBM4 mass production in H2 2026', date: '2026.05.04', url: null },
// ];

const DOMAIN_TO_OUTLET = {
  'hankyung.com':   '한국경제',
  'chosun.com':     '조선일보',
  'biz.chosun.com': '조선비즈',
  'it.chosun.com':  'IT조선',
  'yna.co.kr':      '연합뉴스',
  'newsis.com':     '뉴시스',
  'mk.co.kr':       '매일경제',
  'sedaily.com':    '서울경제',
  'edaily.co.kr':   '이데일리',
  'etnews.com':     '전자신문',
  'zdnet.co.kr':    'ZDNet Korea',
  'fnnews.com':     '파이낸셜뉴스',
  'mt.co.kr':       '머니투데이',
  'asiae.co.kr':    '아시아경제',
  'heraldcorp.com': '헤럴드경제',
  'joongang.co.kr': '중앙일보',
  'donga.com':      '동아일보',
  'ddaily.co.kr':   '디지털데일리',
  'bloter.net':     '블로터',
  'thelec.kr':      '더일렉',
  'bloomberg.com':  'Bloomberg',
  'reuters.com':    'Reuters',
};

const OUTLET_COLORS = {
  '한국경제':    '#3b82f6',
  '조선일보':    '#ef4444',
  '조선비즈':    '#ef4444',
  'IT조선':      '#ef4444',
  '연합뉴스':    '#f59e0b',
  '뉴시스':      '#8b5cf6',
  '매일경제':    '#10b981',
  '서울경제':    '#ec4899',
  '이데일리':    '#8b5cf6',
  '전자신문':    '#06b6d4',
  'ZDNet Korea': '#0ea5e9',
  '파이낸셜뉴스':'#f97316',
  '머니투데이':  '#14b8a6',
  '아시아경제':  '#a855f7',
  '헤럴드경제':  '#6366f1',
  '중앙일보':    '#64748b',
  '동아일보':    '#1d4ed8',
  '디지털데일리':'#0891b2',
  '블로터':      '#7c3aed',
  '더일렉':      '#059669',
  'Bloomberg':   '#6366f1',
  'Reuters':     '#f97316',
};

const FALLBACK_COLORS = ['#6b7280', '#4b5563', '#374151', '#64748b', '#71717a'];

function extractOutlet(url) {
  if (!url) return '기타';
  try {
    const host = new URL(url).hostname.replace(/^www\./, '');
    return DOMAIN_TO_OUTLET[host] ?? host;
  } catch {
    return '기타';
  }
}

function getOutletColor(outlet) {
  if (OUTLET_COLORS[outlet]) return OUTLET_COLORS[outlet];
  let hash = 0;
  for (let i = 0; i < outlet.length; i++) hash += outlet.charCodeAt(i);
  return FALLBACK_COLORS[hash % FALLBACK_COLORS.length];
}

function formatDate(dateStr) {
  return (dateStr ?? '').replace(/-/g, '.');
}

export default function NewsSource({ evidenceNews }) {
  const sources = useMemo(() => {
    if (!evidenceNews?.length) return [];
    return evidenceNews.map((item, i) => ({
      id: i + 1,
      outlet: extractOutlet(item.url),
      title: item.title ?? '',
      date: formatDate(item.published_date),
      url: item.url ?? null,
    }));
  }, [evidenceNews]);

  return (
    <div className="na-card">
      <h3 className="na-card-title">뉴스 출처</h3>
      {sources.length === 0 && (
        <p className="na-empty-msg">뉴스 출처를 불러오지 못했습니다.</p>
      )}
      <ul className="nso-list">
        {sources.map((src) => (
          <li key={src.id} className="nso-item">
            <span
              className="nso-outlet"
              style={{ background: getOutletColor(src.outlet) }}
            >
              {src.outlet}
            </span>
            {src.url ? (
              <a
                href={src.url}
                target="_blank"
                rel="noopener noreferrer"
                className="nso-title nso-title-link"
              >
                {src.title}
              </a>
            ) : (
              <span className="nso-title">{src.title}</span>
            )}
            <span className="nso-date">{src.date}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
