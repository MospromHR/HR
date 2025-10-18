from pydantic import BaseModel, EmailStr, Field

from database.schema.base import UserRole


class PostgresConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    database: str = "appdb"
    username: str = "user"
    password: str = "pass"
    debug: bool = True


class SecurityConfig(BaseModel):
    jwt_secret: str = Field("change-me", min_length=1)
    access_token_expire_minutes: int = Field(60, ge=1)
    refresh_token_expire_minutes: int = Field(60 * 24 * 7, ge=1)


class SuperUserConfig(BaseModel):
    email: EmailStr = "admin@example.com"
    password: str = Field("admin123", min_length=1)
    role: UserRole = UserRole.ADMIN


class Config(BaseModel):
    env: str = "dev"  # dev/stage/prod
    postgres: PostgresConfig = PostgresConfig()
    security: SecurityConfig = SecurityConfig()
    superuser: SuperUserConfig = SuperUserConfig()
