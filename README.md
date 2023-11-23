# Blaise Slack Alerter

This is a Cloud Function which is used to send alerts from Google Cloud Logging to Slack.

## How it Works

Some GCP infrastructure is required for this to working.

1. **A PubSub Topic**:<br>
    Log messages will be put on this topic and trigger the Cloud Function.
2. **Google Cloud Logging [Log Sink](https://cloud.google.com/logging/docs/routing/overview)**:<br>
    - This should be configured to route the log message to the PubSub topic.
    - It should have an appropriate _inclusion_ and _exclusion_ filter.
3. **PubSub IAM policy**:<br>
     Granting `roles/pubsub.publisher` for the Log Sink.
4. **Google Cloud Function**:<br>
    Running this code.

In addition to this, you will need an **[Incoming Slack WebHook](https://api.slack.com/messaging/webhooks) URL**.

### Diagram

```
CLOUD LOGGING -> LOG SINK -> PUBSUB TOPIC -> CLOUD FUNCTION -> SLACK WEBHOOK
```

![Architecture Diagram](./architecture.jpg)

### Granting Sink Access To The PubSub Topic

```shell
gcloud logging sinks describe --format='value(writerIdentity)' <SINK_NAME>
gcloud pubsub topics add-iam-policy-binding <TOPIC_ID> --member=<WRITER_IDENTITY> --role=roles/pubsub.publisher
```

### Cloud Function Config

**Entry Point**: `send_slack_alert`

| Environment Variable | Value                                                                                              |
|----------------------|----------------------------------------------------------------------------------------------------|
| `SLACK_URL`          | Slack Web Hook URL.                                                                                |
| `GCP_PROJECT_NAME`   | The exact name of the GCP project. This is used to generate links to the GCP dashboard.            |

## Development

This repository uses poetry. After cloning, install the dependencies by running:

```shell
poetry install
```

### Makefile

A `Makefile` is included with some useful tasks to help with development.
Running `make help` will list all available commands.

### GitHub Actions

The GitHub Actions run the linter, typechecker and tests.

To avoid getting failures, it's worth running `make test` before commit.
Note, `make test` also runs the typechecker and linter.

### Linting Errors

Linting errors can usually be fixed quickly with `make format`.

### How to silence prod alerts 
1. Navigate to the log entry in GCP Console and copy the entry to the clipboard
2. Create a test in the `test_main.py` file using the copied log entry
3. Run tests using `make format test` - the test you just created should fail!
4. Navigate to the `lib/filters` dir and create a new `.py` file 
6. Add new functionality to the newly created file (see `osconfig_agent_filter.py` for an example)
7. Navigate to the `tests/lib/filters` dir and create a new `test_XX.py` file
8. Create unit tests that test the actual filter functionality (again, check `test_osconfig_agent_filter.py` for an example). You will need to change the fixture!
9. In `send_alerts.py`, import the function you just created and add it to the filter array `[]` in the `log_entry_skipped` function
```python
def log_entry_skipped(log_entry: ProcessedLogEntry):
    filters = [
        osconfig_agent_filter, 
        auditlog_filter, 
        agent_connect_filter,
        ... etc]
```
10. Run `make format test` - if all pass, push it up!