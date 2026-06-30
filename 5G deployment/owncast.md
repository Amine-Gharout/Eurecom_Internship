# Owncast 5G Live Streaming Deployment

## 1. Executive Summary
Owncast is a self-hosted, open-source live video streaming and chat server. In this architecture, it acts as the external Data Network application, serving as the functional payload to validate Layer 7 routing through an OpenAirInterface (OAI) 5G Core via a simulated User Equipment (UE).

## 2. Component Architecture

| Component | Function | Network Context |
| :--- | :--- | :--- |
| **Owncast Container** | Live streaming web server (Port 8081) and RTMP video ingest (Port 1935). | Attached to the `demo-oai-public-net` Docker bridge. |
| **UPF (User Plane Function)** | The 5G gateway. Routes packets between the internal UE subnet (`12.1.1.0/24`) and the Docker bridge. | Acts as the mandatory gateway for Owncast's return traffic. |
| **gnbsim** | Simulates both the 5G Radio (gNodeB) and the Mobile Phone (UE). | Acquires a dynamic IP (e.g., `12.1.1.2`) from the core network. |

## 3. Configuration Prerequisites (YAML)
To prevent Docker security restrictions from blocking network route injections (`Operation not permitted`), the `owncast` service must be injected into the `docker-compose-basic-nrf.yaml` file with the `NET_ADMIN` Linux capability. 

Append this exact block under `services:` before executing the pipeline:

```yaml
    owncast:
        container_name: owncast
        image: gabekangas/owncast:latest
        restart: always
        cap_add:
            - NET_ADMIN
        ports:
            - "8081:8080"
            - "1935:1935"
        networks:
            public_net: