from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import psycopg2
from psycopg2.extras import RealDictCursor
import datetime
import json

# ===== CẤU HÌNH =====
DB_CONFIG = {
    "host": "localhost",
    "database": "smart_utility_db",
    "user": "postgres",
    "password": "tech",  
    "port": 5432
}

app = FastAPI(title="Smart Utility Incident Management API")

# ===== ĐỊNH NGHĨA MODEL CHO REQUEST =====
class IncidentCreate(BaseModel):
    lat: float
    lng: float
    description: str
    radius: Optional[int] = 100  # mặc định 100m

class IncidentResponse(BaseModel):
    incident_id: int
    affected_count: int
    customers: List[dict]
    message: str

# ===== HELPER: KẾT NỐI DATABASE =====
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# ===== ENDPOINT 1: TẠO SỰ CỐ =====
@app.post("/api/incidents", response_model=IncidentResponse)
async def create_incident(incident: IncidentCreate):
    """
    Tạo sự cố mới và tìm khách hàng bị ảnh hưởng
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Lưu sự cố vào incident_log
        cursor.execute("""
            INSERT INTO incident_log 
            (incident_description, incident_geom, radius_meters)
            VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s)
            RETURNING incident_id
        """, (
            incident.description,
            incident.lng,
            incident.lat,
            incident.radius
        ))
        
        incident_id = cursor.fetchone()['incident_id']
        conn.commit()
        
        # 2. Gọi hàm tìm khách hàng bị ảnh hưởng
        cursor.execute("""
            SELECT * FROM find_affected_customers(%s, %s, %s)
        """, (incident.lat, incident.lng, incident.radius))
        
        affected_customers = cursor.fetchall()
        affected_count = len(affected_customers)
        
        # 3. Cập nhật số lượng khách hàng bị ảnh hưởng
        cursor.execute("""
            UPDATE incident_log 
            SET affected_customers = %s 
            WHERE incident_id = %s
        """, (affected_count, incident_id))
        conn.commit()
        
        # 4. MÔ PHỎNG GỬI CẢNH BÁO (OMS/CRM Integration)
        send_notification(affected_customers, incident.description)
        
        return IncidentResponse(
            incident_id=incident_id,
            affected_count=affected_count,
            customers=[dict(c) for c in affected_customers],
            message=f"Đã tìm thấy {affected_count} khách hàng bị ảnh hưởng"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            cursor.close()
            conn.close()

# ===== ENDPOINT 2: TÌM TÀI SẢN GẦN NHẤT =====
@app.get("/api/assets/nearby")
async def get_nearby_assets(lat: float, lng: float, range_meters: int = 500):
    """
    Tìm tài sản (cột điện/trạm) gần vị trí nhất
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                asset_id,
                asset_name,
                asset_type,
                status,
                ST_Distance(
                    geom::geography,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                ) AS distance_meters,
                ST_X(geom) AS lng,
                ST_Y(geom) AS lat
            FROM 
                network_assets
            WHERE 
                ST_DWithin(
                    geom::geography,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                    %s
                )
            ORDER BY 
                distance_meters
            LIMIT 10
        """, (lng, lat, lng, lat, range_meters))
        
        assets = cursor.fetchall()
        
        return {
            "status": "success",
            "count": len(assets),
            "assets": [dict(a) for a in assets]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            cursor.close()
            conn.close()

# ===== MÔ PHỎNG GỬI CẢNH BÁO (OMS/CRM) =====
def send_notification(customers, message):
    """
    Mô phỏng gửi cảnh báo đến khách hàng
    """
    if not customers:
        print("📭 Không có khách hàng nào bị ảnh hưởng")
        return
    
    print(f"📨 ===== GỬI CẢNH BÁO ĐẾN {len(customers)} KHÁCH HÀNG =====")
    for i, customer in enumerate(customers[:5]):  # Chỉ hiển thị 5 khách hàng đầu
        print(f"  📞 Gọi đến {customer['phone']} - KH: {customer['customer_name']}")
        print(f"     📝 Tin nhắn: Sự cố '{message}' ảnh hưởng đến khu vực của bạn")
    
    if len(customers) > 5:
        print(f"  ... và {len(customers) - 5} khách hàng khác")
    
    # Ghi vào file log để mô phỏng
    with open("notification_log.txt", "a", encoding="utf-8") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"\n[{timestamp}] Đã gửi cảnh báo đến {len(customers)} khách hàng\n")
        for c in customers:
            f.write(f"  - {c['customer_name']} ({c['phone']})\n")

# ===== RUN =====
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)