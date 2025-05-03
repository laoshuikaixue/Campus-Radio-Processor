import hashlib
import json
import os
import uuid
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pydub import AudioSegment

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
            print(f"加载元数据时出错: {e}")
            return []
    return []


def save_metadata(metadata):
    try:
        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"保存元数据时出错: {e}")


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
                print(
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
                print(f"无法获取文件 {original_filename} 的音频时长: {e}")

            # 将新文件的元数据添加到总元数据列表和本次处理结果列表
            metadata.append(file_metadata)
            uploaded_metadata_results.append(file_metadata)

            # 递增顺序计数器
            new_file_order_counter += 1

        except Exception as e:
            print(f"处理文件 {original_filename} 时出错: {e}")
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
    for item in metadata:
        if item.get('merged', False):
            new_metadata.append(item)
        else:
            try:
                if os.path.exists(item['path']):
                    os.remove(item['path'])
            except Exception as e:
                print(f"删除文件 {item.get('filename', item['id'])} 时出错: {e}")

    current_order = 1
    for item in new_metadata:
        if not item.get('merged', False):
            item['order'] = current_order
            current_order += 1

    save_metadata(new_metadata)
    return {"success": True, "message": "所有未处理音频文件已删除"}


# DELETE /api/processed/all: 删除所有已合并的音频文件
@app.delete("/api/processed/all")
def delete_all_processed():
    metadata = load_metadata()
    new_metadata = []
    for item in metadata:
        if not item.get('merged', False):
            new_metadata.append(item)
        else:
            try:
                if os.path.exists(item['path']):
                    os.remove(item['path'])
            except Exception as e:
                print(f"删除文件 {item.get('filename', item['id'])} 时出错: {e}")
    save_metadata(new_metadata)
    return {"success": True, "message": "所有已处理音频文件已删除"}


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
            except Exception as e:
                print(f"删除文件 {item.get('filename', audio_id)} 时出错: {e}")
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
            except Exception as e:
                print(f"删除文件 {item.get('filename', audio_id)} 时出错: {e}")
            break

    if not item_to_delete:
        raise HTTPException(status_code=404, detail="未找到已处理的音频文件")

    metadata.remove(item_to_delete)
    save_metadata(metadata)
    return {"success": True, "message": f"已处理音频文件 {audio_id} 已删除"}


# POST /api/merge: 合并音频文件
@app.post("/api/merge", status_code=201)
def merge_audio(request: MergeRequest):
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

    try:
        # 这里执行音频合并操作
        if not files_to_merge:
            raise HTTPException(status_code=400, detail="没有有效的音频文件可合并")

        # 创建合并后的音频段
        merged_audio = None
        total_duration = 0.0

        # 首先计算总时长以便后续进度报告
        for idx, file_info in enumerate(files_to_merge):
            # 检查是否已取消处理
            if processing_tasks.get(request_id, {}).get('cancelled', False):
                # 不应抛出异常，而是返回取消状态
                if request_id in processing_tasks:
                    processing_tasks[request_id]['status'] = 'cancelled'
                return {"success": False, "message": "处理任务已被取消", "status": "cancelled"}

            try:
                audio = AudioSegment.from_file(file_info['path'])
                total_duration += len(audio) / 1000  # 转换为秒
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"处理文件 {file_info['displayName']} 时出错: {str(e)}")

        # 执行合并
        for idx, file_info in enumerate(files_to_merge):
            # 检查是否已取消处理
            if processing_tasks.get(request_id, {}).get('cancelled', False):
                # 不应抛出异常，而是返回取消状态
                if request_id in processing_tasks:
                    processing_tasks[request_id]['status'] = 'cancelled'
                return {"success": False, "message": "处理任务已被取消", "status": "cancelled"}

            try:
                # 记录开始处理当前文件
                print(f"处理文件 {idx + 1}/{len(files_to_merge)}: {file_info['displayName']}")

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
                print(f"合并进度: {progress:.2f}%")

            except Exception as e:
                error_msg = f"合并文件 {file_info['displayName']} 时出错: {str(e)}"
                print(error_msg)
                raise HTTPException(status_code=500, detail=error_msg)

        # 检查是否已取消处理
        if processing_tasks.get(request_id, {}).get('cancelled', False):
            # 不应抛出异常，而是返回取消状态
            if request_id in processing_tasks:
                processing_tasks[request_id]['status'] = 'cancelled'
            return {"success": False, "message": "处理任务已被取消", "status": "cancelled"}

        # 如果启用音量标准化
        if getattr(request, 'normalizeVolume', False):
            try:
                gain_adjustment = getattr(request, 'normalizeTargetDb', -3.0)
                print(f"正在应用音量调整: {gain_adjustment} dB")
                
                # 直接应用增益调整值，而不是计算与目标dBFS的差值
                merged_audio = merged_audio.apply_gain(gain_adjustment)
                print(f"音量调整完成: {gain_adjustment:.2f} dB")
                
                # 记录调整后的dBFS值
                final_dBFS = merged_audio.dBFS
                print(f"调整后的音量级别: {final_dBFS:.2f} dBFS")
            except Exception as e:
                print(f"音量调整失败: {str(e)}")
                # 继续使用未调整的音频，不中断处理流程
        
        # 导出合并后的音频文件
        print(f"导出合并文件到: {output_path}")
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
            'normalizeVolume': getattr(request, 'normalizeVolume', False),  # 是否已应用音量调整
            'normalizeTargetDb': getattr(request, 'normalizeTargetDb', -3.0) if getattr(request, 'normalizeVolume', False) else None  # 应用的增益调整值
        }

        # 将合并后的音频文件元数据添加到总元数据列表中
        metadata.append(merged_file_info)

        # 保存更新后的元数据
        save_metadata(metadata)

        # 更新处理状态
        if request_id in processing_tasks:
            processing_tasks[request_id]['status'] = 'completed'

        # 返回合并后的音频文件元数据
        return merged_file_info

    except Exception as e:
        error_msg = f"合并音频文件时出错: {str(e)}"
        print(error_msg)
        # 如果处理过程中出错，确保清理任何可能创建的临时文件
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except:
                pass

        # 更新处理状态
        if request_id in processing_tasks:
            processing_tasks[request_id]['status'] = 'failed'

        raise HTTPException(status_code=500, detail=error_msg)


