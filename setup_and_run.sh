#!/bin/bash

# ========== 設定 ==========
PROJECT_NAME="secure_file_transfer"
MAIN_FILE="main.py"

# ========== アップデート ==========
echo "[*] パッケージ情報更新..."
sudo apt update && sudo apt upgrade -y

# ========== 必要パッケージのインストール ==========
echo "[*] 必要パッケージをインストール中..."
sudo apt install -y \
  python3-pip \
  python3-tk \
  python3-pygame \
  libffi-dev \
  build-essential \
  python3-dev

# ========== 仮想環境の作成 ==========
echo "[*] 仮想環境を作成中..."
python3 -m venv venv

# ========== 仮想環境をアクティブ化 ==========
source venv/bin/activate

# ========== pipアップグレード ==========
pip install --upgrade pip

# ========== cryptographyインストール ==========
pip install cryptography

# ========== ファイル配置 ==========
echo "[*] メインスクリプト配置..."
mkdir -p $PROJECT_NAME
cp "$MAIN_FILE" "$PROJECT_NAME/"

# ========== 実行 ==========
echo "[*] 実行中..."
cd $PROJECT_NAME
python3 "$MAIN_FILE"
