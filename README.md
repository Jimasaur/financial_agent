# Financial Research Agent

A powerful AI agent that performs comprehensive financial research, verifies facts, and visualizes stock data.

## Features

-   **Multi-Agent Architecture**: Uses specialized agents for Planning, Searching, Writing, Risk Analysis, and Financials.
-   **Real-time Web Search**: Fetches the latest market news and data.
-   **Fact-Checking**: A dedicated Verifier agent cross-references claims with web sources.
-   **Live Charts**: Displays 30-day stock price charts and performance trends.
-   **Activity Logging**: Watch the agents think and act in real-time.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure Environment**:
    Copy the example environment file:
    ```bash
    cp financial_research_agent/.env.example financial_research_agent/.env
    ```
    Edit `financial_research_agent/.env` and add your API keys:
    -   `OPENAI_API_KEY`: Required for the agents.
    -   `ALPHAVANTAGE_API_KEY`: Optional, for live charts. Get a free key [here](https://www.alphavantage.co/support/#api-key).

## Running the Agent

### Web Interface (Recommended)

Run the Flask application:

```bash
python -m financial_research_agent.app
```

Open your browser to: http://localhost:5000

### CLI Mode

Run the agent in the terminal:

```bash
python -m financial_research_agent.main
```

## Project Structure

-   `financial_research_agent/`: Main package code.
    -   `app.py`: Flask web server.
    -   `manager.py`: Orchestrates the agent workflow.
    -   `agents/`: Agent definitions.
    -   `static/`: Frontend assets (HTML/CSS/JS).
