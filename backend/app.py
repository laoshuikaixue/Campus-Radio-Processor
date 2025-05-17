import hashlib
import json
import os
import sys
import uuid
import threading
import concurrent.futures
import asyncio
from typing import List, Optional, Dict

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from loguru import logger
from pydantic import BaseModel
from pydub import AudioSegment

# 配置loguru
logger.remove()  # 移除默认处理器
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "backend/logs/app.log",
    rotation="10 MB",
    retention="7 days",
    compression="zip",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
)

app = FastAPI()

# 配置CORS - 默认允许所有源，但可以通过环境变量限制

# 加载环境变量
load_dotenv()

# 获取允许的源，默认为所有
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置上传文件夹和处理后文件夹的路径
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
PROCESSED_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'processed')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# 存储音频文件元数据的文件路径
METADATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audio_metadata.json')

# 存储当前处理任务的ID和状态
processing_tasks = {}

# 创建线程池，用于执行耗时的音频处理任务
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)  # 最多同时处理2个音频合成任务

# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket客户端连接，当前活跃连接数: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket客户端断开连接，当前活跃连接数: {len(self.active_connections)}")

    async def broadcast(self, message: Dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"广播消息失败: {e}")
                disconnected.append(connection)

        # 移除断开的连接
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)


manager = ConnectionManager()


# 数据模型
class AudioUpdate(BaseModel):
    displayName: Optional[str] = None
    order: Optional[int] = None


class MergeRequest(BaseModel):
    audioIds: List[str]
    outputName: str
    requestId: Optional[str] = None
    normalizeVolume: bool = False
    normalizeTargetDb: float = -3.0


class ReorderRequest(BaseModel):
    newOrder: List[str]


# --- WebSocket 路由 ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # 等待客户端消息，但不做任何处理
            # 此连接主要用于服务器向客户端推送处理状态
            data = await websocket.receive_text()
            logger.debug(f"从WebSocket接收到消息: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket连接发生错误: {e}")
        manager.disconnect(websocket)


# --- 元数据加载和保存 ---
def load_metadata():
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content:
                    return []
                data = json.loads(content)
                for item in data:
                    if 'hash' not in item:
                        item['hash'] = ''
                return data
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"加载元数据时出错: {e}")
            return []
    return []


def save_metadata(metadata):
    try:
        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"保存元数据时出错: {e}")


# --- 文件哈希计算 ---
# 计算文件的 SHA256 哈希值，分块读取以处理大文件
async def calculate_sha256(file: UploadFile):
    sha256 = hashlib.sha256()
    await file.seek(0)
    while chunk := await file.read(4096):
        sha256.update(chunk)
    await file.seek(0)
    return sha256.hexdigest()


# --- API 路由 ---

