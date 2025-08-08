import psutil
import time
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.crud.monitoring import system_metrics, gpu_metrics, task_metrics, monitoring_alert
from app.schemas.monitoring import (
    SystemMetricsCreate, GPUMetricsCreate, TaskMetricsCreate, 
    MonitoringAlertCreate, AlertLevel, AlertType, AlertStatus
)

# 配置日志
logger = logging.getLogger(__name__)

# 尝试导入GPU监控库
try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    logger.warning("GPUtil not available, GPU monitoring will be disabled")

try:
    import nvidia_ml_py3 as nvml
    nvml.nvmlInit()
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False
    logger.warning("nvidia-ml-py3 not available, advanced GPU monitoring will be disabled")


class MonitoringService:
    """监控数据收集服务"""
    
    def __init__(self):
        self.is_running = False
        self.collection_interval = 5  # 数据收集间隔（秒）
        self.alert_thresholds = {
            'cpu_usage': 80.0,      # CPU使用率告警阈值
            'memory_usage': 85.0,   # 内存使用率告警阈值
            'gpu_usage': 90.0,      # GPU使用率告警阈值
            'gpu_memory': 90.0,     # GPU内存使用率告警阈值
            'gpu_temperature': 80.0, # GPU温度告警阈值
            'disk_usage': 90.0,     # 磁盘使用率告警阈值
        }
    
    def get_system_metrics(self) -> SystemMetricsCreate:
        """收集系统监控指标"""
        try:
            # CPU指标
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # CPU频率（在macOS上可能不可用）
            cpu_freq = None
            try:
                cpu_freq = psutil.cpu_freq()
            except (OSError, AttributeError):
                # macOS上可能不支持cpu_freq()
                pass
                
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)
            cpu_per_core = psutil.cpu_percent(percpu=True)
            
            # 内存指标
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # 磁盘指标
            disk_usage = {}
            disk_io = None
            
            try:
                disk_io = psutil.disk_io_counters()
            except Exception:
                # 某些系统上可能无法获取磁盘IO统计
                pass
            
            # 获取所有磁盘分区的使用情况
            for partition in psutil.disk_partitions():
                try:
                    # 跳过特殊分区，但保留重要的系统分区
                    if partition.mountpoint:
                        # 先检查是否是macOS的重要分区
                        if partition.mountpoint in ['/', '/System/Volumes/Data']:
                            pass  # 保留这些重要分区
                        # 在Linux系统上跳过这些特殊分区
                        elif any(skip in partition.mountpoint for skip in ['/dev', '/proc', '/sys', '/run', '/snap']):
                            continue
                        
                        # 对于macOS，重点关注主要分区
                        if partition.mountpoint in ['/', '/System/Volumes/Data']:
                            partition_usage = psutil.disk_usage(partition.mountpoint)
                            if partition_usage.total > 0:
                                # 使用更友好的分区名称
                                if partition.mountpoint == '/':
                                    partition_name = "系统盘"
                                elif partition.mountpoint == '/System/Volumes/Data':
                                    partition_name = "用户数据"
                                else:
                                    partition_name = "数据盘"
                                disk_usage[partition_name] = (
                                    partition_usage.used / partition_usage.total * 100
                                )
                        # 对于其他系统，包含所有主要分区
                        elif not partition.mountpoint.startswith('/System/Volumes/'):
                            partition_usage = psutil.disk_usage(partition.mountpoint)
                            if partition_usage.total > 1024**3:  # 只包含大于1GB的分区
                                disk_usage[partition.device] = (
                                    partition_usage.used / partition_usage.total * 100
                                )
                except (PermissionError, OSError):
                    continue
            
            # 网络指标
            network_io = None
            network_connections = 0
            
            try:
                network_io = psutil.net_io_counters()
            except Exception:
                pass
                
            try:
                network_connections = len(psutil.net_connections())
            except Exception:
                # 某些系统上可能需要特殊权限才能获取网络连接
                pass
            
            # 系统指标
            boot_time = psutil.boot_time()
            current_time = time.time()
            uptime = current_time - boot_time
            process_count = len(psutil.pids())
            
            # CPU温度（如果可用）
            cpu_temp = None
            try:
                if hasattr(psutil, "sensors_temperatures"):
                    temps = psutil.sensors_temperatures()
                    if temps:
                        # 尝试获取CPU温度
                        for name, entries in temps.items():
                            if 'cpu' in name.lower() or 'core' in name.lower():
                                if entries:
                                    cpu_temp = entries[0].current
                                    break
            except Exception:
                pass
            
            return SystemMetricsCreate(
                # CPU指标
                cpu_usage_percent=cpu_percent,
                cpu_temperature=cpu_temp,
                cpu_frequency=cpu_freq.current if cpu_freq else None,
                cpu_cores=cpu_count,
                load_average_1m=load_avg[0],
                load_average_5m=load_avg[1],
                load_average_15m=load_avg[2],
                cpu_per_core_usage=cpu_per_core,
                
                # 内存指标
                memory_usage_percent=memory.percent,
                memory_used_gb=memory.used / (1024**3),
                memory_total_gb=memory.total / (1024**3),
                memory_available_gb=memory.available / (1024**3),
                memory_cached_gb=getattr(memory, 'cached', 0) / (1024**3),
                swap_used_gb=swap.used / (1024**3),
                swap_total_gb=swap.total / (1024**3),
                
                # 磁盘指标
                disk_usage_percent=disk_usage,
                disk_read_speed=disk_io.read_bytes / (1024**2) if disk_io else 0,
                disk_write_speed=disk_io.write_bytes / (1024**2) if disk_io else 0,
                disk_read_iops=disk_io.read_count if disk_io else 0,
                disk_write_iops=disk_io.write_count if disk_io else 0,
                
                # 网络指标
                network_upload_speed=network_io.bytes_sent / (1024**2) if network_io else 0,
                network_download_speed=network_io.bytes_recv / (1024**2) if network_io else 0,
                network_connections=network_connections,
                
                # 系统指标
                system_uptime=uptime,
                process_count=process_count,
                task_queue_length=0,  # 这个需要从任务管理系统获取
                active_tasks_count=0,  # 这个需要从任务管理系统获取
            )
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetricsCreate()
    
    def get_gpu_metrics(self) -> List[GPUMetricsCreate]:
        """收集GPU监控指标"""
        gpu_metrics_list = []
        
        if not GPU_AVAILABLE:
            return gpu_metrics_list
        
        try:
            gpus = GPUtil.getGPUs()
            for gpu in gpus:
                gpu_metric = GPUMetricsCreate(
                    gpu_index=gpu.id,
                    gpu_name=gpu.name,
                    gpu_usage_percent=gpu.load * 100,
                    gpu_memory_usage_percent=gpu.memoryUtil * 100,
                    gpu_memory_used_gb=gpu.memoryUsed / 1024,
                    gpu_memory_total_gb=gpu.memoryTotal / 1024,
                    gpu_temperature=gpu.temperature,
                )
                
                # 如果有NVML，获取更详细的信息
                if NVML_AVAILABLE:
                    try:
                        handle = nvml.nvmlDeviceGetHandleByIndex(gpu.id)
                        power_usage = nvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # 转换为瓦特
                        fan_speed = nvml.nvmlDeviceGetFanSpeed(handle)
                        
                        gpu_metric.gpu_power_usage = power_usage
                        gpu_metric.gpu_fan_speed = fan_speed
                    except Exception as e:
                        logger.warning(f"Error getting NVML data for GPU {gpu.id}: {e}")
                
                gpu_metrics_list.append(gpu_metric)
                
        except Exception as e:
            logger.error(f"Error collecting GPU metrics: {e}")
        
        return gpu_metrics_list
    
    def get_task_metrics(self) -> List[TaskMetricsCreate]:
        """收集任务监控指标"""
        task_metrics_list = []
        
        try:
            # 这里需要与任务管理系统集成
            # 暂时返回空列表，后续实现任务监控
            pass
            
        except Exception as e:
            logger.error(f"Error collecting task metrics: {e}")
        
        return task_metrics_list
    
    def check_alerts(self, system_data: SystemMetricsCreate, gpu_data: List[GPUMetricsCreate]) -> List[MonitoringAlertCreate]:
        """检查告警条件"""
        alerts = []
        
        try:
            # 检查CPU使用率告警
            if system_data.cpu_usage_percent and system_data.cpu_usage_percent > self.alert_thresholds['cpu_usage']:
                alerts.append(MonitoringAlertCreate(
                    alert_type=AlertType.CPU,
                    alert_level=AlertLevel.WARNING if system_data.cpu_usage_percent < 95 else AlertLevel.CRITICAL,
                    alert_message=f"CPU使用率过高: {system_data.cpu_usage_percent:.1f}%",
                    alert_value=system_data.cpu_usage_percent,
                    threshold_value=self.alert_thresholds['cpu_usage']
                ))
            
            # 检查内存使用率告警
            if system_data.memory_usage_percent and system_data.memory_usage_percent > self.alert_thresholds['memory_usage']:
                alerts.append(MonitoringAlertCreate(
                    alert_type=AlertType.MEMORY,
                    alert_level=AlertLevel.WARNING if system_data.memory_usage_percent < 95 else AlertLevel.CRITICAL,
                    alert_message=f"内存使用率过高: {system_data.memory_usage_percent:.1f}%",
                    alert_value=system_data.memory_usage_percent,
                    threshold_value=self.alert_thresholds['memory_usage']
                ))
            
            # 检查磁盘使用率告警
            if system_data.disk_usage_percent:
                for device, usage in system_data.disk_usage_percent.items():
                    if usage > self.alert_thresholds['disk_usage']:
                        alerts.append(MonitoringAlertCreate(
                            alert_type=AlertType.DISK,
                            alert_level=AlertLevel.WARNING if usage < 95 else AlertLevel.CRITICAL,
                            alert_message=f"磁盘使用率过高 ({device}): {usage:.1f}%",
                            alert_value=usage,
                            threshold_value=self.alert_thresholds['disk_usage']
                        ))
            
            # 检查GPU告警
            for gpu_data_item in gpu_data:
                # GPU使用率告警
                if gpu_data_item.gpu_usage_percent and gpu_data_item.gpu_usage_percent > self.alert_thresholds['gpu_usage']:
                    alerts.append(MonitoringAlertCreate(
                        alert_type=AlertType.GPU,
                        alert_level=AlertLevel.WARNING,
                        alert_message=f"GPU {gpu_data_item.gpu_index} 使用率过高: {gpu_data_item.gpu_usage_percent:.1f}%",
                        alert_value=gpu_data_item.gpu_usage_percent,
                        threshold_value=self.alert_thresholds['gpu_usage']
                    ))
                
                # GPU内存使用率告警
                if gpu_data_item.gpu_memory_usage_percent and gpu_data_item.gpu_memory_usage_percent > self.alert_thresholds['gpu_memory']:
                    alerts.append(MonitoringAlertCreate(
                        alert_type=AlertType.GPU,
                        alert_level=AlertLevel.WARNING,
                        alert_message=f"GPU {gpu_data_item.gpu_index} 内存使用率过高: {gpu_data_item.gpu_memory_usage_percent:.1f}%",
                        alert_value=gpu_data_item.gpu_memory_usage_percent,
                        threshold_value=self.alert_thresholds['gpu_memory']
                    ))
                
                # GPU温度告警
                if gpu_data_item.gpu_temperature and gpu_data_item.gpu_temperature > self.alert_thresholds['gpu_temperature']:
                    alerts.append(MonitoringAlertCreate(
                        alert_type=AlertType.GPU,
                        alert_level=AlertLevel.CRITICAL if gpu_data_item.gpu_temperature > 85 else AlertLevel.WARNING,
                        alert_message=f"GPU {gpu_data_item.gpu_index} 温度过高: {gpu_data_item.gpu_temperature:.1f}°C",
                        alert_value=gpu_data_item.gpu_temperature,
                        threshold_value=self.alert_thresholds['gpu_temperature']
                    ))
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
        
        return alerts
    
    def collect_and_store_metrics(self):
        """收集并存储监控指标"""
        db = SessionLocal()
        try:
            # 收集系统指标
            system_data = self.get_system_metrics()
            if system_data:
                system_metrics.create(db, obj_in=system_data)
            
            # 收集GPU指标
            gpu_data_list = self.get_gpu_metrics()
            for gpu_data in gpu_data_list:
                gpu_metrics.create(db, obj_in=gpu_data)
            
            # 收集任务指标
            task_data_list = self.get_task_metrics()
            for task_data in task_data_list:
                task_metrics.create(db, obj_in=task_data)
            
            # 检查告警
            alerts = self.check_alerts(system_data, gpu_data_list)
            for alert in alerts:
                monitoring_alert.create(db, obj_in=alert)
            
            logger.debug(f"Collected metrics: system=1, gpu={len(gpu_data_list)}, task={len(task_data_list)}, alerts={len(alerts)}")
            
        except Exception as e:
            logger.error(f"Error in collect_and_store_metrics: {e}")
        finally:
            db.close()
    
    async def start_monitoring(self):
        """启动监控服务"""
        if self.is_running:
            logger.warning("Monitoring service is already running")
            return
        
        self.is_running = True
        logger.info("Starting monitoring service...")
        
        while self.is_running:
            try:
                self.collect_and_store_metrics()
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.collection_interval)
    
    def stop_monitoring(self):
        """停止监控服务"""
        logger.info("Stopping monitoring service...")
        self.is_running = False
    
    def get_system_overview(self) -> Dict[str, Any]:
        """获取系统概览信息"""
        db = SessionLocal()
        try:
            # 获取最新的系统指标
            latest_system = system_metrics.get_latest(db)
            
            # 获取所有GPU的最新指标
            latest_gpu_list = gpu_metrics.get_all_latest(db)
            
            # 获取活跃告警
            active_alerts = monitoring_alert.get_active_alerts(db)
            
            # 构建概览信息
            overview = {
                'system_metrics': latest_system,
                'gpu_metrics': latest_gpu_list or [],
                'active_alerts': active_alerts or [],
                'summary': {
                    'system_status': 'healthy',
                    'timestamp': datetime.utcnow(),
                    'active_alerts_count': len(active_alerts) if active_alerts else 0,
                    'gpu_count': len(latest_gpu_list) if latest_gpu_list else 0,
                }
            }
            
            # 判断系统状态
            if active_alerts:
                critical_alerts = [a for a in active_alerts if a.alert_level == AlertLevel.CRITICAL]
                if critical_alerts:
                    overview['summary']['system_status'] = 'critical'
                else:
                    overview['summary']['system_status'] = 'warning'
            
            return overview
            
        except Exception as e:
            logger.error(f"Error getting system overview: {e}")
            return {
                'system_metrics': None,
                'gpu_metrics': [],
                'active_alerts': [],
                'summary': {
                    'system_status': 'error',
                    'timestamp': datetime.utcnow(),
                    'active_alerts_count': 0,
                    'gpu_count': 0,
                }
            }
        finally:
            db.close()


# 创建全局监控服务实例
monitoring_service = MonitoringService()