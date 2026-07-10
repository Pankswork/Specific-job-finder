.PHONY: run docker-build docker-run clean

run:
	LD_LIBRARY_PATH=/tmp/libnspr/usr/lib/x86_64-linux-gnu:$$LD_LIBRARY_PATH .venv/bin/python -m src.main

docker-build:
	docker build -t ai-job-agent .

docker-run:
	docker run --env-file .env ai-job-agent

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
