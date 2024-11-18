# Steps to setup a Postgres instance on Google Cloud Platform

## Database instance creation
Prerequisites

	•	A Google Cloud Platform (GCP) account.
	•	A GCP project where you’ll create the Cloud SQL instance.
	•	Basic understanding of GCP services.

1. Create or Select a GCP Project

	1.	Access Google Cloud Console: Navigate to console.cloud.google.com.
	2.	Select a Project: Click on the project dropdown at the top of the page and select an existing project or click “New Project” to create a new one.
	•	Creating a New Project:
	•	Provide a Project Name.
	•	Select an Organization (if applicable).
	•	Click “Create”.

2. Enable the Cloud SQL Admin API

Some GCP services require enabling specific APIs.

	1.	Navigate to APIs & Services > Library in the Cloud Console.
	2.	Search for “Cloud SQL Admin API”.
	3.	Click on it and then click “Enable”.

3. Create a Cloud SQL for PostgreSQL Instance

	1.	Navigate to Cloud SQL:
	•	In the Cloud Console, go to Navigation Menu (☰) > SQL.
	2.	Create an Instance:
	•	Click on “Create Instance”.
	•	Choose “PostgreSQL” as the database engine.

4. Configure Your PostgreSQL Instance

	•	Instance ID:
	•	Provide a unique identifier, e.g., langfuse-postgres.
	•	Default User Password:
	•	Set a strong password for the default postgres user.
	•	Region and Zone:
	•	Choose a region close to your deployment environment, e.g., us-central1.
	•	Machine Type and Storage:
	•	Machine Type:
	•	For minimal production use, the default settings may suffice.
	•	You can adjust CPU and memory based on your needs.
	•	Storage:
	•	Set an initial storage size (e.g., 10 GB).
	•	Enable Automatic storage increases to prevent running out of space.
	•	Connectivity Options:
	•	Public IP:
	•	For simplicity, enable Public IP connectivity.
	•	Note: Public IP is less secure than Private IP but easier to set up initially.
	•	Private IP (Optional):
	•	For enhanced security, you can set up a Private IP. This requires additional VPC configuration.
	•	Authentication:
	•	SSL Connections:
	•	Enable “Require SSL connections” to secure data in transit.
	•	Availability Options:
	•	For production environments, consider enabling High Availability features like Failover Replicas.
	•	Backups and Maintenance:
	•	Enable Automated Backups.
	•	Set a Backup Window during off-peak hours.
	•	Configure Maintenance Window settings as needed.
	•	Flags (Optional):
	•	Configure any PostgreSQL flags if necessary.
	•	Labels (Optional):
	•	Add labels to help organize your resources.

	3.	Create the Instance:
	•	Review your settings.
	•	Click “Create Instance”.


## Setup instance connection with Cloud SQL Auth Proxy
Prerequisites

	•	Google Cloud SDK Installed: Ensure that you have the Google Cloud SDK installed on your machine.
	•	gcloud Authentication: You are authenticated with gcloud and have the necessary permissions.

1. Enable the Cloud SQL Admin API

Before using the Cloud SQL Auth Proxy, ensure that the Cloud SQL Admin API is enabled for your project:

gcloud services enable sqladmin.googleapis.com

2. Install the Cloud SQL Auth Proxy

For Linux (64-bit):

curl -o cloud_sql_proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.14.0/cloud-sql-proxy.linux.amd64
chmod +x cloud_sql_proxy

For macOS (Intel):

curl -o cloud_sql_proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.14.0/cloud-sql-proxy.darwin.amd64
chmod +x cloud_sql_proxy

For macOS (M1/M2):

curl -o cloud_sql_proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.14.0/cloud-sql-proxy.darwin.arm64
chmod +x cloud_sql_proxy

For Windows:

Download the appropriate binary from the Cloud SQL Auth Proxy Releases.

3. Authenticate with gcloud

Ensure that you are authenticated and have access to the project where your Cloud SQL instance resides:

gcloud auth login
gcloud config set project YOUR_PROJECT_ID

Replace YOUR_PROJECT_ID with your actual GCP project ID.

4. Determine Your Instance Connection Name

You need the instance connection name for your Cloud SQL instance. You can find it in the Google Cloud Console under your instance’s Overview page, or retrieve it via the gcloud command:

gcloud sql instances describe YOUR_INSTANCE_NAME --format='value(connectionName)'

Replace YOUR_INSTANCE_NAME with the name of your Cloud SQL instance.

The connection name will look like: your-project:region:instance-name

5. Start the Cloud SQL Auth Proxy

