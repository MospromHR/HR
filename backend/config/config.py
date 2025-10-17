from pydantic import BaseModel

class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    

class PostgresConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    database: str = "appdb"
    username: str = "user"
    password: str = "pass"
    debug: bool = True


class Config(BaseModel):
    env: str = "dev" # dev/stage/prod
    postgres: PostgresConfig = PostgresConfig()
    redis: RedisConfig = RedisConfig()

