"""
Web server for The Living Rusted Tankard game.

This module provides the web interface for the game, including the main game view
and API endpoints for game state management.
"""

import os
from pathlib import Path
from flask import Flask, render_template, jsonify, request

# Initialize Flask app
app = Flask(__name__)

# Game state
game_state = {
    'time': 'Morning, Day 1',
    'gold': 10,
    'inventory': ['Rusty Dagger', 'Leather Armor', 'Health Potion (2)', 'Torch'],
    'quests': [
        {'title': 'The Missing Ale', 'description': 'Find the tavern\'s stolen ale recipe'},
        {'title': 'Rat Infestation', 'description': 'Clear the cellar of rats (3/5)'}
    ],
    'narrative': [
        'Welcome to The Living Rusted Tankard! What would you like to do?'
    ]
}


@app.route('/')
def index():
    """Render the main game interface."""
    return render_template('game.html')


@app.route('/api/command', methods=['POST'])
def handle_command():
    """Handle game commands from the client.
    
    Returns:
        JSON response with command result and updated game state.
    """
    data = request.get_json()
    command = data.get('command', '').strip()
    
    # Process the command (placeholder for actual game logic)
    response = {
        'success': True,
        'message': f"You {command.lower()}.",
        'state': game_state
    }
    
    return jsonify(response)


@app.route('/api/state')
def get_state():
    """Get the current game state.
    
    Returns:
        JSON representation of the current game state.
    """
    return jsonify(game_state)


def run_server(host='0.0.0.0', port=5001, debug=True):
    """Run the Flask development server.
    
    Args:
        host: Host to bind the server to.
        port: Port to run the server on.
        debug: Whether to run in debug mode.
    """
    # Ensure the templates directory exists
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    # Set template and static folders
    app.template_folder = str(templates_dir)
    
    # Run the app
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_server()
