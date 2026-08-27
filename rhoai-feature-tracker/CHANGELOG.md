# RHOAI 변경 이력 (CHANGELOG)

## 2026-08-27

### 🆕 신규 (107)
- **3.5 GA new features Migration guide using rhai-cli for upgrading from OpenShift AI 2.25.9 and later to 3.5** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: A new migration guide, Assess and plan for migration from Red Hat OpenShift AI 2.25.9 (and later) to 3.5 , is now available.
- **EvalHub general availability for the Red Hat AI evaluation stack** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: EvalHub is generally available (GA).
- **Support for deploying Red Hat AI Inference fast release container images as a custom serving runtime** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can deploy Red Hat AI Inference fast release container images as custom serving runtimes on your existing Red Hat OpenShift AI installation without upgrading Red Hat OpenShift AI.
- **Adversarial vulnerability scanning for Red Hat-validated models** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: New models added to the Red Hat AI validated models catalog now undergo automated adversarial vulnerability scanning as part of the validation process.
- **EvalCard generation for evaluation runs** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: In OpenShift AI, you can generate standardized Evaluation Cards (EvalCards) for every evaluation run in EvalHub.
- **batch engine for Feast Feature Store** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: SparkApplication Feast Feature Store supports a batch engine.
- **EvalHub server local development mode** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can run the EvalHub Server in a local development mode on macOS, Linux, and Windows workstations.
- **DiffusionGemma (dLLM) model support** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can deploy DiffusionGemma models for inference.
- **GPU-accelerated runtime for predictive machine learning** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: A new MLServer GPU container image and corresponding cluster serving runtime ( mlserver-onnx- gpu ) are available to support NVIDIA GPU-accelerated inference for predictive machine learning workloads.
- **Automated Red Teaming** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Automated Red Teaming is generally available (GA).
- **Kueue workload scheduling visibility in the workbenches overview** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: When Kueue manages workload scheduling in a project, the workbenches overview page displays Kueue-derived scheduling states for each workbench.
- **Custom role creation UI for data science projects** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Project administrators can create, edit, and duplicate custom RBAC roles for workbenches directly from the Roles tab in data science projects, without requiring CLI access or YAML expertise.
- **MLflow integration for AI Pipelines and training environments** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: MLflow is fully integrated to provide centralized machine learning (ML) lifecycle management.
- **Inference-aware pod lifecycle for Distributed Inference with llm-d** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can perform routine deployment operations, such as rolling updates, scale-downs, and node maintenance, without dropping active inference requests.
- **Distributed Inference with llm-d on cross-Kubernetes platforms** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: NEW FEATURES AND ENHANCEMENTS Distributed Inference with llm-d is generally available on Azure Kubernetes Service (AKS), CoreWeave Kubernetes Service (CKS), and OpenShift.
- **Priority-based flow control for mixed Distributed Inference with llm-d workloads** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Flow control for Distributed Inference with llm-d is generally available.
- **Controlled deployment for Distributed Inference with llm-d** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: With this update, you can use controlled deployment with Distributed Inference with llm-d to validate engine upgrades, model version rotations, and configuration changes on a fraction of production traffic before a full promotion.
- **Observability reference dashboards for Distributed Inference with llm-d using Perses** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can monitor Distributed Inference with llm-d deployments by using reference dashboards delivered through Perses and the Cluster Observability Operator.
- **Multimodal input support for Distributed Inference with llm-d** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Platform Operators serving multimodal models benefit from prefix cache-aware routing that accounts for image, audio, and video content.
- **End-to-end distributed tracing for Distributed Inference with llm-d** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Distributed Inference with llm-d supports end-to-end distributed tracing across the full inference Red Hat OpenShift AI Self-Managed 3.5 Release notes Distributed Inference with llm-d supports end-to-end distributed tracing across the full inference request path.
- **User-request header routing for external OGX providers** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can pass specific user-request headers to external OGX (formerly Llama Stack) providers.
- **Existing Kubernetes Secrets as workbench environment variables** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can reference pre-existing Kubernetes Secrets as environment variables when creating or editing a workbench.
- **GPU topology and utilization dashboard** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: In OpenShift AI, a new Infrastructure page provides platform administrators with an integrated view of accelerator cluster health.
- **Automated generation of tool-calling evaluation data for custom MCP servers** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can automatically generate tool-calling evaluation benchmark data from custom Model Context Protocol (MCP) servers.
- **KubeRay operator upgraded to version 1.6.x** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Your existing and RayJob workloads remain fully supported and will continue to function normally after the upgrade without requiring changes.
- **Support for Hosted Control Planes on OpenShift Virtualization** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can deploy OpenShift AI on Hosted Control Planes (HCP) running on OpenShift Virtualization.
- **Automated prompt optimization for agentic systems** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can automate the optimization of prompts for your agentic systems by using Training Hub.
- **Per-tenant EvalHub deployment** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Namespace administrators can deploy a dedicated EvalHub instance in their own namespace without cluster administrator or OpenShift AI administrator involvement.
- **Integration of Training Hub in Ray for distributed fine-tuning** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can use Training Hub fine-tuning algorithms on Ray clusters.
- **Automatic Prometheus monitoring integration for EvalHub on OpenShift** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: ServiceMonitor The TrustyAI Service Operator automatically creates a resource when EvalHub is deployed with metrics enabled.
- **NeMo Guardrails support on IBM Z** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: NeMo Guardrails is supported on IBM Z (s390x).
- **3.5 EA2 new features Responses API on OGX** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: The Responses API is generally available on OGX.
- **Safety and Security Insights tab in the Red Hat AI Model Catalog** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: The Red Hat AI Model Catalog includes a new Safety and Security Insights tab that displays AI security evaluation results for each model.
- **3.5 EA1 new features Support for OGX and KubeRay on IBM Power** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Red Hat OpenShift AI 3.5 EA1 introduces official support for both OGX (which replaces Llama Stack) and KubeRay on the IBM Power architecture.
- **3.5 GA enhancements Canary rollout support for KServe RawDeployment mode** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: In OpenShift AI, you can perform canary rollouts for KServe InferenceService deployments in RawDeployment mode.
- **Observability dashboards installed by default for Distributed Inference with llm-d** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Distributed Inference with llm-d includes observability dashboards installed by default in the ConfigMap OpenShift web console.
- **Non-cluster administrator access and embeddable Perses-based dashboards** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: In OpenShift AI, non-cluster administrators, such as data scientists, can access Perses-based metrics dashboards scoped to their authorized namespaces.
- **View the vLLM version for distributed inference deployments** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: When using distributed inference with Distributed Inference with llm-d, platform administrators can Red Hat OpenShift AI Self-Managed 3.5 Release notes view the version of vLLM that is running directly from the OpenShift AI dashboard.
- **Option to disable TLS within Distributed Inference with llm-d deployments** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Platform Operators can disable built-in TLS on LLMInferenceService workload pods by setting spec.tls.enabled:
- **Enhancements to Distributed Inference with llm-d EndPoint Picker scheduler configuration** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: The OpenShift AI 3.4 default scheduler configuration used two scorer plugins, queue-scorer prefix-cache-scorer kv- (weight:
- **Service-level SLI metrics for Distributed Inference with llm-d** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can monitor end-to-end inference performance from the user’s perspective by using service- level Prometheus histogram metrics exposed by the Endpoint Picker in Distributed Inference with llm-d deployments.
- **Targeted vLLM access-log filtering for LLMInferenceService** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: The default LLMInferenceServiceConfig templates switch from the blanket --disable-uvicorn- access-log to vLLM 0.16’s --disable-access-log-for-endpoints /health,/metrics,/ping with a runtime fallback to the old flag on vLLM below 0.16.
- **Feature store and workbench bidirectional visibility** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can view connections between feature stores and workbenches directly in the OpenShift AI web console.
- **Hiding default workbench images** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Administrators can hide out-of-the-box workbench images from the image selection drop-down list.
- **Telemetry collection for OGX API adoption metrics** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Telemetry data collection is introduced for OGX (formerly Llama Stack) API usage.
- **PVC as a storage source for EvalHub evaluation test data** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can use a PersistentVolumeClaim (PVC) as a storage source for custom test data in EvalHub evaluation jobs.
- **MLflow-compatible agent connectors for Synthetic Data Generation (SDG) Hub** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: The Synthetic Data Generation (SDG) Hub features MLflow-compatible agent connectors.
- **CPU-only support for AutoRAG deployments** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: AutoRAG optimization supports CPU-only infrastructure, enabling you to evaluate Retrieval- Augmented Generation (RAG) pipelines without requiring GPU resources.
- **Training Hub RLVR and GRPO dependencies in universal workbench images** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: The universal workbench image includes all dependencies required for Reinforcement Learning from Verifiable Rewards (RLVR) and Group Relative Policy Optimization (GRPO) training workflows.
- **Trace archival support for MLflow at scale** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can use age-based trace archival for MLflow to manage large volumes of trace data.
- **Guided tours for the OpenShift AI dashboard** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: A new guided tour system is available in the dashboard.
- **Ability to self-manage ClusterQueues and LocalQueues** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: ClusterQueue LocalQueue In OpenShift AI, you can self-manage and resources for your data science projects.
- **OpenAI-compatible body-based model routing for Models-as-a-Service** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can send inference requests to the standard OpenAI /v1/chat/completions endpoint with the model name in the request body, and MaaS applies subscription, rate-limiting, and authorization policies automatically.
- **Unified MaaS governance page for subscriptions and authorization policies** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: This enhancement combines the Subscriptions and Authorization policies pages in Settings into a single MaaS governance page, accessible from Settings → MaaS governance.
- **Code Interpreter flow for synthetic Python code generation** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: In OpenShift AI, SDG Hub includes a Code Interpreter flow for synthetic Python code generation.
- **Distributed Inference with llm-d tokenizer runs as a dedicated external service** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: The Distributed Inference with llm-d tokenizer runs as a dedicated external service, which requires it to run on an amd64 node.
- **Inference scheduler routing logic and scorer weight configuration** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Platform operators can configure the routing logic used by the inference scheduler and tune scorer weights to optimize for specific workloads.
- **MCP gateway Operator as an external dependency for MCP management workflows** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: The MCP gateway Operator is an optional external prerequisite for OpenShift AI MCP management workflows, including agentic AI workflows, that route agent tool calls through a governed protocol gateway layer.
- **Unified dashboard experience for generative AI model deployment workflows** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Generative AI model deployment workflows are in a unified dashboard experience, replacing separate entry points for different model serving runtimes with a single guided wizard.
- **Default vector store for GenAI Studio** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: GenAI Studio includes a default PostgreSQL vector store with the pgvector extension enabled for playground Retrieval-Augmented Generation (RAG) workflows.
- **Enhanced trained model insights for AutoML** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: AutoML tabular and time-series pipelines generate and persist detailed evaluation artifacts to S3- compatible object storage.
- **Model Context Protocol (MCP) Lifecycle Operator** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: The Model Context Protocol (MCP) Lifecycle Operator is available as a Technology Preview feature.
- **MCP Catalog support tier labeling** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: The Model Context Protocol (MCP) Catalog in Red Hat OpenShift AI displays explicit support tier labels for server entries, allowing you to easily identify official support commitments before deployment.
- **Ray 2.55.1 runtime images for distributed workloads** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: New Ray 2.55.1 runtime images are included in Distributed Workloads.
- **DP-aware load balancing for Distributed Inference with llm-d WideEP deployments** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Known limitations in this Technology Preview feature include:
- **API surface full-stack passthrough for tool calling in Distributed Inference with llm-d** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Tool calling parameters pass through the full Distributed Inference with llm-d serving stack without modification.
- **Multimodal support in the Gen AI Studio playground** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: The Gen AI Studio playground supports multimodal interactions, allowing you to experiment with models that process text, images, and audio.
- **Inference-aware scheduling for Distributed Inference with llm-d on Amazon EKS** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Platform Operators can deploy Distributed Inference with llm-d on Amazon Elastic Kubernetes Service (EKS) with inference-aware scheduling as a Technology Preview.
- **EKS platform support for Distributed Inference with llm-d** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Platform Operators can deploy and operate Distributed Inference with llm-d on Amazon EKS as a Technology Preview, using the same installation paths, observability, and tooling as on other validated Kubernetes platforms.
- **MaaS multi-tenancy with per-tenant gateway and identity isolation** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Platform administrators can provision isolated tenants for Models-as-a-Service by using a single custom resource.
- **AutoGluon serving runtime** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Red Hat OpenShift AI includes AutoGluon as a pre-configured serving runtime for deploying AutoML models as a Technology Preview.
- **Multi-provider API passthrough for Models-as-a-Service external models** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: You can route inference requests through the Models-as-a-Service (MaaS) gateway using native /v1/messages provider API formats—such as the Anthropic Messages API at or the OpenAI Responses API at /v1/responses —without format translation.
- **Autoscaling support for Ray distributed workloads** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: You can enable cluster autoscaling for your Ray distributed workloads.
- **Chat metrics and observability tracing in Gen AI Studio** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: This Technology Preview feature introduces an inline metrics panel that displays key performance indicators for each chat instance, including time to first token (TTFT), tokens per second, total token usage, payload sizes, and estimated costs.
- **Global prompt registry namespaces in Gen AI Studio playground** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: You can browse, load, and iterate on organization-curated prompts from global registry namespaces in the Gen AI Studio playground.
- **Interactive Spark job management in workbenches** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: You can interactively manage and execute PySpark workloads directly from your workbenches using the Kube-native Spark Operator (KSO).
- **Kueue support for the Kubeflow Spark Operator** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: SparkApplication workloads managed by the Kubeflow Spark Operator (KSO) can be admitted and scheduled through Kueue.
- **Monitoring Spark jobs with the Spark Application UI and History Server** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Red Hat OpenShift AI Self-Managed 3.5 Release notes You can monitor Spark jobs submitted with the Kubeflow Spark Operator by using the Spark Application UI through OpenShift routes or port forwarding.
- **OpenCode coding agent deployment and operation** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: You can deploy and operate OpenCode, an open-source, terminal-based coding agent.
- **AutoML experimentation visibility and transparency** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: You can view detailed AutoML experimentation data directly in the dashboard.
- **AutoRAG visual pipeline representation for experimentation** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: The AutoRAG user interface includes a visual pipeline representation of the experimentation process.
- **OpenTelemetry metrics export for EvalHub** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: OTLP metrics export is available as a Technology Preview feature.
- **Verify connection credentials before saving** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: This feature is available as a Technology Preview.
- **View external model endpoints in the dashboard** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: You can view registered external model endpoints and their associated provider details from the → OpenShift AI dashboard.
- **AWS Security Token Service (STS) authentication for AWS Bedrock** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: You can use AWS Security Token Service (STS) authentication with the AWS Bedrock inference provider.
- **Multi-lingual support for AutoRAG** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: AutoRAG includes multi-lingual capabilities, allowing you to discover optimal Retrieval-Augmented Generation (RAG) patterns for non-English and mixed-language document corpora.
- **EvalHub job execution log access via HTTP API and CLI** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: This feature is available as a Technology Preview.
- **Cross-namespace shared workspace access for curated resources** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: You can access curated resources, starting with prompts in GenAI Studio, from a designated global Red Hat OpenShift AI Self-Managed 3.5 Release notes workspace.
- **Structural contextualization support for AutoRAG** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: In OpenShift AI, AutoRAG supports structural contextualization (LLM contextual enrichment) during document chunking.
- **Loki-based showback and user-scoped dashboards for Models-as-a-Service** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Models-as-a-Service (MaaS) includes a Loki-based structured log pipeline for showback data in addition to the existing metrics-based dashboard.
- **Side-by-side evaluation run comparison in EvalHub** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: This Technology Preview feature enables you to select runs from the evaluations list, initiate a comparison, and view metrics and parameters for all selected runs in an embedded MLflow comparison view.
- **OGX Server custom resource definition (CRD) runtime updates** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: OpenShift AI 3.5EA2 introduces enhancements to the OGX Server CRD by natively exposing config.yaml runtime configuration fields.
- **Model Cache for faster inference startup** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: You can pre-download and cache large language model (LLM) artifacts on node-local Non-Volatile Memory Express (NVMe) storage to reduce InferenceService cold-start latency.
- **OGX servers require installation of the PostgreSQL Operator** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: In OpenShift AI 3.2, the PostgreSQL Operator is required to deploy a OGX server.
- **Secure agent sandboxing and policy enforcement using OpenShell** [self-managed 3.5] DP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: A Developer Preview of OpenShell is available for secure agent onboarding on OpenShift.
- **Agent Catalog in AI Hub for agent starter kit discovery** [self-managed 3.5] DP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: The Agent Catalog in AI Hub provides a centralized interface for discovering and exploring agent starter kits as a Developer Preview.
- **Configuration persistence for Gen AI Studio** [self-managed 3.5] DP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: You can save your Gen AI Studio Playground configuration as a named, reusable agent scoped to your project namespace.
- **Hierarchical KV Cache Tiering** [self-managed 3.5] DP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: Hierarchical KV cache tiering for GPU inference workloads allows platform operators to serve more concurrent users on the same GPU footprint, directly improving the cost-effectiveness of inference deployments.
- **LoRA-aware request routing for Distributed Inference with llm-d** [self-managed 3.5] DP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: Platform operators can route requests to pods where the target LoRA adapter is already loaded, avoiding cold-load latency from on-demand adapter swaps.
- **Latency-aware routing for Distributed Inference with llm-d** [self-managed 3.5] DP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: Platform operators can declare per-request latency targets for Time To First Token (TTFT) and Time Per Output Token (TPOT).
- **External metering for per-user token usage and cost tracking** [self-managed 3.5] DP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: In OpenShift AI, an external metering IPP plugin and standalone metering service are available as a Developer Preview feature.
- **MCP Catalog administrative interface for managing entries** [self-managed 3.5] DP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: In OpenShift AI, administrators can manage Model Context Protocol (MCP) Catalog source configurations directly from the Settings page of the dashboard.
- **MiDojo adversarial testing execution engine** [self-managed 3.5] DP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: In OpenShift AI, you can use MiDojo, a man-in-the-middle adversarial testing execution engine for AI agents, available as a Developer Preview feature.
- **External metering integration for Models-as-a-Service** [self-managed 3.5] DP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: You can connect Models-as-a-Service (MaaS) inference traffic to an external metering or billing system by using Backend-Based Routing (BBR) plugins.
- **View running agent deployments in the dashboard** [self-managed 3.5] DP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: In OpenShift AI, you can view a list of running agent deployments directly in the dashboard.
- **Text-mode training for multimodal models in Training Hub** [self-managed 3.5] DP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: Training Hub supports text-only training ("text mode") for multimodal model architectures.
- **The remote::anthropic inference provider for OGX** [self-managed 3.5] DP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: The remote::anthropic inference provider is available on OGX.

### ⬆️ 승격 (2)
- **External OIDC authentication for Models-as-a-Service** [self-managed 3.5] GA (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can configure Models-as-a-Service to authenticate users with an external OpenID Connect (OIDC) identity provider.
- **EvalHub client SDK and CLI** [self-managed 3.5] GA (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: OpenShift AI includes the EvalHub client SDK and command-line interface (CLI).

### 🗑️ 문서에서 제거 (60)
- **Responses API on OGX** [self-managed 3.5] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: The Responses API is generally available on OGX.
- **Support for OGX and KubeRay on IBM Power** [self-managed 3.5] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Red Hat OpenShift AI 3.4 GA introduces official support for both OGX and KubeRay on the IBM Power architecture.
- **Support for direct authentication with an OIDC identity provider** [self-managed 3.5] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Direct authentication with an OpenID Connect (OIDC) identity provider is now available as a GA feature.
- **Migration guide available for transitioning from vLLM-based InferenceService to LLMInferenceService** [self-managed 3.5] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Platform Operators deploying Distributed Inference with llm-d on OpenShift AI can follow a step-by- step guide covering LLMInferenceServiceConfig, YAML examples, and migration from vLLM-based InferenceService deployments.
- **Prometheus metrics for Distributed Inference with llm-d** [self-managed 3.5] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can now monitor llm-d distributed inference deployments using documented Prometheus metrics and PromQL query examples.
- **MLFlow SDK pre-installed in workbench and runtime images** [self-managed 3.5] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: The MLFlow SDK is now pre-installed and included in the datascience, tensorflow (CUDA & ROCm), pytorch (CUDA & ROCm), and codeserver workbench and runtime images.
- **MLflow Operator is now a managed component in the DataScienceCluster CR** [self-managed 3.5] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Starting with Red Hat OpenShift AI 3.4, the MLflow Operator is a managed component in the DataScienceCluster mlflowoperator custom resource (CR).
- **NeMo Guardrails to enable AI safety** [self-managed 3.5] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: NeMo Guardrails, introduced in Red Hat OpenShift AI 3.3 as a Technology Preview, is fully supported with this release.
- **Models-as-a-Service now Generally Available** [self-managed 3.5] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Models-as-a-Service (MaaS) is now Generally Available in Red Hat OpenShift AI 3.4.
- **The Models-as-a-Service subscription model redesign** [self-managed 3.5] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: The Models-as-a-Service (MaaS) subscription model has been redesigned to replace the tier-based model introduced in version 3.3.
- **Self-service API key management for Models-as-a-Service** [self-managed 3.5] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can now create and manage your own API keys for programmatic access to large language models through Models-as-a-Service.
- **OCI-compliant storage layer for model registry** [self-managed 3.5] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can now use the OpenShift AI dashboard to register a model from an S3-compatible source or URI, transform it into an OCI ModelCar image, and store it in an OCI registry.
- **MLServer ServingRuntime for KServe is now generally available** [self-managed 3.5] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: The MLServer ServingRuntime for KServe is now generally available in Red Hat OpenShift AI.
- **MLflow operator promoted to a managed component** [self-managed 3.5] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Starting with Red Hat OpenShift AI 3.4, the MLflow Operator is a managed component in the DataScienceCluster custom resource (CR).
- **Automatic MLflow SDK configuration for workbenches** [self-managed 3.5] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: When the MLflow Operator is enabled, you can annotate workbench notebook resources with opendatahub.io/mlflow-instance to automatically configure the MLflow SDK.
- **Granular RBAC for workbenches** [self-managed 3.5] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Project administrators can now define custom, fine-grained roles for workbench resources by using oc the CLI or by importing YAML in the OpenShift web console.
- **Multi-architecture support for the model catalog** [self-managed 3.5] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: The model catalog includes support for IBM Power (ppc64le) architecture.
- **Just-In-Time Checkpointing and S3 Storage for Kubeflow Trainer** [self-managed 3.5] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Kubeflow Trainer now provides Just-In-Time (JIT) and periodic checkpointing for distributed training jobs on OpenShift AI.
- **Workbench and runtime images default to Red Hat Python index** [self-managed 3.5] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Workbench and runtime images default to the Red Hat Python index.
- **Garak evaluation provider available in OGX distribution** [self-managed 3.5] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: The Garak evaluation provider is available in the OGX distribution.
- **PostgreSQL database support for Model Registry** [self-managed 3.5] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can configure a PostgreSQL database as the backend for Model Registry from the OpenShift AI Red Hat OpenShift AI Self-Managed 3.5 Release notes You can configure a PostgreSQL database as the backend for Model Registry from the OpenShift AI dashboard.
- **Default database solution for Model Registry** [self-managed 3.5] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Model Registry includes a default database solution for testing.
- **vLLM uvicorn access logs are disabled by default in Distributed Inference with llm-d** [self-managed 3.5] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: vLLM uvicorn access logs are disabled by default in LLMInferenceServiceConfig, including logs generated by router-scheduler /metrics endpoint polling.
- **Simplified configuration for Distributed Inference with llm-d scheduler settings** [self-managed 3.5] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Configure Distributed Inference with llm-d scheduler settings using the endpointPickerConfig field in the LLMInferenceService specification.
- **Configure vLLM runtime arguments using Kubernetes container args field** [self-managed 3.5] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can configure vLLM runtime arguments using the standard Kubernetes container args field in LLMInferenceService resources.
- **Hybrid search support for Qdrant remote vector database provider** [self-managed 3.5] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Vector Store Search supports hybrid and keyword search for the Qdrant Vector IO provider.
- **Priority-based flow control for mixed llm-d workloads** [self-managed 3.5] TP (was TP) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Platform Operators can assign priority tiers to workload classes and configure queuing policies so that latency-sensitive requests are served ahead of throughput-oriented batch traffic.
- **Model-as-a-Service (MaaS) integration** [self-managed 3.5] TP (was TP) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: This feature is available as a Technology Preview.
- **MLServer ServingRuntime for KServe** [self-managed 3.5] TP (was TP) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: The MLServer serving runtime for KServe is now available as a technology preview feature in Red Hat OpenShift AI.
- **OGX servers now require installation of the PostgreSQL Operator** [self-managed 3.5] TP (was TP) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: In OpenShift AI 3.2, the PostgreSQL Operator is now required to deploy a OGX server.
- **NVIDIA NeMo Guardrails** [self-managed 3.5] TP (was TP) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: You can use NVIDIA NeMo Guardrails as a Technology Preview feature to add guardrails and safety controls to your deployed models in Red Hat OpenShift AI.
- **Kubeflow Trainer v2** [self-managed 3.5] TP (was TP) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Kubeflow Trainer v2 is now available as a Technology Preview feature in OpenShift AI 3.2.
- **RStudio Server workbench image** [self-managed 3.5] TP (was TP) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: With the RStudio Server workbench image, you can access the RStudio IDE, an integrated development environment for R.
- **CUDA - RStudio Server workbench image** [self-managed 3.5] TP (was TP) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: With the CUDA - RStudio Server workbench image, you can access the RStudio IDE and NVIDIA CUDA Toolkit.
- **The inference provider for OGX** [self-managed 3.5] DP (was DP) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: The remote::anthropic inference provider is available on OGX.
- **End-to-end distributed tracing for llm-d** [self-managed 3.5] DP (was DP) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: Platform operators can trace distributed inference requests end-to-end across service boundaries by using OpenTelemetry-compatible distributed tracing.
- **Distributed Tracing for Distributed Inference with llm-d** [self-managed 3.5] DP (was DP) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: Platform Operators can trace distributed inference with llm-d requests end-to-end across service boundaries using OpenTelemetry-compatible distributed tracing.
- **Batch inference compatible with OpenAI batch APIs in Distributed Inference with llm-d** [self-managed 3.5] DP (was DP) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: Platform Operators can submit large request volumes asynchronously through the OpenAI- /v1/batches compatible API and retrieve results without maintaining an active connection.
- **Tool calling metadata on model cards in the model catalog** [self-managed 3.5] DP (was DP) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: Red Hat OpenShift AI now displays tool callin, also known as function calling, configuration metadata directly in the model catalog.
- **Ray-based multi-node vLLM template** [self-managed 3.5] Deprecated (was Deprecated) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: In Red Hat OpenShift AI 3.3, the Ray-based multi-node vLLM template remains available as a Technology Preview.
- **Training images and ClusterTrainingRuntimes for Kubeflow Training Operator v1** [self-managed 3.5] Deprecated (was Deprecated) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: The Kubeflow Training Operator (v1) is deprecated starting OpenShift AI 2.25 and is scheduled to be removed.
- **Deprecated SQLite as a production metadata store for OGX** [self-managed 3.5] Deprecated (was Deprecated) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: Starting with OpenShift AI 3.2, SQLite is deprecated for use as a metadata store in production OGX deployments.
- **Deprecated annotation format for Connection Secrets::** [self-managed 3.5] Deprecated (was Deprecated) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: Starting with OpenShift AI 3.0, the opendatahub.io/connection-type-ref annotation format for creating Connection Secrets is deprecated.
- **Deprecated Kubeflow Training operator v1** [self-managed 3.5] Deprecated (was Deprecated) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: The Kubeflow Training Operator (v1) is deprecated starting OpenShift AI 2.25 and is planned to be removed in a future release.
- **Deprecated TrustyAI service CRD v1alpha1** [self-managed 3.5] Deprecated (was Deprecated) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: Starting with OpenShift AI 2.25, the v1apha1 version is deprecated and planned for removal in an upcoming release.
- **Deprecated KServe Serverless deployment mode** [self-managed 3.5] Deprecated (was Deprecated) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: Starting with OpenShift AI 2.25, The KServe Serverless deployment mode is deprecated.
- **Deprecated model registry API v1alpha1** [self-managed 3.5] Deprecated (was Deprecated) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: v1alpha1 Starting with OpenShift AI 2.24, the model registry API version is deprecated and will be removed in a future release of OpenShift AI.
- **Multi-model serving platform (ModelMesh)** [self-managed 3.5] Deprecated (was Deprecated) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: Starting with OpenShift AI version 2.19, the multi-model serving platform based on ModelMesh is deprecated.
- **Accelerator Profiles and legacy Container Size selector deprecated** [self-managed 3.5] Deprecated (was Deprecated) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: Starting with OpenShift AI 3.0, Accelerator Profiles and the Container Size selector for workbenches are deprecated.
- **Deprecated OpenVINO Model Server (OVMS) plugin** [self-managed 3.5] Deprecated (was Deprecated) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: The CUDA plugin for the OpenVINO Model Server (OVMS) is now deprecated and will no longer be available in future releases of OpenShift AI.
- **OpenShift AI dashboard user management moved from to** [self-managed 3.5] Deprecated (was Deprecated) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)
- **Deprecated cluster configuration parameters** [self-managed 3.5] Deprecated (was Deprecated) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: When using the CodeFlare SDK to run distributed workloads in Red Hat OpenShift AI, the following parameters in the Ray cluster configuration are now deprecated and should be replaced with the new parameters as indicated.
- **CodeFlare Operator removed** [self-managed 3.5] Removed (was Removed) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: Starting with OpenShift AI 3.0, the CodeFlare Operator has been removed.
- **Microsoft SQL Server command-line tool removal** [self-managed 3.5] Removed (was Removed) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: Starting with OpenShift AI 2.24, the Microsoft SQL Server command-line tools (sqlcmd, bcp) have been removed from workbenches.
- **Model registry ML Metadata (MLMD) server removal** [self-managed 3.5] Removed (was Removed) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: Starting with OpenShift AI 2.23, the ML Metadata (MLMD) server has been removed from the model registry component.
- **Embedded subscription channel not used in some versions** [self-managed 3.5] Removed (was Removed) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: For OpenShift AI 2.8 to 2.20 and 2.22 to 3.5, the embedded subscription channel is not used.
- **Anaconda removal** [self-managed 3.5] Removed (was Removed) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: Starting with OpenShift AI version 2.18, Anaconda is no longer included in OpenShift AI, and Anaconda resources are no longer supported or managed by OpenShift AI.
- **Pipeline logs for Python scripts running in Elyra pipelines are no longer stored in S3** [self-managed 3.5] Removed (was Removed) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: Logs are no longer stored in S3-compatible storage for Python scripts which are running in Elyra pipelines.
- **Beta subscription channel no longer used** [self-managed 3.5] Removed (was Removed) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: Starting with OpenShift AI 2.5, the beta subscription channel is no longer used.
- **HabanaAI workbench image removal** [self-managed 3.5] Removed (was Removed) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: Support for the HabanaAI 1.10 workbench image has been removed.


## 2026-07-26

### ⚠️ Deprecated (1)
- **Deprecation of Llama Stack and transition to OGX** [self-managed 2.25] Deprecated — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/2.25/html/release_notes/support-removals_relnotes)  
    근거: Previously, Llama Stack was available as a Technology Preview in OpenShift AI 2.25.


## 2026-07-19

### 🆕 신규 (23)
- **Support for customizing OAuth proxy sidecar resource allocation via the DataScienceCluster API** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Administrators can configure OAuth proxy sidecar resource requests and limits directly in the DataScienceCluster CR under spec.components.kserve.oauthProxy.resources , without changing any component state from Managed to Unmanaged .
- **Cold-start load time and vRAM metrics in the model catalog** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: The model catalog displays operational metrics for validated models, including cold-start load time, minimum vRAM requirements, and the runtime command used for benchmarking.
- **Self-service Subscriptions tab for Models-as-a-Service users** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: With this update, you can view your Models-as-a-Service subscription assignments, browse associated models, and check token rate limits from the Subscriptions tab on the API keys page in
- **MLflow, AutoML, AutoRAG, and OGX enhancements on IBM Power** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Red Hat OpenShift AI extends support for MLflow, AutoML, AutoRAG, the GenAI playground, milvus-lite , and the OGX ecosystem to the IBM Power architecture.
- **Configure vLLM runtime arguments using Kubernetes container args field** [self-managed 3.5] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can configure vLLM runtime arguments using the standard Kubernetes container args field in LLMInferenceService resources.
- **NeMo Guardrails integration with MCP Gateway for agent tool-call enforcement** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: You can integrate NeMo Guardrails with the MCP Gateway to enforce guardrails on agent tool calls at the gateway layer.
- **Validated tool-calling configuration for models in the model catalog** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: The model catalog displays validated vLLM deployment arguments for models with confirmed tool- calling support.
- **Multi-tenancy support in OGX** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: OGX supports multi-tenancy, allowing teams to share infrastructure while isolating data and access.
- **GPU-accelerated Docling SDK container image for batch document processing** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Red Hat OpenShift AI provides the docling-sdk-cuda-ubi9 container image for GPU-accelerated document conversion using the Docling SDK 2.88.0 with NVIDIA CUDA 13.0 support.
- **Docling Serve API container image for on-demand document conversion** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Red Hat OpenShift AI provides the docling-serve-cuda-ubi9 container image, which offers a REST API for on-demand document conversion, chunking, and GPU-accelerated parsing.
- **Batch inference with the OpenAI-compatible Batches API in llm-d** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Distributed Inference with llm-d supports batch inference through the OpenAI-compatible /v1/batches API.
- **Prompt management with template variables in Gen AI Studio** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: You can save, version, and reuse system instructions as named prompts in Gen AI Studio.
- **Kueue support in EvalHub for evaluation job scheduling** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: You can route EvalHub evaluation jobs through Red Hat build of Kueue LocalQueues by specifying a queue name when creating an evaluation job.
- **EvalHub MCP server for AI coding agents** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: The EvalHub Model Context Protocol (MCP) server is available as a Technology Preview.
- **Thresholds support in evaluation runs in the OpenShift AI dashboard** [self-managed 3.5] TP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: EvalHub introduces threshold configuration in evaluation runs as a Technology Preview.
- **The inference provider for OGX** [self-managed 3.5] DP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: The remote::anthropic inference provider is available on OGX.
- **File Processors API on OGX** [self-managed 3.5] DP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: The File Processors API is available on OGX.
- **The remote::gemini inference provider for OGX** [self-managed 3.5] DP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: The remote::gemini inference provider is available on OGX.
- **OpenClaw agent starter kit** [self-managed 3.5] DP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: You can deploy and manage OpenClaw, an open-source general-purpose agent, on Red Hat CHAPTER 4.
- **Claude Code agent starter kit** [self-managed 3.5] DP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: You can deploy and configure the Anthropic Claude Code agent on Red Hat OpenShift AI by using a new agentic starter kit.
- **Kale JupyterLab extension for notebook-to-pipeline conversion** [self-managed 3.5] DP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: You can use the Kale (Kubeflow Automated pipeLines Engine) JupyterLab extension to convert annotated Jupyter notebooks into AI Pipelines without writing Kubeflow Pipelines SDK code.
- **End-to-end distributed tracing for llm-d** [self-managed 3.5] DP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: Platform operators can trace distributed inference requests end-to-end across service boundaries by using OpenTelemetry-compatible distributed tracing.
- **CSV export for model catalog data** [self-managed 3.5] DP ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: You can export model catalog metadata to CSV format by using a standalone Python CLI script.

### ⬆️ 승격 (1)
- **Responses API on OGX** [self-managed 3.5] GA (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: The Responses API is generally available on OGX.

### 🗑️ 문서에서 제거 (2)
- **Configure vLLM runtime arguments using Kubernetes container field** [self-managed 3.5] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can configure vLLM runtime arguments using the standard Kubernetes container args field in LLMInferenceService resources.
- **OGX Responses API parity with OpenAI** [self-managed 3.5] TP (was TP) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: The OGX Responses API in OpenShift AI 3.4 introduces systematic alignment with OpenAI’s Responses API.


## 2026-06-21

### 🆕 신규 (32)
- **Support for OGX and KubeRay on IBM Power** [self-managed 3.5] GA — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Red Hat OpenShift AI 3.4 GA introduces official support for both OGX and KubeRay on the IBM Power architecture.
- **Task Shortcuts section added to the dashboard homepage** [self-managed 3.5] GA — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: The Red Hat OpenShift AI dashboard homepage now includes a Task Shortcuts section.
- **ROCm TensorFlow workbench image defaults to Red Hat Python index** [self-managed 3.5] GA — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Workbench and runtime images default to the Red Hat Python index.
- **Garak evaluation provider available in OGX distribution** [self-managed 3.5] GA — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: The Garak evaluation provider is available in the OGX distribution.
- **OGX Responses API parity with OpenAI** [self-managed 3.5] TP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: The OGX Responses API in OpenShift AI 3.4 introduces systematic alignment with OpenAI’s Responses API.
- **Responses API on OGX** [self-managed 3.5] TP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: TECHNOLOGY PREVIEW FEATURES The Responses API on OGX is now available on OpenShift AI as a Technology Preview, previously available as a Developer Preview.
- **TLS and proxy configuration for all OGX remote inference providers** [self-managed 3.5] TP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Red Hat OpenShift AI 3.4 EA2 introduces a standardized network configuration block for all OGX remote inference providers.
- **OGX versions in Red Hat OpenShift AI 3.4 EA2** [self-managed 3.5] TP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Red Hat OpenShift AI 3.4 EA2 includes Open Data Hub OGX version 0.6.0.1+rhai0, which is based on upstream OGX version 0.6.0.
- **NeMo Guardrails in Gen AI Studio** [self-managed 3.5] TP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Red Hat OpenShift AI 3.5 EA1 updates the guardrails experience in the Gen AI Studio playground.
- **Renaming of Llama Stack to OGX** [self-managed 3.5] TP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Starting in OpenShift AI 3.5 EA1, Llama Stack and its associated variables and configurations are renamed to OGX.
- **Conversations API on OGX** [self-managed 3.5] TP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: The OpenAI Conversations API is now available on OGX as a Technology Preview in OpenShift AI 3.5 EA1.
- **OGX versions in OpenShift AI 3.4 EA1** [self-managed 3.5] TP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: OpenShift AI 3.4 EA1 includes Open Data Hub OGX version 0.5.0+rhai0, which is based on upstream OGX version 0.5.0.
- **OGX Connectors** [self-managed 3.5] TP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: OGX Connectors provide a high-level abstraction for AI registries such as MCP.
- **OpenAI-compatible annotations for search and responses in OGX** [self-managed 3.5] TP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Starting with OpenShift AI 3.3, OGX provides OpenAI-compatible grounding and citation annotations for search-backed responses as a Technology Preview feature.
- **The OGX Operator available on multi-architecture clusters** [self-managed 3.5] TP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: The OGX Operator is deployable on multi-architecture clusters in OpenShift AI version 3.3 and is available by default.
- **OGX versions in OpenShift AI 3.3** [self-managed 3.5] TP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: OpenShift AI 3.3.0 includes Open Data Hub OGX version 0.4.2.1+rhai0, which is based on upstream OGX version 0.4.2.
- **The OGX Operator with ConfigMap driven image updates** [self-managed 3.5] TP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: The OGX Operator in OpenShift AI 3.3 now offers ConfigMap driven image updates for OGXServer resources.
- **pgvector support as a remote vector store provider in OGX** [self-managed 3.5] TP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Starting with OpenShift AI 3.2, you can use PostgreSQL with the pgvector extension as a remote vector store provider for the OGX vector_store endpoint as a Technology Preview feature.
- **OGX versions in OpenShift AI 3.2** [self-managed 3.5] TP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: OpenShift AI 3.2.0 uses the Open Data Hub OGX version 0.3.5+rhai0 in the OGX Distribution, which is based on the upstream OGX version 0.3.5.
- **OGX servers now require installation of the PostgreSQL Operator** [self-managed 3.5] TP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: In OpenShift AI 3.2, the PostgreSQL Operator is now required to deploy a OGX server.
- **Enabling high availability on OGX** [self-managed 3.5] TP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: OGX servers can be configured to remain operational in the event of a single point of failure as a Technology Preview feature.
- **Custom embeddings on OGX** [self-managed 3.5] TP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: OpenShift AI 3.2 allows you to customize your embedding models as a Technology Preview feature.
- **TrustyAI–OGX integration for safety, guardrails, and evaluation** [self-managed 3.5] TP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: You can now use the Guardrails Orchestrator from TrustyAI with OGX as a Technology Preview feature.
- **Support for air-gapped OGX deployments** [self-managed 3.5] TP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: You can now install and operate OGX and RAG/Agentic components in fully disconnected (air- gapped) OpenShift AI environments.
- **Build Generative AI Apps with OGX on OpenShift AI** [self-managed 3.5] TP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: With this release, the OGX Technology Preview feature enables Retrieval-Augmented Generation (RAG) and agentic workflows for building next-generation generative AI applications.
- **Support for OGX Distribution version 0.3.0** [self-managed 3.5] TP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: The OGX Distribution now includes version 0.3.0 as a Technology Preview feature.
- **OGX support and optimization for single node OpenShift (SNO)** [self-managed 3.5] TP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: OGX core can now deploy and run efficiently on single node OpenShift (SNO).
- **FIPS support for OGX and RAG deployments** [self-managed 3.5] TP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: You can now deploy OGX and RAG or agentic solutions in regulated environments that require FIPS compliance.
- **RAGAS evaluation provider for OGX (inline and remote)** [self-managed 3.5] TP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: You can now use the Retrieval-Augmented Generation Assessment (RAGAS) evaluation provider to measure the quality and reliability of RAG systems in OpenShift AI.
- **Run evaluations for TrustyAI-OGX using LM-Eval** [self-managed 3.5] DP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: You can now run evaluations using LM-Eval on OGX with TrustyAI as a Developer Preview feature, using the built-in LM-Eval component and advanced content moderation tools.
- **Compatibility of OGX remote providers and SDK with MCP HTTP streaming protocol** [self-managed 3.5] DP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: This feature is available as a Developer Preview.
- **Human-in-the-Loop (HIL) functionality in the OGX agent** [self-managed 3.5] DP — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: Human-in-the-Loop (HIL) functionality has been added to the OGX agent to allow users to approve unread tool calls before execution.

### ⬇️ 강등 (2)
- **Kubeflow Trainer v2** [self-managed 3.5] TP (was GA) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Kubeflow Trainer v2 is now available as a Technology Preview feature in OpenShift AI 3.2.
- **Enable targeted deployment of workbenches to specific worker nodes in Red Hat OpenShift AI Dashboard using node selectors** [self-managed 3.5] TP (was GA) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: The hardware profiles feature enables users to target specific worker nodes for workbenches or model-serving workloads.

### ⚠️ Deprecated (13)
- **Ray-based multi-node vLLM template** [self-managed 3.5] Deprecated (was Deprecated) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: In Red Hat OpenShift AI 3.3, the Ray-based multi-node vLLM template remains available as a Technology Preview.
- **Training images and ClusterTrainingRuntimes for Kubeflow Training Operator v1** [self-managed 3.5] Deprecated (was Deprecated) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: The Kubeflow Training Operator (v1) is deprecated starting OpenShift AI 2.25 and is scheduled to be removed.
- **Deprecated SQLite as a production metadata store for OGX** [self-managed 3.5] Deprecated — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: Starting with OpenShift AI 3.2, SQLite is deprecated for use as a metadata store in production OGX deployments.
- **Deprecated annotation format for Connection Secrets::** [self-managed 3.5] Deprecated (was Deprecated) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: Starting with OpenShift AI 3.0, the opendatahub.io/connection-type-ref annotation format for creating Connection Secrets is deprecated.
- **Deprecated Kubeflow Training operator v1** [self-managed 3.5] Deprecated (was Deprecated) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: The Kubeflow Training Operator (v1) is deprecated starting OpenShift AI 2.25 and is planned to be removed in a future release.
- **Deprecated TrustyAI service CRD v1alpha1** [self-managed 3.5] Deprecated (was Deprecated) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: Starting with OpenShift AI 2.25, the v1apha1 version is deprecated and planned for removal in an upcoming release.
- **Deprecated KServe Serverless deployment mode** [self-managed 3.5] Deprecated (was Deprecated) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: Starting with OpenShift AI 2.25, The KServe Serverless deployment mode is deprecated.
- **Deprecated model registry API v1alpha1** [self-managed 3.5] Deprecated (was Deprecated) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: v1alpha1 Starting with OpenShift AI 2.24, the model registry API version is deprecated and will be removed in a future release of OpenShift AI.
- **Multi-model serving platform (ModelMesh)** [self-managed 3.5] Deprecated (was Deprecated) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: Starting with OpenShift AI version 2.19, the multi-model serving platform based on ModelMesh is deprecated.
- **Accelerator Profiles and legacy Container Size selector deprecated** [self-managed 3.5] Deprecated (was Deprecated) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: Starting with OpenShift AI 3.0, Accelerator Profiles and the Container Size selector for workbenches are deprecated.
- **Deprecated OpenVINO Model Server (OVMS) plugin** [self-managed 3.5] Deprecated (was Deprecated) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: The CUDA plugin for the OpenVINO Model Server (OVMS) is now deprecated and will no longer be available in future releases of OpenShift AI.
- **OpenShift AI dashboard user management moved from to** [self-managed 3.5] Deprecated (was Deprecated) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)
- **Deprecated cluster configuration parameters** [self-managed 3.5] Deprecated (was Deprecated) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: When using the CodeFlare SDK to run distributed workloads in Red Hat OpenShift AI, the following parameters in the Ray cluster configuration are now deprecated and should be replaced with the new parameters as indicated.

### ❌ Removed (8)
- **CodeFlare Operator removed** [self-managed 3.5] Removed (was Removed) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: Starting with OpenShift AI 3.0, the CodeFlare Operator has been removed.
- **Microsoft SQL Server command-line tool removal** [self-managed 3.5] Removed (was Removed) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: Red Hat OpenShift AI Self-Managed 3.5 Release notes Starting with OpenShift AI 2.24, the Microsoft SQL Server command-line tools (sqlcmd, bcp) have been removed from workbenches.
- **Model registry ML Metadata (MLMD) server removal** [self-managed 3.5] Removed (was Removed) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: Starting with OpenShift AI 2.23, the ML Metadata (MLMD) server has been removed from the model registry component.
- **Embedded subscription channel not used in some versions** [self-managed 3.5] Removed (was Removed) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: embedded For OpenShift AI 2.8 to 2.20 and 2.22 to 3.5, the subscription channel is not used.
- **Anaconda removal** [self-managed 3.5] Removed (was Removed) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: Starting with OpenShift AI version 2.18, Anaconda is no longer included in OpenShift AI, and Anaconda resources are no longer supported or managed by OpenShift AI.
- **Pipeline logs for Python scripts running in Elyra pipelines are no longer stored in S3** [self-managed 3.5] Removed (was Removed) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: Logs are no longer stored in S3-compatible storage for Python scripts which are running in Elyra pipelines.
- **Beta subscription channel no longer used** [self-managed 3.5] Removed (was Removed) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: Starting with OpenShift AI 2.5, the beta subscription channel is no longer used.
- **HabanaAI workbench image removal** [self-managed 3.5] Removed (was Removed) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/support-removals_relnotes)  
    근거: Support for the HabanaAI 1.10 workbench image has been removed.

