# Kubernetes 部署指南

本文档介绍如何在 Kubernetes (K8s) 集群中部署 hereOffer 系统，适用于生产环境。

## 目录

- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [配置文件](#配置文件)
- [部署步骤](#部署步骤)
- [服务暴露](#服务暴露)
- [持久化存储](#持久化存储)
- [配置管理](#配置管理)
- [自动扩缩容](#自动扩缩容)
- [监控和日志](#监控和日志)
- [故障排查](#故障排查)

---

## 环境要求

### Kubernetes 集群

| 组件 | 版本要求 | 说明 |
|------|---------|------|
| Kubernetes | >= 1.20 | 支持主流云服务商（AWS EKS、阿里云 ACK、腾讯云 TKE） |
| kubectl | >= 1.20 | 命令行工具 |
| Helm | >= 3.0 | 包管理工具（可选） |

### 集群资源

**最低配置**（测试环境）:
- 节点数量: 3 个
- 节点规格: 2 核 4GB 内存
- 总资源: 6 核 12GB 内存

**推荐配置**（生产环境）:
- 节点数量: 6 个以上
- 节点规格: 4 核 8GB 内存
- 总资源: 24 核 48GB 内存

### 依赖服务

以下服务可以使用托管版本或自行部署：

| 服务 | 推荐方案 | 说明 |
|------|---------|------|
| MySQL | 阿里云 RDS / AWS RDS | 托管数据库服务 |
| Redis | 阿里云 Redis / AWS ElastiCache | 托管缓存服务 |
| MinIO | 阿里云 OSS / AWS S3 | 对象存储（或自建 MinIO） |

---

## 快速开始

### 1. 准备 Kubernetes 集群

```bash
# 检查集群状态
kubectl cluster-info
kubectl get nodes

# 创建命名空间
kubectl create namespace hereoffer
```

### 2. 创建 Secret（敏感信息）

```bash
# 创建数据库密码
kubectl create secret generic hereoffer-secrets \
  --from-literal=mysql-root-password=YOUR_ROOT_PASSWORD \
  --from-literal=mysql-password=YOUR_MYSQL_PASSWORD \
  --from-literal=jwt-secret=YOUR_JWT_SECRET_AT_LEAST_32_CHARS \
  --from-literal=dashscope-api-key=YOUR_DASHSCOPE_API_KEY \
  -n hereoffer
```

### 3. 应用配置文件

```bash
# 应用所有配置
kubectl apply -f k8s/ -n hereoffer

# 查看部署状态
kubectl get all -n hereoffer
```

### 4. 验证部署

```bash
# 检查 Pod 状态
kubectl get pods -n hereoffer

# 查看服务
kubectl get svc -n hereoffer

# 测试 API
kubectl port-forward svc/hereoffer-api 8000:8000 -n hereoffer
curl http://localhost:8000/healthz
```

---

## 配置文件

### 目录结构

推荐的 K8s 配置文件结构：

```
k8s/
├── namespace.yaml              # 命名空间
├── configmap.yaml              # 配置映射
├── secret.yaml.example         # Secret 示例（不提交真实值）
├── mysql/
│   ├── statefulset.yaml        # MySQL StatefulSet
│   ├── service.yaml            # MySQL Service
│   └── pvc.yaml                # 持久化卷声明
├── redis/
│   ├── deployment.yaml         # Redis Deployment
│   └── service.yaml            # Redis Service
├── minio/
│   ├── deployment.yaml         # MinIO Deployment
│   ├── service.yaml            # MinIO Service
│   └── pvc.yaml                # 持久化卷声明
├── api/
│   ├── deployment.yaml         # API Deployment
│   ├── service.yaml            # API Service
│   └── hpa.yaml                # 水平自动扩缩容
├── worker/
│   ├── deployment.yaml         # Worker Deployment
│   └── hpa.yaml                # 水平自动扩缩容
└── ingress.yaml                # Ingress 配置
```

---

## 部署步骤

### 1. Namespace

**k8s/namespace.yaml**:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: hereoffer
  labels:
    name: hereoffer
    environment: production
```

### 2. ConfigMap

**k8s/configmap.yaml**:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: hereoffer-config
  namespace: hereoffer
data:
  # 数据库配置
  DATABASE_HOST: "hereoffer-mysql"
  DATABASE_PORT: "3306"
  DATABASE_NAME: "hereoffer"
  DATABASE_USER: "hereoffer_user"
  
  # Redis 配置
  REDIS_HOST: "hereoffer-redis"
  REDIS_PORT: "6379"
  
  # MinIO 配置
  MINIO_ENDPOINT: "hereoffer-minio:9000"
  MINIO_BUCKET: "resumes"
  MINIO_USE_SSL: "false"
  
  # 应用配置
  LOG_LEVEL: "INFO"
  CORS_ORIGINS: "https://app.hereoffer.com"
  JWT_ALGORITHM: "HS256"
  JWT_EXPIRATION_MINUTES: "10080"
  
  # LLM 配置
  LLM_MODEL: "qwen-plus"
  LLM_TIMEOUT: "60"
  
  # 文件配置
  MAX_UPLOAD_SIZE: "10485760"
```

### 3. MySQL StatefulSet

**k8s/mysql/statefulset.yaml**:
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: hereoffer-mysql
  namespace: hereoffer
spec:
  serviceName: hereoffer-mysql
  replicas: 1
  selector:
    matchLabels:
      app: hereoffer-mysql
  template:
    metadata:
      labels:
        app: hereoffer-mysql
    spec:
      containers:
      - name: mysql
        image: mysql:8.0
        env:
        - name: MYSQL_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: hereoffer-secrets
              key: mysql-root-password
        - name: MYSQL_DATABASE
          valueFrom:
            configMapKeyRef:
              name: hereoffer-config
              key: DATABASE_NAME
        - name: MYSQL_USER
          valueFrom:
            configMapKeyRef:
              name: hereoffer-config
              key: DATABASE_USER
        - name: MYSQL_PASSWORD
          valueFrom:
            secretKeyRef:
              name: hereoffer-secrets
              key: mysql-password
        ports:
        - containerPort: 3306
          name: mysql
        volumeMounts:
        - name: mysql-data
          mountPath: /var/lib/mysql
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
  volumeClaimTemplates:
  - metadata:
      name: mysql-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: "standard"  # 根据云服务商调整
      resources:
        requests:
          storage: 20Gi
```

**k8s/mysql/service.yaml**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: hereoffer-mysql
  namespace: hereoffer
spec:
  clusterIP: None
  selector:
    app: hereoffer-mysql
  ports:
  - port: 3306
    targetPort: 3306
    name: mysql
```

### 4. Redis Deployment

**k8s/redis/deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hereoffer-redis
  namespace: hereoffer
spec:
  replicas: 1
  selector:
    matchLabels:
      app: hereoffer-redis
  template:
    metadata:
      labels:
        app: hereoffer-redis
    spec:
      containers:
      - name: redis
        image: redis:7.2-alpine
        ports:
        - containerPort: 6379
          name: redis
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        volumeMounts:
        - name: redis-data
          mountPath: /data
      volumes:
      - name: redis-data
        emptyDir: {}  # 或使用 PVC
```

**k8s/redis/service.yaml**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: hereoffer-redis
  namespace: hereoffer
spec:
  selector:
    app: hereoffer-redis
  ports:
  - port: 6379
    targetPort: 6379
    name: redis
```

### 5. MinIO Deployment

**k8s/minio/deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hereoffer-minio
  namespace: hereoffer
spec:
  replicas: 1
  selector:
    matchLabels:
      app: hereoffer-minio
  template:
    metadata:
      labels:
        app: hereoffer-minio
    spec:
      containers:
      - name: minio
        image: minio/minio:latest
        args:
        - server
        - /data
        - --console-address
        - ":9001"
        env:
        - name: MINIO_ROOT_USER
          value: "minioadmin"
        - name: MINIO_ROOT_PASSWORD
          value: "minioadmin"
        ports:
        - containerPort: 9000
          name: api
        - containerPort: 9001
          name: console
        volumeMounts:
        - name: minio-data
          mountPath: /data
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
      volumes:
      - name: minio-data
        persistentVolumeClaim:
          claimName: minio-pvc
```

**k8s/minio/service.yaml**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: hereoffer-minio
  namespace: hereoffer
spec:
  selector:
    app: hereoffer-minio
  ports:
  - port: 9000
    targetPort: 9000
    name: api
  - port: 9001
    targetPort: 9001
    name: console
```

**k8s/minio/pvc.yaml**:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: minio-pvc
  namespace: hereoffer
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: "standard"
  resources:
    requests:
      storage: 50Gi
```

### 6. API Deployment

**k8s/api/deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hereoffer-api
  namespace: hereoffer
  labels:
    app: hereoffer-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hereoffer-api
  template:
    metadata:
      labels:
        app: hereoffer-api
    spec:
      initContainers:
      - name: wait-for-mysql
        image: busybox:1.28
        command: ['sh', '-c', 'until nc -z hereoffer-mysql 3306; do echo waiting for mysql; sleep 2; done']
      containers:
      - name: api
        image: your-registry/hereoffer-api:latest  # 替换为你的镜像
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          name: http
        env:
        # 从 ConfigMap 读取
        - name: DATABASE_HOST
          valueFrom:
            configMapKeyRef:
              name: hereoffer-config
              key: DATABASE_HOST
        - name: DATABASE_PORT
          valueFrom:
            configMapKeyRef:
              name: hereoffer-config
              key: DATABASE_PORT
        - name: DATABASE_NAME
          valueFrom:
            configMapKeyRef:
              name: hereoffer-config
              key: DATABASE_NAME
        - name: DATABASE_USER
          valueFrom:
            configMapKeyRef:
              name: hereoffer-config
              key: DATABASE_USER
        # 从 Secret 读取
        - name: DATABASE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: hereoffer-secrets
              key: mysql-password
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: hereoffer-secrets
              key: jwt-secret
        - name: DASHSCOPE_API_KEY
          valueFrom:
            secretKeyRef:
              name: hereoffer-secrets
              key: dashscope-api-key
        # 构建 DATABASE_URL
        - name: DATABASE_URL
          value: "mysql+pymysql://$(DATABASE_USER):$(DATABASE_PASSWORD)@$(DATABASE_HOST):$(DATABASE_PORT)/$(DATABASE_NAME)"
        - name: REDIS_URL
          value: "redis://hereoffer-redis:6379/0"
        - name: MINIO_ENDPOINT
          valueFrom:
            configMapKeyRef:
              name: hereoffer-config
              key: MINIO_ENDPOINT
        - name: MINIO_ACCESS_KEY
          value: "minioadmin"
        - name: MINIO_SECRET_KEY
          value: "minioadmin"
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: hereoffer-config
              key: LOG_LEVEL
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /healthz
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
```

**k8s/api/service.yaml**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: hereoffer-api
  namespace: hereoffer
spec:
  type: ClusterIP
  selector:
    app: hereoffer-api
  ports:
  - port: 8000
    targetPort: 8000
    protocol: TCP
    name: http
```

### 7. Worker Deployment

**k8s/worker/deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hereoffer-worker
  namespace: hereoffer
spec:
  replicas: 2
  selector:
    matchLabels:
      app: hereoffer-worker
  template:
    metadata:
      labels:
        app: hereoffer-worker
    spec:
      containers:
      - name: worker
        image: your-registry/hereoffer-api:latest  # 使用同一镜像
        command: ["python", "worker/run_worker.py"]
        env:
        # 环境变量配置同 API
        - name: DATABASE_URL
          value: "mysql+pymysql://$(DATABASE_USER):$(DATABASE_PASSWORD)@$(DATABASE_HOST):$(DATABASE_PORT)/$(DATABASE_NAME)"
        - name: REDIS_URL
          value: "redis://hereoffer-redis:6379/0"
        - name: DASHSCOPE_API_KEY
          valueFrom:
            secretKeyRef:
              name: hereoffer-secrets
              key: dashscope-api-key
        # ... 其他环境变量 ...
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

---

## 服务暴露

### Ingress 配置

**k8s/ingress.yaml**:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: hereoffer-ingress
  namespace: hereoffer
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: "letsencrypt-prod"  # 自动 HTTPS
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.hereoffer.com
    secretName: hereoffer-tls
  rules:
  - host: api.hereoffer.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: hereoffer-api
            port:
              number: 8000
```

### 安装 Ingress Controller

```bash
# 使用 Helm 安装 NGINX Ingress Controller
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace
```

---

## 持久化存储

### StorageClass 示例

**阿里云 ACK**:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: alicloud-disk-ssd
provisioner: diskplugin.csi.alibabacloud.com
parameters:
  type: cloud_ssd
reclaimPolicy: Retain
allowVolumeExpansion: true
```

**AWS EKS**:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-sc
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
reclaimPolicy: Retain
allowVolumeExpansion: true
```

---

## 配置管理

### 更新 ConfigMap

```bash
# 编辑 ConfigMap
kubectl edit configmap hereoffer-config -n hereoffer

# 或使用文件更新
kubectl apply -f k8s/configmap.yaml -n hereoffer

# 重启 Pod 使其生效
kubectl rollout restart deployment hereoffer-api -n hereoffer
kubectl rollout restart deployment hereoffer-worker -n hereoffer
```

### 更新 Secret

```bash
# 更新 Secret
kubectl create secret generic hereoffer-secrets \
  --from-literal=jwt-secret=NEW_SECRET \
  --dry-run=client -o yaml | kubectl apply -f - -n hereoffer

# 重启 Pod
kubectl rollout restart deployment hereoffer-api -n hereoffer
```

---

## 自动扩缩容

### Horizontal Pod Autoscaler (HPA)

**k8s/api/hpa.yaml**:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: hereoffer-api-hpa
  namespace: hereoffer
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: hereoffer-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 2
        periodSeconds: 30
```

**k8s/worker/hpa.yaml**:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: hereoffer-worker-hpa
  namespace: hereoffer
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: hereoffer-worker
  minReplicas: 2
  maxReplicas: 8
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 应用 HPA

```bash
# 确保 Metrics Server 已安装
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# 应用 HPA
kubectl apply -f k8s/api/hpa.yaml -n hereoffer
kubectl apply -f k8s/worker/hpa.yaml -n hereoffer

# 查看 HPA 状态
kubectl get hpa -n hereoffer
```

---

## 监控和日志

### Prometheus + Grafana

**安装**:
```bash
# 使用 Helm 安装 kube-prometheus-stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

**访问 Grafana**:
```bash
# 获取 admin 密码
kubectl get secret -n monitoring prometheus-grafana \
  -o jsonpath="{.data.admin-password}" | base64 --decode

# 端口转发
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# 访问 http://localhost:3000
```

### 日志收集

**使用 EFK (Elasticsearch + Fluentd + Kibana)**:

```bash
# 安装 Elasticsearch
helm repo add elastic https://helm.elastic.co
helm install elasticsearch elastic/elasticsearch \
  --namespace logging \
  --create-namespace

# 安装 Fluentd
helm install fluentd stable/fluentd-elasticsearch \
  --namespace logging

# 安装 Kibana
helm install kibana elastic/kibana \
  --namespace logging
```

**查看日志**:
```bash
# 查看 API 日志
kubectl logs -f deployment/hereoffer-api -n hereoffer

# 查看 Worker 日志
kubectl logs -f deployment/hereoffer-worker -n hereoffer

# 查看最近 100 行
kubectl logs --tail=100 deployment/hereoffer-api -n hereoffer
```

---

## 故障排查

### 常见问题

#### 1. Pod 无法启动

**检查步骤**:
```bash
# 查看 Pod 状态
kubectl get pods -n hereoffer

# 查看 Pod 详情
kubectl describe pod <pod-name> -n hereoffer

# 查看 Pod 日志
kubectl logs <pod-name> -n hereoffer

# 查看上一次的日志（如果 Pod 重启）
kubectl logs <pod-name> --previous -n hereoffer
```

#### 2. 数据库连接失败

**检查步骤**:
```bash
# 测试 MySQL 连接
kubectl run mysql-client --image=mysql:8.0 -it --rm --restart=Never \
  -n hereoffer -- \
  mysql -h hereoffer-mysql -u hereoffer_user -p

# 检查 DNS 解析
kubectl run dnsutils --image=tutum/dnsutils -it --rm --restart=Never \
  -n hereoffer -- \
  nslookup hereoffer-mysql
```

#### 3. Ingress 无法访问

**检查步骤**:
```bash
# 查看 Ingress 状态
kubectl get ingress -n hereoffer
kubectl describe ingress hereoffer-ingress -n hereoffer

# 查看 Ingress Controller 日志
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller

# 测试内部服务
kubectl port-forward svc/hereoffer-api 8000:8000 -n hereoffer
curl http://localhost:8000/healthz
```

#### 4. HPA 不工作

**检查步骤**:
```bash
# 查看 HPA 状态
kubectl get hpa -n hereoffer
kubectl describe hpa hereoffer-api-hpa -n hereoffer

# 检查 Metrics Server
kubectl get deployment metrics-server -n kube-system
kubectl top nodes
kubectl top pods -n hereoffer
```

#### 5. 持久化卷挂载失败

**检查步骤**:
```bash
# 查看 PVC 状态
kubectl get pvc -n hereoffer

# 查看 PV 状态
kubectl get pv

# 查看 StorageClass
kubectl get storageclass

# 查看 Pod 事件
kubectl describe pod <pod-name> -n hereoffer
```

### 调试技巧

**进入容器调试**:
```bash
# 进入 API 容器
kubectl exec -it deployment/hereoffer-api -n hereoffer -- /bin/bash

# 进入 MySQL 容器
kubectl exec -it hereoffer-mysql-0 -n hereoffer -- mysql -u root -p

# 运行临时 Pod 调试网络
kubectl run curl --image=curlimages/curl -it --rm --restart=Never \
  -n hereoffer -- curl http://hereoffer-api:8000/healthz
```

---

## 最佳实践

### 1. 资源限制

始终为容器设置 `requests` 和 `limits`，避免资源耗尽。

### 2. 健康检查

配置 `livenessProbe` 和 `readinessProbe`，确保服务健康。

### 3. 滚动更新

使用滚动更新策略，零停机部署：

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```

### 4. 亲和性和反亲和性

将 API Pod 分散到不同节点：

```yaml
spec:
  affinity:
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
            - key: app
              operator: In
              values:
              - hereoffer-api
          topologyKey: kubernetes.io/hostname
```

### 5. 安全

- 使用 RBAC 限制权限
- 使用 NetworkPolicy 隔离网络
- 定期更新镜像，修复安全漏洞
- 使用 Secret 存储敏感信息

---

## 下一步

- [Docker 部署](./DOCKER.md) - 本地开发和测试
- [环境变量配置](./ENVIRONMENT.md) - 详细配置说明
- [生产环境最佳实践](./PRODUCTION.md) - 性能优化和安全加固

---

**最后更新**: 2026-02-01
