.PHONY=lint
lint:
	@poetry run black --check .

.PHONY=format
format:
	@poetry run black .

.PHONY=check-types
check-types:
	@poetry run mypy .

.PHONY=test
test: lint check-types
	@poetry run python -m pytest

requirements.txt:
	@poetry export -f requirements.txt --without-hashes --output requirements.txt

# TODO remove me
.PHONY=deploy-slack-alerts
deploy-slack-alerts: requirements.txt
	 @gcloud functions deploy slack-alerts \
        --region=europe-west2 \
        --entry-point=send_slack_alert \
        --trigger-topic=slack-alerts \
        --runtime=python310 \
        --set-env-vars SLACK_URL=$$SLACK_URL,ENVIRONMENT=$$ENVIRONMENT

# TODO remove me
.PHONY=deploy-log-error
deploy-log-error: requirements.txt
	 @gcloud functions deploy log-error \
        --region=europe-west2 \
        --entry-point=log_error \
        --trigger-http \
        --runtime=python39

# TODO remove me
.PHONY=deploy
deploy: deploy-slack-alerts deploy-log-error
