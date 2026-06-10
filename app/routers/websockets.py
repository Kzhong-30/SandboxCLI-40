from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from ..services.websocket_manager import manager
import json

router = APIRouter(tags=["告警推送 (WebSocket)"])


@router.websocket(
    "/ws/alerts",
    name="实时告警推送 WebSocket",
)
async def websocket_endpoint(
    websocket: WebSocket,
    monitor_id: str = Query(..., description="订阅的监控任务ID"),
):
    """
    WebSocket 实时告警推送接口：
    - 连接时指定 monitor_id 参数订阅该监控任务的告警
    - 当触发告警时，会主动推送 JSON 格式消息
    - 消息格式: {"type": "ALERT", "data": {...}, "timestamp": "..."}
    - 客户端定期发送 {"type": "PING"} 保持连接
    """
    await manager.connect(monitor_id, websocket)

    try:
        welcome_msg = json.dumps({
            "type": "CONNECTED",
            "message": f"已成功订阅监控任务 {monitor_id} 的告警推送",
            "monitor_id": monitor_id,
        }, ensure_ascii=False)
        await websocket.send_text(welcome_msg)

        while True:
            data = await websocket.receive_text()
            try:
                parsed = json.loads(data)
                if parsed.get("type") == "PING":
                    pong = json.dumps({
                        "type": "PONG",
                        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
                    })
                    await websocket.send_text(pong)
            except Exception:
                pass

    except WebSocketDisconnect:
        manager.disconnect(monitor_id, websocket)
