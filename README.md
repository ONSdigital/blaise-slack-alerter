# Blaise Slack Alerter

This is a Cloud Function which is used to send alerts from Google Cloud Logging to Slack.

## How it Works

Some GCP infrastructure is required for this to work.

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

### Linting and Testing

The [GitHub Actions](https://docs.github.com/en/actions), a CI/CD platform, runs the linter, typechecker and tests (using workflows), whenever a GitHub PR is raised.

To minimise chances of failures when the GitHub Actions are ran, it's worth running `make test` before you push and commit to GitHub.
Note, `make test` also runs the typechecker and linter.

Linting errors can usually be fixed quickly with `make format`.

### How to silence specific event logs

1. Navigate to the log entry in GCP Console and copy the entry to the clipboard
2. Create a test in the `test_main.py` file using the copied log entry
3. Run tests using `make format test` - the test you just created should fail!
4. Navigate to the `lib/filters` dir and create a new `.py` file
5. Add new functionality to the newly created file (see `osconfig_agent_filter.py` for an example)
6. Navigate to the `tests/lib/filters` dir and create a new `test_XX.py` file
7. Create unit tests that test the actual filter functionality (again, check `test_osconfig_agent_filter.py` for an example). You will need to change the fixture!
    - **NB** Event logs can be difficult to replicate in a sandbox, so it is important that the unit tests are present and accurately written before it is deployed to an environment.
8. In `send_alerts.py`, import the function you just created and add it to the filter array `[]` in the `log_entry_skipped` function

```python
def log_entry_skipped(log_entry: ProcessedLogEntry):
    filters = [
        osconfig_agent_filter, 
        auditlog_filter, 
        agent_connect_filter,
        ... etc]
```

9. Run `make format test` - if the checks pass, push and commit!
10. Deploy the Cloud Function in a sandbox and ensure it works as expected.

### How to enable Slack alerts in sandboxes

Logs coming from sandboxes are filtered by default. If you want to reproduce error logs within a sandbox, make sure to remove the following filters in `send_alerts/log_entry_skipped` before deploying the Cloud Function:

- `sandbox_filter`
- `all_preprod_and_training_alerts_except_erroneous_questionnaire_filter`
