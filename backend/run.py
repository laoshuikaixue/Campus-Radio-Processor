import os
import sys
from loguru import logger


def check_dependencies():
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from pydub import AudioSegment
        import uvicorn
        import loguru
        logger.info("所有依赖已安装。")
        return True
    except ImportError as e:
        logger.error(f"缺少依赖: {e}")
        logger.error("请运行: pip install -r requirements.txt")
        return False


def check_ffmpeg():
    try:
        from pydub.utils import which
        if which("ffmpeg") is None:
            logger.warning("警告: 未检测到FFmpeg。音频处理功能可能无法正常工作。")
            logger.warning("请安装FFmpeg: https://ffmpeg.org/download.html")
            return False
        return True
    except Exception as e:
        logger.error(f"检查FFmpeg时出错: {e}")
        return False


def create_directories():
    # 创建上传、处理和日志目录
    upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    processed_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'processed')
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')

    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)

    logger.info(f"上传目录: {upload_dir}")
    logger.info(f"处理目录: {processed_dir}")
    logger.info(f"日志目录: {logs_dir}")


def setup_logger():
    # 配置loguru
    logger.remove()  # 移除默认处理器
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )

    # 添加文件日志
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    logger.add(
        os.path.join(logs_dir, "app.log"),
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
    )


def run_app():
    # 设置日志
    setup_logger()

    if not check_dependencies():
        return

    check_ffmpeg()
    create_directories()

    logger.info("\n启动后端服务器...")
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 切换到当前目录
    os.chdir(current_dir)
    # 直接使用uvicorn模块启动，而不是通过os.system
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    run_app()
