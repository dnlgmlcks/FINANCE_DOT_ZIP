# Company Batch Summary

## 실행 기준
- limit: none
- batch_size: 500
- source: corpCode.xml, company.json
- market 기준: company.json corp_cls

## API 호출 범위
- corpCode.xml: 상장 후보 기업의 corp_code, stock_code, corp_name 매핑용
- company.json: corp_cls, stock_name, induty_code, acc_mt 보강용
- fnlttSinglAcntAll.json: 호출하지 않음

## 처리 결과
- master rows: 3963
- log rows: 3963

## log status counts
- success: 3963

## market counts
- KONEX: 110
- KOSDAQ: 1817
- KOSPI: 838
- OTHER: 1198

## updated batch companies files
- data\export\kospi_001\companies.csv
- data\export\kospi_002\companies.csv
- data\export\kosdaq_001\companies.csv
- data\export\kosdaq_002\companies.csv
- data\export\kosdaq_003\companies.csv
- data\export\kosdaq_004\companies.csv
- data\export\konex_001\companies.csv
