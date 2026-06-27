# OAI Simulator Architecture: `docker-compose-gnbsim.yaml`

**BLUF:** This file is a signaling stress-test script. It simulates a 5G antenna (gNodeB) and a phone (UE) attempting to authenticate, establish a session, and ping an external server. It is a temporary validation tool, not a permanent network component.

## 1. Architectural Reality Check
The default file contains 6 separate services (`gnbsim`, `gnbsim2` ... `gnbsim5`, `gnbsim-fqdn`).
* **The Risk:** Running `docker compose up -d` on this file launches all 6 privileged containers simultaneously. On a local development machine, this unnecessarily consumes CPU and RAM.
* **The Solution:** Execute only the first service block (`gnbsim`) to validate the Control Plane (AMF/SMF) functionality. 

## 2. Core Component Breakdown
The `gnbsim` container requires precise configuration to trick the 5G core into accepting its connection.

### A. System Permissions & Networking
* **`privileged: true`:** Mandatory. The simulator must create low-level Linux network interfaces (GTP tunnels) to route the fake data packets. Standard Docker containers cannot do this.
* **`networks: public_net (external: True)`:** Forces the simulator to attach to the exact Docker bridge network already established by the `basic-nrf` core. 

### B. Network Identity (PLMN & Slicing)
The simulator must claim to belong to the correct network.
* **`MCC=208` & `MNC=95`:** Public Land Mobile Network (PLMN) ID. Matches the default test network ID hardcoded into the OAI AMF configuration.
* **`SST=222` & `SD=00007b`:** Network Slicing parameters (Slice/Service Type and Slice Differentiator). Directs the connection request to a specific virtual network slice handled by the core.

### C. Authentication Cryptography
The core's MySQL database holds pre-configured dummy subscriber profiles. The simulator must present matching credentials.
* **`MSIN=0000000031`:** The unique identifier for this specific fake SIM card.
* **`KEY` & `OPc`:** Hardcoded cryptographic keys required to solve the authentication challenge issued by the `oai-ausf` component.

### D. Execution & Payload
* **`AMF_FQDN=oai-amf`:** Uses Docker's internal DNS to locate the AMF container by name.
* **`URL=http://www.asnt.org:8080/`:** The success metric. Once authenticated and assigned an IP by the SMF, the simulator attempts an HTTP GET request to this external URL. If it downloads the file, the test passes, proving the Data Plane (UPF) is actively routing traffic to the internet.