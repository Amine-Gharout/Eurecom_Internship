# Technical Architecture: UERANSIM eBPF Deployment

**BLUF:** This document breaks down the `docker-compose-ueransim-ebpf.yaml` configuration. It explains how the radio access network (RAN) simulator bypasses standard kernel bottlenecks using eBPF, and how it integrates with the host system to enable real application traffic routing — a strict requirement for extracting reliable latency metrics in a reinforcement learning pipeline.

***

## 1. Core Service: `ueransim`

This block defines the single container that simulates both the gNodeB (base station) and the UE (smartphone).

- **`image: oaisoftwarealliance/ueransim:...`** — Specifies the prebuilt Docker image containing UERANSIM C++ binaries.
- **`privileged: true` / `cap_add: - NET_ADMIN`** — Critical directives. They grant the container administrative rights over the host machine's kernel networking subsystem. Without this, the container cannot create the virtual interface (`uesimtun0`) on Pop!_OS.
- **`devices: - /dev/net/tun:/dev/net/tun`** — Maps the host's network tunnel device into the container. This is the hardware bridge that allows standard IP traffic to be encapsulated into 5G packets.

### Environment Variables

- **`USE_EBPF=true`** — Enables packet processing via eBPF (Extended Berkeley Packet Filter). This allows routing logic to execute directly in kernel space at high speed, avoiding user-space CPU overhead. This ensures that throughput drops measured by the RL agent originate from the 5G network, not from local CPU saturation.
- **`MCC`, `MNC`** — Mobile Country Code and Network Code. Cryptographic network identifiers that must exactly match the AMF and SMF configuration for the N1/N2 connection to be accepted.
- **`SST`, `SD`** — Slice/Service Type identifiers. Must also align precisely with the core network slice configuration.

***

## 2. Network Definitions

The container must connect to two distinct networks managed by the 5G core:

- **`demo-oai-public-net`** — Management and Control Plane network. UERANSIM uses it to send authentication requests (N1/N2) to the AMF.
- **`demo-oai-n3-net`** — High-throughput Data Plane network. UERANSIM uses it to send raw user traffic (N3) directly to the eBPF UPF.

> **Note:** These networks are marked as `external: true`, meaning this Docker Compose file will **not** create them. They must already exist (deployed by the OAI core) before launching this configuration.

***

## 3. Volume Management

- **`volumes: - ./config:/openair-ueransim/config`** — Injects local configuration files (YAML or JSON) into the container. This allows modifying the destination IP address of the AMF or UPF without rebuilding the full UERANSIM Docker image.

***

## 4. Dependencies (`depends_on`)

If this section is present, it instructs the Docker engine to wait until specific containers (such as `oai-amf` or `oai-upf`) are marked as **healthy** before attempting to start the radio simulator. This prevents UERANSIM from flooding the network with connection requests before the core network is ready to handle them.

***

## Network Plane Architecture

| Network | Purpose | Protocol Interface | Connected To |
|---|---|---|---|
| `demo-oai-public-net` | Control Plane (auth, signaling) | N1/N2 | AMF |
| `demo-oai-n3-net` | Data Plane (user traffic) | N3 | UPF (eBPF) |

***

## Key Security & Capability Flags

| Flag | Effect | Risk if Omitted |
|---|---|---|
| `privileged: true` | Full kernel access for the container | Cannot create `uesimtun0` tunnel interface |
| `cap_add: NET_ADMIN` | Fine-grained network admin capability | Cannot configure routing tables or tunnel devices |
| `/dev/net/tun` device mount | Access to host TUN/TAP kernel subsystem | No IP-over-5G encapsulation possible |
| `USE_EBPF=true` | Kernel-space packet processing | Fallback to user-space; adds CPU overhead, skews RL latency metrics |