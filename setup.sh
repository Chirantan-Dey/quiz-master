#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if running in WSL
is_wsl() {
    if [ -f /proc/version ]; then
        if grep -qi microsoft /proc/version; then
            return 0
        fi
    fi
    return 1
}

# Function to check if a command exists
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}Error: $1 is not installed${NC}"
        return 1
    fi
    return 0
}

# Function to create necessary directories
create_directories() {
    echo -e "${YELLOW}Creating directory structure...${NC}"
    
    # Create main directories
    mkdir -p \
        instance \
        logs \
        static/charts/admin \
        static/charts/user \
        static/components \
        static/pages \
        static/utils \
        templates/emails \
        tests/unit \
        tests/integration
        
    echo -e "${GREEN}Directory structure created${NC}"
}

# Function to setup environment file
setup_env() {
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}Creating .env file...${NC}"
        cat > .env << EOL
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
DATABASE_URL=sqlite:///instance/data.db
REDIS_URL=redis://localhost:6379/0
MAIL_SERVER=localhost
MAIL_PORT=1025
MAIL_USE_TLS=False
MAIL_USE_SSL=False
MAIL_USERNAME=null
MAIL_PASSWORD=null
EOL
        echo -e "${GREEN}.env file created${NC}"
    else
        echo -e "${YELLOW}.env file already exists${NC}"
    fi
}

# Function to setup pre-commit hooks
setup_git_hooks() {
    echo -e "${YELLOW}Setting up git hooks...${NC}"
    if [ -d ".git" ]; then
        pre-commit install
        echo -e "${GREEN}Git hooks installed${NC}"
    else
        echo -e "${RED}Not a git repository${NC}"
    fi
}

# Main setup script
echo -e "${YELLOW}Setting up Quiz Master environment...${NC}"

# Check Python version
if ! check_command python3; then
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check Redis
if ! check_command redis-server; then
    echo "Please install Redis server"
    exit 1
fi

# Create directories
create_directories

# Setup environment file
setup_env

# Setup Python virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
if check_command pip; then
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo -e "${RED}pip not found in virtual environment${NC}"
    exit 1
fi

# Install development tools
echo -e "${YELLOW}Installing development tools...${NC}"
pip install black flake8 mypy pytest pre-commit

# Setup git hooks
setup_git_hooks

# Install MailHog in WSL if needed
if is_wsl; then
    echo -e "${YELLOW}Setting up MailHog in WSL...${NC}"
    if ! command -v mailhog &> /dev/null; then
        echo "Installing MailHog..."
        sudo apt-get update
        sudo apt-get install -y mailhog
    else
        echo -e "${GREEN}MailHog is already installed${NC}"
    fi
else
    echo -e "${YELLOW}NOTE: Please ensure MailHog is installed in your WSL environment:${NC}"
    echo "1. Open WSL terminal"
    echo "2. Run: sudo apt-get update && sudo apt-get install -y mailhog"
fi

# Initialize database
echo -e "${YELLOW}Initializing database...${NC}"
export FLASK_APP=app.py
flask db upgrade
python create_initial_data.py

# Verify services
echo -e "${YELLOW}Verifying services...${NC}"

# Check Redis
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}Redis is running${NC}"
else
    echo -e "${RED}Redis is not running${NC}"
fi

# Check MailHog
if nc -z localhost 1025 2>/dev/null; then
    echo -e "${GREEN}MailHog SMTP is accessible${NC}"
else
    echo -e "${RED}MailHog SMTP is not accessible${NC}"
fi

echo -e "\n${GREEN}Setup complete!${NC}"
echo -e "${YELLOW}You can now:${NC}"
echo "1. Start the application: ./run.sh"
echo "2. Start in development mode: ./run.sh --dev"
echo "3. Run tests: pytest"
echo "4. Format code: black ."
echo "5. Check types: mypy ."
echo -e "\n${YELLOW}Development URLs:${NC}"
echo "- Application: http://localhost:5000"
echo "- MailHog UI: http://localhost:8025"

# Cleanup
deactivate