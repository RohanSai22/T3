# Novah Backend

LangGraph-based backend service for the Novah AI platform.

## Features

- **LangGraph Integration**: Powerful workflow orchestration with LangGraph
- **Multi-Tool Support**: Web search, financial data, and code execution capabilities
- **FastAPI Server**: RESTful API endpoints for frontend integration
- **AI Agent System**: Intelligent conversational agents with tool access

## Setup

1. Install dependencies:

   ```bash
   poetry install
   ```

2. Set up environment variables:

   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. Run the development server:
   ```bash
   langgraph dev
   ```

## Tools Available

- **Web Search**: Real-time web search capabilities
- **Financial Data**: Access to financial market information
- **Code Execution**: Safe code execution environment
- **File Operations**: File reading and writing capabilities

## Testing

Run integration tests:

```bash
python test_integration.py
```

Run API tests:

```bash
pytest test_api.py
```

## Development

The backend uses LangGraph for workflow management and includes:

- Agent configuration and state management
- Tool registration and execution
- Message processing and routing
- Error handling and validation
