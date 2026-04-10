#!/usr/bin/env python3
"""
EXE 解压服务 - 后端版
支持 AES-256 加密的 ZIP 文件
"""

import os
import subprocess
from pathlib import Path
from flask import Flask, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
import logging

app = Flask(__name__, static_folder='static')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB
app.config['UPLOAD_FOLDER'] = '/tmp/exe_uploads'
app.config['EXTRACT_FOLDER'] = '/tmp/exe_extracts'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['EXTRACT_FOLDER'], exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = app.logger

# 存储已上传文件的会话信息
sessions = {}

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def check_encryption_with_7z(file_path):
    """使用 7z l 命令快速检测文件是否加密（< 2秒）"""
    try:
        result = subprocess.run(
            ['7z', 'l', '-slt', file_path],
            capture_output=True,
            text=True,
            timeout=5,
            stdin=subprocess.DEVNULL
        )
        output = result.stdout + result.stderr
        if 'Encrypted = +' in output:
            return True
        return False
    except Exception as e:
        logger.error(f"7z 检测错误: {e}")
        return False

def extract_with_7z(file_path, extract_to, password=None):
    """使用 7z 解压"""
    cmd = ['7z', 'x', '-y', f'-o{extract_to}']
    if password:
        cmd.append(f'-p{password}')
    else:
        cmd.append('-p')
    cmd.append(file_path)
    
    logger.info(f"执行 7z 解压")
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=120,
            stdin=subprocess.DEVNULL
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Timeout"

def extract_with_unrar(file_path, extract_to, password=None):
    """使用 unrar 解压 RAR 文件"""
    cmd = ['unrar', 'x', '-y', '-o+']
    if password:
        cmd.append(f'-p{password}')
    else:
        cmd.append('-p-')
    cmd.append(file_path)
    cmd.append(extract_to + '/')
    
    logger.info(f"执行 unrar 解压")
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=60,
            stdin=subprocess.DEVNULL
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Timeout"

def detect_archive_type_fast(file_path):
    """快速检测压缩文件类型"""
    with open(file_path, 'rb') as f:
        header = f.read(100)
    
    if header[:4] == b'PK\x03\x04':
        return 'zip'
    if header[:6] == b'Rar!\x1a\x07':
        return 'rar'
    if header[:6] == b'7z\xbc\xaf\x27\x1c':
        return '7z'
    
    with open(file_path, 'rb') as f:
        data = f.read(1024 * 1024)
    
    if b'Rar!\x1a\x07' in data:
        return 'rar'
    if b'PK\x03\x04' in data:
        return 'zip'
    if b'7z\xbc\xaf\x27\x1c' in data:
        return '7z'
    
    return 'unknown'

