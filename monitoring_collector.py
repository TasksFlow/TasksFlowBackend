#!/usr/bin/env python3
"""
独立的监控数据收集器
运行在单独的进程中，定期收集系统监控数据并存储到数据库
"""

import asyncio
import logging
import signal
import sys
import time

# 导入应用模块（必须在路径设置后）
from app.services.monitoring import MonitoringService
from app.db.session import SessionLocal
from app.crud.monitoring import (
    system_metrics, gpu_metrics, task_metrics, monitoring_alert
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitoring_collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MonitoringCollector:
    """独立的监控数据收集器"""
    
    def __init__(self, collection_interval: int = 5):
        self.collection_interval = collection_interval
        self.is_running = False
        self.monitoring_service = MonitoringService()
        
    def collect_and_store_data(self):
        """收集并存储监控数据"""
        db = SessionLocal()
        try:
            logger.debug("开始收集监控数据...")
            
            # 收集系统指标
            system_data = self.monitoring_service.get_system_metrics()
            if system_data:
                system_metrics.create(db, obj_in=system_data)
                logger.debug(
                    f"系统指标已保存: CPU={system_data.cpu_usage_percent}%, "
                    f"Memory={system_data.memory_usage_percent}%"
                )
            
            # 收集GPU指标
            gpu_data_list = self.monitoring_service.get_gpu_metrics()
            for gpu_data in gpu_data_list:
                gpu_metrics.create(db, obj_in=gpu_data)
            if gpu_data_list:
                logger.debug(f"GPU指标已保存: {len(gpu_data_list)}个GPU")
            
            # 收集任务指标
            task_data_list = self.monitoring_service.get_task_metrics()
            for task_data in task_data_list:
                task_metrics.create(db, obj_in=task_data)
            if task_data_list:
                logger.debug(f"任务指标已保存: {len(task_data_list)}个任务")

            # 检查告警
            alerts = self.monitoring_service.check_alerts(
                system_data, gpu_data_list
            )
            for alert in alerts:
                monitoring_alert.create(db, obj_in=alert)
            if alerts:
                logger.warning(f"发现告警: {len(alerts)}个")
            
            db.commit()
            logger.info(
                f"数据收集完成: 系统=1, GPU={len(gpu_data_list)}, "
                f"任务={len(task_data_list)}, 告警={len(alerts)}"
            )
            
        except Exception as e:
            logger.error(f"数据收集失败: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def run(self):
        """运行监控收集器"""
        logger.info(
            f"启动监控数据收集器，收集间隔: {self.collection_interval}秒"
        )
        self.is_running = True
        
        while self.is_running:
            try:
                start_time = time.time()
                self.collect_and_store_data()
                
                # 计算实际执行时间，确保精确的间隔
                execution_time = time.time() - start_time
                sleep_time = max(0, self.collection_interval - execution_time)
                
                if execution_time > self.collection_interval:
                    logger.warning(
                        f"数据收集耗时 {execution_time:.2f}s "
                        f"超过间隔时间 {self.collection_interval}s"
                    )
                
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"监控循环出错: {e}")
                await asyncio.sleep(self.collection_interval)
    
    def stop(self):
        """停止监控收集器"""
        logger.info("停止监控数据收集器...")
        self.is_running = False


def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"收到信号 {signum}，准备退出...")
    collector.stop()


if __name__ == "__main__":
    # 创建收集器实例
    collector = MonitoringCollector(collection_interval=5)
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 运行收集器
        asyncio.run(collector.run())
    except KeyboardInterrupt:
        logger.info("收到键盘中断，退出...")
    except Exception as e:
        logger.error(f"收集器运行失败: {e}")
        sys.exit(1)
    
    logger.info("监控数据收集器已退出")