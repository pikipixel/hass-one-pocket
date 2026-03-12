"""Constants for the ONE Pocket integration."""

import logging

DOMAIN = "one_pocket"
LOGGER = logging.getLogger(__package__)

DEFAULT_BASE_URL = "https://oneconnect.edifice.io"
OAUTH_CLIENT_ID = "app-e"
OAUTH_CLIENT_SECRET = "yTFxAPupNnKb9VcKwA6E5DA3"
OAUTH_SCOPES = "userinfo conversation directory homeworks schoolbook timeline actualites blog"

CONF_BASE_URL = "base_url"
CONF_CHILD_ID = "child_id"
CONF_CHILD_NAME = "child_name"
CONF_STRUCTURE_ID = "structure_id"

DEFAULT_SCAN_INTERVAL = 15  # minutes
