"""
模拟agent-connect包的功能

用于测试目的，提供DidWbaVerifier的基础实现
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class DidWbaVerifierError(Exception):
    """DID-WBA验证错误"""

    def __init__(self, message: str, status_code: int = 401):
        super().__init__(message)
        self.status_code = status_code


class DidWbaVerifierConfig:
    """DID-WBA验证器配置"""

    def __init__(
        self,
        jwt_private_key: Optional[str] = None,
        jwt_public_key: Optional[str] = None,
        jwt_algorithm: str = "RS256",
        access_token_expire_minutes: int = 60,
        nonce_expiration_minutes: int = 5,
        timestamp_expiration_minutes: int = 5,
    ):
        self.jwt_private_key = jwt_private_key
        self.jwt_public_key = jwt_public_key
        self.jwt_algorithm = jwt_algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.nonce_expiration_minutes = nonce_expiration_minutes
        self.timestamp_expiration_minutes = timestamp_expiration_minutes


class DidWbaVerifier:
    """模拟的DID-WBA验证器"""

    def __init__(self, config: DidWbaVerifierConfig):
        self.config = config
        logger.info("Initialized mock DidWbaVerifier")

    async def verify_auth_header(self, auth_header: str, domain: str) -> Dict[str, Any]:
        """
        模拟验证认证头

        Args:
            auth_header: Authorization头值
            domain: 请求域名

        Returns:
            认证用户数据

        Raises:
            DidWbaVerifierError: 认证失败时抛出
        """
        logger.info(f"Mock verification: auth_header={auth_header}, domain={domain}")

        # 简单的模拟验证逻辑
        if not auth_header:
            raise DidWbaVerifierError("Missing authorization header", 401)

        if not auth_header.startswith("Bearer ") and not auth_header.startswith("DIDWba "):
            raise DidWbaVerifierError("Invalid authorization header format", 401)

        token = auth_header[7:]  # 移除 "Bearer " 前缀

        # 模拟令牌验证失败
        if not token or token == "invalid-token":
            raise DidWbaVerifierError("Invalid token", 401)

        # 对于测试，我们可以接受特定的测试令牌
        if token == "test-mock-jwt-token":
            return {
                "user_id": "test-user",
                "domain": domain,
                "token_type": "bearer",
                "access_token": token
            }

        # 其他情况都视为认证失败
        raise DidWbaVerifierError("Token verification failed", 401)
