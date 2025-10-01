"""YAML Router for serving YAML API definition files.

This module handles requests for YAML interface definitions
used by the test agent's natural language interface.
"""

import logging
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from config import get_api_file_path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents")

@router.get("/test/api_files/{yaml_file}")
async def get_yaml_file(yaml_file: str):
    """
    获取测试智能体的YAML接口定义文件
    
    Args:
        yaml_file: YAML文件名
        
    Returns:
        YAML格式的接口定义文件
    """
    try:
        # 构建YAML文件路径
        yaml_file_path = get_api_file_path(yaml_file)

        # 检查文件是否存在且是YAML文件
        if not os.path.exists(yaml_file_path):
            logging.warning(f"YAML file not found: {yaml_file}")
            raise HTTPException(status_code=404, detail="YAML文件不存在")

        if not (yaml_file.endswith('.yaml') or yaml_file.endswith('.yml')):
            logging.warning(f"Invalid file type: {yaml_file}")
            raise HTTPException(status_code=400, detail="只支持YAML格式的文件")

        logging.info(f"Successfully serving YAML file: {yaml_file}")
        return FileResponse(
            path=yaml_file_path,
            media_type="application/x-yaml",
            filename=yaml_file
        )

    except Exception as e:
        logging.error(f"Error serving YAML file {yaml_file}: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


