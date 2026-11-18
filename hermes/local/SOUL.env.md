## 🖥️ Workspace — Local Mode (รันบนเครื่องของ Conde)

### 📌 Architecture Summary
- **ตัวเธอ (Mochi)** รันอยู่บน **เครื่อง Windows PC ของ Conde โดยตรง** (local Hermes) — ไม่ใช่ Railway container
- รันคำสั่งด้วย terminal tool บนเครื่องนี้ได้เลย ❌ **ห้ามใช้ `ssh mypc`** เพราะเธออยู่บนเครื่องนั้นแล้ว และ **ไม่ต้องขอ OTP**
- Terminal เป็น Git Bash ใช้พาธแบบ `/f/...` ได้ ส่วน PowerShell/Windows ใช้พาธแบบ `F:\...`

### 📂 Project & File Locations
- **Discord Bot Repo (`discord-manager-bot`)**: `F:\discord-manager-bot` (Git Bash: `/f/discord-manager-bot`)
- **CyberCase Framework Repo**: `F:\Cybercase Framework` (Git Bash: `/f/Cybercase Framework`)
- โฟลเดอร์งาน เอกสาร และโปรเจกต์อื่นๆ ของ Conde อยู่บน Drive `C:` และ `F:`
