To use this template for your own project:

1. Create a new repository using this template by following GitHub's [template repository guide](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template#creating-a-repository-from-a-template)
2. Clone your new repository and navigate to it: `cd your-project-name`
3. Make sure you have Python 3.12 installed

Once completed, proceed to the [Setup](#setup) section below.

## Setup

### Installing Required Tools

#### 1. uv
uv is used to manage Python dependencies in the backend. Install uv by following the [official installation guide](https://docs.astral.sh/uv/getting-started/installation/).

#### 2. Node.js, npm, and pnpm
To run the frontend, ensure Node.js and npm are installed. Follow the [Node.js installation guide](https://nodejs.org/en/download/).
After that, install pnpm by running:
```bash
npm install -g pnpm
```

#### 3. Docker (Optional)
Docker is optional for this project. The backend now uses SQLite, which doesn't require Docker. However, Docker can still be used if you prefer containerized development. Follow the appropriate installation guide:

- [Install Docker for Mac](https://docs.docker.com/docker-for-mac/install/)
- [Install Docker for Windows](https://docs.docker.com/docker-for-windows/install/)
- [Get Docker CE for Linux](https://docs.docker.com/install/linux/docker-ce/)

#### 4. Docker Compose (Optional)
Only needed if you plan to use Docker. Refer to the [Docker Compose installation guide](https://docs.docker.com/compose/install/).

### Setting Up Environment Variables

**Backend (`fastapi_backend/.env`):**

Copy the `.env.example` files to `.env` and update the variables with your own values.
   ```bash
   cd fastapi_backend && cp .env.example .env
   ```
You will only need to update the secret keys. You can use the following command to generate a new secret key:
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```

- The DATABASE now uses SQLite (sqlite+aiosqlite:///./app.db) which doesn't require Docker or external services.

- The MAIL, OPENAPI, CORS, and FRONTEND_URL settings are ready to use locally.

- The OPENAPI_URL setting is commented out. Uncommenting it will hide the /docs and openapi.json URLs, which is ideal for production.

You can check the .env.example file for more information about the variables.

**Frontend (`nextjs-frontend/.env.local`):**

Copy the `.env.example` files to `.env.local`. These values are unlikely to change, so you can leave them as they are.
   ```bash
   cd nextjs-frontend && cp .env.example .env.local
   ```

### Build the project (without Docker):
To set the project environment locally, use the following commands:

#### Backend

Navigate to the `fastapi_backend` directory and run:
   ```bash
   uv sync
   ```

After installing dependencies, set up the SQLite database by running migrations:
   ```bash
   make generate-migration migration_name="Initial schema"
   make migrate-db
   ```

This will create the SQLite database file (`app.db`) with all necessary tables.

#### Frontend
Navigate to the `nextjs-frontend` directory and run:
   ```bash
   pnpm install
   ```

### Build the project (with Docker):

Build the backend and frontend containers:
   ```bash
   make docker-build
   ```

## Running the Application

**If you are not using Docker:**

Start the FastAPI server:
   ```bash
   make start-backend
   ```

Start the Next.js development server:
   ```bash
   make start-frontend
   ```

**If you are using Docker:**

Start the FastAPI server container:
   ```bash
   make docker-start-backend
   ```
Start the Next.js development server container:
   ```bash
   make docker-start-frontend
   ```

- **Backend**: Access the API at `http://localhost:8000`.
- **Frontend**: Access the web application at `http://localhost:3000`.

## Important Considerations
- **Environment Variables**: Ensure your `.env` files are up-to-date.
- **Database Setup**: The project now uses SQLite by default, which doesn't require Docker or external database services. The database file (`app.db`) will be created automatically when you run migrations.
- **Docker**: Docker is now optional. You can run the entire project locally with just `uv` and `pnpm`, or use Docker if you prefer containerized development.
- **Database File**: The SQLite database file (`app.db` and `test.db`) will be created in the `fastapi_backend` directory. Make sure to add these to `.gitignore` if not already present.
