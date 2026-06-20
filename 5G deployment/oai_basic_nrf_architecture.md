# OAI 5G Core Architecture: `docker-compose-basic-nrf.yaml`

This document breaks down the components of the `docker-compose-basic-nrf.yaml` file from the OpenAirInterface (OAI) repository. This file represents the standard Service-Based Architecture (SBA) for a 5G Core and serves as the baseline infrastructure for the Intent-Based Networking (IBN) project.

## 1. Foundation & Infrastructure

### Docker Networks (`networks`)
* **Role:** Defines the isolated subnet (e.g., `192.168.70.0/24`) where all 5G containers communicate.
* **IBN Relevance:** When your LLM generates custom deployments, it must strictly adhere to static IP addressing within this subnet to ensure components can route traffic to one another.

### `mysql` (Database)
* **Role:** The persistent storage layer. It holds the `oai_db` database, which contains subscriber profiles, cryptographic keys, and SIM card configurations (IMSI).
* **IBN Relevance:** If a natural language intent requires adding new users or IoT devices to the network, your system must execute SQL insertions into this container.

## 2. The Service-Based Architecture Hub

### `oai-nrf` (Network Repository Function)
* **Role:** The central discovery directory. In modern 5G, components do not rely on hardcoded IP addresses for everything; they register with the NRF. When the AMF needs to talk to the SMF, it asks the NRF where the SMF is located.
* **Boot Order:** This is the anchor container. Almost all other containers have a `depends_on: oai-nrf` rule. If the NRF crashes, the core fails to initialize.

## 3. The Control Plane (Signaling)

### `oai-amf` (Access and Mobility Management Function)
* **Role:** The entry point for signaling. It authenticates the User Equipment (UE) and manages mobility (handovers between antennas).
* **Key Environment Variables:** Look for `MCC` (Mobile Country Code) and `MNC` (Mobile Network Code). These define the network's global identity.

### `oai-smf` (Session Management Function)
* **Role:** The session planner. Once the AMF authenticates a user, the SMF establishes the connection tunnel and dictates traffic rules.
* **Key Environment Variables:** The SMF configuration explicitly defines the IP address of the UPF. This maps the logical Control Plane to the physical Data Plane.
* **IBN Relevance:** The LLM will modify variables here (like Slice/Service Types - SST/SD) when an intent requests a specific network slice (e.g., ultra-low latency vs. high bandwidth).

## 4. Security & Subscriber Management

### `oai-udr` (Unified Data Repository)
* **Role:** The only component that directly reads from/writes to the MySQL database to retrieve subscriber data.

### `oai-udm` (Unified Data Management)
* **Role:** Processes the raw subscriber data from the UDR into actionable network rules and access privileges.

### `oai-ausf` (Authentication Server Function)
* **Role:** Handles the security cryptography. It generates the authentication challenges sent to the UE's SIM card to verify its identity.

## 5. The Data Plane (Traffic Routing)

### `oai-spgwu-tiny` (User Plane Function / UPF)
* **Role:** The main data router. All actual user traffic (e.g., Owncast video streams) flows through this container. It acts as the bridge between the radio network (gNodeB) and the external internet.
* **IBN Relevance:** **This is the primary target for your Reinforcement Learning (RL) agent.** The RL agent will continuously monitor this container and dynamically adjust its Docker resource limits (CPU/RAM) to prevent latency spikes and maintain Service Level Objectives (SLOs).

### `oai-ext-dn` (External Data Network)
* **Role:** A NAT (Network Address Translation) router. It takes data exiting the UPF and routes it to the host machine's internet connection, allowing the simulated 5G network to access the real world.