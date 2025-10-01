"""API Router for serving JSON API definition files.

This module handles requests for OpenRPC JSON interface definitions
used by the test agent.
"""

import json
import logging
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from config import get_api_file_path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents")

@router.get("/test/api/{json_file}")
async def get_json_file(json_file: str):
    """
    获取测试智能体的API接口定义文件
    
    Args:
        json_file: API文件名
        
    Returns:
        JSON格式的API接口定义
    """
    try:
        # 构建API文件路径
        api_file_path = get_api_file_path(json_file)

        # 检查文件是否存在且是JSON文件
        if not os.path.exists(api_file_path):
            logging.warning(f"API file not found: {json_file}")
            raise HTTPException(status_code=404, detail="API文件不存在")

        if not json_file.endswith('.json'):
            logging.warning(f"Invalid file type: {json_file}")
            raise HTTPException(status_code=400, detail="只支持JSON格式的API文件")

        # 读取并返回JSON文件内容
        with open(api_file_path, encoding='utf-8') as file:
            json_content = json.load(file)

        logging.info(f"Successfully served API file: {json_file}")
        return JSONResponse(content=json_content)

    except json.JSONDecodeError as e:
        logging.error(f"JSON parsing error for file {json_file}: {str(e)}")
        raise HTTPException(status_code=500, detail="JSON文件格式错误")
    except Exception as e:
        logging.error(f"Error serving API file {json_file}: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


