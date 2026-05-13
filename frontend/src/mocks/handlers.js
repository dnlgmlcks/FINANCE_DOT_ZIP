import { http, HttpResponse } from 'msw';
import { EXPECTED_AI_OUTPUT_MOCK } from '../mock_data';

const MOCK_COMPANIES = [
  { CORP_NAME: '삼성전자', CORP_CODE: '005930' },
  { CORP_NAME: '테스트기업', CORP_CODE: '000000' },
  { CORP_NAME: 'SK하이닉스', CORP_CODE: '000660' },
  { CORP_NAME: 'LG전자', CORP_CODE: '066570' },
];

export const handlers = [
  http.post('/api/initData', () => {
    return HttpResponse.json({
      errCd: 0,
      data: MOCK_COMPANIES,
    });
  }),

  http.post('/api/searchCompany', () => {
    return HttpResponse.json({
      errCd: 0,
      data: {
        reportData: EXPECTED_AI_OUTPUT_MOCK,
        newsData:   EXPECTED_AI_OUTPUT_MOCK,
        disclosureData: null,
      },
    });
  }),
];