def get_file_tree(directory):
    """获取文件列表"""
    files = []
    base = Path(directory)
    
    for path in base.rglob('*'):
        if path.is_file():
            rel = path.relative_to(base)
            files.append({
                'name': path.name,
                'path': str(rel),
                'size': path.stat().st_size,
                'sizeFormatted': format_size(path.stat().st_size)
            })
    
    return sorted(files, key=lambda x: x['path'].lower())

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/upload', methods=['POST'])
def upload():
    """上传并检测文件"""
    # 检查是否是继续解压（提供 sessionId 和 password）
    session_id = request.form.get('sessionId')
    password = request.form.get('password')
    
    if session_id and password:
        # 继续解压已上传的文件
        return continue_extract(session_id, password)
    
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    file = request.files['file']
    if not file.filename:
        return jsonify({'error': '没有选择文件'}), 400
    
    # 新上传
    session_id = os.urandom(8).hex()
    upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
    extract_dir = os.path.join(app.config['EXTRACT_FOLDER'], session_id)
    os.makedirs(upload_dir)
    os.makedirs(extract_dir)
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)
    
    file_size = os.path.getsize(file_path)
    logger.info(f"上传文件: {file_path}, 大小: {file_size}")
    
    try:
        # 快速检测文件类型和加密
        archive_type = detect_archive_type_fast(file_path)
        is_encrypted = check_encryption_with_7z(file_path)
        
        logger.info(f"类型: {archive_type}, 加密: {is_encrypted}")
        
        # 保存会话信息
        sessions[session_id] = {
            'file_path': file_path,
            'archive_type': archive_type,
            'is_encrypted': is_encrypted,
            'filename': filename
        }
        
        # 如果检测到加密且没有提供密码，返回需要密码
        if is_encrypted and not password:
            return jsonify({
                'success': False,
                'needPassword': True,
                'sessionId': session_id,
                'message': '该压缩包已加密，请输入密码',
                'archiveType': archive_type
            })
        
        # 解压
        return do_extract(session_id, password)
                
    except Exception as e:
        logger.error(f"解压失败: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

def continue_extract(session_id, password):
    """继续解压已上传的文件（无需重新上传）"""
    if session_id not in sessions:
        return jsonify({'success': False, 'error': '会话已过期，请重新上传'}), 400
    
    session = sessions[session_id]
    logger.info(f"继续解压: {session['file_path']}, 密码: 已提供")
    
    try:
        return do_extract(session_id, password)
    except Exception as e:
        logger.error(f"解压失败: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

def do_extract(session_id, password):
    """执行解压"""
    session = sessions[session_id]
    file_path = session['file_path']
    archive_type = session['archive_type']
    extract_dir = os.path.join(app.config['EXTRACT_FOLDER'], session_id)
    
    # RAR 优先用 unrar
    if archive_type == 'rar':
        success, output = extract_with_unrar(file_path, extract_dir, password)
        if not success:
            logger.info("unrar 失败，尝试 7z")
            success, output = extract_with_7z(file_path, extract_dir, password)
    else:
        success, output = extract_with_7z(file_path, extract_dir, password)
    
    if not success:
        output_lower = output.lower()
        password_errors = [
            'enter password', 'wrong password', 'password is incorrect',
            'incorrect password', 'all files in archive are encrypted',
            'encrypted file', 'crc failed', 'checksum error', 'data error',
        ]
        
        is_password_error = any(err in output_lower for err in password_errors)
        
        if is_password_error or 'Timeout' in output:
            if not password:
                return jsonify({
                    'success': False,
                    'needPassword': True,
                    'sessionId': session_id,
                    'message': '该压缩包需要密码'
                })
            else:
                return jsonify({
                    'success': False,
                    'needPassword': True,
                    'sessionId': session_id,
                    'message': '密码错误，请重试'
                })
        
        return jsonify({
            'success': False,
            'error': f'解压失败: {output[:500]}'
        }), 400
    
    files = get_file_tree(extract_dir)
    logger.info(f"解压成功，找到 {len(files)} 个文件")
    
    # 清理会话
    if session_id in sessions:
        del sessions[session_id]
    
    return jsonify({
        'success': True,
        'files': files,
        'sessionId': session_id,
        'totalFiles': len(files),
        'totalSize': format_size(sum(f['size'] for f in files))
    })

@app.route('/api/download/<session_id>/<path:file_path>')
def download_file(session_id, file_path):
    extract_dir = os.path.join(app.config['EXTRACT_FOLDER'], session_id)
    full_path = os.path.join(extract_dir, file_path)
    
    if not os.path.exists(full_path):
        return jsonify({'error': '文件不存在'}), 404
    
    if not os.path.abspath(full_path).startswith(os.path.abspath(extract_dir)):
        return jsonify({'error': '非法路径'}), 403
    
    return send_file(full_path, as_attachment=True)

@app.route('/api/download-all/<session_id>')
def download_all(session_id):
    import zipfile
    extract_dir = os.path.join(app.config['EXTRACT_FOLDER'], session_id)
    
    if not os.path.exists(extract_dir):
        return jsonify({'error': '会话不存在'}), 404
    
    temp_zip = os.path.join(app.config['UPLOAD_FOLDER'], f'{session_id}.zip')
    
    with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, extract_dir)
                zf.write(file_path, arcname)
    
    return send_file(temp_zip, as_attachment=True, download_name='extracted_files.zip')

@app.route('/api/cleanup/<session_id>', methods=['POST'])
def cleanup(session_id):
    import shutil
    for folder in [app.config['UPLOAD_FOLDER'], app.config['EXTRACT_FOLDER']]:
        path = os.path.join(folder, session_id)
        if os.path.isdir(path):
            shutil.rmtree(path)
    if session_id in sessions:
        del sessions[session_id]
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
