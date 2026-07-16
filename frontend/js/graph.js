class KnowledgeGraph {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.graph = null;
    }

    render(data) {
        // Clear container
        this.container.innerHTML = '';
        
        if (!data || !data.nodes || data.nodes.length === 0) {
            this.container.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-network-wired"></i>
                    <p>Run a search to generate the knowledge graph.</p>
                </div>
            `;
            return;
        }

        // Initialize ForceGraph
        this.graph = ForceGraph()(this.container)
            .graphData(data)
            .backgroundColor('#0f111a')
            .nodeId('id')
            .nodeLabel('label')
            .nodeVal('size')
            .nodeColor(node => {
                if (node.type === 'method') return '#ec4899'; // Pink for methods
                if (node.type === 'paper') {
                    // Color by citations
                    if (node.citations > 50) return '#14b8a6'; // Teal for high impact
                    if (node.citations > 10) return '#6366f1'; // Indigo for medium
                    return '#94a3b8'; // Muted for others
                }
                return '#ffffff';
            })
            .linkColor(() => 'rgba(255,255,255,0.1)')
            .linkWidth(link => link.weight || 1)
            .onNodeClick(node => {
                // Center/zoom on node
                this.graph.centerAt(node.x, node.y, 1000);
                this.graph.zoom(8, 2000);
            })
            .nodeCanvasObject((node, ctx, globalScale) => {
                // Draw circle
                const size = Math.sqrt(node.size || 1) * 2;
                ctx.beginPath();
                ctx.arc(node.x, node.y, size, 0, 2 * Math.PI, false);
                ctx.fillStyle = node.color;
                ctx.fill();

                // Draw label if zoomed in enough or if it's a prominent node
                if (globalScale > 1.5 || node.size > 15) {
                    const label = node.label;
                    const fontSize = Math.max(12 / globalScale, 4);
                    ctx.font = `${fontSize}px Sans-Serif`;
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
                    ctx.fillText(label, node.x, node.y + size + fontSize);
                }
            });

        // Fit graph to container
        setTimeout(() => {
            this.graph.zoomToFit(400, 20);
        }, 500);
    }
}

// Global instance
const kg = new KnowledgeGraph('graph-container');
