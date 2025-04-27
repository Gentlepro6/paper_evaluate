#!/usr/bin/env python3
"""
清理项目脚本 - 用于在上传到GitHub前清理不必要的文件
此脚本会删除：
1. Python缓存文件 (__pycache__, .pyc, .pyo)
2. 虚拟环境目录 (venv)
3. 数据库文件 (*.db)
4. 日志文件 (*.log)
5. 临时上传文件
6. Node.js模块 (node_modules)
7. 构建目录 (build, dist)
8. IDE配置文件 (.vscode, .idea)
9. 系统文件 (.DS_Store)
"""

import os
import shutil
import fnmatch
import argparse
from pathlib import Path

# 要删除的文件和目录模式
PATTERNS_TO_REMOVE = [
    # Python缓存
    "**/__pycache__",
    "**/*.pyc",
    "**/*.pyo",
    "**/*.pyd",
    "**/.pytest_cache",
    "**/.coverage",
    "**/.mypy_cache",
    
    # 虚拟环境
    "venv",
    "env",
    ".env",
    ".venv",
    
    # 数据库文件
    "**/databases/**/*.db",
    "**/databases/**/*.sqlite",
    "**/databases/**/*.sqlite3",
    
    # 日志文件
    "logs",
    "**/*.log",
    
    # 临时上传文件
    "data/temp/**",
    "data/uploads/**",
    "data/papers/**",
    "data/knowledge/**",
    
    # Node.js
    "**/node_modules",
    "**/package-lock.json",
    "**/yarn.lock",
    "**/.cache",
    "**/.npm",
    
    # 构建目录
    "**/build",
    "**/dist",
    "**/.next",
    
    # IDE配置
    ".vscode",
    ".idea",
    "**/*.sublime-*",
    
    # 系统文件
    "**/.DS_Store",
    "**/Thumbs.db",
    
    # Git相关
    ".git/objects/**",
    ".git/hooks/**",
    ".git/logs/**",
    
    # 模型和大文件
    "**/*.h5",
    "**/*.pkl",
    "**/*.model",
    "**/*.bin",
    "**/*.onnx",
    "**/*.pt",
    "**/*.pth",
    "**/*.weights",
    
    # 其他临时文件
    "**/*.bak",
    "**/*.swp",
    "**/*.tmp",
    "**/*.temp",
    "**/*.zip",
    "**/*.tar",
    "**/*.tar.gz",
    "**/*.rar",
]

# 需要保留的目录（即使它们是空的）
DIRS_TO_KEEP = [
    "data",
    "data/papers",
    "data/knowledge",
    "data/temp",
    "data/uploads",
    "backend/databases",
    "backend/databases/model",
    "backend/databases/paper",
    "backend/databases/knowledge",
    "backend/databases/evaluate",
    "backend/utils",
    "logs",
    "frontend/public",
    "frontend/src",
]

def confirm(message):
    """请求用户确认操作"""
    response = input(f"{message} [y/N]: ").lower()
    return response in ("y", "yes")

def clean_project(project_path, dry_run=False, verbose=False, force=False):
    """清理项目中的不必要文件"""
    project_path = Path(project_path).resolve()
    
    if not project_path.exists() or not project_path.is_dir():
        print(f"错误: 项目路径 {project_path} 不存在或不是目录")
        return False
    
    print(f"开始清理项目: {project_path}")
    
    # 创建要保留的目录
    for dir_path in DIRS_TO_KEEP:
        full_path = project_path / dir_path
        if not full_path.exists():
            if verbose:
                print(f"创建目录: {full_path}")
            if not dry_run:
                full_path.mkdir(parents=True, exist_ok=True)
    
    # 查找要删除的文件和目录
    items_to_remove = []
    for pattern in PATTERNS_TO_REMOVE:
        if "**" in pattern:
            # 处理递归模式
            for path in project_path.glob(pattern):
                if path.is_relative_to(project_path):
                    items_to_remove.append(path)
        else:
            # 处理非递归模式
            path = project_path / pattern
            if path.exists():
                items_to_remove.append(path)
    
    # 排序以便目录在其内容之后删除
    items_to_remove.sort(key=lambda x: str(x), reverse=True)
    
    if not items_to_remove:
        print("没有找到需要清理的文件")
        return True
    
    # 显示要删除的文件列表
    if verbose or dry_run:
        print("\n将删除以下文件和目录:")
        for item in items_to_remove:
            print(f"  - {item.relative_to(project_path)}")
    
    # 请求确认
    if not force and not dry_run:
        if not confirm(f"确定要删除这 {len(items_to_remove)} 个文件/目录吗?"):
            print("操作已取消")
            return False
    
    # 执行删除
    removed_count = 0
    for item in items_to_remove:
        try:
            if dry_run:
                print(f"将删除: {item.relative_to(project_path)}")
                removed_count += 1
            else:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                if verbose:
                    print(f"已删除: {item.relative_to(project_path)}")
                removed_count += 1
        except Exception as e:
            print(f"删除 {item} 时出错: {e}")
    
    print(f"\n{'将删除' if dry_run else '已删除'} {removed_count} 个文件/目录")
    
    # 创建空的.gitkeep文件以保留空目录
    if not dry_run:
        for dir_path in DIRS_TO_KEEP:
            full_path = project_path / dir_path
            if full_path.exists() and full_path.is_dir() and not any(full_path.iterdir()):
                gitkeep_file = full_path / ".gitkeep"
                if not gitkeep_file.exists():
                    if verbose:
                        print(f"创建 {gitkeep_file}")
                    gitkeep_file.touch()
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="清理项目中不必要的文件")
    parser.add_argument("--path", "-p", default=".", help="项目路径 (默认: 当前目录)")
    parser.add_argument("--dry-run", "-d", action="store_true", help="仅显示将要删除的文件，不实际删除")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
    parser.add_argument("--force", "-f", action="store_true", help="不请求确认直接删除")
    
    args = parser.parse_args()
    
    clean_project(args.path, args.dry_run, args.verbose, args.force)
