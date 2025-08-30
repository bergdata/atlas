# Atlas CRM Integration

A comprehensive Python application for integrating with the Atlas CRM system, featuring task management and token-based authentication.

## Features

- 🔐 **OAuth2 Token Management**: Automated token generation and refresh using PKCE flow
- ✅ **Task Management**: CRM task retrieval and management
- 🎯 **Destination Configuration**: Configurable destination-specific settings and employee assignments
- 👥 **User Management**: CRM user operations and team assignments
- 🏷️ **Label Management**: CRM label operations and management
- 📊 **Data Processing**: Pandas-based data manipulation and analysis
- 🌐 **Multi-Environment Support**: Staging and production environment configurations
- 📝 **Comprehensive Logging**: Detailed logging for debugging and monitoring

## Project Structure

```
Atlas/
├── .gitignore              # Git ignore rules
├── requirements.txt         # Python dependencies
├── config.py               # Configuration management
├── token_manager.py        # OAuth2 token management
├── crm_mail.py            # CRM mail API integration
├── crm_task.py            # CRM task API integration
├── Support_functions/      # CRM support modules
│   ├── crm_destination.py # Destination management
│   ├── crm_entity.py      # Entity management
│   ├── crm_label.py       # Label management
│   ├── crm_pax.py         # Passenger management
│   ├── crm_team.py        # Team management
│   └── crm_user.py        # User management
├── Functions/              # Additional function modules
│   ├── assign_user.py     # User assignment functionality
│   └── mark_email_done.py # Email completion marking
├── output/                 # Generated output files
├── tokens/                 # Token storage directory
└── README.md              # This file
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the Atlas directory with your configuration:

```env
# Environment Configuration
ENVIRONMENT=staging  # or production

# Atlas API Credentials
ATLAS_USERNAME=your_username
ATLAS_PASSWORD=your_password

# API URLs (optional - defaults provided)
STAGING_AUTH_URL=https://staging-atlas-auth.rickshawnetwork.com
STAGING_API_URL=https://staging-atlas-api.rickshawnetwork.com
STAGING_REDIRECT_URI=https://staging-atlas.rickshawnetwork.com

PRODUCTION_AUTH_URL=https://atlas-auth.rickshawnetwork.com
PRODUCTION_API_URL=https://atlas-api.rickshawnetwork.com
PRODUCTION_REDIRECT_URI=https://atlas.rickshawnetwork.com

# Client Configuration
CLIENT_ID=Atlas_App

# Destination Configuration
DESTINATION_IDS=111,93
ENTITY_ID=1

# Telegram Bot Configuration (optional)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here  # Will be auto-populated after setup
```

### 4. Telegram Bot Setup (Optional)

If you want to receive notifications on your phone via Telegram:

1. **Create a Telegram Bot**:
   - Message [@BotFather](https://t.me/botfather) on Telegram
   - Create a new bot and get your bot token
   - Add the token to your `.env` file

2. **Set up Chat ID** (one-time setup):
   ```bash
   # Option 1: Automatic setup (recommended)
   python setup_telegram.py
   
   # Option 2: Manual setup (if you know your chat ID)
   python set_chat_id.py 123456789
   ```

3. **How it works**:
   - The chat ID is automatically saved to `config.py` after first use
   - Future runs will use the saved chat ID without API calls
   - No more "No chat ID found" warnings!

### 3. Token Setup

The application uses OAuth2 PKCE flow for authentication. Tokens are automatically generated and stored in the `tokens/` directory.

## Usage

### CRM Mail Retrieval

```python
from crm_mail import make_api_request
from token_manager import TokenManager

token_manager = TokenManager()
data = token_manager.api_request_with_token_refresh(make_api_request)
print(data)
```

### CRM Task Retrieval

```python
from crm_task import make_api_request
from token_manager import TokenManager

token_manager = TokenManager()
data = token_manager.api_request_with_token_refresh(make_api_request)
print(data)
```

### CRM Support Functions

#### User Management

```python
from Support_functions.crm_user import make_api_request
from token_manager import TokenManager

token_manager = TokenManager()
users = token_manager.api_request_with_token_refresh(make_api_request)
print(users)
```

#### Destination Management

```python
from Support_functions.crm_destination import make_api_request
from token_manager import TokenManager

token_manager = TokenManager()
destinations = token_manager.api_request_with_token_refresh(make_api_request)
print(destinations)
```

#### Team Management

```python
from Support_functions.crm_team import make_api_request
from token_manager import TokenManager

token_manager = TokenManager()
teams = token_manager.api_request_with_token_refresh(make_api_request)
print(teams)
```

#### Entity Management

```python
from Support_functions.crm_entity import make_api_request
from token_manager import TokenManager

token_manager = TokenManager()
entities = token_manager.api_request_with_token_refresh(make_api_request)
print(entities)
```

#### Label Management

```python
from Support_functions.crm_label import make_api_request
from token_manager import TokenManager

