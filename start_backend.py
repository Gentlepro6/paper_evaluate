import os
import sys
import subprocess

# 将backend目录添加到Python路径中
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.append(backend_dir)

# 启动后端服务
cmd = ["python", "-m", "uvicorn", "backend.main:app", "--reload"]
subprocess.run(cmd)
