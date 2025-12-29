import socket
import ssl
import sys


def test_connection():
    host = "db.jfzkqlynhzlzbuqihbxj.supabase.co"
    port = 5432

    print(f"Тестирование подключения к {host}:{port}")

    # 1. Проверка DNS
    try:
        # Принудительно ищем IPv6 адрес
        info = socket.getaddrinfo(host, port, socket.AF_INET6, socket.SOCK_STREAM)
        ipv6_addr = info[0][4][0]
        print(f"✅ IPv6 адрес найден: {ipv6_addr}")
    except Exception as e:
        print(f"❌ Ошибка DNS: {e}")

        # Пробуем получить через nslookup
        import subprocess
        result = subprocess.run(['nslookup', host], capture_output=True, text=True)
        print(f"Результат nslookup:\n{result.stdout}")
        return False

    # 2. Проверка TCP подключения
    try:
        # Создаем сокет с IPv6
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock.settimeout(5)

        print(f"Попытка подключения к {ipv6_addr}:{port}...")
        sock.connect((ipv6_addr, port))
        print("✅ TCP подключение успешно!")

        # Проверяем SSL/TLS (PostgreSQL использует SSL)
        context = ssl.create_default_context()
        ssl_sock = context.wrap_socket(sock, server_hostname=host)
        print("✅ SSL подключение успешно!")

        ssl_sock.close()
        return True

    except socket.timeout:
        print("❌ Таймаут подключения")
    except ConnectionRefusedError:
        print("❌ Подключение отклонено")
    except Exception as e:
        print(f"❌ Ошибка подключения: {type(e).__name__}: {e}")

    return False


if __name__ == "__main__":
    test_connection()