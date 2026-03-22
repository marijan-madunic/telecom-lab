# 📡 Telecom Lab – Mini Telco Core on Kubernetes

![CI](https://github.com/marijan-madunic/telecom-lab/actions/workflows/ci.yml/badge.svg)

![Python](https://img.shields.io/badge/python-3.11-blue)
![Flask](https://img.shields.io/badge/framework-flask-green)
![Docker](https://img.shields.io/badge/container-docker-blue)
![Kubernetes](https://img.shields.io/badge/orchestration-kubernetes-blue)
![Redis](https://img.shields.io/badge/cache-redis-red)
![Status](https://img.shields.io/badge/status-learning%20project-orange)


📡 Telecom Lab – Mini Telco Core on Kubernetes

Mini telecom core simulation napravljen s Python mikroservisima i Kubernetesom.
Projekt simulira osnovne komponente mobilne mreže poput AAA, UDM, PCRF i OCS.

Cilj projekta je demonstrirati:

mikroservisnu arhitekturu
telco policy logiku
charging / balance check
caching
Kubernetes deployment
self-healing infrastrukturu

🧩 Arhitektura
Client
  │
  ▼
AAA Service
  │
  ├── UDM  → subscriber data (plan, roaming)
  │
  ├── PCRF → policy decision
  │
  ├── OCS  → balance / charging
  │
  └── Redis → cache
  
⚙️ Servisi
Service	Description
AAA	Authentication, orchestration, roaming logic
UDM	Subscriber database simulator
PCRF	Policy decision engine
OCS	Online charging system (balance check)
Redis	Cache layer
🚀 Tehnologije
Python (Flask)
Redis
Docker
Kubernetes
Minikube


🔎 AAA Flow

1️⃣ Client šalje zahtjev

GET /auth/<IMSI>

2️⃣ AAA provjerava Redis cache

3️⃣ Ako nema cache:

AAA zove:

UDM → subscriber data
PCRF → policy
OCS → balance

4️⃣ AAA vraća finalni odgovor.

🧪 Primjer odgovora
curl http://AAA/auth/001010000000001
{
  "auth": "granted",
  "balance": 900,
  "imsi": "001010000000001",
  "is_roaming": false,
  "plan": "gold",
  "policy": "premium",
  "source": "udm"
}
🌍 Roaming logika

Ako je subscriber u roamingu:

gold → silver
silver → bronze

PCRF zatim dodjeljuje policy za novi plan.

🧠 Cache

AAA koristi Redis TTL cache.

Primjer:

source: udm

sljedeći request:

source: cache

❤️ Kubernetes

Svaki servis ima:

Deployment
Service
Health endpoint
Liveness probe
Readiness probe

Kubernetes automatski radi:

restart podova
self healing
rolling updates

📊 Primjer logova
Cache MISS → calling UDM
Calling PCRF
Calling OCS

ili

Cache HIT

🛠 Pokretanje projekta
minikube start
eval $(minikube docker-env)

build image-a:

docker build -t aaa-service .
docker build -t udm-service .
docker build -t pcrf-service .
docker build -t ocs-service .

deploy:

kubectl apply -f kubernetes/

🔮 Sljedeći koraci
CI/CD pipeline
usage tracking
throttling
observability (Prometheus/Grafana)
distributed tracing
📚 Projektni cilj

Projekt demonstrira kako telco core logika može biti implementirana kao cloud-native mikroservisi na Kubernetesu.
