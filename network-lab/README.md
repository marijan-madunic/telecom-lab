# 🌐 BGP Network Lab – Container-based Routing Simulation

## Overview

This lab demonstrates a simple **eBGP (external BGP) setup** using container-based routers with **FRRouting** and **Containerlab**.

It simulates communication between two autonomous systems:

- AS65001 (R1)
- AS65002 (R2)

Each router advertises its local subnet, enabling end-to-end connectivity between clients.

---

## Topology

[ PC1 ] 192.168.1.10
    |
    |
[ R1 ] AS65001
    |
10.0.12.0/30
    |
[ R2 ] AS65002
    |
    |
[ PC2 ] 192.168.2.10

---

## Technologies Used

- Containerlab
- FRRouting (FRR)
- Docker
- Linux networking

---

## How to Run

```bash
sudo containerlab deploy -t bgp-lab.clab.yml
```

## Validation

### BGP Session

```bash
docker exec -it clab-bgp-lab-r1 vtysh -c "show ip bgp summary"
```
Output:

IPv4 Unicast Summary (VRF default):
BGP router identifier 1.1.1.1, local AS number 65001

Neighbor        V    AS   State/PfxRcd
10.0.12.2       4 65002   1


✔️ BGP session successfully established (1 prefix received)


### Routing Table

```bash
docker exec -it clab-bgp-lab-r1 vtysh -c "show ip route"
```

Output:

B>* 192.168.2.0/24 via 10.0.12.2
✔️ Route successfully learned via BGP


### Connectivity Test

```bash
docker exec -it clab-bgp-lab-pc1 sh -c "ping -c 4 192.168.2.10"
```

Output:

4 packets transmitted, 4 received, 0% packet loss

✔️ End-to-end connectivity between subnets verified


##  Key Learnings

- BGP session establishment between autonomous systems
- Route advertisement and exchange
- Linux-based routing and forwarding
- Troubleshooting default gateway and connectivity issues
- Container-based network simulation


## Relation to Telecom Lab

This lab complements the main telecom project by adding a network layer simulation, bridging:

- Telecom services (AAA, PCRF, UDM, OCS)
- Underlying IP routing infrastructure


## Future Improvements

- Add OSPF for internal routing
- Simulate link failure (failover testing)
- Integrate Prometheus for network monitoring
- Expand topology (multi-AS design)




