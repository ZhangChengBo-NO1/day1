import hashlib
import os
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from models import Database, User


class AuthManager:
    def __init__(self, db: Database):
        self.db = db
        self.user_model = User(db)
        self.current_user: Optional[Dict[str, Any]] = None

    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def register(self, username: str, password: str, role: str = "user") -> Tuple[bool, str]:
        if len(username) < 3 or len(username) > 20:
            return False, "用户名长度必须在3-20之间"
        if len(password) < 6:
            return False, "密码长度不能少于6位"

        hashed_password = self.hash_password(password)
        user_id = self.user_model.create_user(username, hashed_password, role)

        if user_id == -1:
            return False, "用户名已存在"
        return True, f"注册成功，用户ID: {user_id}"

    def login(self, username: str, password: str) -> Tuple[bool, str]:
        hashed_password = self.hash_password(password)
        user = self.user_model.verify_user(username, hashed_password)

        if user:
            self.current_user = user
            return True, f"登录成功，欢迎 {username}!"
        return False, "用户名或密码错误"

    def logout(self) -> Tuple[bool, str]:
        if self.current_user:
            self.current_user = None
            return True, "已退出登录"
        return False, "当前没有登录用户"

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        return self.current_user

    def is_admin(self) -> bool:
        if self.current_user:
            return self.current_user.get("role") == "admin"
        return False

    def is_logged_in(self) -> bool:
        return self.current_user is not None

    def require_login(self) -> Tuple[bool, str]:
        if not self.is_logged_in():
            return False, "请先登录"
        return True, ""

    def require_admin(self) -> Tuple[bool, str]:
        logged_in, msg = self.require_login()
        if not logged_in:
            return False, msg
        if not self.is_admin():
            return False, "需要管理员权限"
        return True, ""


class Config:
    def __init__(self, config_dir: str = "."):
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "finance_config.txt")
        self._ensure_config()

    def _ensure_config(self):
        if not os.path.exists(self.config_file):
            default_config = {
                "db_path": "finance.db",
                "export_dir": "exports",
                "chart_dir": "charts",
                "default_currency": "¥"
            }
            self.save_config(default_config)

    def load_config(self) -> Dict[str, str]:
        config = {}
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        except Exception:
            pass
        return config

    def save_config(self, config: Dict[str, str]):
        os.makedirs(self.config_dir, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            for key, value in config.items():
                f.write(f"{key}={value}\n")

    def get(self, key: str, default: str = "") -> str:
        config = self.load_config()
        return config.get(key, default)

    def set(self, key: str, value: str):
        config = self.load_config()
        config[key] = value
        self.save_config(config)


class DateUtils:
    @staticmethod
    def get_current_date_str() -> str:
        return datetime.now().strftime("%Y-%m-%d")

    @staticmethod
    def get_current_datetime_str() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def get_month_start(year: int, month: int) -> str:
        return f"{year}-{month:02d}-01"

    @staticmethod
    def get_month_end(year: int, month: int) -> str:
        if month == 12:
            return f"{year + 1}-01-01"
        return f"{year}-{month + 1:02d}-01"

    @staticmethod
    def parse_date(date_str: str) -> Optional[datetime]:
        formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None


class FileUtils:
    @staticmethod
    def ensure_dir(directory: str):
        os.makedirs(directory, exist_ok=True)

    @staticmethod
    def get_unique_filename(base_path: str, extension: str) -> str:
        counter = 1
        path = f"{base_path}.{extension}"
        while os.path.exists(path):
            path = f"{base_path}_{counter}.{extension}"
            counter += 1
        return path

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"



