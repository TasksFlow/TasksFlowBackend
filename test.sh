#!/bin/bash

# 后端测试运行脚本
echo "🧪 开始运行后端测试..."

# 检查是否在正确的目录
if [ ! -f "requirements.txt" ]; then
    echo "❌ 错误: 请在backend目录下运行此脚本"
    exit 1
fi

# 检查虚拟环境
if [ -z "$CONDA_DEFAULT_ENV" ] || [ "$CONDA_DEFAULT_ENV" != "task-management-system" ]; then
    echo "⚠️  警告: 未检测到正确的conda环境，尝试激活..."
    source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null || source ~/anaconda3/etc/profile.d/conda.sh 2>/dev/null
    conda activate task-management-system
    if [ $? -ne 0 ]; then
        echo "❌ 无法激活conda环境，请先运行 ./start.sh 来设置环境"
        exit 1
    fi
fi

# 安装测试依赖（如果需要）
echo "📦 检查测试依赖..."
pip install pytest pytest-cov httpx

# 运行测试
echo "🚀 运行单元测试..."
python -m pytest tests/ -v

# 运行测试覆盖率
echo "📊 生成测试覆盖率报告..."
python -m pytest tests/ --cov=app --cov-report=html --cov-report=term

echo "✅ 测试完成！"
echo "📄 覆盖率报告已生成在 htmlcov/ 目录中"
echo "🌐 打开 htmlcov/index.html 查看详细覆盖率报告"