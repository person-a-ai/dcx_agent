from pathlib import Path

from pydantic_settings import BaseSettings

_ENV_FILE = str(Path(__file__).resolve().parents[2] / ".env")


class Settings(BaseSettings):
    # 저장소: "s3" (AWS) 또는 "local" (로컬 디스크)
    storage: str = "s3"
    local_data_dir: str = "data"

    s3_bucket: str = "x"
    s3_region: str = "x"
    naver_client_id: str = "x"
    naver_client_secret: str = "x"
    claude_api_key: str = "x"
    pinecone_api_key: str = "x"
    voyage_api_key: str = "x"

    # Crawl4AI 튜닝
    crawl4ai_concurrency: int = 5
    crawl4ai_min_delay: float = 1.0
    crawl4ai_max_delay: float = 3.0
    crawl4ai_max_retries: int = 3

    # 작성자 해시 소금 — 수집 레코드의 author_hash 를 만든다.
    # 작성자가 누구인지는 저장하지 않고 몇 명인지만 세기 위한 값이다.
    # **배포마다 고정**되어야 한다 — 값이 바뀌면 같은 작성자가 다른 사람으로
    # 집계되어 08·10 의 "작성자 N명"이 어긋난다.
    # 프로덕션에서는 반드시 .env 의 AUTHOR_HASH_SALT 로 덮어쓴다.
    author_hash_salt: str = "dcx-dev-salt-change-me"

    # 배포 설정
    cors_origins: str = "*"  # 프로덕션: "https://your-domain.com"

    class Config:
        env_file = _ENV_FILE


settings = Settings()
