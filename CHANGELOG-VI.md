# Nhật ký thay đổi PCShieldStream

## 1.3.0
- Trình phát tiếp tục hoạt động nếu API tiến độ hoặc phụ đề phụ trợ tạm thời lỗi.
- Lưu tiến độ mỗi 15 giây, khi ứng dụng chuyển nền/thoát trình phát; đặt tiến độ về 0 khi xem hết phim.
- Cache poster không tìm thấy trong 6 giờ, cache poster thành công 30 ngày; không cache lỗi mạng tạm thời.
- Giới hạn tối đa 3 lượt tìm poster đồng thời.
- Thêm trạng thái focus dễ thấy cho thẻ phim/thư mục khi dùng remote TV.
- Server dùng cache tiến độ trong bộ nhớ, ghi file JSON nguyên tử, kiểm tra path video cho API tiến độ.
- Server từ chối kết nối có IP nguồn không thuộc loopback/private/link-local; thêm hướng dẫn giới hạn Windows Firewall theo mạng Private.
- Cập nhật workflow SDK để không cài gói `tools` đã bị ngừng phát hành.

## 1.2.0
- Bản nền: thư viện phim, lưu IP, poster, HTTP Range và Media3 ExoPlayer.
