import socket
from flask import Flask, render_template, jsonify, request, render_template_string
import threading

# UDP 서버 설정
server_ip = "192.168.201.24"
server_port = 9001
server_addr_port = (server_ip, server_port)
client_ip = "192.168.201.30"
client_port = 8008
client_addr_port = (client_ip, client_port)
buffersize = 1024

# UDP 소켓 설정
udp_server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
udp_server_socket.bind(server_addr_port)

# Flask 웹 서버 설정
app = Flask(__name__)

# 상태 변수 (수신된 클라이언트 메시지)
client_message = {
    "airbag": 0,
    "occupants": 0,
    "driver": 0,
    "front_passenger": 0,
    "rear_left": 0,
    "rear_right": 0
}

# 웹페이지 템플릿
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Server Status</title>
</head>
<body>
    <h1>Client Message Status</h1>
    <p>Airbag Deployed: {{ data.airbag }}</p>
    <p>Occupants: {{ data.occupants }}</p>
    <p>Driver Seat Occupied: {{ data.driver }}</p>
    <p>Front Passenger Seat Occupied: {{ data.front_passenger }}</p>
    <p>Rear Left Seat Occupied: {{ data.rear_left }}</p>
    <p>Rear Right Seat Occupied: {{ data.rear_right }}</p>
    <button onclick="sendEmergencyCall()">119 신고</button>

    <script>
        function sendEmergencyCall() {
            fetch('/emergency', { method: 'POST' })
                .then(response => response.json())
                .then(data => alert(data.message))
                .catch(error => console.error('Error:', error));
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(html_template, data=client_message)

@app.route('/emergency', methods=['POST'])
def emergency():
    try:
        # 2바이트 메시지 생성 및 전송
        emergency_message = bytearray([8, 1])
        udp_server_socket.sendto(emergency_message, client_addr_port)
        return jsonify({"message": "Emergency signal sent!"})
    except Exception as e:
        return jsonify({"message": "Error sending signal", "error": str(e)}), 500

def udp_server():
    global client_message
    print("UDP server is up and listening")
    while True:
        try:
            byte_addr_pair = udp_server_socket.recvfrom(buffersize)
            msg = byte_addr_pair[0]
            addr = byte_addr_pair[1]

            if len(msg) == 6:
                # 메시지 디코딩 및 갱신
                client_message["airbag"] = msg[0]
                client_message["occupants"] = msg[1]
                client_message["driver"] = msg[2]
                client_message["front_passenger"] = msg[3]
                client_message["rear_left"] = msg[4]
                client_message["rear_right"] = msg[5]

                print(f"Updated message: {client_message}")

                # 2바이트 응답 생성 및 전송
                response_message = bytearray([9, 1])
                udp_server_socket.sendto(response_message, addr)  # 클라이언트에게 전송

        except BlockingIOError:
            continue
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    # UDP 서버를 별도 스레드에서 실행
    udp_thread = threading.Thread(target=udp_server, daemon=True)
    udp_thread.start()

    # Flask 웹 서버 실행
    app.run(host="0.0.0.0", port=5000)
