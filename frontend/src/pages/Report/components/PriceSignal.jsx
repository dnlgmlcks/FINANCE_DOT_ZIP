const MOCK = {
  price: '65,100',
  change: '+1,200',
  changeRate: '+1.88',
  direction: 'up',
  signals: [
    { label: '시가총액',     value: '388조',   dir: 'neu' },
    { label: '외국인보유율', value: '+28.5%',  dir: 'up'  },
    { label: '52주 고가',   value: '88,800',   dir: 'neu' },
    { label: '52주 저가',   value: '49,900',   dir: 'neu' },
  ],
};

export default function PriceSignal({ signalData = MOCK }) {
  const { price, change, changeRate, direction, signals } = signalData;

  return (
    <div className="na-card ps-wrap">
      <p className="na-card-title">주요 변동 Signal</p>

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
