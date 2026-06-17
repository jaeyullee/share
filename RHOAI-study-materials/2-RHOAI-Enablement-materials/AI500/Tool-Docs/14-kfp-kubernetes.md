# kfp-kubernetes — 공식 문서

- **링크**: https://kfp-kubernetes.readthedocs.io/en/kfp-kubernetes-1.4.0/
- **분류**: Tool-Docs / AI
- **한 줄**: KFP SDK에 Kubernetes 네이티브 기능을 더하는 애드온 라이브러리.

## 추가 기능

- **Secrets / ConfigMaps** — 환경변수·볼륨으로 마운트
- **Storage** — PersistentVolumeClaim으로 태스크 간 영속 데이터 공유
- **Pod 설정** — label, annotation, node selector, toleration 등 스케줄링 제약
- **이미지 관리** — pull 정책(Always/IfNotPresent)
- **Ephemeral Volume** — Pod 생애주기에 묶인 임시 스토리지
- **Field Exposure** — K8s 메타데이터를 환경변수로 노출

## 사용 패턴

`@dsl.component`·`@dsl.pipeline`로 정의한 뒤, `kubernetes.use_secret_as_env()`, `kubernetes.mount_pvc()` 같은 헬퍼로 태스크 동작을 보강. 설치: `pip install kfp[kubernetes]`.

## 워크숍 맥락

[13-kfp-sdk](13-kfp-sdk.md)만으로 부족한 시크릿/볼륨/스케줄링을 RHOAI 파이프라인에서 제어할 때 사용.
