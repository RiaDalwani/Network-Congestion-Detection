# DTN Congestion Recovery Simulator

An interactive network congestion simulation platform implementing DTN-inspired Contact Graph Routing (CGR) concepts for congestion recovery and buffering in dynamic internet topologies.

## Features

- Real-time network traffic simulation
- Interactive congestion visualization
- Contact Graph Routing (CGR) implementation
- Delay Tolerant Networking (DTN) concepts
- Dynamic bottleneck detection
- Buffer-based congestion recovery
- Router failure simulation
- Live monitoring dashboard
- Cloudflare Radar traffic integration
- Network topology visualization using NetworkX

## Technologies Used

### Backend
- Python
- Flask
- NetworkX
- Matplotlib

### Frontend
- HTML
- Bootstrap
- JavaScript

## Concepts Implemented

- Dijkstra Shortest Path Routing
- Betweenness Centrality
- Congestion Detection
- Delay Tolerant Networking (DTN)
- Contact Graph Routing (CGR)
- Store-Carry-Forward Communication
- Network Traffic Engineering

## Project Workflow

1. Generate network topology
2. Inject simulated internet traffic
3. Detect congestion bottlenecks
4. Apply CGR-based buffering
5. Simulate delayed recovery
6. Restore communication paths

## How to Run

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Application

```bash
python app.py
```

Open:

```text
http://localhost:5000
```

## Project Structure

```text
dtn-congestion-recovery/
│
├── app.py
├── requirements.txt
├── README.md
├── templates/
│   └── index.html
└── .gitignore
```

## Future Improvements

- Real packet tracing
- Reinforcement learning routing
- Multi-path routing optimization
- Docker deployment
- Real-time analytics dashboard
- Large-scale topology generation

## Author

Ria Dalwani
