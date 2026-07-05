from __future__ import annotations

import logging
import sys

from flask import Flask


def init_logging(app: Flask) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    app.logger.handlers = logging.getLogger().handlers
    app.logger.setLevel(logging.INFO)