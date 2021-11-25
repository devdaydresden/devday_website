import logging
import os
from datetime import datetime, timedelta
from urllib.parse import urljoin

import requests
from apscheduler.schedulers.background import BackgroundScheduler

__all__ = ["vault_integration", "update_token_scheduler"]

from devday.apps import get_scheduler


class VaultIntegration(object):
    __instance = None
    vault_token = None
    secret_url = None

    def __new__(cls):
        if VaultIntegration.__instance is None:
            VaultIntegration.__instance = object.__new__(cls)
        return VaultIntegration.__instance

    def __init__(self):
        super()
        self.vault_url = os.environ["VAULT_URL"]
        self.vault_path = os.environ["VAULT_PATH"]
        self.logger = logging.getLogger(__name__)
        self.logger.info("new VaultIntegration instance")
        self.login_to_vault()

    def login_to_vault(self):
        self.logger.info("login_to_vault called")
        if self.vault_token:
            return

        vault_role_id = os.environ["VAULT_ROLE_ID"]
        vault_secret_id = os.environ["VAULT_SECRET_ID"]

        self.logger.debug(
            "vault_role_id: %s vault_secret_id: %s", vault_role_id, vault_secret_id
        )
        response = requests.post(
            urljoin(self.vault_url, "/v1/auth/approle/login"),
            json={"role_id": vault_role_id, "secret_id": vault_secret_id},
        )
        if response.status_code != 200:
            self.logger.error(
                "%d %s\n\n%s", response.status_code, response.reason, response.json()
            )
            return

        vault_token = response.json()["auth"]["client_token"]
        self.logger.debug("got token: %s", vault_token)
        self.vault_token = vault_token
        self.secret_url = urljoin(self.vault_url, self.vault_path)

    def get_settings_from_vault(self):
        if self.vault_token is None:
            self.login_to_vault()

        response = requests.get(
            self.secret_url,
            headers={"X-Vault-Token": self.vault_token},
        )
        response.raise_for_status()
        config_data = response.json()
        return config_data["data"]["data"]

    def refresh_vault_token(self):
        if self.vault_token is None:
            self.login_to_vault()

        response = requests.post(
            urljoin(self.vault_url, "/v1/auth/token/renew-self"),
            json={"increment": "5m"},
            headers={"X-Vault-Token": self.vault_token},
        )
        response.raise_for_status()

        self.logger.info("refreshed vault token")
        duration = response.json()["auth"]["lease_duration"]
        self.logger.info("lease duration %d", duration)
        return duration


vault_integration = VaultIntegration()


def update_token_scheduler():
    interval = vault_integration.refresh_vault_token() - 60
    next_run_time = datetime.now() + timedelta(seconds=interval)
    logger = logging.getLogger(__name__)
    logger.info(
        "scheduling Vault token refresh task with interval %d, next run time %s",
        interval,
        next_run_time,
    )
    get_scheduler().add_job(
        vault_integration.refresh_vault_token,
        "interval",
        seconds=interval,
        next_run_time=next_run_time,
        id="refresh_vault_token",
    )
