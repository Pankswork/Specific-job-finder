.PHONY: run docker-build docker-run clean

run:
	python -m src.main

docker-build:
	docker build -t ai-job-agent .

docker-run:
	docker run --env-file .env ai-job-agent

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
