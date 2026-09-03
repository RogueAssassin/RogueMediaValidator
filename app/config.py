from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RMV_", env_file=".env", extra="ignore")

    app_name: str = "RogueMediaValidator"
    host: str = "0.0.0.0"
    port: int = 7811
    data_dir: Path = Path("/data")
    poll_seconds: int = 2
    dry_run: bool = True
    log_level: str = "INFO"

    qb_url: str = "http://qbittorrent:8080"
    qb_username: str = ""
    qb_password: str = ""
    # Fail closed when no categories are configured. Use "*" explicitly to
    # inspect every non-empty qBittorrent category.
    qb_categories: str = ""
    qb_inspect_all_states: bool = True
    qb_category_refresh_seconds: int = 60
    qb_action_states: str = (
        "pausedDL,stoppedDL,downloading,stalledDL,metaDL,queuedDL,"
        "checkingDL,forcedDL,allocating,checkingResumeData,moving"
    )

    allowed_video_extensions: str = "mkv,mp4,m4v,avi,ts,m2ts,webm,mov"
    allowed_support_extensions: str = "srt,ass,ssa,sub,idx,nfo,jpg,jpeg,png,txt"
    blocked_extensions: str = (
        "exe,scr,com,bat,cmd,msi,msix,ps1,psm1,vbs,vbe,js,jse,wsf,wsh,lnk,pif,cpl,jar,apk,dll"
    )
    min_video_size_mb: int = 50
    remove_rejected: bool = True
    delete_rejected_data: bool = True
    auto_resume_valid: bool = True

    @staticmethod
    def _csv(value: str) -> frozenset[str]:
        return frozenset(x.strip().lower().lstrip(".") for x in value.split(",") if x.strip())

    @property
    def video_exts(self) -> frozenset[str]:
        return self._csv(self.allowed_video_extensions)

    @property
    def support_exts(self) -> frozenset[str]:
        return self._csv(self.allowed_support_extensions)

    @property
    def blocked_exts(self) -> frozenset[str]:
        return self._csv(self.blocked_extensions)

    @property
    def categories(self) -> frozenset[str]:
        return self._csv(self.qb_categories)

    @property
    def action_states(self) -> frozenset[str]:
        return self._csv(self.qb_action_states)


@lru_cache
def get_settings() -> Settings:
    return Settings()
