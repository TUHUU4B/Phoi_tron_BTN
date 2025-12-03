# Ứng dụng Thiết kế Phối trộn Cốt liệu BTN

Ứng dụng Streamlit giúp tính toán **tỷ lệ phối trộn cốt liệu** cho bê tông nhựa (BTN) sao cho đường cong hạt của hỗn hợp nằm **trong giới hạn yêu cầu** theo tiêu chuẩn **TCVN 13567-1:2022**.

## Tính năng chính

- ✅ Tính toán tự động tỷ lệ phối trộn tối ưu cho các loại BTN (C25, C19, C16, C12,5, C9,5, C4,75)
- ✅ Giới hạn cấp phối theo **TCVN 13567-1:2022, Bảng 1** (có thể chỉnh sửa trực tiếp)
- ✅ Tự động ẩn các cỡ sàng không liên quan khi chọn loại BTN
- ✅ Cho phép chỉnh sửa tỷ lệ phối trộn sau khi tính toán
- ✅ Phân loại cấp phối (thô/mịn) theo **TCVN 13567-1:2022, Bảng 2**
- ✅ Biểu đồ thành phần hạt với trục logarit
- ✅ Định dạng số theo quy cách Việt Nam (dấu phẩy cho thập phân, dấu chấm cho hàng nghìn)

## Yêu cầu hệ thống

- Python 3.8 trở lên
- Các thư viện Python (xem `requirements.txt`)

## Cài đặt

1. **Clone hoặc tải xuống thư mục dự án**

2. **Cài đặt các thư viện cần thiết:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Chuẩn bị file logo (tùy chọn):**
   - Đặt file `logo.png` trong cùng thư mục với `app.py` để hiển thị logo công ty

## Chạy ứng dụng

```bash
streamlit run app.py
```

Ứng dụng sẽ tự động mở trong trình duyệt tại địa chỉ `http://localhost:8501`

## Hướng dẫn sử dụng

### Bước 1: Chọn loại BTN và số lượng cốt liệu

- Trong **sidebar bên trái**, chọn loại BTN cần thiết kế (ví dụ: BTN C19, BTN C16...)
- Nhập số lượng cốt liệu tham gia phối trộn (2-6 loại)

### Bước 2: Kiểm tra/Chỉnh sửa giới hạn cấp phối yêu cầu

- Bảng **"Giới hạn cấp phối yêu cầu"** hiển thị các giới hạn theo TCVN 13567-1:2022, Bảng 1
- Bạn có thể **chỉnh sửa trực tiếp** các giá trị Cận dưới và Cận trên nếu cần
- Các cỡ sàng không liên quan sẽ tự động ẩn đi

### Bước 3: Nhập cấp phối từng loại cốt liệu

- Trong bảng **"Cấp phối từng loại cốt liệu (% lọt sàng tích lũy)"**, nhập:
  - **% lọt sàng tích lũy** cho từng cỡ sàng
  - Ví dụ: đá dăm, cát, bột khoáng...
- Số liệu được nhập theo định dạng Việt Nam (ví dụ: `12,5` thay vì `12.5`)

### Bước 4: Tính toán phối trộn

- Nhấn nút **"Tính phối trộn"** để chương trình tự động tính toán
- Thuật toán sử dụng **Lập trình tuyến tính (Linear Programming)** để tìm tỷ lệ tối ưu
- Kết quả sẽ hiển thị:
  - **Tỷ lệ phối trộn tối ưu** (có thể chỉnh sửa)
  - **Phân loại cấp phối** (thô/mịn) theo Bảng 2
  - **Bảng so sánh đường cong hạt** với giới hạn
  - **Biểu đồ thành phần hạt** với trục logarit

### Bước 5: Điều chỉnh tỷ lệ (tùy chọn)

- Sau khi tính toán, bạn có thể **chỉnh sửa lại tỷ lệ (%)** cho từng cốt liệu
- Chương trình sẽ tự động **chuẩn hóa tổng về 100%**
- Đường cong cấp phối và biểu đồ sẽ được **cập nhật tự động** theo tỷ lệ mới

## Cấu trúc dự án

```
Phoi tron BTN/
├── app.py                 # File ứng dụng chính
├── requirements.txt       # Danh sách thư viện cần thiết
├── README.md             # File hướng dẫn này
└── logo.png              # Logo công ty (tùy chọn)
```

## Thuật toán

Ứng dụng sử dụng **Lập trình tuyến tính (Linear Programming)** với thư viện `PuLP` để:

1. Tìm tỷ lệ phối trộn các cốt liệu sao cho:
   - Tổng tỷ lệ = 100%
   - Đường cong hạt hỗn hợp nằm trong dải [Cận dưới, Cận trên] cho mọi cỡ sàng
   - Tối ưu hóa: kết quả nằm gần giữa dải yêu cầu

2. Phân loại cấp phối theo TCVN 13567-1:2022, Bảng 2:
   - Dựa trên % lọt qua cỡ sàng khống chế
   - Xác định loại: **Cấp phối thô** hoặc **Cấp phối mịn**

## Lưu ý

- Nếu không tìm được phương án phối trộn thỏa mãn, hãy kiểm tra lại:
  - Giới hạn cấp phối yêu cầu
  - Cấp phối từng loại cốt liệu
  - Có thể cần điều chỉnh số liệu đầu vào

- Các giá trị trong bảng giới hạn có thể được chỉnh sửa để phù hợp với tài liệu thiết kế thực tế

## Thông tin liên hệ

**CÔNG TY TỨ HỮU**  
Tác giả: MR Tuấn - 0946135156

## Giấy phép

Dự án này được phát triển cho mục đích sử dụng nội bộ.

