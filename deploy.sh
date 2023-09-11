set -x

docker build . -t us-west1-docker.pkg.dev/zerok-dev/stage/zk-gpt:pinecone-inference
docker push us-west1-docker.pkg.dev/zerok-dev/stage/zk-gpt:pinecone-inference

kubectl apply -k ./k8s