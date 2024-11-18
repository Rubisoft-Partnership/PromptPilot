echo "Stopping langfuse"
docker stop langfuse
echo "Removing langfuse"
docker rm langfuse

echo "Pulling langfuse/langfuse:2"
docker pull langfuse/langfuse:2
echo "Running langfuse/langfuse:2"
docker run --name langfuse \
  --env-file .env \
  -p 3000:3000 \
  langfuse/langfuse:2