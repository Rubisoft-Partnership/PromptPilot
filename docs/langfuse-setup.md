# Set Up LangFuse

1. Prepare Environment Variables

You need to set up the necessary environment variables for LangFuse. Create a .env file in your project directory to store these variables securely.

Create a .env File:

touch .env

Edit the .env File:

Add the following content to your .env file:

# Database Configuration
DATABASE_URL=postgresql://langfuse_user:<DB_PASSWORD>@127.0.0.1:5432/langfuse_db

# Authentication Configuration
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=<YOUR_GENERATED_SECRET>

# Security Keys
SALT=<YOUR_GENERATED_SALT>
ENCRYPTION_KEY=<YOUR_GENERATED_ENCRYPTION_KEY>

# Optional Settings
HOSTNAME=0.0.0.0
LANGFUSE_CSP_ENFORCE_HTTPS=false

Replace the Placeholders:

	•	<DB_PASSWORD>: Replace with your database user’s password.
	•	langfuse_user: Use the database user you created (or the default postgres user if you didn’t create a new one).
	•	langfuse_db: Replace with your database name if different.

Generate Secure Random Values:

You need to generate secure random strings for NEXTAUTH_SECRET, SALT, and ENCRYPTION_KEY.

Generate NEXTAUTH_SECRET and SALT:

openssl rand -base64 32

Copy the output and paste it into the respective fields in your .env file.

Generate ENCRYPTION_KEY:

openssl rand -hex 32

Copy the 64-character hex string and paste it into the ENCRYPTION_KEY field.

2. Pull the LangFuse Docker Image

Pull the latest LangFuse Docker image:

docker pull langfuse/langfuse:2

3. Run the LangFuse Docker Container

Start the LangFuse container using your .env file:

docker run --name langfuse \
  --env-file .env \
  -p 3000:3000 \
  langfuse/langfuse:2

Explanation:

	•	--name langfuse: Names the container “langfuse”.
	•	--env-file .env: Loads environment variables from your .env file.
	•	-p 3000:3000: Maps port 3000 of the container to port 3000 on your host machine.
	•	langfuse/langfuse:2: Specifies the Docker image to use.

Note: Ensure that your .env file is in the current directory when you run this command.

4. Verify LangFuse is Running

Open your web browser and navigate to:

http://localhost:3000

You should see the LangFuse login or sign-up page.

5. Create an Account

Since this is your first time running LangFuse:

	•	Click on “Sign Up”.
	•	Provide your email and create a password.
	•	Complete the sign-up process.

6. Set Up an Organization and Project

Once logged in:

	•	Create an Organization:
	•	Provide a name for your organization.
	•	Create a Project:
	•	Within your organization, create a new project.
	•	This project will be where you monitor your LLM’s activities.

7. Obtain API Keys

	•	Navigate to Project Settings.
	•	Locate your Public and Secret API keys.
	•	You’ll need these keys to configure LangFuse in your application.

8. Integrate LangFuse into Your Application

Depending on your application’s language and framework, you can use the appropriate LangFuse SDK.

	•	Available SDKs:
	•	LangFuse Node.js SDK
	•	LangFuse Python SDK
	•	LangFuse Java SDK

Configure the SDK:

	•	Set the publicKey and secretKey with the API keys obtained.
	•	Set the baseUrl to your LangFuse instance:

const langfuse = new Langfuse({
  publicKey: "your_public_key",
  secretKey: "your_secret_key",
  baseUrl: "http://localhost:3000",
});



9. Test the Integration

	•	Run your application and perform some actions that should be logged.
	•	Check the LangFuse dashboard to see if the data appears.

10. (Optional) Set Up HTTPS

For local development, using HTTP is acceptable. However, if you plan to access LangFuse remotely or expose it over the internet, you should set up HTTPS.

	•	Use a reverse proxy like Nginx or Traefik to handle SSL termination.
	•	Obtain SSL certificates via Let’s Encrypt or another certificate authority.
	•	Configure the reverse proxy to forward requests to your LangFuse container.

Example Nginx Configuration:

server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

Additional Considerations

Database Connectivity

	•	Since the Cloud SQL Auth Proxy is running on 127.0.0.1:5432, ensure that the DATABASE_URL in your .env file points to 127.0.0.1 and port 5432.
	•	Ensure that your database user (langfuse_user or postgres) has the necessary permissions on the langfuse_db database.

Data Persistence

	•	Your LangFuse data will be stored in the Cloud SQL database, which is persistent.
	•	If you stop and restart the LangFuse container, your data will remain intact.

Container Management

	•	To stop the LangFuse container:

docker stop langfuse


	•	To start it again:

docker start langfuse


	•	To view logs:

docker logs langfuse



Updating LangFuse

	•	To update LangFuse to the latest version within the same major version:

docker pull langfuse/langfuse:2
docker stop langfuse
docker rm langfuse
docker run --name langfuse \
  --env-file .env \
  -p 3000:3000 \
  langfuse/langfuse:2



Next Steps

Integrate Your LLM (Ollama) with LangFuse

Now that LangFuse is running and accessible, you can proceed to connect your LLM hosted with Ollama to LangFuse.

	•	Configure Your LLM Application:
	•	Ensure your application sends tracing and monitoring data to LangFuse.
	•	Use the appropriate SDK or API calls to log events.

Set Up the Prompt Optimization Loop

Recall your project’s components:

	•	LangFuse: Monitoring and observability platform.
	•	LLM Hosted with Ollama: Your language model instance.
	•	Monte Carlo Tree Search (MCTS): For prompt optimization.
	•	Prompt Repository: Version-controlled storage for prompts.

Implement the Following:

	1.	Instrument Your Application:
	•	Use the LangFuse SDK to log prompts, responses, and metrics.
	•	Ensure that each interaction with the LLM is captured.
	2.	Collect Metrics:
	•	Define the metrics you want to collect (e.g., response quality, latency).
	•	Use LangFuse to aggregate and visualize these metrics.
	3.	Implement MCTS for Prompt Optimization:
	•	Develop the MCTS algorithm to explore and exploit prompt variations.
	•	Use feedback from LangFuse metrics to guide the optimization.
	4.	Automate Prompt Updates:
	•	When the MCTS suggests a new prompt, update the prompt in your application.
	•	Ensure that changes are tracked in your Prompt Repository (e.g., Git).
	5.	Iterate and Improve:
	•	Run the optimization loop over multiple iterations.
	•	Monitor improvements in the metrics collected by LangFuse.

Troubleshooting

	•	LangFuse Not Accessible:
	•	Ensure the container is running: docker ps
	•	Check if port 3000 is in use or blocked.
	•	Database Connection Errors:
	•	Verify that the Cloud SQL Auth Proxy is running.
	•	Check the DATABASE_URL in your .env file.
	•	Ensure the database user credentials are correct.
	•	Cannot Log In or Sign Up:
	•	Check the container logs for errors: docker logs langfuse
	•	Ensure that NEXTAUTH_SECRET is set correctly.
	•	Data Not Appearing in LangFuse Dashboard:
	•	Verify that your application is sending data to LangFuse.
	•	Check SDK configurations and API keys.

Security Considerations

	•	Protect Sensitive Information:
	•	Keep your .env file secure.
	•	Do not commit it to version control.
	•	Consider using environment variable management tools for production.
	•	Service Account Key:
	•	Ensure that the service account key used by the Cloud SQL Auth Proxy is stored securely.
	•	Limit access permissions to the key file.
