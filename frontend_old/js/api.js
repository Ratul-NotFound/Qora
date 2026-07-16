class QoraAPI {
    constructor() {
        this.baseUrl = document.getElementById('api-base-url').value.replace(/\/$/, "");
        this.ws = null;
    }

    async startResearch(topic, sources, onProgress) {
        try {
            const response = await fetch(`${this.baseUrl}/api/research`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    topic: topic,
                    sources: sources,
                    max_papers: 50,
                    depth: 1
                })
            });

            if (!response.ok) throw new Error("API request failed");
            
            const session = await response.json();
            
            // Connect to WebSocket for progress
            this.connectWebSocket(session.id, onProgress);
            
            return session.id;
        } catch (error) {
            console.error("Start research error:", error);
            throw error;
        }
    }

    connectWebSocket(sessionId, onProgress) {
        const wsUrl = this.baseUrl.replace(/^http/, 'ws') + `/ws/research/${sessionId}`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'progress') {
                onProgress(data.message, data.progress);
            }
        };

        this.ws.onerror = (error) => {
            console.error("WebSocket error:", error);
        };
    }

    async getResults(sessionId) {
        try {
            const response = await fetch(`${this.baseUrl}/api/research/${sessionId}/results`);
            if (!response.ok) throw new Error("Failed to fetch results");
            return await response.json();
        } catch (error) {
            console.error("Fetch results error:", error);
            throw error;
        }
    }

    async checkStatus(sessionId) {
        try {
            const response = await fetch(`${this.baseUrl}/api/research/${sessionId}`);
            return await response.json();
        } catch (error) {
            console.error("Check status error:", error);
            return null;
        }
    }
}

// Global API instance
const api = new QoraAPI();
