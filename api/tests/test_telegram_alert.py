import requests
import time

# Đảm bảo URL này trỏ đúng vào port mà FastAPI của bạn đang chạy trên máy host (thường là 8000)
API_BASE_URL = "http://localhost:8000/security"


def test_critical_alert():
    print("🚀 Đang gửi bài test CRITICAL (Tự động chặn)...")
    payload = {
        "attack_type": "DDoS Flooding",
        "severity": "CRITICAL",
        "dpid": "1152921504606846977",
        "attacker_mac": "02:00:00:00:00:00",
        "details": "Massive ICMP packets detected",  # Thêm trường này nếu schema Alert của bạn có
    }

    try:
        response = requests.post(f"{API_BASE_URL}/alert", json=payload)
        response.raise_for_status()
        print("✅ Thành công! Hãy kiểm tra Telegram xem có tin nhắn CRITICAL không.\n")
    except requests.exceptions.RequestException as e:
        print(f"❌ Thất bại: Không thể kết nối tới FastAPI. Lỗi: {e}\n")


def test_warning_alert():
    print("🚀 Đang gửi bài test WARNING (Kèm nút bấm)...")
    payload = {
        "attack_type": "ARP Spoofing",
        "severity": "WARNING",
        "dpid": 1,
        "attacker_mac": "AA:BB:CC:DD:EE:22",
        "details": "Suspicious ARP replies detected",
    }

    try:
        response = requests.post(f"{API_BASE_URL}/alert", json=payload)
        response.raise_for_status()
        print(
            "✅ Thành công! Hãy kiểm tra Telegram xem có tin nhắn WARNING kèm 2 nút bấm không.\n"
        )
    except requests.exceptions.RequestException as e:
        print(f"❌ Thất bại: Không thể kết nối tới FastAPI. Lỗi: {e}\n")


if __name__ == "__main__":
    print("========== BẮT ĐẦU TEST TELEGRAM ALERTS ==========\n")

    test_critical_alert()

    # Nghỉ 3 giây để Telegram không bị dội bom tin nhắn quá nhanh
    time.sleep(3)

    test_warning_alert()

    print("========== HOÀN TẤT ==========")
    print("👉 Bây giờ hãy mở Telegram trên điện thoại của bạn lên. ")
    print(
        "👉 Bạn hãy thử bấm vào nút [Bo Qua] hoặc [Chan Ngay] để test luôn luồng Callback nhé!"
    )
