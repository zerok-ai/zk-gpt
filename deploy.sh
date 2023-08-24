set -x

docker build . -t us-west1-docker.pkg.dev/zerok-dev/zk-client/zk-gpt:new-span
docker push us-west1-docker.pkg.dev/zerok-dev/zk-client/zk-gpt:new-span

kubectl apply -k ./k8s