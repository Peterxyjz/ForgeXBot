"""Centralized configuration loader.

Chỉ module này đọc `.env` và biến môi trường. Các nơi khác chỉ
gọi `load_config()` để lấy dict cấu hình đã hợp nhất.

Thứ tự:
1. Đọc YAML `config/config.yaml`
2. Nạp `.env` (nếu có)
3. Ghi đè bằng biến môi trường (nếu set)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any
import yaml
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Mapping (section, key) -> (ENV_VAR, caster)
ENV_MAP = {
	("mt5", "login"): ("MT5_LOGIN", int),
	("mt5", "password"): ("MT5_PASSWORD", str),
	("mt5", "server"): ("MT5_SERVER", str),
	("mt5", "path"): ("MT5_PATH", str),
	("telegram", "bot_token"): ("TELEGRAM_BOT_TOKEN", str),
	("telegram", "chat_id"): ("TELEGRAM_CHAT_ID", str),
	("system", "log_level"): ("LOG_LEVEL", str),
}


def load_config(config_path: str | os.PathLike = "config/config.yaml") -> Dict[str, Any]:
	path = Path(config_path)
	if not path.exists():
		raise FileNotFoundError(f"Config file not found: {config_path}")

	with path.open("r", encoding="utf-8") as f:
		data: Dict[str, Any] = yaml.safe_load(f) or {}

	# Đảm bảo các section tồn tại
	for section, _ in { (s, k) for (s, k) in ENV_MAP.keys() }:
		data.setdefault(section, {})

	# Nạp .env (nếu không có thì bỏ qua, không lỗi)
	load_dotenv()

	applied: list[str] = []
	for (section, key), (env_name, caster) in ENV_MAP.items():
		raw = os.getenv(env_name)
		if raw in (None, ""):
			continue
		try:
			value = caster(raw) if caster is int else raw
			data[section][key] = value
			applied.append(env_name)
		except ValueError:
			logger.warning("Env var %s có giá trị không hợp lệ: %s", env_name, raw)

	if applied:
		logger.info("Applied env overrides: %s", ", ".join(applied))
	else:
		logger.debug("Không có env override nào")

	return data


__all__ = ["load_config"]

