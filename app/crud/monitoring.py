from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from app.crud.base import CRUDBase
from app.models.monitoring import SystemMetrics, GPUMetrics, TaskMetrics, MonitoringAlert
from app.schemas.monitoring import (
    SystemMetricsCreate, SystemMetricsResponse,
    GPUMetricsCreate, GPUMetricsResponse,
    TaskMetricsCreate, TaskMetricsResponse,
    MonitoringAlertCreate, MonitoringAlertUpdate, MonitoringAlertResponse,
    AlertStatus
)


class CRUDSystemMetrics(CRUDBase[SystemMetrics, SystemMetricsCreate, SystemMetricsCreate]):
    def get_latest(self, db: Session) -> Optional[SystemMetrics]:
        """获取最新的系统监控数据"""
        return db.query(SystemMetrics).order_by(desc(SystemMetrics.timestamp)).first()
    
    def get_by_time_range(
        self, 
        db: Session, 
        start_time: datetime, 
        end_time: datetime,
        limit: int = 1000
    ) -> List[SystemMetrics]:
        """根据时间范围获取系统监控数据"""
        return db.query(SystemMetrics).filter(
            and_(
                SystemMetrics.timestamp >= start_time,
                SystemMetrics.timestamp <= end_time
            )
        ).order_by(desc(SystemMetrics.timestamp)).limit(limit).all()
    
    def get_aggregated_data(
        self,
        db: Session,
        start_time: datetime,
        end_time: datetime,
        interval_minutes: int = 5
    ) -> List[Dict[str, Any]]:
        """获取聚合的监控数据（按时间间隔分组）"""
        # 计算时间间隔的分组
        time_group = func.date_trunc('minute', SystemMetrics.timestamp)
        
        query = db.query(
            time_group.label('time_bucket'),
            func.avg(SystemMetrics.cpu_usage_percent).label('avg_cpu_usage'),
            func.max(SystemMetrics.cpu_usage_percent).label('max_cpu_usage'),
            func.avg(SystemMetrics.memory_usage_percent).label('avg_memory_usage'),
            func.max(SystemMetrics.memory_usage_percent).label('max_memory_usage'),
            func.avg(SystemMetrics.disk_read_speed).label('avg_disk_read'),
            func.avg(SystemMetrics.disk_write_speed).label('avg_disk_write'),
            func.avg(SystemMetrics.network_upload_speed).label('avg_network_up'),
            func.avg(SystemMetrics.network_download_speed).label('avg_network_down'),
        ).filter(
            and_(
                SystemMetrics.timestamp >= start_time,
                SystemMetrics.timestamp <= end_time
            )
        ).group_by(time_group).order_by(time_group).all()
        
        return [
            {
                'timestamp': row.time_bucket,
                'avg_cpu_usage': float(row.avg_cpu_usage or 0),
                'max_cpu_usage': float(row.max_cpu_usage or 0),
                'avg_memory_usage': float(row.avg_memory_usage or 0),
                'max_memory_usage': float(row.max_memory_usage or 0),
                'avg_disk_read': float(row.avg_disk_read or 0),
                'avg_disk_write': float(row.avg_disk_write or 0),
                'avg_network_up': float(row.avg_network_up or 0),
                'avg_network_down': float(row.avg_network_down or 0),
            }
            for row in query
        ]
    
    def cleanup_old_data(self, db: Session, days_to_keep: int = 30) -> int:
        """清理旧的监控数据"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        deleted_count = db.query(SystemMetrics).filter(
            SystemMetrics.timestamp < cutoff_date
        ).delete()
        db.commit()
        return deleted_count


class CRUDGPUMetrics(CRUDBase[GPUMetrics, GPUMetricsCreate, GPUMetricsCreate]):
    def get_latest_by_gpu(self, db: Session, gpu_index: int) -> Optional[GPUMetrics]:
        """获取指定GPU的最新监控数据"""
        return db.query(GPUMetrics).filter(
            GPUMetrics.gpu_index == gpu_index
        ).order_by(desc(GPUMetrics.timestamp)).first()
    
    def get_all_latest(self, db: Session) -> List[GPUMetrics]:
        """获取所有GPU的最新监控数据"""
        # 子查询获取每个GPU的最新时间戳
        subquery = db.query(
            GPUMetrics.gpu_index,
            func.max(GPUMetrics.timestamp).label('max_timestamp')
        ).group_by(GPUMetrics.gpu_index).subquery()
        
        # 主查询获取最新数据
        return db.query(GPUMetrics).join(
            subquery,
            and_(
                GPUMetrics.gpu_index == subquery.c.gpu_index,
                GPUMetrics.timestamp == subquery.c.max_timestamp
            )
        ).all()
    
    def get_by_gpu_and_time_range(
        self,
        db: Session,
        gpu_index: int,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000
    ) -> List[GPUMetrics]:
        """根据GPU索引和时间范围获取监控数据"""
        return db.query(GPUMetrics).filter(
            and_(
                GPUMetrics.gpu_index == gpu_index,
                GPUMetrics.timestamp >= start_time,
                GPUMetrics.timestamp <= end_time
            )
        ).order_by(desc(GPUMetrics.timestamp)).limit(limit).all()
    
    def get_gpu_usage_summary(self, db: Session, hours: int = 24) -> Dict[int, Dict[str, Any]]:
        """获取GPU使用情况汇总"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = db.query(
            GPUMetrics.gpu_index,
            func.avg(GPUMetrics.gpu_usage_percent).label('avg_usage'),
            func.max(GPUMetrics.gpu_usage_percent).label('max_usage'),
            func.avg(GPUMetrics.gpu_memory_usage_percent).label('avg_memory'),
            func.max(GPUMetrics.gpu_memory_usage_percent).label('max_memory'),
            func.avg(GPUMetrics.gpu_temperature).label('avg_temperature'),
            func.max(GPUMetrics.gpu_temperature).label('max_temperature'),
            func.count().label('data_points')
        ).filter(
            GPUMetrics.timestamp >= start_time
        ).group_by(GPUMetrics.gpu_index).all()
        
        return {
            row.gpu_index: {
                'avg_usage': float(row.avg_usage or 0),
                'max_usage': float(row.max_usage or 0),
                'avg_memory': float(row.avg_memory or 0),
                'max_memory': float(row.max_memory or 0),
                'avg_temperature': float(row.avg_temperature or 0),
                'max_temperature': float(row.max_temperature or 0),
                'data_points': row.data_points
            }
            for row in query
        }