# POST /api/upload: 上传一个或多个音频文件并进行内容查重
@app.post("/api/upload", status_code=201)
async def upload_audio(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="没有文件部分")

    metadata = load_metadata()
    # 存储本次处理结果的元数据列表 (包括新上传和标记为重复的)
    uploaded_metadata_results = []

    # 创建哈希到已存在未合并文件元数据的映射
    existing_unmerged_hashes = {item['hash']: item for item in metadata if
                                not item.get('merged', False) and item.get('hash')}

    # 获取当前未合并文件的数量，用于计算新文件的初始顺序
    current_unmerged_count = len([item for item in metadata if not item.get('merged', False)])
    new_file_order_counter = current_unmerged_count + 1

    # 遍历上传的文件列表
    for file in files:
        original_filename = os.path.basename(file.filename)

        try:
            # 计算当前上传文件的哈希值
            uploaded_hash = await calculate_sha256(file)

            # 检查是否已存在相同哈希值的未合并文件
            if uploaded_hash in existing_unmerged_hashes:
                # 如果存在重复文件，获取现有文件的元数据
                duplicate_item = existing_unmerged_hashes[uploaded_hash]
                logger.info(
                    f"文件 {original_filename} 是重复的，已找到现有文件 {duplicate_item.get('displayName', duplicate_item['id'])}")

                # 创建一个副本，并添加标记，用于返回给前端
                duplicate_result = duplicate_item.copy()
                duplicate_result['isDuplicate'] = True  # 添加重复标记
                duplicate_result['uploadedName'] = original_filename  # 添加上传时的文件名
                # 将标记后的重复文件元数据添加到本次处理结果列表
                uploaded_metadata_results.append(duplicate_result)

                continue  # 跳过保存和创建新元数据，处理下一个文件

            # 如果文件内容不重复，则保存文件并创建新元数据
            file_extension = os.path.splitext(original_filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

            # 保存文件
            with open(file_path, "wb") as f:
                while chunk := await file.read(1024 * 1024):
                    f.write(chunk)

            # 为新文件创建元数据
            file_metadata = {
                'id': str(uuid.uuid4()),
                'originalName': original_filename,
                'displayName': original_filename,
                'filename': unique_filename,
                'path': file_path,
                'order': new_file_order_counter,
                'duration': 0,
                'merged': False,
                'hash': uploaded_hash
            }

            # 尝试获取音频时长
            try:
                audio = AudioSegment.from_file(file_path)
                file_metadata['duration'] = len(audio) / 1000
            except Exception as e:
                logger.error(f"无法获取文件 {original_filename} 的音频时长: {e}")

            # 将新文件的元数据添加到总元数据列表和本次处理结果列表
            metadata.append(file_metadata)
            uploaded_metadata_results.append(file_metadata)

            # 递增顺序计数器
            new_file_order_counter += 1

        except Exception as e:
            logger.error(f"处理文件 {original_filename} 时出错: {e}")
            # 如果处理单个文件出错，可以记录错误并继续处理下一个

    # 保存更新后的元数据到文件
    save_metadata(metadata)

    # 返回本次处理（包括新上传和标记为重复）的文件的元数据列表
    return uploaded_metadata_results


# GET /api/audio: 获取所有未合并的音频文件元数据
@app.get("/api/audio")
def get_audio_files():
    metadata = load_metadata()
    unmerged_files = [item for item in metadata if not item.get('merged', False)]
    unmerged_files.sort(key=lambda x: x.get('order', 0))
    return unmerged_files


# GET /api/processed: 获取所有已合并的音频文件元数据
@app.get("/api/processed")
def get_processed_files():
    metadata = load_metadata()
    processed_files = [item for item in metadata if item.get('merged', False)]
    return processed_files


# PUT /api/audio/{audio_id}: 更新未合并音频文件的元数据
@app.put("/api/audio/{audio_id}")
def update_audio(audio_id: str, data: AudioUpdate):
    metadata = load_metadata()
    for item in metadata:
        if item['id'] == audio_id and not item.get('merged', False):
            if data.displayName is not None:
                item['displayName'] = data.displayName
            save_metadata(metadata)
            return item
    raise HTTPException(status_code=404, detail="未找到未处理的音频文件")


# PUT /api/processed/{audio_id}: 更新已合并音频文件的元数据
@app.put("/api/processed/{audio_id}")
def update_processed(audio_id: str, data: AudioUpdate):
    metadata = load_metadata()
    for item in metadata:
        if item['id'] == audio_id and item.get('merged', False):
            if data.displayName is not None:
                item['displayName'] = data.displayName
            save_metadata(metadata)
            return item
    raise HTTPException(status_code=404, detail="未找到已处理的音频文件")


# DELETE /api/audio/all: 删除所有未合并的音频文件
@app.delete("/api/audio/all")
def delete_all_audio():
    metadata = load_metadata()
    new_metadata = []
    deleted_count = 0
    error_count = 0

    for item in metadata:
        if item.get('merged', False):
            new_metadata.append(item)
        else:
            try:
                if os.path.exists(item['path']):
                    os.remove(item['path'])
                    deleted_count += 1
                    logger.info(f"已删除文件: {item['path']}")
            except Exception as e:
                error_count += 1
                logger.error(f"删除文件 {item.get('filename', item['id'])} 时出错: {e}")

    logger.info(f"成功删除 {deleted_count} 个文件，处理失败 {error_count} 个文件")
    save_metadata(new_metadata)
    return {"success": True, "message": f"所有未处理音频文件已删除，共 {deleted_count} 个"}


# DELETE /api/processed/all: 删除所有已合并的音频文件
@app.delete("/api/processed/all")
def delete_all_processed():
    metadata = load_metadata()
    new_metadata = []
    deleted_count = 0
    error_count = 0

    for item in metadata:
        if not item.get('merged', False):
            new_metadata.append(item)
        else:
            try:
                if os.path.exists(item['path']):
                    os.remove(item['path'])
                    deleted_count += 1
                    logger.info(f"已删除已处理文件: {item['path']}")
            except Exception as e:
                error_count += 1
                logger.error(f"删除文件 {item.get('filename', item['id'])} 时出错: {e}")

    logger.info(f"成功删除 {deleted_count} 个已处理文件，处理失败 {error_count} 个文件")
    save_metadata(new_metadata)
    return {"success": True, "message": f"所有已处理音频文件已删除，共 {deleted_count} 个"}


# DELETE /api/audio/{audio_id}: 删除指定的未合并音频文件
@app.delete("/api/audio/{audio_id}")
def delete_audio(audio_id: str):
    metadata = load_metadata()
    item_to_delete = None

    for item in metadata:
        if item['id'] == audio_id and not item.get('merged', False):
            item_to_delete = item
            try:
                if os.path.exists(item['path']):
                    os.remove(item['path'])
                    logger.info(f"已删除文件: {item['path']}")
            except Exception as e:
                logger.error(f"删除文件 {item.get('filename', audio_id)} 时出错: {e}")
            break

    if not item_to_delete:
        raise HTTPException(status_code=404, detail="未找到未处理的音频文件")

    metadata.remove(item_to_delete)

    current_order = 1
    for item in metadata:
        if not item.get('merged', False):
            item['order'] = current_order
            current_order += 1

    save_metadata(metadata)
    return {"success": True, "message": f"音频文件 {audio_id} 已删除"}


# DELETE /api/processed/{audio_id}: 删除指定的已处理音频文件
@app.delete("/api/processed/{audio_id}")
def delete_processed_audio(audio_id: str):
    metadata = load_metadata()
    item_to_delete = None

    for item in metadata:
        if item['id'] == audio_id and item.get('merged', True):
            item_to_delete = item
            try:
                if os.path.exists(item['path']):
                    os.remove(item['path'])
                    logger.info(f"已删除已处理文件: {item['path']}")
            except Exception as e:
                logger.error(f"删除文件 {item.get('filename', audio_id)} 时出错: {e}")
            break

    if not item_to_delete:
        raise HTTPException(status_code=404, detail="未找到已处理的音频文件")

    metadata.remove(item_to_delete)
    save_metadata(metadata)
    return {"success": True, "message": f"已处理音频文件 {audio_id} 已删除"}


# POST /api/merge: 合并音频文件
@app.post("/api/merge", status_code=201)
async def merge_audio(request: MergeRequest):
    if not request.audioIds:
        raise HTTPException(status_code=400, detail="没有提供要合并的音频文件ID")

    # 验证输出文件名
    if not request.outputName or not request.outputName.strip():
        raise HTTPException(status_code=400, detail="必须提供输出文件名")

    merged_output_name = request.outputName.strip()

    # 获取请求ID，用于取消处理
    request_id = getattr(request, 'requestId', str(uuid.uuid4()))
    processing_tasks[request_id] = {'status': 'processing', 'cancelled': False}

    # 加载元数据
    metadata = load_metadata()

    # 获取所有待合并文件的元数据信息，并验证它们都是有效的
    files_to_merge = []
    for audio_id in request.audioIds:
        audio_file = next((item for item in metadata if item['id'] == audio_id and not item.get('merged', False)), None)
        if not audio_file:
            raise HTTPException(status_code=404, detail=f"未找到ID为 {audio_id} 的待处理音频文件")
        files_to_merge.append(audio_file)

    # 根据 order 属性排序待合并的文件
    files_to_merge.sort(key=lambda x: x.get('order', 0))

    # 创建唯一的输出文件名
    output_filename = f"{uuid.uuid4()}.mp3"  # 使用 MP3 作为合并后的格式
    output_path = os.path.join(PROCESSED_FOLDER, output_filename)
    
    # 将音频处理任务提交到线程池中异步执行
    thread_pool.submit(
        process_audio_files,
        files_to_merge,
        merged_output_name,
        output_filename,
        output_path,
        request_id,
        getattr(request, 'normalizeVolume', False),
        getattr(request, 'normalizeTargetDb', -3.0)
    )
    
    # 立即返回处理状态，不等待处理完成
    return {
        "id": request_id,
        "status": "processing",
        "message": "音频处理任务已提交到后台执行",
        "totalFiles": len(files_to_merge)
    }

# 后台执行音频处理的函数
def process_audio_files(files_to_merge, merged_output_name, output_filename, output_path, 
                        request_id, normalize_volume, normalize_target_db):
    logger.info(f"开始后台处理音频文件 (请求ID: {request_id})")
    
    try:
        # 这里执行音频合并操作
        if not files_to_merge:
            logger.error("没有有效的音频文件可合并")
            processing_tasks[request_id]['status'] = 'failed'
            # 通知前端处理失败
            asyncio.run(manager.broadcast({
                "type": "merge_failed",
                "requestId": request_id,
                "stage": "failed",
                "message": "没有有效的音频文件可合并"
            }))
            return

        # 创建合并后的音频段
        merged_audio = None
        total_duration = 0.0

        # 首先计算总时长以便后续进度报告
        for idx, file_info in enumerate(files_to_merge):
            # 检查是否已取消处理
            if processing_tasks.get(request_id, {}).get('cancelled', False):
                logger.info(f"处理任务 {request_id} 已被取消")
                if request_id in processing_tasks:
                    processing_tasks[request_id]['status'] = 'cancelled'
                # 通知前端处理已取消
                asyncio.run(manager.broadcast({
                    "type": "merge_cancelled",
                    "requestId": request_id,
                    "stage": "cancelled",
                    "message": "处理任务已被取消"
                }))
                return

            try:
                audio = AudioSegment.from_file(file_info['path'])
                total_duration += len(audio) / 1000  # 转换为秒
            except Exception as e:
                error_msg = f"处理文件 {file_info['displayName']} 时出错: {str(e)}"
                logger.error(error_msg)
                # 通知前端处理出错
                asyncio.run(manager.broadcast({
                    "type": "merge_failed",
                    "requestId": request_id,
                    "stage": "failed",
                    "message": error_msg,
                    "fileInfo": file_info
                }))
                processing_tasks[request_id]['status'] = 'failed'
                return

        # 执行合并
        for idx, file_info in enumerate(files_to_merge):
            # 检查是否已取消处理
            if processing_tasks.get(request_id, {}).get('cancelled', False):
                logger.info(f"处理任务 {request_id} 已被取消")
                if request_id in processing_tasks:
                    processing_tasks[request_id]['status'] = 'cancelled'
                # 通知前端处理已取消
                asyncio.run(manager.broadcast({
                    "type": "merge_cancelled",
                    "requestId": request_id,
                    "stage": "cancelled",
                    "message": "处理任务已被取消"
                }))
                return

            try:
                # 记录开始处理当前文件
                logger.info(f"处理文件 {idx + 1}/{len(files_to_merge)}: {file_info['displayName']}")

                # 通知前端当前处理进度
                asyncio.run(manager.broadcast({
                    "type": "merge_progress",
                    "requestId": request_id,
                    "currentFile": idx + 1,
                    "totalFiles": len(files_to_merge),
                    "fileName": file_info['displayName'],
                    "fileId": file_info['id'],
                    "stage": "processing_file"
                }))

                # 加载当前音频段
                audio = AudioSegment.from_file(file_info['path'])

                # 如果是第一个文件，初始化合并音频
                if merged_audio is None:
                    merged_audio = audio
                else:
                    # 合并当前音频段
                    merged_audio += audio

                # 计算并打印进度
                progress = (idx + 1) / len(files_to_merge) * 100
                logger.info(f"合并进度: {progress:.2f}%")

                # 通知前端处理进度
                asyncio.run(manager.broadcast({
                    "type": "merge_progress",
                    "requestId": request_id,
                    "progress": progress,
                    "currentFile": idx + 1,
                    "totalFiles": len(files_to_merge),
                    "stage": "file_processed"
                }))

                # 更新进度
                if request_id in processing_tasks:
                    processing_tasks[request_id]['progress'] = int((idx + 1) / len(files_to_merge) * 60)  # 0-60%
                    processing_tasks[request_id]['stage'] = f"merging {file_info['displayName']}"
                    processing_tasks[request_id]['message'] = f"正在合并: {file_info['displayName']}"

            except Exception as e:
                error_msg = f"合并文件 {file_info['displayName']} 时出错: {str(e)}"
                logger.error(error_msg)
                # 通知前端处理出错
                asyncio.run(manager.broadcast({
                    "type": "merge_failed",
                    "requestId": request_id,
                    "stage": "failed",
                    "message": error_msg,
                    "fileInfo": file_info
                }))
                processing_tasks[request_id]['status'] = 'failed'
                return

        # 检查是否已取消处理
        if processing_tasks.get(request_id, {}).get('cancelled', False):
            logger.info(f"处理任务 {request_id} 已被取消")
            if request_id in processing_tasks:
                processing_tasks[request_id]['status'] = 'cancelled'
            # 通知前端处理已取消
            asyncio.run(manager.broadcast({
                "type": "merge_cancelled",
                "requestId": request_id,
                "stage": "cancelled",
                "message": "处理任务已被取消"
            }))
            return

        # 通知前端音量调整阶段开始
        asyncio.run(manager.broadcast({
            "type": "merge_progress",
            "requestId": request_id,
            "stage": "volume_normalizing",
            "normalizeVolume": normalize_volume
        }))

        # 如果启用音量标准化
        if normalize_volume:
            try:
                gain_adjustment = normalize_target_db
                logger.info(f"正在应用音量调整: {gain_adjustment} dB")

                # 直接应用增益调整值，而不是计算与目标dBFS的差值
                merged_audio = merged_audio.apply_gain(gain_adjustment)
                logger.info(f"音量调整完成: {gain_adjustment:.2f} dB")

                # 记录调整后的dBFS值
                final_dBFS = merged_audio.dBFS
                logger.info(f"调整后的音量级别: {final_dBFS:.2f} dBFS")

                # 通知前端音量调整完成
                asyncio.run(manager.broadcast({
                    "type": "merge_progress",
                    "requestId": request_id,
                    "stage": "volume_normalized",
                    "gainApplied": gain_adjustment,
                    "finalDbFS": final_dBFS
                }))

                # 音量标准化阶段
                if request_id in processing_tasks:
                    processing_tasks[request_id]['progress'] = 70
                    processing_tasks[request_id]['stage'] = "normalizing"
                    processing_tasks[request_id]['message'] = "正在进行音量标准化..."
            except Exception as e:
                error_msg = f"音量调整失败: {str(e)}"
                logger.error(error_msg)
                # 通知前端音量调整警告
                asyncio.run(manager.broadcast({
                    "type": "merge_warning",
                    "requestId": request_id,
                    "stage": "volume_normalizing",
                    "message": error_msg
                }))
                # 继续使用未调整的音频，不中断处理流程

        # 通知前端导出阶段开始
        asyncio.run(manager.broadcast({
            "type": "merge_progress",
            "requestId": request_id,
            "stage": "exporting"
        }))

        # 导出合并后的音频文件
        logger.info(f"导出合并文件到: {output_path}")
        merged_audio.export(output_path, format="mp3")

        # 创建合并后的音频文件元数据
        merged_file_info = {
            'id': str(uuid.uuid4()),
            'originalName': merged_output_name,
            'displayName': merged_output_name,
            'filename': output_filename,
            'path': output_path,
            'duration': len(merged_audio) / 1000,  # 以秒为单位的时长
            'merged': True,
            'mergedFrom': [f['id'] for f in files_to_merge],
            'normalizeVolume': normalize_volume,  # 是否已应用音量调整
            'normalizeTargetDb': normalize_target_db if normalize_volume else None  # 应用的增益调整值
        }

        # 加载最新的元数据
        metadata = load_metadata()
        
        # 将合并后的音频文件元数据添加到总元数据列表中
        metadata.append(merged_file_info)

        # 保存更新后的元数据
        save_metadata(metadata)

        # 更新处理状态
        if request_id in processing_tasks:
            processing_tasks[request_id]['status'] = 'completed'
            processing_tasks[request_id]['fileInfo'] = merged_file_info

        # 通知前端处理完成
        asyncio.run(manager.broadcast({
            "type": "merge_completed",
            "requestId": request_id,
            "stage": "completed",
            "fileInfo": merged_file_info,
            "message": "音频处理任务已完成"
        }))
        
        logger.info(f"音频处理任务 {request_id} 已完成")

        # 完成
        if request_id in processing_tasks:
            processing_tasks[request_id]['progress'] = 100
            processing_tasks[request_id]['stage'] = "completed"
            processing_tasks[request_id]['message'] = "处理完成"

    except Exception as e:
        error_msg = f"合并音频文件时出错: {str(e)}"
        logger.error(error_msg)
        # 如果处理过程中出错，确保清理任何可能创建的临时文件
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except Exception as cleanup_error:
                logger.error(f"清理临时文件失败: {cleanup_error}")

        # 更新处理状态
        if request_id in processing_tasks:
            processing_tasks[request_id]['status'] = 'failed'
            processing_tasks[request_id]['progress'] = 0
            processing_tasks[request_id]['stage'] = "failed"
            processing_tasks[request_id]['message'] = str(e)

        # 通知前端处理失败
        asyncio.run(manager.broadcast({
            "type": "merge_failed",
            "requestId": request_id,
            "stage": "failed",
            "message": error_msg
        }))
        
        logger.error(f"音频处理任务 {request_id} 失败: {error_msg}")


# POST /api/cancel-processing: 取消处理任务
@app.post("/api/cancel-processing")
async def cancel_processing(request: dict):
    request_id = request.get('requestId')
    if not request_id:
        raise HTTPException(status_code=400, detail="未提供处理任务ID")

    if request_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="找不到指定的处理任务")

    # 标记任务为已取消
    processing_tasks[request_id]['cancelled'] = True
    processing_tasks[request_id]['status'] = 'cancelled'

    # 通过WebSocket广播任务已取消（统一type和结构）
    await manager.broadcast({
        "type": "merge_cancelled",
        "requestId": request_id,
        "stage": "cancelled",
        "message": "处理任务已被取消"
    })

    return {"success": True, "message": "处理任务已标记为取消"}


