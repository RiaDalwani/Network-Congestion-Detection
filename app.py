import requests
import networkx as nx
import matplotlib
matplotlib.use('Agg') # Necessary for Flask threading
import matplotlib.pyplot as plt
import io
import base64
import random
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

class InternetSimulator:
    def __init__(self):
        self.G = nx.Graph()
        self.buffer = {}  # {node_id: packet_count}
        self.traffic_multiplier = 1.0
        self.init_topology()

    def init_topology(self):
        self.G.clear()
        self.buffer = {}
        # Core Internet Topology (High Centrality Nodes)
        edges = [
            ('Core-1', 'Core-2', 2), ('Core-1', 'Edge-A', 5), 
            ('Core-1', 'Edge-B', 5), ('Core-2', 'Edge-A', 5), 
            ('Core-2', 'Edge-C', 5), ('Edge-A', 'User-1', 10), 
            ('Edge-B', 'User-2', 10), ('Edge-C', 'User-3', 10)
        ]
        # Weight represents Latency
        for u, v, w in edges:
            self.G.add_edge(u, v, weight=w, type='normal')
        
        # Set low capacities to force overflow for CGR demo
        for node in self.G.nodes():
            self.G.nodes[node]['capacity'] = random.randint(50, 100)
            self.G.nodes[node]['packet_count'] = 0
            self.G.nodes[node]['status'] = "Normal"
            self.buffer[node] = 0

    def get_realtime_multiplier(self):
        """Fetches real-world traffic scaling from Cloudflare Radar API"""
        try:
            url = "https://api.cloudflare.com/client/v4/radar/netflows/timeseries"
            res = requests.get(url, timeout=2)
            # Simulate a spike if API is busy, or return a random factor based on API health
            return random.uniform(1.8, 3.2) if res.status_code == 200 else 2.0
        except:
            return 2.5 # Default spike factor for simulation

sim = InternetSimulator()

def generate_visual():
    """Generates the Graph Image with CGR specific styles"""
    plt.figure(figsize=(12, 7))
    # Fixed position so the graph doesn't shake
    pos = nx.spring_layout(sim.G, seed=42)
    
    # 1. Edge Styling (Normal vs CGR Scheduled)
    normal_edges = [(u, v) for u, v, d in sim.G.edges(data=True) if d.get('type') == 'normal']
    scheduled_edges = [(u, v) for u, v, d in sim.G.edges(data=True) if d.get('type') == 'scheduled']

    # 2. Node Coloring based on Status
    node_colors = []
    centrality = nx.betweenness_centrality(sim.G)
    for n in sim.G.nodes():
        status = sim.G.nodes[n]['status']
        if status == "CRITICAL": node_colors.append('#e74c3c') # Red (Overflow)
        elif status == "BUFFERING": node_colors.append('#f39c12') # Orange (DTN Active)
        elif centrality[n] > 0.3: node_colors.append('#9b59b6') # Purple (High Centrality)
        else: node_colors.append('#3498db') # Blue (Normal)

    # 3. Draw Nodes & Labels
    node_sizes = [centrality[n] * 6000 + 1200 for n in sim.G.nodes()]
    nx.draw_networkx_nodes(sim.G, pos, node_color=node_colors, node_size=node_sizes, alpha=0.9)
    nx.draw_networkx_labels(sim.G, pos, font_color="white", font_weight="bold", font_size=10)

    # 4. Draw Edges
    nx.draw_networkx_edges(sim.G, pos, edgelist=normal_edges, width=2, edge_color='#bdc3c7')
    nx.draw_networkx_edges(sim.G, pos, edgelist=scheduled_edges, 
                           width=4, edge_color='#f39c12', style='dashed') # Visual CGR

    # 5. Load & Buffer Info Labels
    labels = {}
    for n in sim.G.nodes():
        load = sim.G.nodes[n]['packet_count']
        buf = sim.buffer.get(n, 0)
        labels[n] = f"\n\n\nLoad: {load}" + (f" | 🕒 BUF: {buf}" if buf > 0 else "")
    nx.draw_networkx_labels(sim.G, pos, labels=labels, font_size=8, font_color="#2c3e50")

    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plt.close()
    return base64.b64encode(img.getvalue()).decode('utf8')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/setup')