# POST /api/cancel-processing: 取消处理任务
@app.post("/api/cancel-processing")
def cancel_processing(request: dict):
    request_id = request.get('requestId')
    if not request_id:
        raise HTTPException(status_code=400, detail="未提供处理任务ID")

    if request_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="找不到指定的处理任务")

    # 标记任务为已取消
    processing_tasks[request_id]['cancelled'] = True
    processing_tasks[request_id]['status'] = 'cancelled'

    return {"success": True, "message": "处理任务已标记为取消"}


# GET /api/download/{audio_id}: 下载指定的音频文件
@app.get("/api/download/{audio_id}")
def download_audio(audio_id: str):
    metadata = load_metadata()
    for item in metadata:
        if item['id'] == audio_id:
            if not os.path.exists(item['path']):
                raise HTTPException(status_code=404, detail="文件未找到")
            
            # 确保下载文件名带有.mp3后缀
            display_name = item['displayName']
            if item.get('merged', False) and not display_name.lower().endswith('.mp3'):
                display_name = f"{display_name}.mp3"
                
            return FileResponse(
                path=item['path'],
                filename=display_name,
                media_type='application/octet-stream'
            )
    raise HTTPException(status_code=404, detail="未找到音频文件")


# POST /api/reorder: 重新排序未合并的音频文件
@app.post("/api/reorder")
def reorder_audio(request: ReorderRequest):
    new_order_ids = request.newOrder
    if not new_order_ids:
        raise HTTPException(status_code=400, detail="未提供新的顺序")

    metadata = load_metadata()
    id_to_item = {item['id']: item for item in metadata}

    current_unmerged_ids = {item['id'] for item in metadata if not item.get('merged', False)}
    if set(new_order_ids) != current_unmerged_ids:
        raise HTTPException(status_code=400, detail="提供的顺序列表与当前未处理文件列表不匹配")

    for i, audio_id in enumerate(new_order_ids):
        if audio_id in id_to_item:
            if not id_to_item[audio_id].get('merged', False):
                id_to_item[audio_id]['order'] = i + 1
        else:
            print(f"警告: 在重新排序时找不到ID: {audio_id}")

    save_metadata(metadata)
    updated_unmerged_files = [item for item in metadata if not item.get('merged', False)]
    updated_unmerged_files.sort(key=lambda x: x.get('order', 0))
    return updated_unmerged_files


# 添加根路径的API文档重定向
@app.get("/")
def read_root():
    return {"message": "欢迎使用校园广播处理系统API", "docs_url": "/docs"}
