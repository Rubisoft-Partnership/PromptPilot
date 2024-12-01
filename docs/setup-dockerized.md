Quick Guide: Running Your Container with Docker Compose

Follow these steps to get your container up and running using Docker Compose.

Step 1: Create a .env File

Create a .env file in your project directory with the following content:

# .env

# Google Cloud Configuration
GCLOUD_PROJECT=your-google-cloud-project
GCLOUD_REGION=your-region
GCLOUD_INSTANCE=your-cloud-sql-instance
GCLOUD_CONNECTION_NAME=${GCLOUD_PROJECT}:${GCLOUD_REGION}:${GCLOUD_INSTANCE}

# Cloud SQL Auth Proxy Configuration
CLOUD_SQL_PROXY_VERSION=2.5.0
CLOUD_SQL_PROXY_CREDENTIALS=/secrets/cloudsql/credentials.json
CLOUD_SQL_PROXY_CREDENTIALS_PATH=./secrets/cloudsql
CLOUD_SQL_PROXY_CREDENTIALS_VOLUME=/secrets/cloudsql
CLOUD_SQL_PROXY_PORT=5432

# Database Configuration
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_NAME=your-db-name
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@cloud_sql_proxy:${CLOUD_SQL_PROXY_PORT}/${DB_NAME}

# Authentication Configuration
LANGFUSE_PORT=3000
NEXTAUTH_URL=http://localhost:${LANGFUSE_PORT}
NEXTAUTH_SECRET=your-nextauth-secret

# Security Keys
SALT=your-salt-value
ENCRYPTION_KEY=your-encryption-key

# Optional Settings
HOSTNAME=0.0.0.0
LANGFUSE_CSP_ENFORCE_HTTPS=false
LANGFUSE_IMAGE_VERSION=2

# Ollama Configuration
LLM_ENDPOINT=http://ollama:11434/v1
OLLAMA_HOST=http://ollama:11434

# LangFuse API Keys
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=http://langfuse:${LANGFUSE_PORT}
LANGFUSE_DEBUG=False

Please replace the placeholders (e.g., your-google-cloud-project, your-db-user) with your actual configuration values.

Step 2: Verify Your docker-compose.yml File

Ensure your docker-compose.yml file is set up to use the variables from your .env file. It should reference the variables appropriately using the ${VARIABLE_NAME} syntax.

Step 3: Run Docker Compose

In your terminal, navigate to the directory containing your docker-compose.yml file and run:

docker-compose up --build
