import asyncio
import httpx
import websockets
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

async def run_pipeline():
    async with httpx.AsyncClient(timeout=60) as client:
        for _ in range(10):
            try:
                res = await client.get(f"{API_URL}/api/health")
                if res.status_code == 200:
                    print("Backend API is online!")
                    break
            except Exception:
                await asyncio.sleep(1)

        print("\nTriggering research session for: 'acoustic surveillance'...")
        payload = {
            "topic": "acoustic surveillance",
            "depth": 2,
            "max_papers": 15,
            "sources": ["arxiv", "semantic_scholar", "pubmed", "openalex"]
        }
        res = await client.post(f"{API_URL}/api/research", json=payload)
        session = res.json()
        session_id = session["id"]
        print(f"Session created: {session_id}")

        ws_endpoint = f"{WS_URL}/ws/research/{session_id}"
        print(f"Connecting to WebSocket stream: {ws_endpoint}")
        
        try:
            async with websockets.connect(ws_endpoint) as ws:
                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    if data.get("type") == "progress":
                        progress_pct = int(data.get("progress", 0) * 100)
                        message = data.get("message", "")
                        print(f"[{progress_pct}%] {message}")
                        if data.get("progress", 0) >= 1.0:
                            break
        except Exception as e:
            print(f"WebSocket monitoring finished: {e}")

        # Poll status until backend flags completion
        print("\nPolling session status until pipeline fully completes...")
        for attempt in range(40):
            try:
                s_res = await client.get(f"{API_URL}/api/research/{session_id}")
                s_data = s_res.json()
                status = s_data.get("status")
                if status in ["completed", "failed"]:
                    print(f"Pipeline status reached: {status}!")
                    break
            except Exception:
                pass
            await asyncio.sleep(2)

        print("Fetching final synthesis results...")
        res = await client.get(f"{API_URL}/api/research/{session_id}/results")
        results = res.json()

        papers = results.get("papers", [])
        report = results.get("report", "")
        intelligence = results.get("intelligence", {})

        print(f"\n==========================================")
        print(f"RESEARCH PIPELINE COMPLETE!")
        print(f"Total Papers Analyzed: {len(papers)}")
        print(f"Gaps Detected: {len(intelligence.get('gaps', []))}")
        print(f"Hypotheses Generated: {len(intelligence.get('hypotheses', []))}")
        print(f"Report Length: {len(report)} characters")
        print("==========================================\n")

        print("--- LITERATURE REVIEW PREVIEW ---")
        print(report[:1500] if report else "No report generated.")
        print("\n----------------------------------")

if __name__ == "__main__":
    asyncio.run(run_pipeline())
