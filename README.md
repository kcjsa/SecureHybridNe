# SecureHybridNet（Linux専用）

SecureHybridNetは、Linux環境向けに設計された安全な通信方式を実装したプロジェクトです。  
AES-256暗号化とTCP/UDPハイブリッド送信を組み合わせ、高速かつ信頼性の高いファイル転送を実現します。

---

## 対応環境

- OS: Linux（Ubuntu、Debian、Fedoraなど主要ディストリビューションを想定）  
- Python: 3.8以上

---

## 主な機能・特徴

- AES-256による強力なデータ暗号化  
- TCPとUDPのハイブリッド通信方式で効率的なデータ送信  
- UDPパケットの再送制御で信頼性を確保  
- Python実装（GUIはPygame使用）  
- Linuxのネットワーク環境に最適化

---

## ライセンス

本ソフトウェアは **Mozilla Public License 2.0 (MPL 2.0)** の下で提供されています。  

詳細は [LICENSE](./LICENSE) ファイルをご確認ください。

---

## 特別利用許諾について

作者（kcjsa）との別途契約により、以下の条件での特別利用を認めます。

- 改変の公開義務の免除  
- 業務利用における最小限のライセンス付与

特別利用許諾については、[Discord](https://discord.gg/xSgcs4y2jw)までお問い合わせください。

---

## インストール・使い方

### 必要環境

- Linux OS（動作未検証の環境は動作保証対象外です）  
- Python 3.8以上
  
linux(ubuntu用)のsystem構築用ファイルは一緒に入れておきます。

----------------
English
----------------
SecureHybridNet (Linux Only)
SecureHybridNet is a project that implements a secure communication protocol designed for Linux environments.
By combining AES-256 encryption with hybrid TCP/UDP transmission, it achieves fast and reliable file transfer.

Supported Environment
OS: Linux (Designed for major distributions like Ubuntu, Debian, Fedora, etc.)

Python: Version 3.8 or higher

Key Features
Strong data encryption using AES-256

Efficient data transmission with a hybrid TCP and UDP communication model

Reliable delivery through retransmission control of UDP packets

Fully implemented in Python (GUI built with Pygame)

Optimized for Linux network environments

License
This software is provided under the Mozilla Public License 2.0 (MPL 2.0).

For details, please see the LICENSE file.

About Special Usage License
A separate agreement with the author (kcjsa) may allow special usage under the following conditions:

Exemption from the obligation to publish modifications

Minimal licensing granted for commercial or enterprise use

For inquiries about special usage licenses, please contact us via Discord.
discord https://discord.gg/xSgcs4y2jw

Installation & Usage
Requirements
Linux OS (Other environments are not officially supported)

Python 3.8 or later

A system setup script for Linux (Ubuntu) is included in this repository.

