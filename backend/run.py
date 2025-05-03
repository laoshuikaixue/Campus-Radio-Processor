import os
import sys

def check_dependencies():
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from pydub import AudioSegment
        import uvicorn
        print("所有依赖已安装。")
        return True
    except ImportError as e:
        print(f"缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def check_ffmpeg():
    try:
        from pydub.utils import which
        if which("ffmpeg") is None:
            print("警告: 未检测到FFmpeg。音频处理功能可能无法正常工作。")
            print("请安装FFmpeg: https://ffmpeg.org/download.html")
            return False
        return True
    except Exception as e:
        print(f"检查FFmpeg时出错: {e}")
        return False

def create_directories():
    # 创建上传和处理目录
    upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    processed_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'processed')
    
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    
    print(f"上传目录: {upload_dir}")
    print(f"处理目录: {processed_dir}")

def run_app():
    if not check_dependencies():
        return
    
    check_ffmpeg()
    create_directories()
    
    print("\n启动后端服务器...")
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 切换到当前目录
    os.chdir(current_dir)
    # 直接使用uvicorn模块启动，而不是通过os.system
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    run_app()