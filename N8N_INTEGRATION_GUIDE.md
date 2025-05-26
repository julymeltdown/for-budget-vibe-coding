# n8n Integration Guide for Claude Desktop Automation

## Overview

This guide explains how to use n8n to automate Claude Desktop interactions for software development tasks. The integration includes token management, context preservation, and comprehensive monitoring.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│     n8n         │────▶│  Dashboard API   │────▶│   tasks.json    │
│  (Orchestrator) │     │   (Port 5002)    │     │ progress.json   │
└────────┬────────┘     └──────────────────┘     └─────────────────┘
         │
         │ HTTP
         ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Claude API     │────▶│ Claude Desktop   │────▶│  Task Master    │
│  (Port 5001)    │     │  Automation      │     │     MCP         │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Quick Start

### 1. Prerequisites

- Docker Desktop installed and running
- Claude Desktop application installed
- Python 3.8+ with required packages installed
- Task Master MCP configured

### 2. Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs n8n_data shared_workspace assets
```

### 3. Configuration

Create or update `.env` file:

```bash
# n8n Configuration
N8N_ENCRYPTION_KEY=your_secure_key_here_change_this

# API Configuration
CLAUDE_API_HOST=host.docker.internal
CLAUDE_API_PORT=5001
DASHBOARD_API_HOST=host.docker.internal
DASHBOARD_API_PORT=5002
```

### 4. Start Services

```bash
# Start all services
./start_automation.sh

# Services will be available at:
# - n8n: http://localhost:5678
# - Claude API: http://localhost:5001
# - Dashboard API: http://localhost:5002
```

### 5. Import n8n Workflow

1. Open n8n at http://localhost:5678
2. Click menu → Import from File
3. Select `n8n_workflows/claude_automation_workflow.json`
4. Configure project name in workflow nodes

## Key Features

### Token Management

The integration automatically manages Claude conversation tokens:

- **Proactive New Chat Creation**: Creates new chats before hitting token limits
- **Token Tracking**: Monitors token usage in real-time
- **Context Preservation**: Maintains context across chat transitions

### Context Summary Management

- **Automatic Summarization**: Creates concise summaries of ongoing work
- **Persistent Storage**: Saves context between runs
- **Smart Truncation**: Maintains relevant context within size limits

### Error Recovery

- **Automatic Retries**: Handles transient failures
- **Usage Limit Handling**: Detects and manages rate limits
- **Comprehensive Logging**: Detailed logs for debugging

## API Endpoints

### Claude Automation API (Port 5001)

- `POST /api/automation/run` - Execute automation
- `GET /api/automation/status/{task_id}` - Check task status
- `GET /api/automation/tokens` - Get token usage
- `POST /api/automation/create_new_chat` - Force new chat

### Dashboard API (Port 5002)

- `GET /api/tasks` - List all tasks
- `GET /api/progress/current` - Current progress
- `GET /api/logs/stream` - Real-time log streaming
- `GET /api/tests/latest` - Latest test results

## Workflow Customization

### Adding Complexity Scoring

```javascript
// Add to "Prepare Claude Prompt" node
const complexity = analyzeTaskComplexity($json.task_description);
return {
  ...previous,
  task_complexity: complexity
};
```

### Parallel Task Processing

1. Add "Split in Batches" node after task retrieval
2. Configure batch size (recommended: 2-3)
3. Connect to parallel branches

### Custom Notifications

1. Add notification nodes (Slack, Email, etc.)
2. Configure credentials in n8n
3. Connect to success/failure branches

## Monitoring

### Real-time Dashboard

Access the monitoring dashboard:

```bash
# View current progress
curl http://localhost:5002/api/progress/current | jq

# Stream logs
curl http://localhost:5002/api/logs/stream
```

### n8n Execution History

1. Click "Executions" in n8n sidebar
2. View detailed logs for each run
3. Debug failed executions

## Troubleshooting

### Common Issues

#### "Connection refused" errors
```bash
# Check if services are running
ps aux | grep -E "claude_desktop_api|dashboard_api"
docker ps

# Check logs
tail -f logs/claude_api.log
tail -f logs/dashboard_api.log
docker-compose logs -f n8n
```

#### Token limit errors
```bash
# Check current token usage
curl http://localhost:5001/api/automation/tokens | jq

# Force new chat
curl -X POST http://localhost:5001/api/automation/create_new_chat \
  -H "Content-Type: application/json" \
  -d '{"project_name": "your-project"}'
```

#### Claude window not found
```bash
# Ensure Claude Desktop is running
# Check window title configuration
grep window_title claude_desktop_config.json
```

### Debug Mode

Enable detailed logging:

```bash
# Set debug environment variables
export N8N_LOG_LEVEL=debug
export FLASK_DEBUG=1

# Restart services
./stop_automation.sh
./start_automation.sh
```

## Best Practices

### 1. Task Organization

- Keep tasks focused and specific
- Use clear task IDs and descriptions
- Group related subtasks together

### 2. Token Management

- Monitor token usage regularly
- Set conservative thresholds (70-80%)
- Include context summaries for continuity

### 3. Error Handling

- Implement proper retry logic
- Log all errors comprehensively
- Set up alerting for critical failures

### 4. Performance

- Process tasks in small batches
- Use appropriate timeouts
- Monitor system resources

## Advanced Configuration

### Custom Token Limits

Update `claude_desktop_config.json`:

```json
{
  "max_tokens_per_conversation": 90000,
  "token_warning_threshold": 0.75,
  "interaction_count_threshold": 15
}
```

### Dynamic Timeouts

Configure based on task complexity:

```json
{
  "response_max_wait_s": 300,
  "max_wait_for_complex_tasks_s": 1800,
  "activity_timeout_extension_s": 300
}
```

## Security Considerations

1. **API Security**
   - Run APIs on localhost only
   - Use strong encryption keys
   - Implement authentication for production

2. **Data Protection**
   - Encrypt sensitive configuration
   - Secure log files
   - Regular backup of progress data

3. **Access Control**
   - Restrict n8n access
   - Use environment variables for secrets
   - Audit API usage

## Maintenance

### Daily Tasks

- Check log files for errors
- Monitor token usage trends
- Verify task completion rates

### Weekly Tasks

- Clean up old log files
- Review failed tasks
- Update context summaries

### Monthly Tasks

- Analyze performance metrics
- Optimize workflow efficiency
- Update dependencies

## Support

For issues or questions:

1. Check logs in `logs/` directory
2. Review n8n execution history
3. Consult the troubleshooting section
4. Submit issues with detailed logs

## Next Steps

1. Customize workflow for your needs
2. Integrate with CI/CD pipeline
3. Set up monitoring alerts
4. Scale with multiple workers