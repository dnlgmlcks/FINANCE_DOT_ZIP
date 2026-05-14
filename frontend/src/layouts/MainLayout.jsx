import { useRef, useState, useCallback } from 'react';
import AIChatPanel from '../components/ChatArea/AIchatpanel';
import { Building2, Bot } from 'lucide-react';
import './MainLayout.css';

const TABS = [
  { id: 'report',      label: '보고서' },
  { id: 'news',        label: '뉴스 분석' },
  { id: 'disclosure',  label: '공시 분석' },
];

const CHAT_MIN = 220;
const CHAT_MAX = 600;
const CHAT_DEFAULT = 340;

export default function MainLayout({ activeTab, onTabChange, children, companyName, stockCode }) {
  const [chatWidth, setChatWidth] = useState(CHAT_DEFAULT);
  const dragging = useRef(false);
  const startX = useRef(0);
  const startWidth = useRef(0);

  const onMouseDown = useCallback((e) => {
    e.preventDefault();
    dragging.current = true;
    startX.current = e.clientX;
    startWidth.current = chatWidth;

    const onMouseMove = (e) => {
      if (!dragging.current) return;
      const delta = startX.current - e.clientX;
      const next = Math.min(CHAT_MAX, Math.max(CHAT_MIN, startWidth.current + delta));
      setChatWidth(next);
    };

    const onMouseUp = () => {
      dragging.current = false;
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  }, [chatWidth]);

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
        <div className="ml-content">
          
          {children ? (
              children
            ) : (
              <div>
                {/* 데이터가 없는 경우 default 부분 */}      
                <div className="default-report-wrap">
                  <Building2 size={64} className="mx-auto mb-4 opacity-50" />
                  <p>기업을 검색하여 재무 보고서를 확인하세요</p>
                </div>
              </div>
            )
          }
          
        </div>

        <div className="ml-resizer" onMouseDown={onMouseDown}>
          <div className="ml-resizer-handle">
            <span /><span /><span /><span /><span /><span />
          </div>
        </div>

        <aside className="ml-chat" style={{ width: chatWidth }}>
          {companyName ? (
              <AIChatPanel companyName={companyName} stockCode={stockCode} />
            ) : (
              <div>
                <div className="default-chat-wrap">
                  <Bot size={64} className="mx-auto mb-4 opacity-50" />
                  <p>기업을 검색하면 AI 어시스턴트와<br />대화를 시작할 수 있습니다</p>
                </div>
              </div>
            )
          }
        </aside>
      </div>
    </div>
  );
}