token_manager = TokenManager()
labels = token_manager.api_request_with_token_refresh(make_api_request)
print(labels)
```

#### Passenger Management

```python
from Support_functions.crm_pax import make_api_request
from token_manager import TokenManager

token_manager = TokenManager()
passengers = token_manager.api_request_with_token_refresh(make_api_request)
print(passengers)
```

### Additional Functions

#### User Assignment

```python
from Functions.assign_user import assign_user_to_task

# Assign a user to a specific task
result = assign_user_to_task(task_id, user_id)
print(result)
```

#### Mark Email as Done

```python
from Functions.mark_email_done import mark_email_complete

# Mark an email as completed
result = mark_email_complete(email_id)
print(result)
```

### Token Management

```python
from token_manager import TokenManager

token_manager = TokenManager()

# Generate new token
new_token = token_manager._generate_new_token()

# Get active token
active_token = token_manager.get_active_token_value()

# List all tokens
tokens = token_manager.list_tokens()
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment (staging/production) | `staging` |
| `ATLAS_USERNAME` | Atlas username | Required |
| `ATLAS_PASSWORD` | Atlas password | Required |
| `CLIENT_ID` | OAuth client ID | `Atlas_App` |
| `DESTINATION_IDS` | Comma-separated destination IDs | `111,93` |
| `ENTITY_ID` | Entity ID for API requests | `1` |

### Destination Configuration

The application supports destination-specific configurations in `config.py`:

```python
DESTINATION_CONFIGS = {
    "vietnam": {
        "destination_ids": ["93", "111"],
        "assigned_users": ["Charona", "Anne-Karlijn"],
        "base_user": "Charona",
        "employee_keywords": {
            "Charona": ["charona"],
            "Anne-Karlijn": ["anne-karlijn"]
        }
    }
}
```

## Features

### Task Management

- **Task Retrieval**: Fetches active tasks from CRM
- **Deadline Sorting**: Sorts tasks by deadline date
- **Destination Filtering**: Filters tasks by destination IDs
- **Status Tracking**: Tracks task completion status

### CRM Support Functions

- **User Management**: Complete user operations and team assignments
- **Destination Management**: Destination-specific configurations and operations
- **Team Management**: Team operations and member management
- **Entity Management**: Entity operations and configurations
- **Label Management**: Label operations and categorization
- **Passenger Management**: Passenger data operations and management

### Additional Functions

- **User Assignment**: Automated user assignment to tasks
- **Email Completion**: Mark emails as completed in the system

### Token Management

- **OAuth2 PKCE**: Secure token generation using PKCE flow
- **Automatic Refresh**: Handles token refresh automatically
- **Usage Tracking**: Tracks token usage and success/failure rates
- **Token Storage**: Persistent token storage in JSON format
- **Multi-Environment**: Supports different environments with separate token storage

## Dependencies

- `requests==2.32.3` - HTTP requests
- `pandas==2.2.3` - Data manipulation
- `playwright==1.47.0` - Browser automation for OAuth
- `python-dotenv==1.0.1` - Environment variable management
- `beautifulsoup4==4.12.3` - HTML parsing

## Deployment to EC2

### 1. Prepare Your Code

```bash
# Create a deployment package
tar -czf atlas-deployment.tar.gz Atlas/
```

### 2. Upload to EC2

```bash
# Using SCP
scp -i your-key.pem atlas-deployment.tar.gz ec2-user@your-ec2-instance:/home/ec2-user/

# Or using AWS CLI
aws s3 cp atlas-deployment.tar.gz s3://your-bucket/
```

### 3. Setup on EC2

```bash
# Connect to your EC2 instance
ssh -i your-key.pem ec2-user@your-ec2-instance

# Extract and setup
tar -xzf atlas-deployment.tar.gz
cd Atlas

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Create and configure .env file
cp env.example .env
# Edit .env with your production settings

# Test the setup
python crm_task.py
```

### 4. Running as a Service (Optional)

Create a systemd service for automatic startup:

```bash
sudo nano /etc/systemd/system/atlas-crm.service
```

Add the following content:

```ini
[Unit]
Description=Atlas CRM Integration
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/Atlas
ExecStart=/usr/bin/python3 /home/ec2-user/Atlas/crm_task.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable atlas-crm
sudo systemctl start atlas-crm
```

## Security Best Practices

1. **Never commit `.env` files** - They're already in `.gitignore`
2. **Use IAM roles** on EC2 for AWS API access
3. **Rotate credentials** regularly
4. **Use HTTPS** for all API communications
5. **Monitor logs** for suspicious activity
6. **Secure token storage** - Tokens are stored locally in `tokens/` directory

## Troubleshooting

### Common Issues

1. **Missing Dependencies**: Run `pip install -r requirements.txt`
2. **Playwright Issues**: Run `playwright install chromium`
3. **Configuration Errors**: Check your `.env` file format
4. **Network Issues**: Verify your EC2 security groups allow outbound HTTPS
5. **Token Generation**: Ensure credentials are correct in `.env` file

### Debug Mode

Enable debug logging by modifying the logging configuration in the respective modules.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License. 