class CRUDTaskMetrics(CRUDBase[TaskMetrics, TaskMetricsCreate, TaskMetricsCreate]):
    def get_by_task_id(self, db: Session, task_id: str) -> List[TaskMetrics]:
        """根据任务ID获取监控数据"""
        return db.query(TaskMetrics).filter(
            TaskMetrics.task_id == task_id
        ).order_by(desc(TaskMetrics.timestamp)).all()
    
    def get_active_tasks_metrics(self, db: Session) -> List[TaskMetrics]:
        """获取活跃任务的最新监控数据"""
        # 获取最近5分钟内有数据的任务
        recent_time = datetime.utcnow() - timedelta(minutes=5)
        
        # 子查询获取每个任务的最新时间戳
        subquery = db.query(
            TaskMetrics.task_id,
            func.max(TaskMetrics.timestamp).label('max_timestamp')
        ).filter(
            TaskMetrics.timestamp >= recent_time
        ).group_by(TaskMetrics.task_id).subquery()
        
        # 主查询获取最新数据
        return db.query(TaskMetrics).join(
            subquery,
            and_(
                TaskMetrics.task_id == subquery.c.task_id,
                TaskMetrics.timestamp == subquery.c.max_timestamp
            )
        ).all()
    
    def get_task_resource_summary(
        self, 
        db: Session, 
        task_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取任务资源使用汇总"""
        query = db.query(
            func.avg(TaskMetrics.task_cpu_usage).label('avg_cpu'),
            func.max(TaskMetrics.task_cpu_usage).label('max_cpu'),
            func.avg(TaskMetrics.task_memory_usage).label('avg_memory'),
            func.max(TaskMetrics.task_memory_usage).label('max_memory'),
            func.sum(TaskMetrics.task_execution_time).label('total_time'),
            func.count().label('data_points')
        ).filter(TaskMetrics.task_id == task_id).first()
        
        if not query or query.data_points == 0:
            return None
            
        return {
            'avg_cpu': float(query.avg_cpu or 0),
            'max_cpu': float(query.max_cpu or 0),
            'avg_memory': float(query.avg_memory or 0),
            'max_memory': float(query.max_memory or 0),
            'total_time': float(query.total_time or 0),
            'data_points': query.data_points
        }


class CRUDMonitoringAlert(CRUDBase[MonitoringAlert, MonitoringAlertCreate, MonitoringAlertUpdate]):
    def get_active_alerts(self, db: Session) -> List[MonitoringAlert]:
        """获取活跃的告警"""
        return db.query(MonitoringAlert).filter(
            MonitoringAlert.is_resolved == AlertStatus.ACTIVE
        ).order_by(desc(MonitoringAlert.timestamp)).all()
    
    def get_by_type_and_level(
        self, 
        db: Session, 
        alert_type: str, 
        alert_level: str
    ) -> List[MonitoringAlert]:
        """根据告警类型和级别获取告警"""
        return db.query(MonitoringAlert).filter(
            and_(
                MonitoringAlert.alert_type == alert_type,
                MonitoringAlert.alert_level == alert_level
            )
        ).order_by(desc(MonitoringAlert.timestamp)).all()
    
    def resolve_alert(self, db: Session, alert_id: int) -> Optional[MonitoringAlert]:
        """解决告警"""
        alert = self.get(db, alert_id)
        if alert:
            alert.is_resolved = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            db.commit()
            db.refresh(alert)
        return alert
    
    def get_alert_statistics(self, db: Session, days: int = 7) -> Dict[str, Any]:
        """获取告警统计信息"""
        start_time = datetime.utcnow() - timedelta(days=days)
        
        # 按类型统计
        type_stats = db.query(
            MonitoringAlert.alert_type,
            func.count().label('count')
        ).filter(
            MonitoringAlert.timestamp >= start_time
        ).group_by(MonitoringAlert.alert_type).all()
        
        # 按级别统计
        level_stats = db.query(
            MonitoringAlert.alert_level,
            func.count().label('count')
        ).filter(
            MonitoringAlert.timestamp >= start_time
        ).group_by(MonitoringAlert.alert_level).all()
        
        # 解决状态统计
        status_stats = db.query(
            MonitoringAlert.is_resolved,
            func.count().label('count')
        ).filter(
            MonitoringAlert.timestamp >= start_time
        ).group_by(MonitoringAlert.is_resolved).all()
        
        return {
            'by_type': {row.alert_type: row.count for row in type_stats},
            'by_level': {row.alert_level: row.count for row in level_stats},
            'by_status': {row.is_resolved: row.count for row in status_stats},
            'total': sum(row.count for row in type_stats)
        }


# 创建CRUD实例
system_metrics = CRUDSystemMetrics(SystemMetrics)
gpu_metrics = CRUDGPUMetrics(GPUMetrics)
task_metrics = CRUDTaskMetrics(TaskMetrics)
monitoring_alert = CRUDMonitoringAlert(MonitoringAlert)