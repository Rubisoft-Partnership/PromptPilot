brew install --cask google-cloud-sdk &&
gcloud init &&
gcloud services enable sqladmin.googleapis.com &&
curl -o cloud_sql_proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.14.0/cloud-sql-proxy.darwin.arm64
chmod +x cloud_sql_proxy &&
gcloud auth login
gcloud config set project swift-branch-441009-j8 &&
gcloud sql instances describe langfuse-postgres --format='value(connectionName)' &&
./cloud_sql_proxy --instances=langfuse-postgres=tcp:5432 &&
./cloud_sql_proxy --instances=swift-branch-441009-j8:europe-west3:langfuse-postgres=tcp:5432 &&
./cloud_sql_proxy swift-branch-441009-j8:europe-west3:langfuse-postgres --address=127.0.0.1 --port=5432 &&
chmod 600 PromptPilot/cloud_sql_proxy/keys/swift-branch-441009-j8-6f886a56b51b.json &&
./cloud_sql_proxy swift-branch-441009-j8:europe-west3:langfuse-postgres \
  --address=127.0.0.1 \
  --port=5432 \
  --credentials-file=PromptPilot/cloud_sql_proxy/keys/swift-branch-441009-j8-6f886a56b51b.json &