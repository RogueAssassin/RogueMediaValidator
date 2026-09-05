import hashlib
import json
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
    setup_unlock: bool = False
    admin_username: str = ""
    admin_password: str = ""

    torrent_client: str = ""
    torrent_url: str = ""
    torrent_username: str = ""
    torrent_password: str = ""
    torrent_scopes: str = ""
    torrent_auto_bootstrap_scopes: bool = True
    torrent_inspect_all_states: bool = True
    torrent_scope_refresh_seconds: int = 60
    torrent_action_states: str = (
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
    def scopes(self) -> frozenset[str]:
        return self._csv(self.torrent_scopes)

    @property
    def action_states(self) -> frozenset[str]:
        return self._csv(self.torrent_action_states)

    @property
    def policy_fingerprint(self) -> str:
        policy = {
            "video_extensions": sorted(self.video_exts),
            "support_extensions": sorted(self.support_exts),
            "blocked_extensions": sorted(self.blocked_exts),
            "min_video_size_mb": self.min_video_size_mb,
        }
        encoded = json.dumps(policy, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()[:16]


@lru_cache
def get_settings() -> Settings:
    return Settings()
