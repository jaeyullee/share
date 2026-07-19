# RHOAI Hands-On v1.0

RHOAI 3.4를 대상으로 한 실습 커리큘럼과 실행 자료다. OpenShift와 Kubernetes 기본기를 갖추고, 동등한 테스트 인프라를 준비할 수 있는 실습자를 대상으로 한다. 검증 기준 환경은 disconnected OpenShift 4.22와 RHOAI 3.4이다.

## 시작 순서

1. [커리큘럼 XLSX](RHOAI-3.4-HandsOn-커리큘럼-v1.0.xlsx)에서 전체 범위와 환경 의존성을 확인한다.
2. [실습자료 검토 항목](00-실습자료-검토항목.md)을 먼저 읽고, 자신의 환경과 다른 조건을 확인한다.
3. [Week1 Day1&2 환경 구성](Week1-Day1&2-환경구성.md)으로 OpenShift AI 기본 구성과 공통 의존성을 준비한다.
4. Week1부터 Week3까지를 순서대로 수행한다. 이는 모델 서빙, 학습과 파이프라인, 모델 레지스트리, 보안, 관측성, MaaS를 다루는 기본 과정이다.
5. Week4부터 Week7까지는 추가 스터디다. 각 Week의 Step0 사전점검을 통과한 경우에만 다음 Step을 진행한다.

## 필요한 환경

- OpenShift cluster-admin 권한과 `oc`, `jq`, `curl`, `git`, `openssl`, `python3`, MinIO Client(`mc`)를 사용할 수 있는 Bastion.
- 기본 과정용 CPU 자원. GPU 과정은 NVIDIA GPU 노드와 GPU Operator가 추가로 필요하다.
- 동등한 StorageClass와 S3 호환 object storage. 각 문서의 `<MINIO_ID>`, `<MINIO_PW>` 등 표시는 자신의 Secret 값으로 대체한다.
- disconnected 환경이면 필요한 Operator catalog, 컨테이너 이미지, Python 의존성, 모델 artifact를 사전에 mirror한다.
- Week5는 Gitea, OpenShift Pipelines, OpenShift GitOps, 내부 이미지 레지스트리와 S3를 사용한다. Week6은 물리 GPU 2개, Week7은 RHBK, RHCL, OADP, Kueue, Ray 등의 추가 인프라 또는 권한을 요구한다.

검증 환경의 IP, 도메인, StorageClass, image digest, GPU 토폴로지는 예시 값이다. 값을 복사하기 전에 반드시 자신의 환경 값으로 치환한다. 비밀값은 문서나 Git 저장소에 기록하지 않고, Secret 또는 실행 중 입력으로만 제공한다.

## 과정 구성

| 범위 | 주제 | 시작 문서 |
|---|---|---|
| Week1 | RHOAI 설치와 KServe 모델 서빙 | [Day1&2](Week1-Day1&2-환경구성.md) |
| Week2 | Workbench, Pipelines, Model Registry, RBAC | [Day6](<Week2-Day6 실습.md>) |
| Week3 | GPU 운영, 관측성, MaaS, 통합 장애 대응 | [Day11](<Week3-Day11 실습.md>) |
| Week4 | GPU sharing과 Kueue cohort | [Step0](<Week4-Step0 사전점검 실습.md>) |
| Week5 | LLM MLOps CI/CD | [Step0](<Week5-Step0 사전점검 실습.md>) |
| Week6 | 2-GPU vLLM Tensor Parallel | [Step0](<Week6-Step0 사전점검 실습.md>) |
| Week7 | 인증·인가, 백업/복구, Ray, 운영 관리 | [Step0](<Week7-Step0 사전점검 실습.md>) |

## 실행 원칙

- 각 문서의 사전점검, 적용 확인, 원복 절을 같은 실행 단위로 수행한다.
- 별도 터미널 또는 SSH 재접속 전에는 문서가 요구하는 환경변수와 백업 경로를 다시 확인한다. 특히 Week7은 `/tmp/week7-before-*` 백업 디렉터리를 선택해 `WEEK7_BACKUP_DIR`를 export한 뒤 원복 절을 실행한다.
- 실습 실패 시 다음 Step으로 넘어가지 않는다. 해당 문서의 상태 확인과 rollback 절을 먼저 수행한다.
- Week4~7은 기본 RHOAI 설치 외 Operator와 외부 서비스를 추가한다. 전체 과정을 끝낸 뒤에는 각 문서의 cleanup을 수행하고, 필요한 경우 Week1 Day1&2의 기본 상태 기준으로 복귀한다.

## 포함 자료

- [datasets/README.md](datasets/README.md): 합성 데이터와 disconnected MNIST 캐시의 용도 및 경로.
- [models/README.md](models/README.md): 학습 및 모델 변환 스크립트.
- [models/llm-serving-models.md](models/llm-serving-models.md): LLM 모델 반입 참고.

이 자료는 검증 환경의 재현 가능한 절차를 제공하지만, 모든 플랫폼 조합을 일반화하지 않는다. 환경별 차이와 지원 범위는 [실습자료 검토 항목](00-실습자료-검토항목.md)을 정본으로 확인한다.
