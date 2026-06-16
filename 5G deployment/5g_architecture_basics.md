# 5G Core Architecture Fundamentals

This document outlines the foundational architecture of a 5G Core Network, specifically focusing on the separation between the Control Plane and the Data Plane. This architecture is the basis for our OpenAirInterface (OAI) deployments and the Intent-Based Networking (IBN) project.

## 1. The Core Concept: Control Plane vs. Data Plane

To understand how a 5G network processes requests, the system must be viewed as two distinct but parallel "worlds":

### The Control Plane (The Brain & Logistics)
The Control Plane handles signaling. It **never** touches user payload data (like video streams or file downloads). Its sole job is to authenticate devices, grant network access, and configure the routing paths.

* **AMF (Access and Mobility Management Function):** Acts as the security gatekeeper. It authenticates the User Equipment (UE), verifies access rights, and manages device mobility (ensuring the connection remains stable as the UE moves between different antennas).
* **SMF (Session Management Function):** Acts as the session planner. Once the AMF validates a user, the SMF dictates how the data will travel. It establishes the session and pushes the configuration rules down to the data routing components.

### The Data Plane / User Plane (The Highway)
The Data Plane is responsible for the actual transportation of user traffic.

* **UPF (User Plane Function):** The main router of the 5G core and the gateway to the external Data Network (Internet). It functions as a direct data tunnel. 
    > **Note for IBN Project:** The UPF is the central component for our Reinforcement Learning (RL) Assurance agent. When the network is under heavy load, the RL agent will dynamically adjust the UPF container's resources (CPU/RAM) to maintain strict Service Level Agreements (SLAs) like latency and throughput.

## 2. Edge Components

* **UE (User Equipment):** The end-user device. In a real-world scenario, this is a 5G smartphone or IoT device. In our local Docker environment, this will be a simulated software client.
* **gNodeB (Next-Generation NodeB):** The 5G radio antenna that bridges the wireless UE connection into the wired 5G Core.

## 3. The Step-by-Step Data Flow

When a UE wants to send data to an external application (such as an Owncast live-streaming server), the process occurs in two phases:

### Phase A: Signaling (Setting up the path)
1.  **Connection Request:** The UE powers on and sends a signal to the **gNodeB**.
2.  **Authentication:** The gNodeB forwards this request to the **AMF**.
3.  **Validation:** The AMF verifies the user's identity and requests the **SMF** to prepare a network connection.
4.  **Tunnel Creation:** The SMF contacts the **UPF** and configures a virtual tunnel tailored to the user's requested parameters (SLOs).

### Phase B: Traffic Routing (Moving the data)
5.  **Transmission:** The path is officially open.
6.  **Direct Flow:** The data packets flow directly from the **UE ➔ gNodeB ➔ UPF ➔ Internet**. 
    *Crucially, this data stream completely bypasses the AMF and SMF.*