# POST /api/check-processing-status: 检查处理任务状态
@app.post("/api/check-processing-status")
async def check_processing_status(request: dict):
    request_id = request.get('requestId')
    if not request_id:
        raise HTTPException(status_code=400, detail="未提供处理任务ID")

    if request_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="找不到指定的处理任务")
    
    # 获取当前任务状态
    task_status = processing_tasks[request_id].get('status', 'processing')
    progress = processing_tasks[request_id].get('progress', 0)
    stage = processing_tasks[request_id].get('stage', '')
    message = processing_tasks[request_id].get('message', '')
    
    # 构建响应数据
    response_data = {
        "requestId": request_id,
        "status": task_status,
        "progress": progress,
        "stage": stage,
        "message": message
    }
    
    # 如果任务已完成且有关联的文件信息，添加到响应中
    if task_status == 'completed' and 'fileInfo' in processing_tasks[request_id]:
        response_data['fileInfo'] = processing_tasks[request_id]['fileInfo']
    
    logger.info(f"检查处理状态: 请求ID={request_id}, 状态={task_status}, 进度={progress}, 阶段={stage}")
    
    return response_data


# GET /api/download/{audio_id}: 下载指定的音频文件
@app.get("/api/download/{audio_id}")
def download_audio(audio_id: str):
    try:
        metadata = load_metadata()
        for item in metadata:
            if item['id'] == audio_id:
                if not os.path.exists(item['path']):
                    logger.error(f"文件未找到: {item['path']}")
                    raise HTTPException(status_code=404, detail="文件未找到")

                # 确保下载文件名带有.mp3后缀
                display_name = item['displayName']
                if item.get('merged', False) and not display_name.lower().endswith('.mp3'):
                    display_name = f"{display_name}.mp3"

                logger.info(f"下载文件: {item['path']} (显示为 {display_name})")
                return FileResponse(
                    path=item['path'],
                    filename=display_name,
                    media_type='application/octet-stream'
                )

        logger.warning(f"未找到音频文件ID: {audio_id}")
        raise HTTPException(status_code=404, detail="未找到音频文件")
    except HTTPException:
        # 直接重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"下载音频文件时出错: {e}")
        raise HTTPException(status_code=500, detail=f"下载音频文件时出错: {str(e)}")


