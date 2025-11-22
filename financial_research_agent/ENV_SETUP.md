# Environment Variables Setup

## Required Configuration

To run the Financial Research Agent (both CLI and Web GUI), you need to set up your OpenAI API key.

### Option 1: Using .env file (Recommended)

Create a file named `.env` in the `examples/financial_research_agent` directory:

**Location:** `c:\Users\hans2\Desktop\openai-cookbook-main\openai-agents-python-main\openai-agents-python-main\examples\financial_research_agent\.env`

**Contents:**
```
OPENAI_API_KEY=your_openai_api_key_here
```

### Option 2: System Environment Variable

Set the environment variable in PowerShell:
```powershell
$env:OPENAI_API_KEY="your_openai_api_key_here"
```

Or permanently in Windows:
1. Search for "Environment Variables" in Windows
2. Click "Edit the system environment variables"
3. Click "Environment Variables..." button
4. Under "User variables", click "New"
5. Variable name: `OPENAI_API_KEY`
6. Variable value: your API key

## Getting Your API Key

1. Go to https://platform.openai.com/api-keys
2. Sign in to your OpenAI account
3. Click "Create new secret key"
4. Copy the key and save it securely
5. Add it to your `.env` file

## Charting Configuration (Alpha Vantage)

To enable the live stock price charts, you need an Alpha Vantage API key. This service provides free financial data APIs.

1. Go to https://www.alphavantage.co/support/#api-key
2. Fill out the form (it's free and instant)
3. Copy your API Key
4. Add it to your `.env` file:

```
ALPHAVANTAGE_API_KEY=your_alpha_vantage_key_here
```

If you do not provide this key, the charts will simply show "No Data" or be hidden, but the rest of the application will work normally.

## Optional Configuration

You can also set these optional variables in your `.env` file:

```
# Use a different model (default is gpt-4o-mini)
OPENAI_MODEL=gpt-4o-mini

# Enable API call tracing
OPENAI_ENABLE_TRACING=true
```

## Verifying Setup

After setting up your API key, test it:

```bash
# Test CLI version
python -m examples.financial_research_agent.main

# Test Web GUI
python -m examples.financial_research_agent.app
```

If configured correctly, you should see the agent start without API key errors.
