"""
Flask web application for the Financial Research Agent.
Provides a web GUI with real-time updates via Server-Sent Events.
Run this with: python -m examples.financial_research_agent.app
"""
import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, Response, jsonify
from queue import Queue
from threading import Thread

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / '.env')

from .manager import FinancialResearchManager
from .agents.writer_agent import FinancialReportData
from .agents.verifier_agent import VerificationResult
from .data_fetcher import fetch_stock_data
from .ticker_extractor import extract_ticker

try:
    from .database import ResearchDatabase
    db = ResearchDatabase()
    # Check if connection actually succeeded
    if db and not db.conn:
        print("Warning: Database initialized but connection failed")
        db = None
except Exception as e:
    print(f"Warning: Database not available: {e}")
    db = None

app = Flask(__name__, 
            static_folder='static',
            template_folder='static')


class WebProgressCallback:
    """Callback handler that queues progress updates for SSE streaming."""
    
    def __init__(self, queue: Queue):
        self.queue = queue
    
    def emit_event(self, event_type: str, data: dict):
        """Emit an event to the SSE stream."""
        self.queue.put({
            'event': event_type,
            'data': data
        })

    def log_agent_action(self, agent_name, action, details):
        """Log detailed agent activity"""
        event = {
            'event': 'agent_log',
            'data': {
                'timestamp': datetime.now().isoformat(),
                'agent': agent_name,
                'action': action,
                'details': details,
                'level': 'info'  # info, tool_call, thinking, result
            }
        }
        self.queue.put(event)


def run_research_async(query: str, callback: WebProgressCallback):
    """Run the research in a new event loop (for thread safety)."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Create a custom manager with callbacks
        mgr = FinancialResearchManager(callback=callback)
        
        # Run the research with callback integration
        result = loop.run_until_complete(run_with_callbacks(mgr, query, callback))
        
        # Emit final completion event
        callback.emit_event('complete', result)
    except Exception as e:
        callback.emit_event('error', {'message': str(e)})
    finally:
        loop.close()


async def run_with_callbacks(mgr: FinancialResearchManager, query: str, callback: WebProgressCallback):
    """Modified version of manager.run() that sends progress updates via callbacks."""
    
    callback.emit_event('status', {'stage': 'start', 'message': 'Starting financial research...'})
    
    # Planning phase
    callback.emit_event('status', {'stage': 'planning', 'message': 'Planning searches...'})
    search_plan = await mgr._plan_searches(query)
    callback.emit_event('status', {
        'stage': 'planning',
        'message': f'Will perform {len(search_plan.searches)} searches',
        'done': True
    })
    
    # Search phase
    callback.emit_event('status', {'stage': 'searching', 'message': 'Searching...'})
    search_results = await mgr._perform_searches(search_plan)
    callback.emit_event('status', {
        'stage': 'searching',
        'message': f'Completed {len(search_results)} searches',
        'done': True
    })
    
    # Writing phase
    callback.emit_event('status', {'stage': 'writing', 'message': 'Writing report...'})
    report = await mgr._write_report(query, search_results)
    callback.emit_event('status', {
        'stage': 'writing',
        'message': 'Report completed',
        'done': True
    })
    
    # Verification phase
    callback.emit_event('status', {'stage': 'verifying', 'message': 'Verifying report...'})
    verification = await mgr._verify_report(report)
    callback.emit_event('status', {
        'stage': 'verifying',
        'message': 'Verification completed',
        'done': True
    })
    
    # Return the final results
    result = {
        'short_summary': report.short_summary,
        'markdown_report': report.markdown_report,
        'follow_up_questions': report.follow_up_questions,
        'verification': {
            'verified': verification.verified,
            'issues': verification.issues
        }
    }
    
    # Save to database if available
    if db:
        try:
            # Extract company name and recommendation from summary
            company_name = extract_company_name(query)
            recommendation = determine_recommendation(report.short_summary)
            
            db.save_research(
                query=query,
                company_name=company_name,
                short_summary=report.short_summary,
                full_report=report.markdown_report,
                follow_up_questions=report.follow_up_questions,
                verification=result['verification'],
                recommendation=recommendation
            )
        except Exception as e:
            print(f"Error saving to database: {e}")
    
    return result


@app.route('/')
def index():
    """Serve the main HTML interface."""
    return render_template('index.html')


@app.route('/api/research', methods=['POST'])
def research():
    """Handle research requests and stream progress via SSE."""
    data = request.get_json()
    query = data.get('query', '')
    
    if not query:
        return {'error': 'Query is required'}, 400
    
    # Create a queue for SSE events
    event_queue = Queue()
    callback = WebProgressCallback(event_queue)
    
    # Start research in a background thread
    thread = Thread(target=run_research_async, args=(query, callback))
    thread.daemon = True
    thread.start()
    
    def generate():
        """Generator function for SSE streaming."""
        while True:
            event = event_queue.get()
            if event is None:
                break
            
            # Format as SSE
            yield f"event: {event['event']}\n"
            yield f"data: {json.dumps(event['data'])}\n\n"
            
            # Break on completion or error
            if event['event'] in ('complete', 'error'):
                break
    
    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get recent search history."""
    if not db:
        return {'error': 'Database not available'}, 503
    
    try:
        limit = request.args.get('limit', 10, type=int)
        history = db.get_recent_searches(limit=limit)
        
        # Convert datetime to string for JSON serialization
        for item in history:
            if 'created_at' in item:
                item['created_at'] = item['created_at'].isoformat()
        
        return {'history': history}
    except Exception as e:
        return {'error': str(e)}, 500


@app.route('/api/history/<int:research_id>', methods=['GET'])
def get_research(research_id):
    """Get a specific research result by ID."""
    if not db:
        return {'error': 'Database not available'}, 503
    
    try:
        result = db.get_research_by_id(research_id)
        if not result:
            return {'error': 'Research not found'}, 404
        
        # Convert datetime to string
        if 'created_at' in result:
            result['created_at'] = result['created_at'].isoformat()
        
        return result
    except Exception as e:
        return {'error': str(e)}, 500


@app.route('/api/chart/<query>', methods=['GET'])
def get_chart_data(query):
    """Fetch live chart data based on query string."""
    try:
        ticker = extract_ticker(query)
        if not ticker:
            return {'error': 'Could not identify ticker'}, 404
            
        data = fetch_stock_data(ticker)
        if 'error' in data:
            return data, 400
            
        return jsonify(data)
    except Exception as e:
        return {'error': str(e)}, 500


def extract_company_name(query):
    """Extract company name from query."""
    words = query.lower().split()
    companies = ['amazon', 'apple', 'google', 'microsoft', 'tesla', 'meta', 'nvidia', 'netflix', 'facebook']
    
    for company in companies:
        if company in query.lower():
            return company.capitalize()
    
    return 'Unknown'


def determine_recommendation(summary):
    """Determine buy/sell/hold recommendation from summary."""
    summary_lower = summary.lower()
    
    if 'buy' in summary_lower or 'strong' in summary_lower or 'positive' in summary_lower:
        return 'Buy'
    elif 'sell' in summary_lower or 'negative' in summary_lower or 'avoid' in summary_lower:
        return 'Sell'
    else:
        return 'Hold'


if __name__ == '__main__':
    print("🚀 Starting Financial Research Agent Web GUI...")
    print("📊 Open your browser to: http://localhost:5000")
    print("💾 Database: " + ("Connected" if db else "Not available"))
    app.run(debug=True, threaded=True, port=5000)