# POST /api/reorder: 重新排序未合并的音频文件
@app.post("/api/reorder")
def reorder_audio(request: ReorderRequest):
    new_order_ids = request.newOrder
    if not new_order_ids:
        raise HTTPException(status_code=400, detail="未提供新的顺序")

    try:
        metadata = load_metadata()
        id_to_item = {item['id']: item for item in metadata}

        current_unmerged_ids = {item['id'] for item in metadata if not item.get('merged', False)}
        if set(new_order_ids) != current_unmerged_ids:
            logger.warning("提供的顺序列表与当前未处理文件列表不匹配")
            raise HTTPException(status_code=400, detail="提供的顺序列表与当前未处理文件列表不匹配")

        for i, audio_id in enumerate(new_order_ids):
            if audio_id in id_to_item:
                if not id_to_item[audio_id].get('merged', False):
                    id_to_item[audio_id]['order'] = i + 1
            else:
                logger.warning(f"在重新排序时找不到ID: {audio_id}")

        save_metadata(metadata)
        updated_unmerged_files = [item for item in metadata if not item.get('merged', False)]
        updated_unmerged_files.sort(key=lambda x: x.get('order', 0))
        logger.info(f"已重新排序 {len(updated_unmerged_files)} 个文件")
        return updated_unmerged_files
    except Exception as e:
        logger.error(f"重新排序时出错: {e}")
        raise HTTPException(status_code=500, detail=f"重新排序时出错: {str(e)}")


# 添加根路径的API文档重定向
@app.get("/")
def read_root():
    return {"message": "欢迎使用校园广播处理系统API", "docs_url": "/docs"}
