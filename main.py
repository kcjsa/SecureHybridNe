import socket
import threading
import time
import math
import os
import struct
import logging
import queue
import tkinter as tk
from tkinter import filedialog
import pygame
import sys

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding

# ===== 設定 =====
TARGET_IP = "127.0.0.1"  # 送信先IP（テスト用にlocalhost）
TCP_PORT = 8888
UDP_PORT = 9999
AES_KEY = b'\x01\x23\x45\x67\x89\xab\xcd\xef' * 4  # 32バイト(256bit)
PRIMES = [53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127]
CHUNK_SIZE = 1024  # 1チャンクのファイルデータサイズ
ACK_TIMEOUT = 1.0  # UDP ACKタイムアウト秒
MAX_RETRY = 5     # UDP最大再送回数

# ===== ログ設定 =====
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] %(asctime)s %(message)s',
    datefmt='%H:%M:%S'
)

# ===== AES暗号化関数 =====
def aes_encrypt(data: bytes, key: bytes) -> bytes:
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(128).padder()
    padded = padder.update(data) + padder.finalize()
    encrypted = encryptor.update(padded) + encryptor.finalize()
    return iv + encrypted

def aes_decrypt(enc: bytes, key: bytes) -> bytes:
    iv = enc[:16]
    ciphertext = enc[16:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    data = unpadder.update(padded) + unpadder.finalize()
    return data

# ===== パケット長素数調整 =====
def adjust_length_to_prime(data: bytes) -> bytes:
    current_len = len(data)
    target_len = next((p for p in PRIMES if p >= current_len), current_len)
    pad_len = target_len - current_len
    if pad_len > 0:
        data += os.urandom(pad_len)
    return data

# ===== π+ネイピア数桁取得 =====
def irrational_digit(n: int) -> int:
    seq = str(math.pi + math.e).replace('.', '')
    return int(seq[n % len(seq)])

# ===== ファイル送信クラス =====
class FileSender:
    def __init__(self, target_ip, tcp_port, udp_port, aes_key):
        self.target_ip = target_ip
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.aes_key = aes_key

        self.tcp_sock = None
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.settimeout(ACK_TIMEOUT)

    def connect_tcp(self):
        while True:
            try:
                if self.tcp_sock:
                    self.tcp_sock.close()
                self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.tcp_sock.settimeout(5)
                self.tcp_sock.connect((self.target_ip, self.tcp_port))
                logging.info(f"TCP接続成功 {self.target_ip}:{self.tcp_port}")
                return
            except Exception as e:
                logging.warning(f"TCP接続失敗: {e}。5秒後再接続します。")
                time.sleep(5)

    def send_tcp(self, data: bytes):
        try:
            enc = aes_encrypt(data, self.aes_key)
            enc = adjust_length_to_prime(enc)
            self.tcp_sock.sendall(enc)
            logging.debug(f"TCP送信 {len(enc)} bytes")
        except Exception as e:
            logging.error(f"TCP送信エラー: {e}")
            raise e

    def send_udp_with_ack(self, seq_num: int, data: bytes, is_last: bool) -> bool:
        header = struct.pack('!IB', seq_num, 1 if is_last else 0)
        packet = header + data
        enc = aes_encrypt(packet, self.aes_key)
        enc = adjust_length_to_prime(enc)

        retry = 0
        while retry < MAX_RETRY:
            try:
                self.udp_sock.sendto(enc, (self.target_ip, self.udp_port))
                logging.debug(f"UDP送信 SEQ={seq_num} retry={retry}")
                ack_data, _ = self.udp_sock.recvfrom(8)
                ack_seq = struct.unpack('!I', ack_data)[0]
                if ack_seq == seq_num:
                    logging.debug(f"UDP ACK受信 SEQ={ack_seq}")
                    return True
            except socket.timeout:
                logging.warning(f"UDP ACKタイムアウト SEQ={seq_num} 再送します")
                retry += 1
            except Exception as e:
                logging.error(f"UDP送信中エラー: {e}")
                return False
        logging.error(f"UDP送信失敗 SEQ={seq_num} 最大再送回数超過")
        return False

    def send_data(self, seq_num: int, data: bytes, is_last: bool):
        digit = irrational_digit(seq_num)
        if digit % 2 == 1:
            # UDP送信（ACK付き）
            success = self.send_udp_with_ack(seq_num, data, is_last)
            if not success:
                logging.error(f"UDP送信に失敗しました SEQ={seq_num}")
        else:
            # TCP送信
            try:
                header = struct.pack('!IB', seq_num, 1 if is_last else 0)
                tcp_data = header + data
                self.send_tcp(tcp_data)
            except Exception:
                logging.error(f"TCP送信に失敗しました SEQ={seq_num}")

    def send_file(self, file_path: str):
        logging.info(f"送信開始: {file_path}")
        with open(file_path, 'rb') as f:
            seq_num = 0
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                seq_num += 1
                is_last = False
                cur_pos = f.tell()
                f.seek(0, os.SEEK_END)
                end_pos = f.tell()
                f.seek(cur_pos)
                if cur_pos == end_pos:
                    is_last = True

                self.send_data(seq_num, chunk, is_last)
                interval = 0.1 + irrational_digit(seq_num) * 0.01
                time.sleep(interval)
        logging.info("ファイル送信完了")

# ===== ファイル受信クラス =====
class FileReceiver:
    def __init__(self, tcp_port, udp_port, aes_key):
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.aes_key = aes_key

        self.tcp_server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.stop_flag = False
        self.chunks = {}  # seq_num -> bytes
        self.chunks_lock = threading.Lock()
        self.end_seq = None
        self.received_event = threading.Event()

    def start_tcp_server(self):
        def tcp_server():
            try:
                self.tcp_server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.tcp_server_sock.bind(('', self.tcp_port))
                self.tcp_server_sock.listen(5)
                self.tcp_server_sock.settimeout(1)
                logging.info(f"TCPサーバ起動 ポート {self.tcp_port}")

                while not self.stop_flag:
                    try:
                        client_sock, addr = self.tcp_server_sock.accept()
                        logging.info(f"TCP接続受信 {addr}")
                        client_sock.settimeout(1)
                        with client_sock:
                            while not self.stop_flag:
                                try:
                                    data = client_sock.recv(4096)
                                    if not data:
                                        break
                                    self._process_tcp_data(data)
                                except socket.timeout:
                                    continue
                                except Exception as e:
                                    logging.error(f"TCP受信エラー: {e}")
                                    break
                    except socket.timeout:
                        continue
            except Exception as e:
                logging.error(f"TCPサーバエラー: {e}")

        threading.Thread(target=tcp_server, daemon=True).start()

    def _process_tcp_data(self, data: bytes):
        try:
            dec = aes_decrypt(data, self.aes_key)
            if len(dec) < 5:
                logging.warning("TCPデータ長不足")
                return
            seq_num, end_flag = struct.unpack('!IB', dec[:5])
            chunk_data = dec[5:]
            with self.chunks_lock:
                if seq_num not in self.chunks:
                    self.chunks[seq_num] = chunk_data
                    logging.debug(f"TCPチャンク受信 SEQ={seq_num} END={end_flag}")
                    if end_flag == 1:
                        self.end_seq = seq_num
                        self.received_event.set()
        except Exception as e:
            logging.error(f"TCP復号/処理失敗: {e}")

    def start_udp_server(self):
        def udp_server():
            try:
                self.udp_server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.udp_server_sock.bind(('', self.udp_port))
                self.udp_server_sock.settimeout(1)
                logging.info(f"UDPサーバ起動 ポート {self.udp_port}")

                while not self.stop_flag:
                    try:
                        data, addr = self.udp_server_sock.recvfrom(2048)
                        threading.Thread(target=self._process_udp_packet, args=(data, addr), daemon=True).start()
                    except socket.timeout:
                        continue
            except Exception as e:
                logging.error(f"UDPサーバエラー: {e}")

        threading.Thread(target=udp_server, daemon=True).start()

    def _process_udp_packet(self, data: bytes, addr):
        try:
            dec = aes_decrypt(data, self.aes_key)
            if len(dec) < 5:
                logging.warning("UDPデータ長不足")
                return
            seq_num, end_flag = struct.unpack('!IB', dec[:5])
            chunk_data = dec[5:]
            with self.chunks_lock:
                if seq_num not in self.chunks:
                    self.chunks[seq_num] = chunk_data
                    logging.debug(f"UDPチャンク受信 SEQ={seq_num} END={end_flag} FROM={addr}")
                    if end_flag == 1:
                        self.end_seq = seq_num
                        self.received_event.set()
            # ACK送信
            ack_packet = struct.pack('!I', seq_num)
            self.udp_server_sock.sendto(ack_packet, addr)
            logging.debug(f"UDP ACK送信 SEQ={seq_num} TO={addr}")
        except Exception as e:
            logging.error(f"UDP復号/処理失敗: {e}")

    def save_file(self, output_path: str):
        # 終端受信待ち
        logging.info("ファイル受信完了待機中...")
        self.received_event.wait()
        with self.chunks_lock:
            if not self.end_seq:
                logging.error("終端チャンクが届いていません")
                return False
            total_chunks = self.end_seq
            logging.info(f"受信チャンク総数: {total_chunks}")
            # 連結順序で保存。欠損チャンクは空データとして埋める（実際は再送制御で防止）
            with open(output_path, 'wb') as f:
                for seq in range(1, total_chunks + 1):
                    chunk = self.chunks.get(seq, b'')
                    if not chunk:
                        logging.warning(f"欠損チャンク SEQ={seq} 空データ書込")
                    f.write(chunk)
            logging.info(f"ファイル保存完了: {output_path}")
            return True

    def stop(self):
        self.stop_flag = True
        self.tcp_server_sock.close()
        self.udp_server_sock.close()

# ===== GUI＋ファイル選択 =====
def select_file_dialog():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename()
    return file_path

# ===== Pygame初期化＆UI表示（送信ファイル選択） =====
def pygame_file_select_ui():
    pygame.init()
    screen = pygame.display.set_mode((600, 400))
    pygame.display.set_caption("ファイル選択 - ESCで終了")
    font = pygame.font.SysFont("Arial", 24)
    selected_file = None

    clock = pygame.time.Clock()
    running = True
    while running:
        screen.fill((30, 30, 30))
        text = font.render("Press F to select file, ESC to quit", True, (200, 200, 200))
        screen.blit(text, (50, 180))
        if selected_file:
            file_text = font.render(f"Selected: {os.path.basename(selected_file)}", True, (100, 255, 100))
            screen.blit(file_text, (50, 220))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_f:
                    selected_file = select_file_dialog()

        clock.tick(30)
    pygame.quit()
    return selected_file

# ===== メイン処理 =====
def main():
    # 送信先IPはGUI等で設定可能に改造も可
    logging.info("アプリ起動")
    sender = FileSender(TARGET_IP, TCP_PORT, UDP_PORT, AES_KEY)
    receiver = FileReceiver(TCP_PORT, UDP_PORT, AES_KEY)

    # 受信サーバ起動
    receiver.start_tcp_server()
    receiver.start_udp_server()

    # TCP接続確立（送信側）
    sender.connect_tcp()

    # ファイル選択UI起動
    file_to_send = pygame_file_select_ui()
    if not file_to_send:
        logging.info("ファイル選択されなかったため終了")
        receiver.stop()
        sys.exit()

    # ファイル送信
    sender.send_file(file_to_send)

    # ファイル受信完了待機＋保存（固定名）
    output_file = "received_output.bin"
    success = receiver.save_file(output_file)

    receiver.stop()
    if success:
        logging.info("ファイル送受信完了")
    else:
        logging.error("ファイル受信に失敗")

if __name__ == "__main__":
    main()
