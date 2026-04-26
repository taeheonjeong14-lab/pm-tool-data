import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    appwrite_endpoint: str = os.getenv("APPWRITE_ENDPOINT", "").rstrip("/")
    appwrite_project_id: str = os.getenv("APPWRITE_PROJECT_ID", "")
    appwrite_api_key: str = os.getenv("APPWRITE_API_KEY", "")
    appwrite_database_id: str = os.getenv("APPWRITE_DATABASE_ID", "pm_tool")

    def appwrite_ready(self) -> bool:
        return bool(self.appwrite_endpoint and self.appwrite_project_id and self.appwrite_api_key)


settings = Settings()