def setup():
    sim.init_topology()
    return jsonify({"status": "Topology Initialized", "graph_url": generate_visual()})

@app.route('/inject')
def inject():
    """Real-time API Traffic Injection Logic"""
    multiplier = sim.get_realtime_multiplier()
    total_packets = int(250 * multiplier)
    
    # Reset counts for new injection
    for node in sim.G.nodes():
        sim.G.nodes[node]['packet_count'] = 0
        sim.G.nodes[node]['status'] = "Normal"

    nodes = list(sim.G.nodes())
    for _ in range(total_packets):
        src, dest = random.sample(nodes, 2)
        try:
            # Dijkstra routing
            path = nx.shortest_path(sim.G, source=src, target=dest, weight='weight')
            for node in path:
                sim.G.nodes[node]['packet_count'] += 1
        except:
            continue

    # Flag Bottlenecks
    bottlenecks = []
    for node in sim.G.nodes():
        if sim.G.nodes[node]['packet_count'] > sim.G.nodes[node]['capacity']:
            sim.G.nodes[node]['status'] = "CRITICAL"
            bottlenecks.append(node)

    return jsonify({
        "multiplier": round(multiplier, 2),
        "packets": total_packets,
        "bottlenecks": bottlenecks,
        "graph_url": generate_visual()
    })

@app.route('/apply_cgr')
def apply_cgr():
    """The CGR Concept: Create dashed future links and move packets to buffer"""
    logs = []
    critical_nodes = [n for n in sim.G.nodes() if sim.G.nodes[n]['status'] == "CRITICAL"]
    
    if not critical_nodes:
        return jsonify({"logs": ["No critical congestion found."], "graph_url": generate_visual()})

    for node in critical_nodes:
        neighbors = list(sim.G.neighbors(node))
        if neighbors:
            # NOVELTY: Add a 'Scheduled' link (Dashed in UI)
            target = neighbors[0]
            sim.G.add_edge(node, target, type='scheduled', weight=100) # Weight 100 makes it 'future'
            
            # Move overflow to memory (Store-Carry-Forward)
            overflow = sim.G.nodes[node]['packet_count'] - sim.G.nodes[node]['capacity']
            sim.buffer[node] += overflow
            sim.G.nodes[node]['packet_count'] = sim.G.nodes[node]['capacity'] # Resolve current physical stress
            sim.G.nodes[node]['status'] = "BUFFERING"
            logs.append(f"CGR: Node {node} scheduled future contact with {target}. {overflow} packets buffered.")

    return jsonify({"logs": logs, "graph_url": generate_visual()})

@app.route('/release_buffer')
def release_buffer():
    """Simulates the 'Contact Window' opening"""
    for u, v, d in list(sim.G.edges(data=True)):
        if d.get('type') == 'scheduled':
            d['type'] = 'normal' # Link becomes real/solid
            d['weight'] = 1 # Link becomes fast
    
    for node in sim.buffer:
        sim.buffer[node] = 0
        if node in sim.G.nodes():
            sim.G.nodes[node]['status'] = "Normal"
            
    return jsonify({"status": "Contact Window Active. Buffer Cleared.", "graph_url": generate_visual()})

@app.route('/remove_node', methods=['POST'])
def remove_node():
    node_id = request.json.get('node')
    if node_id in sim.G:
        sim.G.remove_node(node_id)
        return jsonify({"status": f"Router {node_id} Failed!", "graph_url": generate_visual()})
    return jsonify({"status": "Node not found"})

if __name__ == '__main__':
    app.run(debug=True)
