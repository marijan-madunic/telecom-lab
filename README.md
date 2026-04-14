# 📡 Telecom Lab – Mini Telco Core on Kubernetes

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Flask](https://img.shields.io/badge/Flask-microservice-black)
![Docker](https://img.shields.io/badge/Docker-containerized-blue)
![Kubernetes](https://img.shields.io/badge/Kubernetes-orchestrated-326CE5)
![Redis](https://img.shields.io/badge/Redis-cache-red)

A mini telecom core simulation built with Python microservices and Kubernetes.

This project demonstrates a simplified **telecom control plane architecture** implemented using **cloud-native microservices**.

The system simulates typical telecom core components such as **AAA, UDM, PCRF and OCS**, along with caching and orchestration logic.

---

## 🎯 Project Goals

The goal of this project is to demonstrate:

* microservice-based telecom architecture
* subscriber authentication and orchestration logic
* telecom policy control
* charging and balance checking
* Redis-based caching
* Kubernetes deployment
* self-healing infrastructure

This project serves as a **learning lab combining telecom core concepts with modern cloud-native technologies**.

---

## 🧩 Architecture

```text
Client
  |
  v
AAA Service
  |
  |-- UDM   -> subscriber data (plan, roaming status)
  |-- PCRF  -> policy decision
  |-- OCS   -> balance / charging
  \-- Redis -> cache
```

The **AAA service acts as the orchestration layer**, coordinating communication between all services.

---

## 🌐 Architecture Diagram

```mermaid
flowchart LR

    Client[Client / API Request]

    AAA[AAA Service]
    Redis[(Redis Cache)]
    UDM[UDM Service<br/>Subscriber Data]
    PCRF[PCRF Service<br/>Policy Control]
    OCS[OCS Service<br/>Charging System]
    SMSC[SMSC Service]

    Client -->|Auth Request| AAA

    AAA -->|Check Cache| Redis
    Redis -->|Cache Hit| AAA

    AAA -->|Subscriber Data Request| UDM
    AAA -->|Policy Request| PCRF
    AAA -->|Balance Check| OCS

    UDM -->|Subscriber Profile| AAA
    PCRF -->|Policy Result| AAA
    OCS -->|Balance Result| AAA

    AAA -->|Final Response| Client
    Client -->|Send SMS| SMSC
    SMSC -->|Store / Retrieve| Redis
```

This diagram represents a simplified telecom control-plane flow where the **AAA service orchestrates authentication, policy control, charging, and caching**.

---

## ⚙️ Services

| Service | Description                                     |
| ------- | ----------------------------------------------- |
| AAA     | Authentication, orchestration and roaming logic |
| UDM     | Subscriber database simulator                   |
| PCRF    | Policy decision engine                          |
| OCS     | Online charging system (balance check)          |
| SMSC    | SMS messaging service with delivery tracking    |
| Redis   | Cache layer used by AAA                         |


---

## 📩 SMSC Service

The project includes a simplified **SMSC (Short Message Service Center)** microservice for SMS handling and delivery simulation.

### Features
- Send SMS messages via REST API
- Store messages in Redis
- Track delivery status (DELIVERED / FAILED)
- Retrieve subscriber inbox
- Prometheus metrics for observability

<details>
<summary><b>Show API examples</b></summary>

### Send SMS
```bash
curl -X POST http://localhost:8082/send_sms \
  -H "Content-Type: application/json" \
  -d '{
    "from": "385911111111",
    "to": "385922222222",
    "text": "Hello from telecom-lab"
  }'

### Check SMS status
curl http://localhost:8082/sms/<message_id>/status

### Read inbox
curl http://localhost:8082/messages/385922222222

### Health check
curl http://localhost:8082/health
</details> ```

---

## 🚀 Technologies

* Python (Flask)
* Redis
* Docker
* Kubernetes
* Minikube

---

## 🔎 AAA Flow

### 1️⃣ Client sends authentication request

```bash
GET /auth/<IMSI>
```

Example:

```bash
curl http://AAA/auth/001010000000001
```

### 2️⃣ AAA checks Redis cache

### 3️⃣ If cache miss

AAA calls the following services:

* **UDM** → subscriber data
* **PCRF** → policy decision
* **OCS** → balance information

### 4️⃣ AAA builds the final response and returns it to the client

---

## 🧪 Example Response

```bash
curl http://AAA/auth/001010000000001
```

```json
{
  "auth": "granted",
  "balance": 900,
  "imsi": "001010000000001",
  "is_roaming": false,
  "plan": "gold",
  "policy": "premium",
  "source": "udm"
}
```

---

## 🌍 Roaming Logic

If a subscriber is roaming, the service plan is downgraded:

```text
gold -> silver
silver -> bronze
```

After the downgrade, **PCRF assigns a policy based on the adjusted plan**.

---

## 🧠 Cache Behaviour

AAA uses **Redis TTL caching**.

Example behaviour:

First request:

```text
"source": "udm"
```

Next request:

```text
"source": "cache"
```

This reduces service calls and improves response time.

---

## ❤️ Kubernetes Features

Each microservice includes:

* Deployment
* Service
* Health endpoint
* Liveness probe
* Readiness probe

Kubernetes automatically provides:

* pod restart
* self-healing
* rolling updates
* service discovery

---

## 📊 Example Logs

Cache miss scenario:

```text
Cache MISS -> calling UDM
Calling PCRF
Calling OCS
```

Cached request:

```text
Cache HIT
```

---

## 🛠 Running the Project

Start Minikube:

```bash
minikube start
eval $(minikube docker-env)
```

Build Docker images:

```bash
docker build -t aaa-service .
docker build -t udm-service .
docker build -t pcrf-service .
docker build -t ocs-service .
```

Deploy to Kubernetes:

```bash
kubectl apply -f kubernetes/
```

---

### Monitoring

The telecom lab includes a full observability stack:

- Prometheus
- Grafana
- Alertmanager

Prometheus collects metrics from Kubernetes nodes and services,
while Grafana provides visualization dashboards for infrastructure
and telecom service metrics.

## Monitoring

The telecom lab includes a full observability stack using Prometheus and Grafana.

Prometheus collects metrics from Kubernetes nodes and telecom services,
while Grafana visualizes infrastructure and application performance.


Example Kubernetes monitoring dashboard:

![Grafana Dashboard](docs/grafana-kubernetes-dashboard.png)

---

## 🔮 Future Improvements

Planned next steps:

* CI/CD pipeline
* traffic simulation
* usage tracking
* throttling
* observability with Prometheus and Grafana
* distributed tracing
* additional telecom components (future 5G extensions such as PCF)


Already implemented:

- Kubernetes-based microservices architecture
- AAA authentication flow
- policy control (PCRF)
- balance check (OCS)
- Redis caching layer
- Prometheus metrics and Grafana dashboards
- traffic simulation for real-time monitoring
* Short Message Service Center (SMSC)

---

## 📚 Project Purpose

This project demonstrates how **telecom core logic can be implemented as cloud-native microservices running on Kubernetes**.

It serves as a **practical telecom lab combining networking, microservices and cloud-native infrastructure**.

---

## 👨‍💻 Author

Marijan Madunić
