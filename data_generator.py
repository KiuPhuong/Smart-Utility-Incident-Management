import random
import psycopg2
from psycopg2.extras import execute_values
import math
from datetime import datetime

# ===== CẤU HÌNH KẾT NỐI DATABASE =====
DB_CONFIG = {
    "host": "localhost",
    "database": "smart_utility_db",
    "user": "postgres",
    "password": "tech", 
    "port": 5432
}

# ===== TỌA ĐỘ TRUNG TÂM CÁC QUẬN Ở TP.HCM =====
DISTRICTS = {
    "Quận 1": {"lat": 10.7767, "lng": 106.7008, "radius": 1.8},
    "Quận 2": {"lat": 10.7805, "lng": 106.7390, "radius": 3.5},
    "Quận 3": {"lat": 10.7760, "lng": 106.6847, "radius": 1.5},
    "Quận 4": {"lat": 10.7616, "lng": 106.7041, "radius": 1.2},
    "Quận 5": {"lat": 10.7569, "lng": 106.6670, "radius": 1.2},
    "Quận 6": {"lat": 10.7533, "lng": 106.6481, "radius": 1.5},
    "Quận 7": {"lat": 10.7300, "lng": 106.7184, "radius": 3.0},
    "Quận 8": {"lat": 10.7266, "lng": 106.6279, "radius": 2.5},
    "Quận 10": {"lat": 10.7696, "lng": 106.6686, "radius": 1.2},
    "Quận 11": {"lat": 10.7645, "lng": 106.6451, "radius": 1.2},
    "Quận 12": {"lat": 10.8645, "lng": 106.6642, "radius": 4.0},
    "Bình Thạnh": {"lat": 10.8003, "lng": 106.7107, "radius": 2.5},
    "Phú Nhuận": {"lat": 10.7994, "lng": 106.6773, "radius": 1.2},
    "Tân Bình": {"lat": 10.8013, "lng": 106.6507, "radius": 3.0},
    "Tân Phú": {"lat": 10.7870, "lng": 106.6311, "radius": 2.5},
    "Gò Vấp": {"lat": 10.8365, "lng": 106.6738, "radius": 3.0},
    "Bình Tân": {"lat": 10.7738, "lng": 106.6098, "radius": 3.5},
    "Thủ Đức": {"lat": 10.8470, "lng": 106.7724, "radius": 4.5},
}

def generate_random_point_in_district(district_name):
    """Tạo điểm ngẫu nhiên trong bán kính của quận"""
    district = DISTRICTS[district_name]
    center_lat = district["lat"]
    center_lng = district["lng"]
    radius_km = district["radius"]
    
    radius_deg = radius_km / 111.0
    
    angle = random.uniform(0, 2 * math.pi)
    r = math.sqrt(random.uniform(0, 1)) * radius_deg
    
    lat = center_lat + r * math.cos(angle)
    lng = center_lng + r * math.sin(angle)
    
    return (lat, lng)

