/* Signal 태그 클릭 시 나타나는 인라인 상세 패널 */

export default function SignalDetail({ signal, onClose }) {
  if (!signal) return null;

  return (
    <div className="sd-wrap">
      <div className="sd-header">
        <span className="sd-tag" style={{ background: signal.tagBg, color: signal.tagColor }}>
          {signal.tag}
        </span>
        <button className="sd-close" onClick={onClose}>✕</button>
      </div>
      <p className="sd-desc">{signal.description}</p>
      {signal.keywords && (
        <div className="sd-keywords">
          {signal.keywords.map((kw, i) => (
            <span key={i} className="sd-kw">{kw}</span>
          ))}
        </div>
      )}
    </div>
  );
}
