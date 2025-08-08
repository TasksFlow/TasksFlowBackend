from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, List, Any
from enum import Enum


class AlertLevel(str, Enum):
    """告警级别枚举"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """告警类型枚举"""
    CPU = "cpu"
    MEMORY = "memory"
    GPU = "gpu"
    DISK = "disk"
    NETWORK = "network"
    SYSTEM = "system"


class AlertStatus(str, Enum):
    """告警状态枚举"""
    ACTIVE = "active"
    RESOLVED = "resolved"


# 系统监控相关Schema
class SystemMetricsBase(BaseModel):
    """系统监控指标基础模型"""
    # CPU指标
    cpu_usage_percent: Optional[float] = Field(None, description="CPU使用率百分比")
    cpu_temperature: Optional[float] = Field(None, description="CPU温度(摄氏度)")
    cpu_frequency: Optional[float] = Field(None, description="CPU频率(MHz)")
    cpu_cores: Optional[int] = Field(None, description="CPU核心数")
    load_average_1m: Optional[float] = Field(None, description="1分钟负载平均值")
    load_average_5m: Optional[float] = Field(None, description="5分钟负载平均值")
    load_average_15m: Optional[float] = Field(None, description="15分钟负载平均值")
    cpu_per_core_usage: Optional[List[float]] = Field(None, description="各CPU核心使用率")
    
    # 内存指标
    memory_usage_percent: Optional[float] = Field(None, description="内存使用率百分比")
    memory_used_gb: Optional[float] = Field(None, description="已使用内存(GB)")
    memory_total_gb: Optional[float] = Field(None, description="总内存(GB)")
    memory_available_gb: Optional[float] = Field(None, description="可用内存(GB)")
    memory_cached_gb: Optional[float] = Field(None, description="缓存内存(GB)")
    swap_used_gb: Optional[float] = Field(None, description="已使用交换分区(GB)")
    swap_total_gb: Optional[float] = Field(None, description="总交换分区(GB)")
    
    # 磁盘指标
    disk_usage_percent: Optional[Dict[str, float]] = Field(None, description="各分区磁盘使用率")
    disk_read_speed: Optional[float] = Field(None, description="磁盘读取速度(MB/s)")
    disk_write_speed: Optional[float] = Field(None, description="磁盘写入速度(MB/s)")
    disk_read_iops: Optional[float] = Field(None, description="磁盘读取IOPS")
    disk_write_iops: Optional[float] = Field(None, description="磁盘写入IOPS")
    disk_queue_length: Optional[float] = Field(None, description="磁盘I/O队列长度")
    
    # 网络指标
    network_upload_speed: Optional[float] = Field(None, description="网络上传速度(MB/s)")
    network_download_speed: Optional[float] = Field(None, description="网络下载速度(MB/s)")
    network_connections: Optional[int] = Field(None, description="网络连接数")
    
    # 系统整体指标
    system_uptime: Optional[float] = Field(None, description="系统运行时间(秒)")
    process_count: Optional[int] = Field(None, description="进程数量")
    task_queue_length: Optional[int] = Field(None, description="任务队列长度")
    active_tasks_count: Optional[int] = Field(None, description="活跃任务数")


class SystemMetricsCreate(SystemMetricsBase):
    """创建系统监控指标"""
    pass


class SystemMetricsResponse(SystemMetricsBase):
    """系统监控指标响应"""
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True


# GPU监控相关Schema
class GPUMetricsBase(BaseModel):
    """GPU监控指标基础模型"""
    gpu_index: int = Field(..., description="GPU索引号")
    gpu_name: Optional[str] = Field(None, description="GPU名称")
    gpu_usage_percent: Optional[float] = Field(None, description="GPU使用率百分比")
    gpu_memory_usage_percent: Optional[float] = Field(None, description="GPU内存使用率百分比")
    gpu_memory_used_gb: Optional[float] = Field(None, description="GPU已使用内存(GB)")
    gpu_memory_total_gb: Optional[float] = Field(None, description="GPU总内存(GB)")
    gpu_temperature: Optional[float] = Field(None, description="GPU温度(摄氏度)")
    gpu_power_usage: Optional[float] = Field(None, description="GPU功耗(瓦特)")
    gpu_fan_speed: Optional[float] = Field(None, description="GPU风扇转速百分比")


class GPUMetricsCreate(GPUMetricsBase):
    """创建GPU监控指标"""
    pass


class GPUMetricsResponse(GPUMetricsBase):
    """GPU监控指标响应"""
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True


# 任务监控相关Schema
class TaskMetricsBase(BaseModel):
    """任务监控指标基础模型"""
    task_id: str = Field(..., description="任务ID")
    task_name: Optional[str] = Field(None, description="任务名称")
    task_status: Optional[str] = Field(None, description="任务状态")
    task_cpu_usage: Optional[float] = Field(None, description="任务CPU使用率百分比")
    task_memory_usage: Optional[float] = Field(None, description="任务内存使用量(GB)")
    task_execution_time: Optional[float] = Field(None, description="任务执行时间(秒)")
    process_id: Optional[int] = Field(None, description="进程ID")
    process_command: Optional[str] = Field(None, description="执行命令")


class TaskMetricsCreate(TaskMetricsBase):
    """创建任务监控指标"""
    pass


class TaskMetricsResponse(TaskMetricsBase):
    """任务监控指标响应"""
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True


# 监控告警相关Schema
class MonitoringAlertBase(BaseModel):
    """监控告警基础模型"""
    alert_type: AlertType = Field(..., description="告警类型")
    alert_level: AlertLevel = Field(..., description="告警级别")
    alert_message: str = Field(..., description="告警消息")
    alert_value: Optional[float] = Field(None, description="触发告警的数值")
    threshold_value: Optional[float] = Field(None, description="告警阈值")


class MonitoringAlertCreate(MonitoringAlertBase):
    """创建监控告警"""
    pass


class MonitoringAlertUpdate(BaseModel):
    """更新监控告警"""
    is_resolved: AlertStatus = Field(..., description="告警状态")


class MonitoringAlertResponse(MonitoringAlertBase):
    """监控告警响应"""
    id: int
    timestamp: datetime
    is_resolved: str
    resolved_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# 综合监控数据Schema
class SystemOverviewResponse(BaseModel):
    """系统概览响应"""
    system_metrics: Optional[SystemMetricsResponse] = Field(None, description="系统指标")
    gpu_metrics: List[GPUMetricsResponse] = Field(default_factory=list, description="GPU指标列表")
    active_alerts: List[MonitoringAlertResponse] = Field(default_factory=list, description="活跃告警列表")
    summary: Dict[str, Any] = Field(default_factory=dict, description="汇总信息")


class MetricsQueryParams(BaseModel):
    """监控数据查询参数"""
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    interval: Optional[str] = Field("5m", description="数据间隔(1m/5m/15m/1h/1d)")
    limit: Optional[int] = Field(100, description="返回数据条数限制")


class MetricsHistoryResponse(BaseModel):
    """历史监控数据响应"""
    timestamps: List[datetime] = Field(default_factory=list, description="时间戳列表")
    system_metrics: List[SystemMetricsResponse] = Field(default_factory=list, description="系统指标历史")
    gpu_metrics: Dict[int, List[GPUMetricsResponse]] = Field(default_factory=dict, description="GPU指标历史(按GPU索引分组)")
    total_count: int = Field(0, description="总数据条数")