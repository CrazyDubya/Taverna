#!/usr/bin/env python3
"""
Enhanced 3D Demo Server for The Living Rusted Tankard.

This script serves the new 3D-enhanced interface as a standalone demo.
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from pathlib import Path
import os

# Create FastAPI app
app = FastAPI(title="Taverna 3D Enhanced Demo")

# Get the directory paths
current_dir = Path(__file__).parent
templates_dir = current_dir / "living_rusted_tankard" / "game" / "templates"

@app.get("/", response_class=HTMLResponse)
async def get_3d_demo():
    """Serve the 3D enhanced tavern interface."""
    html_file = templates_dir / "demo_3d_local.html"
    
    if html_file.exists():
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return HTMLResponse(content=content)
    else:
        return HTMLResponse(content="""
        <html>
            <body>
                <h1>File not found</h1>
                <p>Could not find demo_3d_local.html at: {}</p>
                <p>Available templates:</p>
                <ul>
        """.format(html_file) + "".join([
            f"<li>{f.name}</li>" for f in templates_dir.glob("*.html")
        ]) + """
                </ul>
            </body>
        </html>
        """)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "3D Enhanced Taverna Demo Server"}

@app.get("/classic", response_class=HTMLResponse)
async def get_classic_demo():
    """Serve the classic enhanced interface for comparison."""
    html_file = templates_dir / "enhanced_game.html"
    
    if html_file.exists():
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return HTMLResponse(content=content)
    else:
        return HTMLResponse(content="<h1>Classic interface not found</h1>")

if __name__ == "__main__":
    print("Starting Taverna 3D Enhanced Demo Server...")
    print("🍺 3D Enhanced Interface: http://localhost:8080/")
    print("🎭 Classic Interface: http://localhost:8080/classic")
    print("❤️ Health Check: http://localhost:8080/health")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8080, 
        log_level="info"
    )