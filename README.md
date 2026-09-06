# ⚡ Smart Utility Incident Management System

**Hệ thống quản lý sự cố thông minh cho mạng lưới điện/nước TP.HCM**

---

## 📌 Vấn đề thực tế

Tại TP.HCM, mỗi khi xảy ra sự cố mất điện hoặc nước, các công ty điện lực phải mất 30-45 phút để xác định danh sách khách hàng bị ảnh hưởng. Việc thông báo vẫn làm thủ công qua điện thoại, dẫn đến bỏ sót nhiều khách hàng và hàng loạt cuộc gọi khiếu nại. Đội sửa chữa thì không biết vị trí chính xác của cột điện hay trạm biến áp gần nhất, gây chậm trễ và tổn thất kinh tế.

Đây là bài toán thực tế mà tôi đã giải quyết trong project này.

---

## 🚀 Giải pháp

Hệ thống cho phép chỉ cần một cú click trên bản đồ để:
- Khoanh vùng ảnh hưởng và **liệt kê chính xác từng khách hàng** bị tác động
- Định vị **cột điện hoặc trạm biến áp gần nhất** để cử người sửa chữa

**Thời gian xử lý giảm từ 30-45 phút xuống còn dưới 10 giây.**

---

## 💻 Công nghệ sử dụng

- **FastAPI** (Python) - Xây dựng RESTful API
- **PostgreSQL + PostGIS** - Lưu trữ và xử lý dữ liệu không gian
- **Leaflet.js** - Bản đồ tương tác
- **Spatial Query** - Truy vấn không gian với ST_DWithin, ST_Distance

---

## 📊 Quy mô dữ liệu

- **1.000.000+** khách hàng giả lập
- **10.000+** tài sản (cột điện, trạm biến áp)
- **18 quận** tại TP.HCM

---

## 🔧 Tính năng nổi bật

### 1. Phát hiện khách hàng bị ảnh hưởng
Sử dụng PostGIS để tìm kiếm không gian, trả về danh sách khách hàng kèm khoảng cách chính xác đến từng mét.

### 2. Tìm tài sản gần nhất
Xác định cột điện hoặc trạm biến áp gần nhất cùng trạng thái hoạt động (active/maintenance/repair).

### 3. Bản đồ tương tác
Hiển thị trực quan vùng ảnh hưởng, vị trí khách hàng và tài sản.

---

## 📦 Demo

```bash
# Cài đặt và chạy
pip install -r requirements.txt
python data_generator.py   # Tạo 1 triệu khách hàng + 10 nghìn tài sản
python app.py              # Chạy backend
# Mở index.html trong trình duyệt