def insert_sample_data():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Xóa dữ liệu cũ
        cursor.execute("DELETE FROM network_assets;")
        cursor.execute("DELETE FROM customers;")
        print("🗑️ Đã xóa dữ liệu cũ")
        
        # Tạo Spatial Index
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_customers_geom 
            ON customers USING GIST (geom);
            
            CREATE INDEX IF NOT EXISTS idx_assets_geom 
            ON network_assets USING GIST (geom);
        """)
        print("✅ Đã tạo Spatial Index")
        
        print("🔹 Đang tạo 1,000,000 khách hàng...")
        print("⏳ Quá trình này có thể mất 15-30 phút!")
        
        # ---- TẠO 1 TRIỆU KHÁCH HÀNG ----
        customers = []
        first_names = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Vũ", "Đặng", "Bùi", "Đỗ", "Hồ",
                       "Ngô", "Dương", "Lý", "Trương", "Phan", "Vương", "Lâm", "Tạ", "Mai", "Chu"]
        
        middle_names = ["Văn", "Thị", "Minh", "Thanh", "Quang", "Thu", "Hải", "Phương", "Đức", "Kim",
                        "Hữu", "Như", "Công", "Thành", "Đình", "Ngọc", "Bảo", "Gia", "Mỹ", "Anh"]
        
        last_names = ["Anh", "Bình", "Cường", "Dung", "Hạnh", "Hùng", "Hương", "Khoa", "Lan", "Mai", 
                      "Nam", "Ngọc", "Phúc", "Quân", "Sơn", "Tâm", "Thảo", "Trang", "Tuấn", "Vinh",
                      "Hiệp", "Ninh", "Khang", "Nhân", "Tín", "Tài", "Lộc", "Phát", "Đạt", "Thắng"]
        
        streets = ["Lê Lợi", "Nguyễn Huệ", "Điện Biên Phủ", "Võ Văn Tần", "Lý Thường Kiệt", 
                   "Hai Bà Trưng", "Trần Hưng Đạo", "Nguyễn Đình Chiểu", "Phạm Ngọc Thạch", 
                   "Nguyễn Thị Minh Khai", "Trần Quốc Thảo", "Cách Mạng Tháng 8", "Hoàng Văn Thụ",
                   "Võ Văn Ngân", "Nguyễn Xí", "Phạm Văn Đồng", "Trần Phú", "Nguyễn Trãi",
                   "Lê Duẩn", "Nguyễn Bỉnh Khiêm", "Tô Hiến Thành", "Đinh Tiên Hoàng",
                   "Nguyễn Du", "Hùng Vương", "Quang Trung", "Trần Nhân Tông"]
        
        district_names = list(DISTRICTS.keys())
        total_customers = 1000000
        customers_per_district = total_customers // len(district_names)
        
        print(f"📊 Mỗi quận sẽ có ~{customers_per_district:,} khách hàng")
        
        count = 0
        for district in district_names:
            radius = DISTRICTS[district]["radius"]
            print(f"⏳ Đang tạo {customers_per_district:,} khách hàng tại {district} (bán kính {radius}km)...")
            
            for i in range(customers_per_district):
                lat, lng = generate_random_point_in_district(district)
                
                first = random.choice(first_names)
                middle = random.choice(middle_names)
                last = random.choice(last_names)
                customer_name = f"{first} {middle} {last}"
                
                contract_no = f"CT-{random.randint(2020, 2024)}-{random.randint(100000, 999999)}"
                phone = f"0{random.randint(700000000, 999999999)}"
                address = f"{random.randint(1, 999)} Đường {random.choice(streets)}, {district}, TP.HCM"
                
                customers.append((
                    customer_name,
                    contract_no,
                    phone,
                    address,
                    f"SRID=4326;POINT({lng} {lat})"
                ))
                
                count += 1
                
                if len(customers) >= 5000:
                    execute_values(
                        cursor,
                        """INSERT INTO customers 
                           (customer_name, contract_no, phone, address, geom) 
                           VALUES %s""",
                        customers
                    )
                    conn.commit()
                    customers = []
                    print(f"   ✅ Đã insert {count:,} khách hàng...")
            
            print(f"✅ Hoàn thành {district} - Tổng: {count:,} khách hàng")
        
        # Insert phần còn lại
        if customers:
            execute_values(
                cursor,
                """INSERT INTO customers 
                   (customer_name, contract_no, phone, address, geom) 
                   VALUES %s""",
                customers
            )
            conn.commit()
        
        # ---- TẠO 10,000 TÀI SẢN ----
        print("⏳ Đang tạo 10,000 tài sản...")
        assets = []
        asset_types = ['pole', 'pole', 'pole', 'pole', 'transformer', 'substation']
        vietnamese_asset_names = [
            "Cột điện", "Trạm biến áp", "Trạm cấp nước", 
            "Cột đèn đường", "Hố ga", "Trạm bơm",
            "Cột viễn thông", "Trạm trung chuyển"
        ]
        
        for i in range(10000):
            district = random.choice(district_names)
            lat, lng = generate_random_point_in_district(district)
            asset_name = f"{random.choice(vietnamese_asset_names)} {i+1}"
            asset_type = random.choice(asset_types)
            status = random.choices(['active', 'active', 'active', 'active', 'maintenance', 'repair'])[0]
            
            assets.append((
                asset_name,
                asset_type,
                status,
                f"SRID=4326;POINT({lng} {lat})"
            ))
            
            if len(assets) >= 1000:
                execute_values(
                    cursor,
                    """INSERT INTO network_assets 
                       (asset_name, asset_type, status, geom) 
                       VALUES %s""",
                    assets
                )
                conn.commit()
                assets = []
        
        if assets:
            execute_values(
                cursor,
                """INSERT INTO network_assets 
                   (asset_name, asset_type, status, geom) 
                   VALUES %s""",
                assets
            )
            conn.commit()
        
        print("\n" + "="*70)
        print("🎉 TẠO DỮ LIỆU THÀNH CÔNG!")
        print("="*70)
        print(f"👥 Tổng số khách hàng: 1,000,000")
        print(f"📊 Tổng số tài sản: 10,000")
        print(f"📍 Phân bố trên {len(district_names)} quận của TP.HCM")
        print("="*70)
        print("📏 Bán kính từng quận:")
        for district, info in DISTRICTS.items():
            print(f"   - {district}: {info['radius']}km")
        print("="*70)
        
    except Exception as e:
        print(f"❌ LỖI: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    print("="*70)
    print("🚀 TẠO 1 TRIỆU KHÁCH HÀNG GIẢ LẬP - TP.HCM")
    print("="*70)
    start_time = datetime.now()
    insert_sample_data()
    end_time = datetime.now()
    print(f"⏱️ Thời gian thực hiện: {(end_time - start_time).seconds} giây")