Authenticate the Cloud SQL Auth Proxy Using a Service Account

    1. Create a Service Account in Google Cloud

        1.	Access the Google Cloud Console:
        •	Navigate to Google Cloud Console - Service Accounts.
        2.	Select Your Project:
        •	Ensure you’re working in the correct GCP project where your Cloud SQL instance resides.
        3.	Create a New Service Account:
        •	Click on “Create Service Account” at the top.
        4.	Configure the Service Account:
        •	Service Account Name: langfuse-cloud-sql-proxy
        •	Service Account ID: This will be auto-filled based on the name.
        •	Description: (Optional) Service account for Cloud SQL Auth Proxy
    Click “Create and Continue”.
        5.	Grant Service Account Access to Project:
        •	Role: Select “Cloud SQL Client”.
        •	In the “Select a role” dropdown, search for “Cloud SQL Client” under “Cloud SQL”.
        •	The “Cloud SQL Client” role includes the necessary permissions (cloudsql.instances.connect) to allow the proxy to connect to your Cloud SQL instance.
    Click “Continue”.
        6.	Grant Users Access to the Service Account:
        •	You can skip this step unless you need others to manage the service account.
    Click “Done”.

    2. Create and Download a Service Account Key

        1.	Locate Your Service Account:
        •	In the list of service accounts, find the one you just created (langfuse-cloud-sql-proxy).
        2.	Generate a Key File:
        •	Click on the email of the service account to open its details.
        •	Navigate to the “Keys” tab.
        •	Click “Add Key” > “Create New Key”.
        3.	Choose Key Type:
        •	Select “JSON”.
        •	Click “Create”.
        4.	Download the Key File:
        •	A JSON file containing the service account key will be downloaded to your computer. This is your authentication file.
    Important: Keep this file secure. It contains credentials that can access your GCP resources.

    3. Secure the Service Account Key File

        •	Move the Key File to a Secure Location:
        •	Choose a directory where you plan to run the Cloud SQL Auth Proxy, e.g., /path/to/keys/.
        •	Set Permissions on the Key File:
        •	Restrict access to the file to only your user account.

    chmod 600 /path/to/keys/service-account-key.json



    4. Start the Cloud SQL Auth Proxy Using the Service Account Key

    Use the --credentials-file flag to provide the path to your service account key file.

    ./cloud_sql_proxy swift-branch-441009-j8:europe-west3:langfuse-postgres \
    --address=127.0.0.1 \
    --port=5432 \
    --credentials-file=/path/to/keys/service-account-key.json &

        •	Replace /path/to/keys/service-account-key.json with the actual path to your key file.

    5. Verify the Proxy Starts Successfully

        •	If everything is configured correctly, the proxy should start without errors:

    2024/11/07 14:50:00 Using credential file for authentication; email=langfuse-cloud-sql-proxy@your-project.iam.gserviceaccount.com
    2024/11/07 14:50:01 Listening on 127.0.0.1:5432 for swift-branch-441009-j8:europe-west3:langfuse-postgres
    2024/11/07 14:50:01 Ready for new connections


7. Update Your LangFuse Configuration

In your .env file or environment variables for LangFuse, update the DATABASE_URL to point to the local proxy:

DATABASE_URL=postgresql://langfuse_user:YOUR_DB_PASSWORD@localhost:5432/langfuse_db

	•	Host: localhost
	•	Port: 5432 (or the port you specified when starting the proxy)
	•	User: Your database user, e.g., langfuse_user
	•	Password: The password for the database user
	•	Database Name: Your database name, e.g., langfuse_db

Example:

DATABASE_URL=postgresql://langfuse_user:securepassword@localhost:5432/langfuse_db

8. Start LangFuse

Now you can start your LangFuse Docker container or application, and it will connect to the Cloud SQL database through the proxy running on your local machine.

Example Docker Run Command:

docker run --name langfuse \
  --env-file .env \
  -p 3000:3000 \
  langfuse/langfuse:2

9. Test the Connection

	•	Access LangFuse at http://localhost:3000 or https://localhost:3000 if you’ve set up HTTPS.
	•	Verify that LangFuse starts without database connection errors.
	•	Check logs for any issues.

Additional Considerations

Authentication and Permissions

	•	Service Account Authentication (Recommended):
	•	Create a service account with the necessary permissions.
	•	Download the service account key JSON file securely.
	•	Set the GOOGLE_APPLICATION_CREDENTIALS environment variable to point to the JSON file.

export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"

	•	Start the proxy with:

./cloud_sql_proxy --credentials-file=/path/to/service-account-key.json --instances=YOUR_INSTANCE_CONNECTION_NAME=tcp:5432


	•	Using Your User Credentials:
	•	If you authenticated with gcloud auth login, the proxy can use your user credentials.
	•	Ensure that your user account has the Cloud SQL Client role.

No Need to Configure Authorized Networks

	•	The Cloud SQL Auth Proxy handles authentication and secure connections.
	•	You don’t need to add your local IP to the Authorized Networks in Cloud SQL.
	•	This is particularly useful if your IP address changes frequently or you’re behind a NAT.

SSL/TLS Encryption

	•	The Cloud SQL Auth Proxy automatically encrypts traffic between your local machine and Cloud SQL.
	•	No need to manage SSL certificates manually.

Port Conflicts

	•	Ensure that the local port you specify for the proxy (5432 in the examples) is not in use.
	•	If necessary, choose an alternative port.

Firewall Considerations

	•	Outbound connections to Cloud SQL from your machine should be allowed.
	•	Ensure that your local firewall or network policies permit outbound connections on required ports (usually port 443 for the proxy’s API calls and port 3307 for connections to Cloud SQL, but the proxy handles these internally).

Running the Proxy in Docker (Optional)

	•	If you prefer, you can run the Cloud SQL Auth Proxy in a Docker container.
	•	However, since you’re running LangFuse in Docker, and the proxy needs to be accessible to LangFuse, this may complicate networking.
	•	For local development, running the proxy directly on your host machine is simpler.

Summary of Steps

	1.	Install the Cloud SQL Auth Proxy on your local machine.
	2.	Authenticate with Google Cloud (user credentials or service account).
	3.	Start the proxy, connecting your local port to your Cloud SQL instance.
	4.	Update LangFuse’s database configuration to point to localhost and the proxy port.
	5.	Run LangFuse, and it should connect through the proxy to the Cloud SQL instance.