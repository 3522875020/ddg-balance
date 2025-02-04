from fastapi import APIRouter, Depends, Header, Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import SecurityService
from app.services.chat.retry_handler import RetryHandler
from app.services.key_manager import KeyManager
from app.services.model_service import ModelService
from app.services.openai_chat_service import OpenAIChatService
from app.services.embedding_service import EmbeddingService
from app.schemas.openai_models import ChatRequest, EmbeddingRequest
from app.core.config import settings
from app.core.logger import get_openai_logger

router = APIRouter()
logger = get_openai_logger()
security = HTTPBearer()

# 初始化服务
security_service = SecurityService(settings.ALLOWED_TOKENS, settings.AUTH_TOKEN)
key_manager = KeyManager(settings.api_key_configs)
model_service = ModelService()
embedding_service = EmbeddingService(key_manager)

# 创建重试处理器
retry_handler = RetryHandler(key_manager)


@router.get("/v1/models")
@router.get("/hf/v1/models")
async def list_models(
    authorization: str = Header(None),
    token: str = Depends(security_service.verify_authorization),
):
    logger.info("-" * 50 + "list_models" + "-" * 50)
    logger.info("Handling models list request")
    try:
        return model_service.get_models()
    except Exception as e:
        logger.error(f"Error getting models list: {str(e)}")
        raise HTTPException(500, "Internal server error while fetching models list") from e


@router.post("/v1/chat/completions")
@router.post("/hf/v1/chat/completions")
async def chat_completion(
    request: ChatRequest,
    authorization: str = Header(None),
    token: str = Depends(security_service.verify_authorization),
):
    chat_service = OpenAIChatService(key_manager)
    logger.info("-" * 50 + "chat_completion" + "-" * 50)
    logger.info(f"Handling chat completion request for model: {request.model}")
    logger.info(f"Request: \n{request.model_dump_json(indent=2)}")

    try:
        response = await chat_service.create_chat_completion(request=request)
        # 处理流式响应
        if request.stream:
            return StreamingResponse(response, media_type="text/event-stream")
        logger.info("Chat completion request successful")
        return response

    except Exception as e:
        logger.error(f"Chat completion failed: {str(e)}")
        raise HTTPException(500, "Chat completion failed") from e


@router.post("/v1/embeddings")
@router.post("/hf/v1/embeddings")
async def embedding(
    request: EmbeddingRequest,
    authorization: str = Header(None),
    token: str = Depends(security_service.verify_authorization),
):
    logger.info("-" * 50 + "embedding" + "-" * 50)
    logger.info(f"Handling embedding request for model: {request.model}")
    try:
        response = await embedding_service.create_embedding(request)
        logger.info("Embedding request successful")
        return response
    except Exception as e:
        logger.error(f"Embedding request failed: {str(e)}")
        raise HTTPException(500, "Embedding request failed") from e


@router.get("/v1/keys/list")
@router.get("/hf/v1/keys/list")
async def get_keys_list(
    authorization: str = Header(None),
    token: str = Depends(security_service.verify_authorization),
):
    """获取有效和无效的API key列表"""
    logger.info("-" * 50 + "get_keys_list" + "-" * 50)
    logger.info("Handling keys list request")
    try:
        keys_status = await key_manager.get_keys_by_status()
        return {
            "status": "success",
            "data": {
                "valid_keys": keys_status["valid_keys"],
                "invalid_keys": keys_status["invalid_keys"]
            },
            "total": len(keys_status["valid_keys"]) + len(keys_status["invalid_keys"])
        }
    except Exception as e:
        logger.error(f"Error getting keys list: {str(e)}")
        raise HTTPException(500, "Internal server error while fetching keys list") from e
