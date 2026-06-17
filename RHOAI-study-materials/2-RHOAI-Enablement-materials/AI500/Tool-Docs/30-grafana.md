# Grafana — 공식 문서

- **링크**: https://grafana.com/docs/grafana/latest/
- **분류**: Tool-Docs / DevOps
- **한 줄**: 메트릭·로그·트레이스를 질의·시각화·알림·탐색하는 오픈소스 관찰성 플랫폼.

## 무엇인가

"query, visualize, alert on, and explore your metrics, logs, and traces wherever they are stored." 오픈소스판과 Enterprise판 존재.

## 핵심 개념

- **Data Sources** — Prometheus·CloudWatch(메트릭), Loki·Elasticsearch(로그), Postgres 등 백엔드 연결
- **Dashboards** — 실시간 그래프·시각화
- **Panels & Visualizations** — 데이터 수집·상관·시각화
- **Alerting** — 문제 발생 시 알림
- **Explore** — 대시보드 없이 즉석 질의

## 문서 범위

셋업, 데이터소스 구성, 대시보드 생성, 시각화 옵션, 알림, 관리, 트러블슈팅, 업그레이드.

## 워크숍 맥락

[../References/07-google-mlops](../References/07-google-mlops.md) Level 2의 "Monitoring"을 구현하는 시각화 레이어. RHOAI/모델 서빙([18-kserve](18-kserve.md))·[15-trustyai](15-trustyai.md) 지표를 대시보드로 관찰. [04-AI-보안-관찰성-기초](../../../4-etc-AI-materials/04-AI-보안-관찰성-기초.md)와 연계.
