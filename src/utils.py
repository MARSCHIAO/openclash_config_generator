#!/usr/bin/env python3
"""
Utilities
工具函数模块
"""

import os
import sys
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    设置日志系统
    
    Args:
        level: 日志级别
        
    Returns:
        配置好的 logger 对象
    """
    # 创建 logger
    logger = logging.getLogger('openclash_generator')
    logger.setLevel(level)
    
    # 如果已经有处理器，直接返回
    if logger.handlers:
        return logger
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # 添加处理器到 logger
    logger.addHandler(console_handler)
    
    # 创建日志目录
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # 创建文件处理器
    log_file = log_dir / f'generator_{datetime.now().strftime("%Y%m%d")}.log'
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


def ensure_dir(path: Path) -> None:
    """
    确保目录存在
    
    Args:
        path: 目录路径
    """
    path.mkdir(parents=True, exist_ok=True)


def validate_config(config: Dict) -> bool:
    """
    验证项目配置文件
    
    Args:
        config: 配置字典
        
    Returns:
        是否有效
    """
    required_keys = ['upstream', 'output', 'openclash']
    
    for key in required_keys:
        if key not in config:
            logging.error(f"配置缺少必需的键: {key}")
            return False
    
    # 验证 upstream 配置
    if 'repo' not in config['upstream']:
        logging.error("upstream 配置缺少 repo 字段")
        return False
    
    # 验证 output 配置
    if 'directory' not in config['output']:
        logging.error("output 配置缺少 directory 字段")
        return False
    
    if 'formats' not in config['output']:
        logging.error("output 配置缺少 formats 字段")
        return False
    
    return True


def calculate_file_hash(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    计算文件哈希值
    
    Args:
        file_path: 文件路径
        algorithm: 哈希算法 (md5, sha1, sha256等)
        
    Returns:
        哈希值字符串
    """
    hash_obj = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


def read_file(file_path: Path, encoding: str = 'utf-8') -> str:
    """
    读取文件内容
    
    Args:
        file_path: 文件路径
        encoding: 文件编码
        
    Returns:
        文件内容字符串
    """
    with open(file_path, 'r', encoding=encoding) as f:
        return f.read()


def write_file(file_path: Path, content: str, encoding: str = 'utf-8') -> None:
    """
    写入文件内容
    
    Args:
        file_path: 文件路径
        content: 文件内容
        encoding: 文件编码
    """
    with open(file_path, 'w', encoding=encoding) as f:
        f.write(content)


def format_bytes(size: int) -> str:
    """
    格式化字节大小
    
    Args:
        size: 字节数
        
    Returns:
        格式化后的字符串 (如 "1.23 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def get_file_info(file_path: Path) -> Dict[str, Any]:
    """
    获取文件信息
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件信息字典
    """
    stat = file_path.stat()
    
    return {
        'path': str(file_path),
        'name': file_path.name,
        'size': stat.st_size,
        'size_formatted': format_bytes(stat.st_size),
        'modified_time': datetime.fromtimestamp(stat.st_mtime),
        'created_time': datetime.fromtimestamp(stat.st_ctime),
        'hash_sha256': calculate_file_hash(file_path, 'sha256'),
    }


def parse_cron_expression(cron_expr: str) -> Dict[str, str]:
    """
    解析 Cron 表达式
    
    Args:
        cron_expr: Cron 表达式字符串 (如 "0 2 * * *")
        
    Returns:
        解析后的字典
    """
    parts = cron_expr.split()
    
    if len(parts) != 5:
        raise ValueError(f"无效的 Cron 表达式: {cron_expr}")
    
    return {
        'minute': parts[0],
        'hour': parts[1],
        'day_of_month': parts[2],
        'month': parts[3],
        'day_of_week': parts[4],
    }


def create_download_url(repo: str, branch: str, file_path: str) -> str:
    """
    创建 GitHub 原始文件下载链接
    
    Args:
        repo: 仓库名称 (如 "HenryChiao/mihomo_yamls")
        branch: 分支名称
        file_path: 文件路径
        
    Returns:
        下载链接
    """
    return f"https://raw.githubusercontent.com/{repo}/{branch}/{file_path}"


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除非法字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        清理后的文件名
    """
    # 移除非法字符
    illegal_chars = '<>:"/\\|?*'
    for char in illegal_chars:
        filename = filename.replace(char, '_')
    
    # 移除前后空格
    filename = filename.strip()
    
    # 限制长度
    max_length = 255
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext
    
    return filename


def compare_versions(version1: str, version2: str) -> int:
    """
    比较版本号
    
    Args:
        version1: 版本号1 (如 "1.2.3")
        version2: 版本号2 (如 "1.2.4")
        
    Returns:
        -1 (version1 < version2)
        0  (version1 == version2)
        1  (version1 > version2)
    """
    v1_parts = [int(x) for x in version1.split('.')]
    v2_parts = [int(x) for x in version2.split('.')]
    
    # 补齐长度
    max_len = max(len(v1_parts), len(v2_parts))
    v1_parts.extend([0] * (max_len - len(v1_parts)))
    v2_parts.extend([0] * (max_len - len(v2_parts)))
    
    for v1, v2 in zip(v1_parts, v2_parts):
        if v1 < v2:
            return -1
        elif v1 > v2:
            return 1
    
    return 0


class GitHelper:
    """Git 操作辅助类"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化 Git 辅助工具
        
        Args:
            logger: 日志对象
        """
        self.logger = logger or logging.getLogger(__name__)
        
        try:
            from git import Repo
            self.git_available = True
        except ImportError:
            self.logger.warning("GitPython 未安装，Git 功能不可用")
            self.git_available = False
    
    def clone_or_pull(self, repo_url: str, local_path: Path, branch: str = 'main') -> bool:
        """
        克隆或拉取仓库
        
        Args:
            repo_url: 仓库 URL
            local_path: 本地路径
            branch: 分支名称
            
        Returns:
            是否成功
        """
        if not self.git_available:
            self.logger.error("GitPython 不可用")
            return False
        
        try:
            from git import Repo
            
            if (local_path / '.git').exists():
                # 更新现有仓库
                repo = Repo(local_path)
                origin = repo.remote('origin')
                origin.pull(branch)
                self.logger.info(f"已更新仓库: {repo_url}")
            else:
                # 克隆新仓库
                Repo.clone_from(repo_url, local_path, branch=branch)
                self.logger.info(f"已克隆仓库: {repo_url}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Git 操作失败: {e}")
            return False
    
    def get_latest_commit_hash(self, local_path: Path) -> Optional[str]:
        """
        获取最新提交哈希
        
        Args:
            local_path: 本地仓库路径
            
        Returns:
            提交哈希字符串，失败返回 None
        """
        if not self.git_available:
            return None
        
        try:
            from git import Repo
            repo = Repo(local_path)
            return repo.head.commit.hexsha
        except Exception as e:
            self.logger.error(f"获取提交哈希失败: {e}")
            return None


if __name__ == '__main__':
    # 测试代码
    logger = setup_logging()
    logger.info("Utils 模块已加载")
    
    # 测试 Cron 解析
    cron = parse_cron_expression("0 2 * * *")
    print(f"Cron 解析结果: {cron}")
    
    # 测试版本比较
    result = compare_versions("1.2.3", "1.2.4")
    print(f"版本比较结果: {result}")
