
clean:
	echo "\n >> clean "
	rm -rf dist build

ci-cd-build-local: clean
	#echo "\n >> ci-cd-build "
	#pyinstaller app/main.py --target-arch arm64 --onefile --name zk-gpt

docker-build: ci-cd-build-local
	echo "\n >> docker-build "
	docker build -t zk-gpt-test:latest .

docker-run: docker-build
	echo "\n >> docker-run "
	docker run -it --rm zk-gpt-test:latest

ci-cd-build:
	#echo "\n >> ci-cd-build "
	#pyinstaller app/main.py --target-arch arm64 --onefile --name zk-gpt

ci-cd-build-migration: