from pydantic_settings import BaseSettings
from typing import List, Dict, Optional, Union
from pydantic import BaseModel, Field, field_validator
import json


class APIKeyConfig(BaseModel):
    key: str
    base_url: Optional[str] = "https://api.openai.com/v1"


class Settings(BaseSettings):
    API_KEYS: List[Union[Dict[str, str], str]] = []
    ALLOWED_TOKENS: List[str] = []
    AUTH_TOKEN: str = ""
    AVAILABLE_MODELS: List[str] = [
        "gpt-4-turbo-preview",
        "gpt-4",
        "gpt-3.5-turbo",
        "text-embedding-3-small"
    ]
    api_key_configs: List[APIKeyConfig] = Field(default_factory=list)

    @field_validator("API_KEYS", "ALLOWED_TOKENS", "AVAILABLE_MODELS", mode="before")
    @classmethod
    def validate_json_string(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v

    def __init__(self):
        super().__init__()
        if not self.AUTH_TOKEN:
            self.AUTH_TOKEN = self.ALLOWED_TOKENS[0] if self.ALLOWED_TOKENS else ""
        
        # 转换API密钥配置
        for key_config in self.API_KEYS:
            if isinstance(key_config, str):
                # 如果是字符串，使用默认base_url
                self.api_key_configs.append(APIKeyConfig(key=key_config))
            elif isinstance(key_config, dict):
                # 如果是字典，包含key和base_url
                self.api_key_configs.append(APIKeyConfig(**key_config))

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'


settings = Settings()
