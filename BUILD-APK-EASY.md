# Cách tạo APK không cần cài Android Studio/SDK trên PC

Workflow GitHub Actions đã được thêm ở `.github/workflows/build-apk.yml`.

1. Tạo một repository GitHub mới (có thể để Private).
2. Upload toàn bộ nội dung thư mục `PCShieldStream` lên repository, giữ nguyên thư mục `.github/workflows` (nếu không thấy `.github`, bật hiển thị file ẩn hoặc upload qua Git).
3. Mở tab **Actions** của repository.
4. Chọn **Build PCShieldStream APK** ở cột trái.
5. Nhấn **Run workflow** → **Run workflow**.
6. Chờ workflow xanh (Success), mở lần chạy đó và tải artifact **PCShieldStream-debug-apk**. Giải nén artifact để lấy `app-debug.apk`.

APK được tạo trên runner Linux sạch với JDK 17, Android SDK 35 và Gradle 8.9. Nếu build lỗi, mở workflow và xem log bước đỏ đầu tiên.

Lưu ý: đây là debug APK để cài thử trong mạng LAN, không phải bản phát hành ký số. Không commit token hay thông tin cá nhân vào repository.
