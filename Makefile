
clean:
	echo "\n >> clean "
	rm -rf dist build

ci-cd-build: clean
	echo "\n >> ci-cd-build "
	pip install pyinstaller
	pyinstaller ./app/main.py --onefile --name zk-gpt

docker-build: ci-cd-build
	echo "\n >> docker-build "
	docker build -t zk-gpt-test:latest .

docker-run: docker-build
	echo "\n >> docker-run "
	docker run -it --rm zk-gpt-test:latest