### 🔄 변경 (81)
- **Support for direct authentication with an OIDC identity provider** [self-managed 3.5] GA (was GA) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Direct authentication with an OpenID Connect (OIDC) identity provider is now available as a GA feature.
- **Migration guide available for transitioning from vLLM-based InferenceService to LLMInferenceService** [self-managed 3.5] GA (was GA) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Platform Operators deploying Distributed Inference with llm-d on OpenShift AI can follow a step-by- step guide covering LLMInferenceServiceConfig, YAML examples, and migration from vLLM-based InferenceService deployments.
- **Prometheus metrics for Distributed Inference with llm-d** [self-managed 3.5] GA (was GA) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can now monitor llm-d distributed inference deployments using documented Prometheus metrics and PromQL query examples.
- **MLFlow SDK pre-installed in workbench and runtime images** [self-managed 3.5] GA (was GA) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: The MLFlow SDK is now pre-installed and included in the datascience, tensorflow (CUDA & ROCm), pytorch (CUDA & ROCm), and codeserver workbench and runtime images.
- **MLflow Operator is now a managed component in the DataScienceCluster CR** [self-managed 3.5] GA (was GA) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Starting with Red Hat OpenShift AI 3.4, the MLflow Operator is a managed component in the DataScienceCluster custom resource (CR).
- **NeMo Guardrails to enable AI safety** [self-managed 3.5] GA (was GA) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: NeMo Guardrails, introduced in Red Hat OpenShift AI 3.3 as a Technology Preview, is fully supported with this release.
- **Models-as-a-Service now Generally Available** [self-managed 3.5] GA (was GA) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Models-as-a-Service (MaaS) is now Generally Available in Red Hat OpenShift AI 3.4.
- **The Models-as-a-Service subscription model redesign** [self-managed 3.5] GA (was GA) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: The Models-as-a-Service (MaaS) subscription model has been redesigned to replace the tier-based model introduced in version 3.3.
- **Self-service API key management for Models-as-a-Service** [self-managed 3.5] GA (was GA) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can now create and manage your own API keys for programmatic access to large language models through Models-as-a-Service.
- **OCI-compliant storage layer for model registry** [self-managed 3.5] GA (was GA) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can now use the OpenShift AI dashboard to register a model from an S3-compatible source or URI, transform it into an OCI ModelCar image, and store it in an OCI registry.
- **MLServer ServingRuntime for KServe is now generally available** [self-managed 3.5] GA (was GA) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: The MLServer ServingRuntime for KServe is now generally available in Red Hat OpenShift AI.
- **MLflow operator promoted to a managed component** [self-managed 3.5] GA (was GA) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Starting with Red Hat OpenShift AI 3.4, the MLflow Operator is a managed component in the DataScienceCluster mlflowoperator custom resource (CR).
- **Automatic MLflow SDK configuration for workbenches** [self-managed 3.5] GA (was GA) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: When the MLflow Operator is enabled, you can annotate workbench notebook resources with opendatahub.io/mlflow-instance to automatically configure the MLflow SDK.
- **Granular RBAC for workbenches** [self-managed 3.5] GA (was GA) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Project administrators can now define custom, fine-grained roles for workbench resources by using the oc CLI or by importing YAML in the OpenShift web console.
- **Multi-architecture support for the model catalog** [self-managed 3.5] GA (was GA) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: The model catalog includes support for IBM Power (ppc64le) architecture.
- **Just-In-Time Checkpointing and S3 Storage for Kubeflow Trainer** [self-managed 3.5] GA (was GA) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Kubeflow Trainer now provides Just-In-Time (JIT) and periodic checkpointing for distributed training jobs on OpenShift AI.
- **Workbench and runtime images default to Red Hat Python index** [self-managed 3.5] GA (was GA) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Workbench and runtime images default to the Red Hat Python index.
- **PostgreSQL database support for Model Registry** [self-managed 3.5] GA (was GA) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can configure a PostgreSQL database as the backend for Model Registry from the OpenShift AI dashboard.
- **Default database solution for Model Registry** [self-managed 3.5] GA (was GA) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Model Registry includes a default database solution for testing.
- **vLLM uvicorn access logs are disabled by default in Distributed Inference with llm-d** [self-managed 3.5] GA (was GA) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: vLLM uvicorn access logs are disabled by default in LLMInferenceServiceConfig, including logs generated by router-scheduler /metrics endpoint polling.
- **Simplified configuration for Distributed Inference with llm-d scheduler settings** [self-managed 3.5] GA (was GA) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Configure Distributed Inference with llm-d scheduler settings using the endpointPickerConfig field in the LLMInferenceService specification.
- **Configure vLLM runtime arguments using Kubernetes container field** [self-managed 3.5] GA (was GA) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can configure vLLM runtime arguments using the standard Kubernetes container args field in LLMInferenceService resources.
- **Hybrid search support for Qdrant remote vector database provider** [self-managed 3.5] GA (was GA) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: Vector Store Search supports hybrid and keyword search for the Qdrant Vector IO provider.
- **Workload variant autoscaler for Distributed Inference with llm-d model deployments** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Platform Operators can enable autoscaling for Distributed Inference with llm-d model deployments based on incoming request volume as a Technical Preview.
- **Priority-based flow control for mixed llm-d workloads** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Platform Operators can assign priority tiers to workload classes and configure queuing policies so that latency-sensitive requests are served ahead of throughput-oriented batch traffic.
- **Gateway discovery for llm-d deployments** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: This Technology Preview feature enables self-service Gateway management, supports multitenant namespace-scoped network isolation, and provides programmatic access through the Gateway discovery REST API.
- **vLLM runtime support for Models-as-a-Service** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: This Technology Preview feature enables you to serve large language models with vLLM’s high- performance inference capabilities while benefiting from MaaS governance and subscription-based controls.
- **External OIDC authentication for Models-as-a-Service** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: This Technology Preview feature enables enterprise-wide access to large language models without requiring OpenShift accounts for every user.
- **Models-as-a-Service observability dashboard** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: This Technology Preview feature provides comprehensive usage metrics for cost attribution and showback reporting to finance teams.
- **External model egress via inference gateway** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: This Technology Preview feature enables you to apply MaaS governance policies, token tracking, and rate limiting to third-party LLM services such as OpenAI, Anthropic, or other external providers.
- **Automate machine learning model training with AutoML** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: AutoML is available as a Technology Preview feature in Red Hat OpenShift AI 3.5.
- **Automate RAG optimization with AutoRAG** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: AutoRAG is available as a Technology Preview feature in Red Hat OpenShift AI 3.4.
- **Recommended vLLM runtime configurations in model catalog** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: During this Technical Preview phase, you can manually apply these recommendations during the model deployment workflow:
- **Artifact signing and verification for model registry** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: This Technology Preview feature enables you to sign artifacts to establish authenticity and verify signatures to confirm integrity.
- **EvalHub client SDK and CLI** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: OpenShift AI includes a Technology Preview of the EvalHub client SDK and command-line interface (CLI).
- **Evaluation Stack user interface** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Red Hat OpenShift AI includes a Technology Preview of the Evaluation Stack user interface.
- **Create ability to sign and verify AI Artifacts in Registry** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: For more information about signing and verifying models in the Model Registry see https://github.com/kubeflow/model-registry/tree/main/clients/python#signing-and-verifying- models.
- **MLflow integration** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: MLflow is no longer a Technology Preview feature.
- **Support for text embedding models in the Model Catalog** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: This Technology Preview feature allows data scientists and AI engineers to discover and deploy models designed specifically for vector generation, a critical Red Hat OpenShift AI Self-Managed 3.5 Release notes component for Retrieval-Augmented Generation (RAG) and semantic search workflows.
- **Workbench and runtime images default to the Red Hat Python index** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Access and use Red Hat built and supported Python packages.
- **YAML viewer for Distributed Inference with llm-d model deployments** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: This Technology Preview feature introduces the following capabilities:
- **Gen AI Playground interface redesign** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: The Gen AI Playground interface provides a prompt-lab-style experience with improved prompt- driven experimentation, rapid iteration capabilities, and clear visual feedback.
- **Multi-instance chat comparison in Playground** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: You can compare results across multiple configurations in the Playground by using multiple chat panes side-by-side.
- **Basic guardrails available in Gen AI Playground** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: The Gen AI Playground provides access to basic safety guardrails from OGX.
- **Conversations API** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: The Conversations API enables multi-turn, context-aware chats by managing message history, tool outputs, and conversation state.
- **Model-as-a-Service (MaaS) integration** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: This feature is available as a Technology Preview.
- **MLServer ServingRuntime for KServe** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: The MLServer serving runtime for KServe is now available as a technology preview feature in Red Hat OpenShift AI.
- **NVIDIA NeMo Guardrails** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: You can use NVIDIA NeMo Guardrails as a Technology Preview feature to add guardrails and safety controls to your deployed models in Red Hat OpenShift AI.
- **Stop button for chatbot in Generative AI Studio** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: You can interrupt the chatbot as it is composing a response to a prompt.
- **AI Available Assets page for deployed models and MCP servers** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: A new AI Available Assets page enables AI engineers and application developers to view and consume deployed AI resources within their projects.
- **Generative AI Playground for model testing and evaluation** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: The Generative AI (GenAI) Playground introduces a unified, interactive experience within the OpenShift AI dashboard for experimenting with foundation and custom models.
- **Feature Store integration with Workbenches and new user access capabilities** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: This feature is available as a Technology Preview.
- **Feature Store user interface** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: The Feature Store component now includes a web-based user interface (UI).
- **IBM Spyre AI Accelerator model serving support on x86 platforms** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: TECHNOLOGY PREVIEW FEATURES Model serving with the IBM Spyre AI Accelerator is now available as a Technology Preview feature for x86 platforms.
- **Centralized platform observability** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Centralized platform observability, including metrics, traces, and built-in alerts, is available as a Technology Preview feature.
- **Support for Kubernetes Event-driven Autoscaling (KEDA)** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: This Technology Preview feature enables metrics-based autoscaling for inference services, allowing for more efficient management of accelerator resources, reduced operational costs, and improved performance for your inference services.
- **LM-Eval model evaluation UI feature** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: TrustyAI now offers a user-friendly UI for LM-Eval model evaluations as Technology Preview.
- **Support for creating and managing Ray Jobs with the CodeFlare SDK** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: You can now create and manage Ray Jobs on Ray Clusters directly through the CodeFlare SDK.
- **Custom flow estimator for Synthetic Data Generation pipelines** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: You can now use a custom flow estimator for synthetic data generation (SDG) pipelines.
- **FAISS vector storage integration** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: You can now use the FAISS (Facebook AI Similarity Search) library as an inline vector store in OpenShift AI.
- **New Feature Store component** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: This Technology Preview release introduces the following capabilities:
- **Validated sdg-hub notebooks for Red Hat AI Platform** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Validated sdg_hub example notebooks are now available to provide a notebook-driven user experience in OpenShift AI 3.0.
- **RStudio Server workbench image** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: With the RStudio Server workbench image, you can access the RStudio IDE, an integrated development environment for R.
- **CUDA - RStudio Server workbench image** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: With the CUDA - RStudio Server workbench image, you can access the RStudio IDE and NVIDIA CUDA Toolkit.
- **Support for multinode deployment of very large models** [self-managed 3.5] TP (was TP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)  
    근거: Serving models over multiple graphical processing unit (GPU) nodes when using a single-model serving runtime is now available as a Technology Preview feature.
- **AgentCard support for post-deployment agent discovery** [self-managed 3.5] DP (was DP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: You can now discover deployed agents and their capabilities through the AgentCard custom resource.
- **Agent deploy and runtime management** [self-managed 3.5] DP (was DP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: You can now manage the runtime concerns of deployed agents using the AgentRuntime custom resource.
- **Distributed Tracing for Distributed Inference with llm-d** [self-managed 3.5] DP (was DP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: Platform Operators can trace distributed inference with llm-d requests end-to-end across service boundaries using OpenTelemetry-compatible distributed tracing.
- **Batch inference compatible with OpenAI batch APIs in Distributed Inference with llm-d** [self-managed 3.5] DP (was DP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: Platform Operators can submit large request volumes asynchronously through the OpenAI- /v1/batches compatible API and retrieve results without maintaining an active connection.
- **Existing vector stores available as RAG knowledge sources in Gen AI Studio Playground** [self-managed 3.5] DP (was DP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: You can surface previously-created vector stores as retrieval-augmented generation (RAG) knowledge sources in the Gen AI Studio Playground.
- **Interact with Red Hat OpenShift AI using MCP clients** [self-managed 3.5] DP (was DP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: Red Hat OpenShift AI provides an MCP (Model Context Protocol) server that enables MCP- compatible clients to interact with your environment through natural-language conversations.
- **Tool calling metadata on model cards in the model catalog** [self-managed 3.5] DP (was DP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: Red Hat OpenShift AI now displays tool callin, also known as function calling, configuration metadata directly in the model catalog.
- **MCP Catalog for enterprise management of MCP servers** [self-managed 3.5] DP (was DP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: The MCP Catalog provides a centralized experience for discovering, deploying, and experimenting with Model Context Protocol (MCP) servers in Red Hat OpenShift AI.
- **Core Evaluation Stack control plane** [self-managed 3.5] DP (was DP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: The Evaluation Stack control plane provides an API REST routing and orchestration layer for AI evaluation, benchmarking, and profiling backends on OpenShift AI.
- **Automatic MLflow experiment creation in EvalHub** [self-managed 3.5] DP (was DP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: The EvalHub service automatically creates an MLflow experiment when you specify experiment.name in the evaluation job request.
- **Kubeflow Spark Operator for distributed data processing** [self-managed 3.5] DP (was DP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: The Kubeflow Spark Operator is now available in OpenShift AI as a Developer Preview.
- **LLM Compressor integration** [self-managed 3.5] DP (was DP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: LLM Compressor capabilities are now available in Red Hat OpenShift AI as a Developer Preview feature.
- **AI Available Assets integration with Model-as-a-Service (MaaS)** [self-managed 3.5] DP (was DP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: This feature is available as a Developer Preview.
- **Additional fields added to Model Deployments for AI Available Assets integration** [self-managed 3.5] DP (was DP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: This feature is available as a Developer Preview.
- **Packaging of ITS Hub dependencies to the Red Hat–maintained Python index** [self-managed 3.5] DP (was DP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: This feature is available as a Developer Preview.
- **Dynamic hardware-aware continual training strategy** [self-managed 3.5] DP (was DP) — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)  
    근거: Static hardware profile support is now available to help users select training methods, models, and hyperparameters based on VRAM requirements and reference benchmarks.


## 2026-06-11

### 🆕 신규 (2)
- **MLflow is fully supported** [self-managed 3.4] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: MLflow, previously available as a Technology Preview and Developer Preview feature, is fully supported with this release.
- **Configure vLLM runtime arguments using Kubernetes container field** [self-managed 3.4] GA ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: You can configure vLLM runtime arguments using the standard Kubernetes container args field in LLMInferenceService resources.

### 🗑️ 문서에서 제거 (1)
- **Configure vLLM runtime arguments using Kubernetes container args field** [self-managed 3.4] GA (was GA) ⚠️rename? — [문서](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/release_notes/new-features-and-enhancements_relnotes)  
    근거: args You can configure vLLM runtime arguments using the standard Kubernetes container field in LLMInferenceService resources.


## 2026-06-08

- 📌 baseline 스냅샷 생성 (433 records, 변경이벤트 없음)
