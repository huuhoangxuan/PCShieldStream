# PCShieldStream 1.2.0 — thay đổi

- Sửa GitHub Actions: chỉ cài `platform-tools` trong bước setup Android SDK, tránh gói `tools` đã bị ngừng cung cấp.
- Giữ Java 17 và Gradle 8.9; workflow xuất đúng file `app-debug.apk` thành artifact.
- Thêm tìm kiếm tên phim/thư mục và chuyển sắp xếp theo tên/dung lượng.
- Thêm trạng thái chờ khi mở phim, hỗ trợ nút Back của remote để đóng trình phát/quay lại.
- Lưu tiến độ trước khi đóng trình phát và tránh release ExoPlayer hai lần.
- Tăng HTTP read timeout, thêm HEAD cho luồng, kiểm tra HTTP Range chặt hơn và xử lý client ngắt kết nối không như lỗi server 500.
- Sửa chuẩn hóa tên phim/series để tìm poster tốt hơn, chỉ cache poster tìm thấy để lỗi Internet tạm thời không lưu kết quả rỗng vĩnh viễn.
- Thêm smoke test Python cho health, duyệt thư mục, HTTP Range, HEAD và làm sạch tên phim.
- Thêm cấu hình thư mục phim thứ hai tùy chọn trong `start_server.bat`.
- Cập nhật icon launcher và version ứng dụng lên 1.2.0.

## Đã kiểm tra

- `python -m py_compile server.py test_server_smoke.py`: đạt.
- `python test_server_smoke.py`: đạt (health/list/range/HEAD/title cleanup).
- Chưa build Android APK trong môi trường này vì không có Android SDK/Gradle toolchain; cần GitHub Actions build và thử nghiệm thực tế trên Shield để xác nhận phần Kotlin/Media3.
