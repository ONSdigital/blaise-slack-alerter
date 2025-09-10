import dataclasses
import datetime

import pytest

from lib.filters.all_preprod_and_training_alerts_except_erroneous_questionnaire_filter import (
    all_preprod_and_training_alerts_except_erroneous_questionnaire_filter,
)
from lib.log_processor import ProcessedLogEntry


@pytest.fixture()
def processed_log_entry_agent_connect_error() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="Agent Connect Error main.go:231: unexpected end of JSON input",
        data=dict(
            description="2023-06-06 14:36:14Z: Agent connect error: The HTTP request timed out after 00:01:00.. Retrying until reconnected.\r\n"
        ),
        severity="ERROR",
        platform="gce_instance",
        application="blaise-gusty-data-entry-1",
        log_name="/logs/gce-example",
        timestamp=datetime.datetime(2023, 2, 25, 3, 46, 57, 99633),
        log_query={
            "resource.type": "gce_instance",
            "resource.labels.instance_id": "458491889528639951",
        },
    )


@pytest.fixture()
def processed_log_entry_failed_install() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="AUDIT_LOG: Failed to install questionnaire OPN2310_FO0",
        data={
            "hostname": "localhost",
            "info": {},
            "time": 1698230214243,
            "req": {"url": "/api/install", "method": "POST"},
            "pid": 11,
            "level": 50,
        },
        severity="ERROR",
        platform="gae_app",
        application="dqs-ui",
        log_name="projects/ons-blaise-v2-preprod/logs/stdout",
        timestamp=datetime.datetime(2023, 10, 25, 10, 36, 54, 419325),
        log_query={"resource.type": "gae_app", "resource.labels.module_id": "dqs-ui"},
        most_important_values=[
            "status",
            "host",
            "method",
            "resource",
            "ip",
            "latency",
            "responseSize",
            "httpVersion",
        ],
    )


class TestErroneousQuestionnaireError:
    def test_filter_returns_true_for_failed_to_install_questionnaire_error_in_sandbox(
        self,
        processed_log_entry_failed_install,
    ):
        # arrange
        processed_log_entry_failed_install_training = dataclasses.replace(
            processed_log_entry_failed_install,
            log_name="projects/ons-blaise-v2-dev-jw09/logs/stdout",
        )

        # act
        result = all_preprod_and_training_alerts_except_erroneous_questionnaire_filter(
            processed_log_entry_failed_install_training
        )

        # assert
        assert result is True

    def test_filter_returns_false_for_failed_to_install_questionnaire_error_in_training(
        self,
        processed_log_entry_failed_install,
    ):
        # arrange
        processed_log_entry_failed_install_training = dataclasses.replace(
            processed_log_entry_failed_install,
            log_name="projects/ons-blaise-v2-dev-training/logs/stdout",
        )

        # act
        result = all_preprod_and_training_alerts_except_erroneous_questionnaire_filter(
            processed_log_entry_failed_install_training
        )

        # assert
        assert result is False

    def test_filter_returns_false_for_failed_to_install_questionnaire_error_in_preprod(
        self, processed_log_entry_failed_install
    ):
        # act
        result = all_preprod_and_training_alerts_except_erroneous_questionnaire_filter(
            processed_log_entry_failed_install
        )

        # assert
        assert result is False

    def test_filter_returns_false_for_failed_to_install_questionnaire_error_in_prod(
        self,
        processed_log_entry_failed_install,
    ):
        # arrange
        processed_log_entry_failed_install_prod = dataclasses.replace(
            processed_log_entry_failed_install,
            log_name="projects/ons-blaise-v2-prod/logs/stdout",
        )

        # act
        result = all_preprod_and_training_alerts_except_erroneous_questionnaire_filter(
            processed_log_entry_failed_install_prod
        )

        # assert
        assert result is False


class TestOtherErrors:
    def test_filter_returns_true_for_for_anything_except_failed_to_install_questionnaire_errors_in_sandbox(
        self,
        processed_log_entry_agent_connect_error,
    ):
        # arrange
        processed_log_entry_agent_connect_error_sandbox = dataclasses.replace(
            processed_log_entry_agent_connect_error,
            log_name="projects/ons-blaise-v2-dev-jw09/logs/stdout",
        )

        # act
        result = all_preprod_and_training_alerts_except_erroneous_questionnaire_filter(
            processed_log_entry_agent_connect_error_sandbox
        )

        # assert
        assert result is True

    def test_filter_returns_true_for_for_anything_except_failed_to_install_questionnaire_errors_in_training(
        self,
        processed_log_entry_agent_connect_error,
    ):
        # arrange
        processed_log_entry_agent_connect_error_training = dataclasses.replace(
            processed_log_entry_agent_connect_error,
            log_name="projects/ons-blaise-v2-dev-training/logs/stdout",
        )

        # act
        result = all_preprod_and_training_alerts_except_erroneous_questionnaire_filter(
            processed_log_entry_agent_connect_error_training
        )

        # assert
        assert result is True

    def test_filter_returns_true_for_for_anything_except_failed_to_install_questionnaire_errors_in_preprod(
        self,
        processed_log_entry_agent_connect_error,
    ):
        # arrange
        processed_log_entry_agent_connect_error_preprod = dataclasses.replace(
            processed_log_entry_agent_connect_error,
            log_name="projects/ons-blaise-v2-preprod/logs/stdout",
        )

        # act
        result = all_preprod_and_training_alerts_except_erroneous_questionnaire_filter(
            processed_log_entry_agent_connect_error_preprod
        )

        # assert
        assert result is True

    def test_filter_returns_false_for_for_anything_except_failed_to_install_questionnaire_errors_in_prod(
        self,
        processed_log_entry_agent_connect_error,
    ):
        # arrange
        processed_log_entry_failed_install_prod = dataclasses.replace(
            processed_log_entry_agent_connect_error,
            log_name="projects/ons-blaise-v2-prod/logs/stdout",
        )

        # act
        result = all_preprod_and_training_alerts_except_erroneous_questionnaire_filter(
            processed_log_entry_failed_install_prod
        )

        # assert
        assert result is False
