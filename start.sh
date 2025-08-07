#!/bin/bash

# 任务管理系统后端启动脚本

echo "=== 任务管理系统后端启动脚本 ==="

# 检查是否在正确的目录
if [ ! -f "environment.yml" ]; then
    echo "错误: 请在 backend 目录下运行此脚本"
    exit 1
fi

# 检查 conda 是否安装
if ! command -v conda &> /dev/null; then
    echo "错误: 未找到 conda，请先安装 Anaconda 或 Miniconda"
    exit 1
fi

# 检查环境是否存在
if conda env list | grep -q "task-management-system"; then
    echo "✓ 发现现有的 conda 环境: task-management-system"
else
    echo "创建新的 conda 环境..."
    conda env create -f environment.yml
    if [ $? -ne 0 ]; then
        echo "错误: 创建 conda 环境失败"
        exit 1
    fi
    echo "✓ conda 环境创建成功"
fi

# 激活环境
echo "激活 conda 环境..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate task-management-system

if [ $? -ne 0 ]; then
    echo "错误: 激活 conda 环境失败"
    exit 1
fi

echo "✓ conda 环境已激活"

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "创建环境变量文件..."
    cp .env.example .env
    echo "✓ 已创建 .env 文件，请根据需要修改配置"
fi

# 初始化数据库
echo "初始化数据库..."
python -m app.db.init_db

if [ $? -ne 0 ]; then
    echo "错误: 数据库初始化失败"
    exit 1
fi

echo "✓ 数据库初始化完成"

# 启动服务器
echo "启动 FastAPI 服务器..."
echo "服务器地址: http://localhost:8000"
echo "API 文档: http://localhost:8000/api/docs"
echo "按 Ctrl+C 停止服务器"
echo ""

python run.py