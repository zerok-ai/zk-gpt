
.PHONY: clean
clean:
	echo "\n >> clean "
	rm -rf dist build

.PHONY: ci-cd-build-local
ci-cd-build-local: clean
	#echo "\n >> ci-cd-build "
	#pyinstaller app/main.py --target-arch arm64 --onefile --name zk-gpt

.PHONY: docker-build
docker-build: ci-cd-build-local
	echo "\n >> docker-build "
	docker build -t zk-gpt-test:latest .

.PHONY: docker-run
docker-run: docker-build
	echo "\n >> docker-run "
	docker run -it --rm zk-gpt-test:latest

.PHONY: ci-cd-build
ci-cd-build:
	#echo "\n >> ci-cd-build "
	#pyinstaller app/main.py --target-arch arm64 --onefile --name zk-gpt

.PHONY: ci-cd-build-migration
ci-cd-build-migration: