"""
Penugasan Individu Pertemuan 10 - Pemrograman IoT (SIF1502)
Simulasi perangkat ESP32 menggunakan Python + MQTT (Mosquitto lokal).

NIM : 2410010364

Fungsi:
1. Kirim suhu (simulasi DHT22) setiap 3 detik -> iot/2410010364/sensor/suhu
2. Terima perintah relay "ON"/"OFF" (simulasi GPIO 26) -> iot/2410010364/aktuator/relay
3. Terima nilai PWM 0-255 (simulasi LED GPIO 2)  -> iot/2410010364/aktuator/pwm
4. Kirim feedback status relay & PWM ke dashboard
"""
import time
import random
import threading
import paho.mqtt.client as mqtt

# ================= KONFIGURASI =================
NIM = "2410010364"
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_CLIENT_ID = f"PythonDevice-{NIM}"

TOPIC_SUHU = f"iot/{NIM}/sensor/suhu"
TOPIC_RELAY = f"iot/{NIM}/aktuator/relay"
TOPIC_PWM = f"iot/{NIM}/aktuator/pwm"
TOPIC_STATUS_RELAY = f"iot/{NIM}/status/relay"
TOPIC_STATUS_PWM = f"iot/{NIM}/status/pwm"

PIN_RELAY = 26   # GPIO 26 -> relay
PIN_LED_PWM = 2  # GPIO 2  -> LED (PWM)
INTERVAL_PUBLISH = 3  # detik

# ================= STATE GLOBAL =================
relay_state = "OFF"
pwm_value = 0


# ================= CALLBACK MQTT =================
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[MQTT] Terhubung ke broker")
        client.subscribe([(TOPIC_RELAY, 0), (TOPIC_PWM, 0)])
        print(f"[MQTT] Subscribe: {TOPIC_RELAY}")
        print(f"[MQTT] Subscribe: {TOPIC_PWM}")
    else:
        print(f"[MQTT] Gagal terhubung, kode: {rc}")


def on_message(client, userdata, msg):
    global relay_state, pwm_value
    payload = msg.payload.decode("utf-8").strip()
    print(f"[MQTT] Pesan masuk [{msg.topic}]: {payload}")

    if msg.topic == TOPIC_RELAY:
        if payload.upper() in ("ON", "1"):
            relay_state = "ON"
            print(f"[AKTUATOR] GPIO {PIN_RELAY} (RELAY) -> HIGH / MENYALA")
        elif payload.upper() in ("OFF", "0"):
            relay_state = "OFF"
            print(f"[AKTUATOR] GPIO {PIN_RELAY} (RELAY) -> LOW / MATI")
        else:
            print(f"[AKTUATOR] Perintah relay tidak dikenal: {payload}")
            return
        client.publish(TOPIC_STATUS_RELAY, relay_state)
        print(f"[MQTT] Publish status: {TOPIC_STATUS_RELAY} -> {relay_state}")

    elif msg.topic == TOPIC_PWM:
        try:
            nilai = int(float(payload))
        except ValueError:
            print(f"[AKTUATOR] Nilai PWM tidak valid: {payload}")
            return
        nilai = max(0, min(255, nilai))  # batasi 0-255
        pwm_value = nilai
        persen = round(nilai / 255 * 100)
        print(f"[AKTUATOR] GPIO {PIN_LED_PWM} (LED PWM) -> {nilai}/255 (kecerahan {persen}%)")
        client.publish(TOPIC_STATUS_PWM, str(pwm_value))
        print(f"[MQTT] Publish status: {TOPIC_STATUS_PWM} -> {pwm_value}")


def on_disconnect(client, userdata, *args):
    print("[MQTT] Terputus dari broker. Mencoba reconnect...")


# ================= SENSOR =================
def baca_suhu():
    """Simulasi DHT22: suhu acak sekitar 27 C."""
    return round(27.0 + random.uniform(-1.5, 1.5), 2)


def publish_loop(client):
    while True:
        try:
            suhu = baca_suhu()
            client.publish(TOPIC_SUHU, str(suhu))
            print(f"[SENSOR] Publish suhu: {TOPIC_SUHU} -> {suhu} °C")
        except Exception as e:
            print(f"[SENSOR] Error: {e}")
        time.sleep(INTERVAL_PUBLISH)


# ================= MAIN =================
def main():
    try:  # paho-mqtt 2.x
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                             client_id=MQTT_CLIENT_ID, protocol=mqtt.MQTTv311)
    except AttributeError:  # paho-mqtt 1.x
        client = mqtt.Client(client_id=MQTT_CLIENT_ID, protocol=mqtt.MQTTv311)

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    print(f"[MQTT] Menghubungkan ke {MQTT_BROKER}:{MQTT_PORT}...")
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()
    time.sleep(1)

    # kirim status awal supaya dashboard sinkron
    client.publish(TOPIC_STATUS_RELAY, relay_state)
    client.publish(TOPIC_STATUS_PWM, str(pwm_value))

    threading.Thread(target=publish_loop, args=(client,), daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[MAIN] Menghentikan program...")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
