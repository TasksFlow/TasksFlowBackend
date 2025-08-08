#!/bin/bash

# 监控数据收集器启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COLLECTOR_SCRIPT="$SCRIPT_DIR/monitoring_collector.py"
PID_FILE="$SCRIPT_DIR/monitoring_collector.pid"
LOG_FILE="$SCRIPT_DIR/monitoring_collector.log"

# 激活conda环境
source /opt/homebrew/Caskroom/miniforge/base/etc/profile.d/conda.sh
conda activate task-management-system

case "$1" in
    start)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p $PID > /dev/null 2>&1; then
                echo "监控收集器已在运行 (PID: $PID)"
                exit 1
            else
                rm -f "$PID_FILE"
            fi
        fi
        
        echo "启动监控数据收集器..."
        cd "$SCRIPT_DIR"
        nohup env PYTHONPATH="$SCRIPT_DIR" python3 "$COLLECTOR_SCRIPT" > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        echo "监控收集器已启动 (PID: $(cat $PID_FILE))"
        echo "日志文件: $LOG_FILE"
        ;;
    
    stop)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p $PID > /dev/null 2>&1; then
                echo "停止监控收集器 (PID: $PID)..."
                kill $PID
                rm -f "$PID_FILE"
                echo "监控收集器已停止"
            else
                echo "监控收集器未运行"
                rm -f "$PID_FILE"
            fi
        else
            echo "监控收集器未运行"
        fi
        ;;
    
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    
    status)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p $PID > /dev/null 2>&1; then
                echo "监控收集器正在运行 (PID: $PID)"
                echo "日志文件: $LOG_FILE"
            else
                echo "监控收集器未运行 (PID文件存在但进程不存在)"
                rm -f "$PID_FILE"
            fi
        else
            echo "监控收集器未运行"
        fi
        ;;
    
    logs)
        if [ -f "$LOG_FILE" ]; then
            tail -f "$LOG_FILE"
        else
            echo "日志文件不存在: $LOG_FILE"
        fi
        ;;
    
    *)
        echo "用法: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "命令说明:"
        echo "  start   - 启动监控数据收集器"
        echo "  stop    - 停止监控数据收集器"
        echo "  restart - 重启监控数据收集器"
        echo "  status  - 查看运行状态"
        echo "  logs    - 查看实时日志"
        exit 1
        ;;
esac