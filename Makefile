NAME = zk-gpt
IMAGE_NAME = zk-gpt
IMAGE_VERSION = 1.0
IMAGE_VERSION_MULTI_ARCH = multiarch

LOCATION ?= us-west1
PROJECT_ID ?= zerok-dev
REPOSITORY ?= zk-gpt

BUILDER_NAME = multi-platform-builder
IMAGE_PREFIX := $(LOCATION)-docker.pkg.dev/$(PROJECT_ID)/$(REPOSITORY)/

# ------- CI-CD ------------
ci-cd-build:

# for local
build-multiarch:
	#Adding remove here again to account for the case when buildx was not removed in previous run.
	docker buildx rm ${BUILDER_NAME} || true
	docker buildx create --use --platform=linux/arm64/v8,linux/amd64 --name ${BUILDER_NAME}
	docker buildx build --platform=linux/arm64,linux/amd64 --push \
	--tag $(IMAGE_PREFIX)$(IMAGE_NAME):$(IMAGE_VERSION) .
	docker buildx rm ${BUILDER_NAME}