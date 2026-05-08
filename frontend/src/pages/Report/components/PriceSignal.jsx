/**
 * PriceSignal.jsx
 * 주요 변동 Signal 카드 (좌측 하단)
 * - 현재가, 등락률, 시가총액, 외국인보유율 등
 * - props: signalData (optional)
 */

const MOCK = {
  price: '65,100',
  change: '+1,200',
  changeRate: '+1.88',
  direction: 'up', // 'up' | 'down'
  signals: [
    { label: '시가총액',     value: '388조',    dir: 'neu' },
    { label: '외국인보유율', value: '+28.5%',   dir: 'up'  },
    { label: '52주 고가',   value: '88,800',    dir: 'neu' },
    { label: '52주 저가',   value: '49,900',    dir: 'neu' },
    { label: '내러티브',    value: '+19.5%',    dir: 'up'  },
  ],
};

export default function PriceSignal({ signalData = MOCK }) {
  const { price, change, changeRate, direction, signals } = signalData;

  return (
    <div className="r-card ps-wrap">
      <p className="r-card-title">주요 변동 Signal</p>

      <div className="ps-price-row">
        <span className="ps-price">{price}</span>
        <span className={`ps-change ${direction}`}>
          {change} ({changeRate}%)
        </span>
      </div>

      <div className="ps-signals">
        {signals.map(({ label, value, dir }) => (
          <div className="ps-signal-item" key={label}>
            <span className="ps-signal-label">{label}</span>
            <span className={`ps-signal-val ${dir}`}>{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
