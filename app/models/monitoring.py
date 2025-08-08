from sqlalchemy import Column, Integer, Float, String, DateTime, JSON, Text
from sqlalchemy.sql import func
from app.db.database import Base


class SystemMetrics(Base):
    """系统资源监控指标表"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # CPU指标
    cpu_usage_percent = Column(Float, nullable=True, comment="CPU使用率百分比")
    cpu_temperature = Column(Float, nullable=True, comment="CPU温度(摄氏度)")
    cpu_frequency = Column(Float, nullable=True, comment="CPU频率(MHz)")
    cpu_cores = Column(Integer, nullable=True, comment="CPU核心数")
    load_average_1m = Column(Float, nullable=True, comment="1分钟负载平均值")
    load_average_5m = Column(Float, nullable=True, comment="5分钟负载平均值")
    load_average_15m = Column(Float, nullable=True, comment="15分钟负载平均值")
    cpu_per_core_usage = Column(JSON, nullable=True, comment="各CPU核心使用率JSON数组")
    
    # 内存指标
    memory_usage_percent = Column(Float, nullable=True, comment="内存使用率百分比")
    memory_used_gb = Column(Float, nullable=True, comment="已使用内存(GB)")
    memory_total_gb = Column(Float, nullable=True, comment="总内存(GB)")
    memory_available_gb = Column(Float, nullable=True, comment="可用内存(GB)")
    memory_cached_gb = Column(Float, nullable=True, comment="缓存内存(GB)")
    swap_used_gb = Column(Float, nullable=True, comment="已使用交换分区(GB)")
    swap_total_gb = Column(Float, nullable=True, comment="总交换分区(GB)")
    
    # 磁盘指标
    disk_usage_percent = Column(JSON, nullable=True, comment="各分区磁盘使用率JSON对象")
    disk_read_speed = Column(Float, nullable=True, comment="磁盘读取速度(MB/s)")
    disk_write_speed = Column(Float, nullable=True, comment="磁盘写入速度(MB/s)")
    disk_read_iops = Column(Float, nullable=True, comment="磁盘读取IOPS")
    disk_write_iops = Column(Float, nullable=True, comment="磁盘写入IOPS")
    disk_queue_length = Column(Float, nullable=True, comment="磁盘I/O队列长度")
    
    # 网络指标
    network_upload_speed = Column(Float, nullable=True, comment="网络上传速度(MB/s)")
    network_download_speed = Column(Float, nullable=True, comment="网络下载速度(MB/s)")
    network_connections = Column(Integer, nullable=True, comment="网络连接数")
    
    # 系统整体指标
    system_uptime = Column(Float, nullable=True, comment="系统运行时间(秒)")
    process_count = Column(Integer, nullable=True, comment="进程数量")
    task_queue_length = Column(Integer, nullable=True, comment="任务队列长度")
    active_tasks_count = Column(Integer, nullable=True, comment="活跃任务数")
    
    def __repr__(self):
        return f"<SystemMetrics(id={self.id}, timestamp='{self.timestamp}', cpu={self.cpu_usage_percent}%)>"


class GPUMetrics(Base):
    """GPU监控指标表"""
    __tablename__ = "gpu_metrics"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # GPU基本信息
    gpu_index = Column(Integer, nullable=False, comment="GPU索引号")
    gpu_name = Column(String(255), nullable=True, comment="GPU名称")
    
    # GPU使用指标
    gpu_usage_percent = Column(Float, nullable=True, comment="GPU使用率百分比")
    gpu_memory_usage_percent = Column(Float, nullable=True, comment="GPU内存使用率百分比")
    gpu_memory_used_gb = Column(Float, nullable=True, comment="GPU已使用内存(GB)")
    gpu_memory_total_gb = Column(Float, nullable=True, comment="GPU总内存(GB)")
    gpu_temperature = Column(Float, nullable=True, comment="GPU温度(摄氏度)")
    gpu_power_usage = Column(Float, nullable=True, comment="GPU功耗(瓦特)")
    gpu_fan_speed = Column(Float, nullable=True, comment="GPU风扇转速百分比")
    
    def __repr__(self):
        return f"<GPUMetrics(id={self.id}, gpu_index={self.gpu_index}, usage={self.gpu_usage_percent}%)>"


class TaskMetrics(Base):
    """任务监控指标表"""
    __tablename__ = "task_metrics"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # 任务基本信息
    task_id = Column(String(255), nullable=False, index=True, comment="任务ID")
    task_name = Column(String(255), nullable=True, comment="任务名称")
    task_status = Column(String(50), nullable=True, comment="任务状态")
    
    # 任务资源使用
    task_cpu_usage = Column(Float, nullable=True, comment="任务CPU使用率百分比")
    task_memory_usage = Column(Float, nullable=True, comment="任务内存使用量(GB)")
    task_execution_time = Column(Float, nullable=True, comment="任务执行时间(秒)")
    
    # 任务进程信息
    process_id = Column(Integer, nullable=True, comment="进程ID")
    process_command = Column(Text, nullable=True, comment="执行命令")
    
    def __repr__(self):
        return f"<TaskMetrics(id={self.id}, task_id='{self.task_id}', status='{self.task_status}')>"


class MonitoringAlert(Base):
    """监控告警表"""
    __tablename__ = "monitoring_alerts"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # 告警信息
    alert_type = Column(String(50), nullable=False, comment="告警类型(cpu/memory/gpu/disk/network)")
    alert_level = Column(String(20), nullable=False, comment="告警级别(info/warning/critical)")
    alert_message = Column(Text, nullable=False, comment="告警消息")
    alert_value = Column(Float, nullable=True, comment="触发告警的数值")
    threshold_value = Column(Float, nullable=True, comment="告警阈值")
    
    # 告警状态
    is_resolved = Column(String(20), default="active", comment="告警状态(active/resolved)")
    resolved_at = Column(DateTime(timezone=True), nullable=True, comment="解决时间")
    
    def __repr__(self):
        return f"<MonitoringAlert(id={self.id}, type='{self.alert_type}', level='{self.alert_level}')>"