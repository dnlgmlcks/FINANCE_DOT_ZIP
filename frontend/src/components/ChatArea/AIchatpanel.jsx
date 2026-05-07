import { useState, useRef, useEffect } from "react";
import "./AIChatPanel.css";

// ── 아이콘 ──────────────────────────────────────────
function BotIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="11" width="18" height="10" rx="2" />
      <circle cx="12" cy="5" r="2" />
      <line x1="12" y1="7" x2="12" y2="11" />
      <line x1="8" y1="15" x2="8" y2="17" />
      <line x1="16" y1="15" x2="16" y2="17" />
    </svg>
  );
}

function UserIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );
}

// ── 타이핑 인디케이터 ──────────────────────────────
function TypingBubble() {
  return (
    <div className="acp-row assistant">
      <div className="acp-avatar bot"><BotIcon /></div>
      <div className="acp-col">
        <div className="acp-bubble acp-typing">
          <span className="acp-dot" />
          <span className="acp-dot" />
          <span className="acp-dot" />
        </div>
      </div>
    </div>
  );
}

// ── 목업 응답 (LLM 연동 전 임시) ─────────────────────
const MOCK_RESPONSES = [
  "삼성전자의 최근 실적을 보면 반도체 부문 회복세가 뚜렷합니다. 다만 환율과 글로벌 수요 불확실성은 여전히 변수로 작용하고 있습니다.",
  "현재 PBR 기준으로 역사적 저점 구간에 있어 밸류에이션 매력은 있습니다. 장기 투자자라면 긍정적으로 볼 수 있는 구간입니다.",
  "HBM 시장 점유율 확대와 함께 AI 인프라 수요 증가가 실적 개선의 핵심 동인이 될 전망입니다.",
  "배당 수익률과 자사주 매입 등 주주환원 정책도 최근 강화되는 추세입니다. 재무 안정성 측면에서는 긍정적입니다.",
  "단기적으로는 메모리 가격 사이클과 중국 수출 규제 이슈가 리스크 요인입니다. 포트폴리오 비중 조절이 필요할 수 있습니다.",
];

// ── 유틸 ─────────────────────────────────────────────
let mockIndex = 0;

function getTime() {
  const now = new Date();
  const h = now.getHours();
  const m = String(now.getMinutes()).padStart(2, "0");
  const ampm = h >= 12 ? "오후" : "오전";
  const hour = h > 12 ? h - 12 : h === 0 ? 12 : h;
  return `${ampm} ${hour}:${m}`;
}

// ── 초기 메시지 ──────────────────────────────────────
const INITIAL_MESSAGES = [
  {
    id: 1,
    role: "assistant",
    content: "안녕하세요! 삼성전자의 재무 분석 보고서에 대해 궁금하신 점이 있으시면 언제든지 질문해주세요.",
    time: getTime(),
  },
];

// ── 컴포넌트 ─────────────────────────────────────────
export default function AIChatPanel() {
  const [messages, setMessages] = useState(INITIAL_MESSAGES);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const bodyRef = useRef(null);
  const inputRef = useRef(null);

  // 새 메시지 올 때마다 스크롤 하단 이동
  useEffect(() => {
    if (bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSend = () => {
    const text = inputValue.trim();
    if (!text || isTyping) return;

    const userMsg = {
      id: Date.now(),
      role: "user",
      content: text,
      time: getTime(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputValue("");
    setIsTyping(true);

    // TODO: 여기를 실제 LLM API 호출로 교체
    const delay = 900 + Math.random() * 700;
    setTimeout(() => {
      const botMsg = {
        id: Date.now() + 1,
        role: "assistant",
        content: MOCK_RESPONSES[mockIndex % MOCK_RESPONSES.length],
        time: getTime(),
      };
      mockIndex++;
      setIsTyping(false);
      setMessages((prev) => [...prev, botMsg]);
      inputRef.current?.focus();
    }, delay);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="acp-panel">
      {/* 헤더 */}
      <div className="acp-header">
        <div className="acp-header-left">
          <div className="acp-bot-icon"><BotIcon /></div>
          <span className="acp-header-title">AI 분석 어시스턴트</span>
        </div>
      </div>

      {/* 메시지 목록 */}
      <div className="acp-body" ref={bodyRef}>
        <div className="acp-messages">
          {messages.map((msg) => (
            <div key={msg.id} className={`acp-row ${msg.role}`}>
              <div className={`acp-avatar ${msg.role === "assistant" ? "bot" : "user"}`}>
                {msg.role === "assistant" ? <BotIcon /> : <UserIcon />}
              </div>
              <div className="acp-col">
                <div className="acp-bubble">{msg.content}</div>
                <span className="acp-time">{msg.time}</span>
              </div>
            </div>
          ))}

          {/* 타이핑 인디케이터 */}
          {isTyping && <TypingBubble />}
        </div>
      </div>

      {/* 입력창 */}
      <div className="acp-input-area">
        <div className="acp-input-box">
          <input
            ref={inputRef}
            className="acp-input"
            placeholder="보고서에 대해 질문해보세요..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isTyping}
            maxLength={300}
          />
          <button
            className="acp-send-btn"
            onClick={handleSend}
            disabled={isTyping || !inputValue.trim()}
          >
            <SendIcon />
          </button>
        </div>
      </div>
    </div>
  );
}