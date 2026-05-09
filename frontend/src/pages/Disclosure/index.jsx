import { useState } from 'react';
import Disclosure from './components/CompDisclosure';
import './Disclosure.css';

export default function DisclosurePage({ disclosureData }) {

  return (
    <div>
      {/* 페이지 헤더 */}
      <div className="na-page-header">
        <div className="na-title-group">
          <h2 className="na-page-title">변동 사유 분석</h2>
          <span className="na-badge">LLM 베타</span>
        </div>
      </div>

      <div className="report-wrap">
        <div className="report-bottom">
          <Disclosure reportData={disclosureData} />
        </div>
      </div>
    </div>
  );
}
