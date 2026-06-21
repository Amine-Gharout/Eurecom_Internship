# Intent-Based Networking (IBN) for Autonomous 5G Core Management

## Overview
This repository houses an Intent-Based Networking (IBN) system designed to automate the deployment and real-time optimization of a private 5G network. The system leverages Large Language Models (LLMs) to translate human intents into infrastructure code, and Deep Reinforcement Learning (RL) to dynamically enforce Service Level Objectives (SLOs) under variable network loads.

This project is conducted as part of a research initiative affiliated with **EURECOM (France)** and **Simula (Norway)**.

## Core Architecture
The system operates across three distinct planes:

1. **Infrastructure Plane (Data & Control):**
   * Built on **OpenAirInterface (OAI)** (`oai-cn5g-fed`).
   * Orchestrated via Docker Compose.
   * Simulates UE/RAN via **UERANSIM** to route real application traffic (e.g., an Owncast live video stream) through the User Plane Function (UPF).

2. **Cognitive Plane (Intent Translation):**
   * Powered by **LangGraph** and Python.
   * Translates natural language requests (e.g., "Deploy a 5G network for live streaming with max 20ms latency") into executable JSON schemas and Docker Compose files.

3. **Assurance Plane (Closed-Loop Control):**
   * A custom **PyTorch Reinforcement Learning** agent.
   * Continuously extracts telemetry (CPU, RAM, latency, throughput) from the UPF container.
   * Executes corrective actions (e.g., dynamically scaling container resources) to prevent SLO violations without human intervention.

## Prerequisites
* **Operating System:** Linux (Pop!_OS or Ubuntu 22.04 LTS).
* **Containerization:** Docker Engine and Docker Compose V2.
* **Development Stack:** Python 3.10+, PyTorch, PostgreSQL (with `pgvector`).

## Repository Structure
* `/docs`: Architecture specifications, task lists, and OAI component breakdowns.
* `/infrastructure`: Modified OAI Docker Compose files and UERANSIM configurations.
* `/cognitive_plane`: LLM prompt templates, LangGraph workflows, and JSON schema definitions.
* `/assurance_plane`: PyTorch RL environment (State/Action/Reward definitions), training loops, and telemetry extraction scripts.

## Phase 1: Quick Start (Core Deployment)
To deploy the baseline 5G core infrastructure:

1. **Clone the Repositories:**
```bash
   git clone <your-repo-url>
   git clone [https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-fed.git](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-fed.git)