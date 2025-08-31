import os
import logging
from typing import Dict, Optional


class TokenParser:
    def __init__(self, config_file: Optional[str] = None):
        self.tokens: Dict[int, str] = {}
        self.config_file = config_file

    def parse_from_env(self) -> Dict[int, str]:
        """
        Parse tokens from environment variables.
        Expected format: MULTI_TOKEN_1, MULTI_TOKEN_2, etc.
        """
        logging.info("Parsing tokens from environment variables...")
        self.tokens = {}

        # Filter only MULTI_TOKEN*
        env_tokens = [
            (key, value)
            for key, value in sorted(os.environ.items())
            if key.startswith("MULTI_TOKEN")
        ]

        if not env_tokens:
            logging.warning("No MULTI_TOKEN environment variables found!")

        for idx, (key, token) in enumerate(env_tokens, start=1):
            if not token.strip():
                logging.warning(f"{key} is empty. Skipping...")
                continue

            if token in self.tokens.values():
                logging.warning(f"Duplicate token found in {key}. Skipping...")
                continue

            self.tokens[idx] = token.strip()

        logging.info(f"Loaded {len(self.tokens)} token(s).")
        return self.tokens

    def parse_from_file(self) -> Dict[int, str]:
        """
        (Optional) Parse tokens from a config file if provided.
        Expected format: one token per line.
        """
        if not self.config_file:
            logging.warning("No config file provided.")
            return self.tokens

        logging.info(f"Parsing tokens from config file: {self.config_file}")
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]

            for idx, token in enumerate(lines, start=len(self.tokens) + 1):
                if token in self.tokens.values():
                    logging.warning("Duplicate token in file. Skipping...")
                    continue
                self.tokens[idx] = token

            logging.info(f"Loaded total {len(self.tokens)} token(s).")

        except FileNotFoundError:
            logging.error(f"Config file not found: {self.config_file}")
        except Exception as e:
            logging.error(f"Error parsing config file: {e}")

        return self.tokens

