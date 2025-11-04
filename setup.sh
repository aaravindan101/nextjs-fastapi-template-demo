#!/bin/bash

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${BLUE}===================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}!${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Clear screen and show banner
clear
print_header "Next.js FastAPI Template - Setup Script"

# ============================================
# STEP 1: Check Prerequisites
# ============================================
print_header "Step 1: Checking Prerequisites"

PREREQUISITES_MET=true

# Check for uv
print_info "Checking for uv..."
if command_exists uv; then
    UV_VERSION=$(uv --version)
    print_success "uv is installed ($UV_VERSION)"
else
    print_error "uv is not installed"
    echo -e "   ${YELLOW}Install uv from: https://docs.astral.sh/uv/getting-started/installation/${NC}"
    PREREQUISITES_MET=false
fi

# Check for Node.js
print_info "Checking for Node.js..."
if command_exists node; then
    NODE_VERSION=$(node --version)
    print_success "Node.js is installed ($NODE_VERSION)"
else
    print_error "Node.js is not installed"
    echo -e "   ${YELLOW}Install Node.js from: https://nodejs.org/en/download/${NC}"
    PREREQUISITES_MET=false
fi

# Check for pnpm
print_info "Checking for pnpm..."
if command_exists pnpm; then
    PNPM_VERSION=$(pnpm --version)
    print_success "pnpm is installed ($PNPM_VERSION)"
else
    print_error "pnpm is not installed"
    echo -e "   ${YELLOW}Install pnpm by running: npm install -g pnpm${NC}"
    PREREQUISITES_MET=false
fi

# Exit if prerequisites are not met
if [ "$PREREQUISITES_MET" = false ]; then
    print_error "\nPrerequisites not met. Please install the required tools and run this script again."
    exit 1
fi

print_success "\nAll prerequisites are installed!"

# ============================================
# STEP 2: Setup Backend
# ============================================
print_header "Step 2: Setting Up Backend"

cd fastapi_backend

# Create .env file if it doesn't exist
print_info "Configuring environment variables..."
if [ ! -f .env ]; then
    cp .env.example .env
    print_success "Created .env file from .env.example"

    # Generate secret keys
    print_info "Generating secret keys..."
    ACCESS_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    RESET_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    VERIFICATION_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")

    # Update .env with generated secrets
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/ACCESS_SECRET_KEY=.*/ACCESS_SECRET_KEY=$ACCESS_SECRET/" .env
        sed -i '' "s/RESET_PASSWORD_SECRET_KEY=.*/RESET_PASSWORD_SECRET_KEY=$RESET_SECRET/" .env
        sed -i '' "s/VERIFICATION_SECRET_KEY=.*/VERIFICATION_SECRET_KEY=$VERIFICATION_SECRET/" .env
    else
        # Linux
        sed -i "s/ACCESS_SECRET_KEY=.*/ACCESS_SECRET_KEY=$ACCESS_SECRET/" .env
        sed -i "s/RESET_PASSWORD_SECRET_KEY=.*/RESET_PASSWORD_SECRET_KEY=$RESET_SECRET/" .env
        sed -i "s/VERIFICATION_SECRET_KEY=.*/VERIFICATION_SECRET_KEY=$VERIFICATION_SECRET/" .env
    fi

    print_success "Generated and saved secret keys"
else
    print_warning ".env file already exists, skipping creation"
fi

# Install backend dependencies
print_info "Installing backend dependencies with uv..."
uv sync
print_success "Backend dependencies installed"

# Delete existing database if it exists
if [ -f app.db ]; then
    print_warning "Removing existing database..."
    rm -f app.db
fi

# Generate and run migrations
print_info "Setting up database..."

# Check if migrations exist (ignore __pycache__)
if [ -z "$(ls -A alembic_migrations/versions/*.py 2>/dev/null)" ]; then
    print_info "Generating initial migration..."
    uv run alembic revision --autogenerate -m "Initial schema"
    print_success "Initial migration created"
else
    print_success "Migrations already exist"
fi

print_info "Running database migrations..."
uv run alembic upgrade head
print_success "Database migrations completed"

# Seed database with test user
print_info "Seeding database with test user..."
PYTHONPATH=. uv run python3 commands/seed_db.py
print_success "Database seeded successfully"

# Generate OpenAPI schema
print_info "Generating OpenAPI schema..."
PYTHONPATH=. uv run python3 commands/generate_openapi_schema.py
print_success "OpenAPI schema generated"

cd ..

# ============================================
# STEP 3: Setup Frontend
# ============================================
print_header "Step 3: Setting Up Frontend"

cd nextjs-frontend

# Create .env.local file if it doesn't exist
print_info "Configuring frontend environment variables..."
if [ ! -f .env.local ]; then
    cp .env.example .env.local
    print_success "Created .env.local file from .env.example"
else
    print_warning ".env.local file already exists, skipping creation"
fi

# Install frontend dependencies
print_info "Installing frontend dependencies with pnpm..."
pnpm install
print_success "Frontend dependencies installed"

# Generate TypeScript API client
print_info "Generating TypeScript API client..."
pnpm run generate-client
print_success "TypeScript API client generated"

cd ..

# ============================================
# FINAL MESSAGE
# ============================================
print_header "Setup Complete!"

echo -e "${GREEN}✓ Backend is ready${NC}"
echo -e "${GREEN}✓ Frontend is ready${NC}"
echo -e "${GREEN}✓ Database is initialized${NC}"
echo -e "${GREEN}✓ Test user created${NC}"
echo -e "${GREEN}✓ OpenAPI schema is generated${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "  1. Start the backend:  ${YELLOW}make start-backend${NC}"
echo -e "  2. Start the frontend: ${YELLOW}make start-frontend${NC}"
echo ""
echo -e "${BLUE}Access your application:${NC}"
echo -e "  • Backend API:  ${YELLOW}http://localhost:8000${NC}"
echo -e "  • API Docs:     ${YELLOW}http://localhost:8000/docs${NC}"
echo -e "  • Frontend:     ${YELLOW}http://localhost:3000${NC}"
echo ""
echo -e "${BLUE}Test user credentials:${NC}"
echo -e "  • Email:    ${YELLOW}test@example.com${NC}"
echo -e "  • Password: ${YELLOW}TestPassword123#${NC}"
echo ""
echo -e "${BLUE}Verify your setup (optional):${NC}"
echo -e "  Run setup tests: ${YELLOW}make setup-test${NC}"
echo -e "  Or run all tests: ${YELLOW}make test-backend${NC}"
echo ""
print_success "Happy coding! 🚀"
echo ""
