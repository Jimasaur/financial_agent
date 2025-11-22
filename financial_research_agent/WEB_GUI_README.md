# Financial Research Agent - Web GUI

A beautiful, modern web interface for the OpenAI Financial Research Agent with real-time progress updates.

## 🚀 Quick Start

### 1. Set up your environment

Create a `.env` file in this directory with your OpenAI API key:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Install dependencies

Make sure Flask is installed:

```bash
pip install flask python-dotenv
```

### 3. Run the web server

From the root directory of the project:

```bash
cd c:\Users\hans2\Desktop\openai-cookbook-main\openai-agents-python-main\openai-agents-python-main
python -m examples.financial_research_agent.app
```

### 4. Open your browser

Navigate to: **http://localhost:5000**

## 💡 Usage

1. Enter a financial research query in the text box
2. Click "Start Research" 
3. Watch real-time progress as the agent:
   - Plans searches
   - Searches the web
   - Writes the report
   - Verifies findings
4. View the complete report with executive summary, full analysis, follow-up questions, and verification results

## 🎨 Features

- **Modern UI** with dark mode, gradients, and smooth animations
- **Real-time updates** via Server-Sent Events (SSE)
- **Progress tracking** for all research stages
- **Collapsible sections** for easy navigation
- **Responsive design** works on all screen sizes
- **Professional styling** with glassmorphism effects

## 📋 Environment Variables

Create a `.env` file with:

- `OPENAI_API_KEY` (required) - Your OpenAI API key from https://platform.openai.com/api-keys
- `OPENAI_MODEL` (optional) - Model to use (default: gpt-4o-mini)

## 🛠️ Technical Details

- **Backend**: Flask with async support for the OpenAI Agents SDK
- **Frontend**: Vanilla HTML/CSS/JavaScript (no frameworks required)
- **Streaming**: Server-Sent Events for real-time progress updates
- **Styling**: Modern CSS with CSS Grid, Flexbox, and animations
