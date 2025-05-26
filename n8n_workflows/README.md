# n8n Workflow Setup for Claude Desktop Automation

This directory contains n8n workflow configurations for automating Claude Desktop interactions.

## Prerequisites

1. Docker and Docker Compose installed
2. Claude Desktop application running on your host machine
3. Required Python scripts and APIs running locally

## Setup Instructions

### 1. Start Required Services

First, ensure the following services are running on your host machine:

```bash
# Start Claude Desktop Automation API (Terminal 1)
python claude_desktop_api_server.py --port 5001

# Start Dashboard API (Terminal 2)
python dashboard_api.py --port 5002
```

### 2. Start n8n with Docker Compose

```bash
# From the project root directory
docker-compose up -d
```

This will start n8n on http://localhost:5678

### 3. Access n8n Interface

1. Open your browser and go to http://localhost:5678
2. Create an account or login if you already have one
3. You'll see the n8n workflow editor

### 4. Import the Workflow

1. In n8n, click on the menu (three lines) in the top left
2. Select "Import from File" 
3. Choose `claude_automation_workflow.json` from this directory
4. The workflow will be imported and displayed

### 5. Configure the Workflow

Before running the workflow, you need to configure:

1. **API Endpoints**: The workflow uses `host.docker.internal` to access host services from Docker. On Linux, you may need to use your actual host IP instead.

2. **Project Name**: Edit the "Prepare Claude Prompt" node to set your Claude project name

3. **Credentials** (if using notifications):
   - Click on the Slack node (or other notification nodes)
   - Add your credentials

### 6. Test the Workflow

1. Click "Execute Workflow" to run it manually
2. Monitor the execution in real-time
3. Check logs in the execution history

## Workflow Overview

The workflow performs the following steps:

1. **Get Pending Tasks**: Queries the Dashboard API for pending tasks
2. **Process Tasks**: Extracts task information for processing
3. **Get Task Details**: Retrieves detailed task information using Task Master
4. **Prepare Claude Prompt**: Formats the task into a prompt for Claude
5. **Trigger Claude Automation**: Sends the prompt to Claude Desktop via API
6. **Check Status**: Monitors the automation status with retry logic
7. **Run Tests**: Executes tests after successful implementation
8. **Update Status**: Updates the task status in Task Master
9. **Send Notification**: Optionally sends success/failure notifications

## Customization

### Adding Token Management

To add token management checks before triggering Claude:

1. Add an HTTP Request node before "Trigger Claude Automation"
2. Set it to GET `http://host.docker.internal:5001/api/automation/tokens`
3. Add an IF node to check if token usage is above threshold
4. Route to a "Create New Chat" flow if needed

### Parallel Processing

To process multiple tasks in parallel:

1. Add a "Split In Batches" node after "Process Tasks"
2. Set batch size according to your needs
3. Connect to parallel execution branches

### Error Handling

The workflow includes basic error handling, but you can enhance it by:

1. Adding error trigger nodes
2. Implementing retry logic with exponential backoff
3. Sending error notifications to different channels

## Scheduling

To run the workflow on a schedule:

1. Replace the "Start" node with a "Cron" node
2. Configure the schedule (e.g., every 30 minutes)
3. Save and activate the workflow

## Monitoring

### Execution History
- Click on "Executions" in the left sidebar to see past runs
- View detailed logs for each execution

### Real-time Monitoring
- Use the Dashboard API endpoints to monitor task progress
- Stream logs using the `/api/logs/stream` endpoint

## Troubleshooting

### Common Issues

1. **"Connection refused" errors**
   - Ensure all required services are running
   - Check if ports 5001 and 5002 are accessible
   - On Linux, use actual host IP instead of `host.docker.internal`

2. **"Task not found" errors**
   - Verify tasks.json file exists and has valid data
   - Check Task Master MCP is properly configured

3. **Claude automation failures**
   - Ensure Claude Desktop is running and accessible
   - Check if required button images are captured
   - Verify project name matches exactly

### Debug Mode

To enable debug logging:

1. Set environment variable: `N8N_LOG_LEVEL=debug`
2. Check Docker logs: `docker-compose logs -f n8n`

## Advanced Features

### Context Preservation

The workflow can be enhanced to preserve context across Claude conversations:

1. Add a "Get Context Summary" node that calls the orchestrator
2. Pass the context summary to the automation API
3. Handle token limit warnings proactively

### Dynamic Complexity Scoring

Implement task complexity scoring:

1. Add a Code node to analyze task description
2. Set complexity score based on keywords or patterns
3. Pass to Claude automation for dynamic timeout adjustment

## Security Considerations

1. Never commit sensitive API keys to version control
2. Use n8n's built-in credential management
3. Restrict API access to localhost only
4. Use environment variables for configuration

## Next Steps

1. Customize the workflow for your specific use case
2. Add more sophisticated error handling
3. Integrate with your existing CI/CD pipeline
4. Set up monitoring and alerting