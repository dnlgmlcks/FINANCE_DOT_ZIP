import AIChatPanel from '../components/ChatArea/AIchatpanel';
import './MainLayout.css';

const TABS = [
  { id: 'report',      label: '보고서' },
  { id: 'news',        label: '뉴스 분석' },
  { id: 'disclosure',  label: '공시 분석' },
];

export default function MainLayout({ activeTab, onTabChange, children }) {
  return (
    <div className="ml-wrap">
      <nav className="ml-tabs">
        {TABS.map(({ id, label }) => (
          <button
            key={id}
            className={`ml-tab-btn ${activeTab === id ? 'active' : ''}`}
            onClick={() => onTabChange(id)}
          >
            {label}
          </button>
        ))}
      </nav>

      <div className="ml-body">
        <div className="ml-content">{children}</div>
        <aside className="ml-chat">
          <AIChatPanel />
        </aside>
      </div>
    </div>
  );
}
