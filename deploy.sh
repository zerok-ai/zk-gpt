set -x

docker build . -t us-west1-docker.pkg.dev/zerok-dev/zk-client/zk-gpt:dev
docker push us-west1-docker.pkg.dev/zerok-dev/zk-client/zk-gpt:dev

kubectl apply -k ./k8s