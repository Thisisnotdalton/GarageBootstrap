from importlib.resources import files
from pathlib import Path
from functools import cached_property, lru_cache
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_url: str = Field('garage.example.com', description='Garage host to connect to.')
    api_key: str = Field('No API key provided', description='Garage API key.')
    api_key_file: str = Field('',
                              description='Path to file containing the Garage API key. Takes precedence over the Garage API key.')
    model_config = SettingsConfigDict(env_prefix='GARAGE_')

    @model_validator(mode="after")
    def load_api_key_from_file(self):
        if isinstance(self.api_key_file, str) and len(self.api_key_file) > 0:
            try:
                self.api_key = Path(self.api_key_file).read_text().strip()
            except Exception as e:
                raise ValueError(f"Failed to read Garage API key file: {e}")

        if not self.api_key:
            raise ValueError("Garage API key must be provided via env or file")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
