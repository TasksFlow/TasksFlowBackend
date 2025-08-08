from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user
from app.core.auth_decorators import admin_required, user_read_required, authenticated_required
from app.crud.monitoring import system_metrics, gpu_metrics, task_metrics, monitoring_alert
from app.schemas.monitoring import (
    SystemMetricsResponse, GPUMetricsResponse, TaskMetricsResponse,
    MonitoringAlertResponse, MonitoringAlertUpdate,
    SystemOverviewResponse, MetricsQueryParams, MetricsHistoryResponse,
    AlertLevel, AlertType, AlertStatus
)
from app.services.monitoring import monitoring_service

router = APIRouter()


@router.get("/overview", response_model=SystemOverviewResponse)
@authenticated_required
def get_system_overview(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取系统监控概览"""
    try:
        overview = monitoring_service.get_system_overview()
        return overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统概览失败: {str(e)}")


@router.get("/system/latest", response_model=Optional[SystemMetricsResponse])
@authenticated_required
def get_latest_system_metrics(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取最新的系统监控指标"""
    try:
        latest_metrics = system_metrics.get_latest(db)
        return latest_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统指标失败: {str(e)}")


@router.get("/system/history", response_model=List[SystemMetricsResponse])
@authenticated_required
def get_system_metrics_history(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    hours: Optional[int] = Query(24, description="获取最近N小时的数据"),
    limit: Optional[int] = Query(100, description="返回数据条数限制"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取系统监控历史数据"""
    try:
        if not start_time:
            start_time = datetime.utcnow() - timedelta(hours=hours)
        if not end_time:
            end_time = datetime.utcnow()
        
        metrics_history = system_metrics.get_by_time_range(db, start_time, end_time, limit)
        return metrics_history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统历史数据失败: {str(e)}")


@router.get("/system/aggregated", response_model=List[Dict[str, Any]])
@authenticated_required
def get_aggregated_system_metrics(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    hours: Optional[int] = Query(24, description="获取最近N小时的数据"),
    interval_minutes: Optional[int] = Query(5, description="聚合间隔（分钟）"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取聚合的系统监控数据"""
    try:
        if not start_time:
            start_time = datetime.utcnow() - timedelta(hours=hours)
        if not end_time:
            end_time = datetime.utcnow()
        
        aggregated_data = system_metrics.get_aggregated_data(db, start_time, end_time, interval_minutes)
        return aggregated_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取聚合数据失败: {str(e)}")


@router.get("/gpu/latest", response_model=List[GPUMetricsResponse])
@authenticated_required
def get_latest_gpu_metrics(db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)):
    """获取所有GPU的最新监控指标"""
    try:
        latest_gpu_metrics = gpu_metrics.get_all_latest(db)
        return latest_gpu_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取GPU指标失败: {str(e)}")


@router.get("/gpu/{gpu_index}/latest", response_model=Optional[GPUMetricsResponse])
@authenticated_required
def get_gpu_latest_metrics(gpu_index: int, db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)):
    """获取指定GPU的最新监控指标"""
    try:
        latest_metrics = gpu_metrics.get_latest_by_gpu(db, gpu_index)
        return latest_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取GPU {gpu_index} 指标失败: {str(e)}")


@router.get("/gpu/{gpu_index}/history", response_model=List[GPUMetricsResponse])
@authenticated_required
def get_gpu_metrics_history(
    gpu_index: int,
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    hours: Optional[int] = Query(24, description="获取最近N小时的数据"),
    limit: Optional[int] = Query(100, description="返回数据条数限制"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取指定GPU的监控历史数据"""
    try:
        if not start_time:
            start_time = datetime.utcnow() - timedelta(hours=hours)
        if not end_time:
            end_time = datetime.utcnow()
        
        metrics_history = gpu_metrics.get_by_gpu_and_time_range(db, gpu_index, start_time, end_time, limit)
        return metrics_history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取GPU {gpu_index} 历史数据失败: {str(e)}")


@router.get("/gpu/summary", response_model=Dict[int, Dict[str, Any]])
@authenticated_required
def get_gpu_usage_summary(
    hours: Optional[int] = Query(24, description="统计最近N小时的数据"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取GPU使用情况汇总"""
    try:
        summary = gpu_metrics.get_gpu_usage_summary(db, hours)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取GPU使用汇总失败: {str(e)}")


@router.get("/tasks/active", response_model=List[TaskMetricsResponse])
@authenticated_required
def get_active_tasks_metrics(db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)):
    """获取活跃任务的监控指标"""
    try:
        active_tasks = task_metrics.get_active_tasks_metrics(db)
        return active_tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取活跃任务指标失败: {str(e)}")


@router.get("/tasks/{task_id}", response_model=List[TaskMetricsResponse])
@authenticated_required
def get_task_metrics_history(task_id: str, db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)):
    """获取指定任务的监控历史数据"""
    try:
        task_history = task_metrics.get_by_task_id(db, task_id)
        return task_history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务 {task_id} 监控数据失败: {str(e)}")


@router.get("/tasks/{task_id}/summary", response_model=Optional[Dict[str, Any]])
@authenticated_required
def get_task_resource_summary(task_id: str, db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)):
    """获取任务资源使用汇总"""
    try:
        summary = task_metrics.get_task_resource_summary(db, task_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务 {task_id} 资源汇总失败: {str(e)}")


@router.get("/alerts", response_model=List[MonitoringAlertResponse])
@authenticated_required
def get_monitoring_alerts(
    alert_type: Optional[AlertType] = Query(None, description="告警类型"),
    alert_level: Optional[AlertLevel] = Query(None, description="告警级别"),
    status: Optional[AlertStatus] = Query(None, description="告警状态"),
    limit: Optional[int] = Query(50, description="返回数据条数限制"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取监控告警列表"""
    try:
        if status == AlertStatus.ACTIVE:
            alerts = monitoring_alert.get_active_alerts(db)
        elif alert_type and alert_level:
            alerts = monitoring_alert.get_by_type_and_level(db, alert_type, alert_level)
        else:
            alerts = monitoring_alert.get_multi(db, limit=limit, order_by="timestamp", order_desc=True)
        
        return alerts[:limit] if limit else alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取告警列表失败: {str(e)}")


@router.put("/alerts/{alert_id}/resolve", response_model=MonitoringAlertResponse)
@admin_required
def resolve_monitoring_alert(alert_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    """解决监控告警"""
    try:
        alert = monitoring_alert.resolve_alert(db, alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="告警不存在")
        return alert
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解决告警失败: {str(e)}")


@router.get("/alerts/statistics", response_model=Dict[str, Any])
@authenticated_required
def get_alert_statistics(
    days: Optional[int] = Query(7, description="统计最近N天的数据"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取告警统计信息"""
    try:
        stats = monitoring_alert.get_alert_statistics(db, days)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取告警统计失败: {str(e)}")


@router.post("/collect", response_model=Dict[str, str])
@admin_required
def trigger_metrics_collection(db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    """手动触发监控数据收集"""
    try:
        monitoring_service.collect_and_store_metrics()
        return {"message": "监控数据收集完成"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"触发数据收集失败: {str(e)}")


@router.delete("/cleanup", response_model=Dict[str, Any])
@admin_required
def cleanup_old_metrics(
    days_to_keep: Optional[int] = Query(30, description="保留最近N天的数据"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """清理旧的监控数据"""
    try:
        deleted_system = system_metrics.cleanup_old_data(db, days_to_keep)
        # 这里可以添加GPU和任务指标的清理逻辑
        
        return {
            "message": "数据清理完成",
            "deleted_system_metrics": deleted_system,
            "days_kept": days_to_keep
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据清理失败: {str(e)}")


@router.get("/status", response_model=Dict[str, Any])
def get_monitoring_status():
    """获取监控服务状态"""
    try:
        return {
            "service_running": monitoring_service.is_running,
            "collection_interval": monitoring_service.collection_interval,
            "alert_thresholds": monitoring_service.alert_thresholds,
            "gpu_available": hasattr(monitoring_service, 'GPU_AVAILABLE') and monitoring_service.GPU_AVAILABLE,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取监控状态失败: {str(e)}")