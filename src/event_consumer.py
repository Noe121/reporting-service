"""
SQS consumer for reporting-service to handle incoming contract events.

Listens for contract.signing.* events to trigger report generation
and track contract-related reporting metrics.
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Callable, Dict, Optional

import boto3
from sqlalchemy.orm import Session

from .reporting_service import (
    ReportGenerationService,
    ReportMetricsService,
    ReportTemplateService,
)

logger = logging.getLogger(__name__)


class ReportingEventConsumer:
    """
    Consumes contract events from SQS queue for reporting purposes.
    """

    # Supported contract event types
    CONTRACT_EVENTS = [
        "contract.signing.requested",
        "contract.signing.partially_signed",
        "contract.signing.completed",
        "contract.signing.canceled",
        "contract.signing.failed",
    ]

    def __init__(self, sqs_client, queue_url: str, db_session_factory: Callable[[], Session]):
        self.sqs_client = sqs_client
        self.queue_url = queue_url
        self.db_session_factory = db_session_factory

    @classmethod
    def from_env(cls, db_session_factory: Callable[[], Session]) -> Optional["ReportingEventConsumer"]:
        """Create consumer from environment variables."""
        queue_url = os.getenv("REPORTING_EVENTS_QUEUE_URL")
        if not queue_url:
            logger.warning("REPORTING_EVENTS_QUEUE_URL not set, event consumer disabled")
            return None

        region = os.getenv("AWS_REGION", "us-east-1")
        sqs_client = boto3.client("sqs", region_name=region)
        return cls(sqs_client=sqs_client, queue_url=queue_url, db_session_factory=db_session_factory)

    def poll_and_process(self, max_messages: int = 10, wait_time_seconds: int = 20):
        """
        Poll SQS queue and process messages.

        Args:
            max_messages: Maximum number of messages to retrieve per poll
            wait_time_seconds: Long polling wait time
        """
        try:
            response = self.sqs_client.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=wait_time_seconds,
                MessageAttributeNames=["All"],
                AttributeNames=["All"],
            )

            messages = response.get("Messages", [])
            if messages:
                logger.info(f"Received {len(messages)} message(s) from SQS")

            for message in messages:
                try:
                    self._process_message(message)
                    # Delete message after successful processing
                    self.sqs_client.delete_message(
                        QueueUrl=self.queue_url,
                        ReceiptHandle=message["ReceiptHandle"],
                    )
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    # Message will remain in queue and be retried

        except Exception as e:
            logger.error(f"Error polling SQS: {e}", exc_info=True)

    def _process_message(self, message: Dict[str, Any]):
        """Process a single SQS message."""
        try:
            # SNS sends messages wrapped in an outer structure
            body = json.loads(message["Body"])

            # Check if this is an SNS notification
            if "Message" in body:
                # Unwrap SNS message
                event_data = json.loads(body["Message"])
            else:
                # Direct SQS message
                event_data = body

            event_type = event_data.get("event_type")
            logger.info(f"Processing event: {event_type}")

            # Route to appropriate handler
            if event_type == "contract.signing.requested":
                self._handle_signing_requested(event_data)
            elif event_type == "contract.signing.partially_signed":
                self._handle_signing_partially_signed(event_data)
            elif event_type == "contract.signing.completed":
                self._handle_signing_completed(event_data)
            elif event_type == "contract.signing.canceled":
                self._handle_signing_canceled(event_data)
            elif event_type == "contract.signing.failed":
                self._handle_signing_failed(event_data)
            else:
                logger.debug(f"Ignoring event type: {event_type}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message body: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            raise

    def _handle_signing_requested(self, event: Dict[str, Any]):
        """
        Handle contract.signing.requested event.

        Track new contract signing for reporting metrics.
        """
        try:
            payload = event.get("payload", event)
            signing_package_id = payload.get("signing_package_id")
            participants = payload.get("participants", [])

            logger.info(f"Recording signing requested for reporting: {signing_package_id}")

            db = self.db_session_factory()
            try:
                # Find contract signing report template
                template = ReportTemplateService.get_template_by_name(
                    db, "Contract Signing Report"
                )

                if template:
                    # Record metric for contract initiation
                    ReportMetricsService.record_metric(
                        db=db,
                        report_id=template.id,  # Using template as aggregate
                        metric_name="contract_signing_initiated",
                        metric_value=1.0,
                        metric_unit="count",
                        metric_category="contracts",
                    )

                    # Track participant count
                    ReportMetricsService.record_metric(
                        db=db,
                        report_id=template.id,
                        metric_name="signing_participants",
                        metric_value=float(len(participants)),
                        metric_unit="count",
                        metric_category="contracts",
                    )

                logger.info(f"Recorded signing requested metrics for {signing_package_id}")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error handling contract.signing.requested: {e}", exc_info=True)
            raise

    def _handle_signing_partially_signed(self, event: Dict[str, Any]):
        """Handle contract.signing.partially_signed event."""
        try:
            payload = event.get("payload", event)
            signing_package_id = payload.get("signing_package_id")
            signed_count = len(payload.get("signed_participants", []))
            pending_count = len(payload.get("pending_participants", []))

            logger.info(f"Recording partial signing for reporting: {signing_package_id}")

            db = self.db_session_factory()
            try:
                template = ReportTemplateService.get_template_by_name(
                    db, "Contract Signing Report"
                )

                if template:
                    # Calculate progress percentage
                    total = signed_count + pending_count
                    progress = (signed_count / total * 100) if total > 0 else 0

                    ReportMetricsService.record_metric(
                        db=db,
                        report_id=template.id,
                        metric_name="signing_progress_percent",
                        metric_value=progress,
                        metric_unit="percent",
                        metric_category="contracts",
                    )

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error handling contract.signing.partially_signed: {e}", exc_info=True)
            raise

    def _handle_signing_completed(self, event: Dict[str, Any]):
        """
        Handle contract.signing.completed event.

        This is a key event for contract reports - track completion metrics.
        """
        try:
            payload = event.get("payload", event)
            signing_package_id = payload.get("signing_package_id")
            source_id = payload.get("source_id")
            participants = payload.get("signed_participants", [])

            logger.info(f"Recording signing completed for reporting: {signing_package_id}")

            db = self.db_session_factory()
            try:
                template = ReportTemplateService.get_template_by_name(
                    db, "Contract Signing Report"
                )

                if template:
                    # Record completion metric
                    ReportMetricsService.record_metric(
                        db=db,
                        report_id=template.id,
                        metric_name="contract_signing_completed",
                        metric_value=1.0,
                        metric_unit="count",
                        metric_category="contracts",
                    )

                    # Track final participant count
                    ReportMetricsService.record_metric(
                        db=db,
                        report_id=template.id,
                        metric_name="completed_signing_participants",
                        metric_value=float(len(participants)),
                        metric_unit="count",
                        metric_category="contracts",
                    )

                logger.info(f"Recorded signing completed metrics for {signing_package_id}")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error handling contract.signing.completed: {e}", exc_info=True)
            raise

    def _handle_signing_canceled(self, event: Dict[str, Any]):
        """Handle contract.signing.canceled event."""
        try:
            payload = event.get("payload", event)
            signing_package_id = payload.get("signing_package_id")

            logger.info(f"Recording signing canceled for reporting: {signing_package_id}")

            db = self.db_session_factory()
            try:
                template = ReportTemplateService.get_template_by_name(
                    db, "Contract Signing Report"
                )

                if template:
                    ReportMetricsService.record_metric(
                        db=db,
                        report_id=template.id,
                        metric_name="contract_signing_canceled",
                        metric_value=1.0,
                        metric_unit="count",
                        metric_category="contracts",
                    )

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error handling contract.signing.canceled: {e}", exc_info=True)
            raise

    def _handle_signing_failed(self, event: Dict[str, Any]):
        """Handle contract.signing.failed event - track failures for reporting."""
        try:
            payload = event.get("payload", event)
            signing_package_id = payload.get("signing_package_id")

            logger.info(f"Recording signing failed for reporting: {signing_package_id}")

            db = self.db_session_factory()
            try:
                template = ReportTemplateService.get_template_by_name(
                    db, "Contract Signing Report"
                )

                if template:
                    ReportMetricsService.record_metric(
                        db=db,
                        report_id=template.id,
                        metric_name="contract_signing_failed",
                        metric_value=1.0,
                        metric_unit="count",
                        metric_category="contracts",
                    )

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error handling contract.signing.failed: {e}", exc_info=True)
            raise

    def run_forever(self):
        """
        Run the event consumer in a loop.
        Use this for background worker processes.
        """
        logger.info(f"Starting reporting event consumer, polling {self.queue_url}")

        while True:
            try:
                self.poll_and_process()
            except KeyboardInterrupt:
                logger.info("Shutting down event consumer")
                break
            except Exception as e:
                logger.error(f"Unexpected error in event consumer: {e}", exc_info=True)
                # Continue processing


def start_event_consumer_worker(db_session_factory: Callable[[], Session]):
    """
    Entry point for running event consumer as a background worker.

    Usage:
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(...)

        start_event_consumer_worker(lambda: SessionLocal())
    """
    consumer = ReportingEventConsumer.from_env(db_session_factory)

    if not consumer:
        logger.error("Event consumer not configured (REPORTING_EVENTS_QUEUE_URL missing)")
        return

    logger.info("Reporting event consumer configured, starting worker...")
    consumer.run_forever()
