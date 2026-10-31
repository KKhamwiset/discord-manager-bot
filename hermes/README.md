# 🌸 Hermes Agent บน Railway + ควบคุม Windows PC ผ่าน Tailscale SSH

โฟลเดอร์นี้ประกอบด้วยระบบติดตั้งและ Deploy **Hermes Agent ([NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent))** ขึ้นบน **Railway** เพื่อทำหน้าที่เป็น AI Agent ส่วนตัวที่สามารถรับคำสั่งผ่าน **Discord** หรือ **Telegram** และสั่งการควบคุมเครื่อง Windows PC ของคุณจากระยะไกลผ่าน **SSH** โดยวิ่งบนเครือข่ายส่วนตัวของ **Tailscale (Userspace Networking)** อย่างปลอดภัย โดย**ไม่ต้องเปิดพอร์ต 22 (SSH) สู่ Public Internet**

---

## 🏛️ สถาปัตยกรรมระบบ (Architecture)

```
[ผู้ใช้]
  │ (Discord / Telegram DM หรือ Server)
  ▼
[Hermes Gateway (Railway Container)]
  │ (รัน hermes gateway + tailscaled userspace networking)
  │ ProxyCommand: tailscale --socket=/tmp/tailscaled.sock nc %h %p
  ▼
[Tailscale Private Mesh Network] (เข้ารหัส WireGuard, ไม่ผ่าน Public IP)
  │ อนุญาตเฉพาะ tag:hermes -> Windows PC:22
  ▼
[Windows PC (OpenSSH Server)]
  │ DefaultShell: Git Bash (C:\Program Files\Git\bin\bash.exe)
  │ Auth: Ed25519 Key-only (ปิด Password Authentication)
  ▼
[รันคำสั่งบนเครื่อง Windows สำเร็จ]
```

---

## 💻 1. การตั้งค่า Windows PC (Target Machine)

ทำขั้นตอนต่อไปนี้บน Windows PC ที่ต้องการให้ Hermes ควบคุม ผ่าน **PowerShell (Run as Administrator)**:

### 1.1 ติดตั้งและเปิดใช้งาน OpenSSH Server
```powershell
# ตรวจสอบและติดตั้ง OpenSSH Server
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0

# สั่งเริ่มการทำงาน sshd และตั้งให้เปิดอัตโนมัติตอนเปิดเครื่อง
Start-Service sshd
Set-Service -Name sshd -StartupType 'Automatic'

# ตรวจสอบสถานะการทำงาน
Get-Service sshd
```

### 1.2 ตั้ง DefaultShell ให้เป็น Git Bash
เพื่อให้คำสั่ง Unix/Linux ทั่วไป (เช่น `ls`, `grep`, `mkdir`, `cat`) สามารถรันได้อย่างราบรื่น:
```powershell
New-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell -Value "C:\Program Files\Git\bin\bash.exe" -PropertyType String -Force
```
*(หากยังไม่มี Git for Windows สามารถติดตั้งผ่าน `winget install Git.Git`)*

### 1.3 แนะนำ: สร้าง Dedicated Non-Admin Windows User สำหรับ Hermes
เพื่อความปลอดภัยตามหลัก Principle of Least Privilege ไม่ควรให้ Hermes ใช้สิทธิ์ Administrator ของเครื่องโดยตรง:

```powershell
# 1. สร้าง User ใหม่ชื่อ 'hermes' พร้อมรหัสผ่าน (เปลี่ยน YOUR_PASSWORD)
net user hermes "YOUR_PASSWORD" /add

# 2. สร้างโฟลเดอร์ .ssh สำหรับ hermes user
$sshDir = "C:\Users\hermes\.ssh"
if (!(Test-Path $sshDir)) { New-Item -ItemType Directory -Path $sshDir -Force }

# 3. นำ Public Key (id_ed25519.pub) มาวางใน authorized_keys
# (นำเนื้อหา public key ที่คู่กับ SSH_PRIVATE_KEY มาใส่)
Set-Content -Path "$sshDir\authorized_keys" -Value "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5... your_comment"

# 4. ตั้งค่า Permissions ของ authorized_keys ให้เข้มงวด (เฉพาะ hermes และ SYSTEM เท่านั้นที่มีสิทธิ์)
icacls "$sshDir" /inheritance:r /grant "hermes:(OI)(CI)F" /grant "SYSTEM:(OI)(CI)F"
icacls "$sshDir\authorized_keys" /inheritance:r /grant "hermes:R" /grant "SYSTEM:F"
```

### 1.4 ปิด Password Authentication (บังคับใช้ Key-Only)
เปิดไฟล์ `C:\ProgramData\ssh\sshd_config` (เช่น `notepad C:\ProgramData\ssh\sshd_config`):
1. ตรวจสอบหรือแก้บรรทัดต่อไปนี้:
   ```sshd_config
   PubkeyAuthentication yes
   PasswordAuthentication no
   ```
2. **⚠️ ข้อควรระวังเรื่อง `administrators_authorized_keys`**:
   หากคุณใช้ Windows User ที่อยู่ในกลุ่ม **Administrators**:
   OpenSSH บน Windows จะ**เพิกเฉย**ต่อไฟล์ `~/.ssh/authorized_keys` ของผู้ใช้นั้น และจะไปอ่านที่:
   `C:\ProgramData\ssh\administrators_authorized_keys` แทน!
   *วิธีแก้ (หากจำเป็นต้องใช้ Admin User):*
   - ให้เปิด `C:\ProgramData\ssh\sshd_config` แล้วใส่ `#` หน้า 2 บรรทัดสุดท้าย:
     ```sshd_config
     # Match Group administrators
     #       AuthorizedKeysFile __PROGRAMDATA__/ssh/administrators_authorized_keys
     ```
   - หรือใช้วิธีที่ **แนะนำที่สุด** คือสร้าง non-admin user ตามข้อ 1.3 ซึ่งจะอ่าน `C:\Users\hermes\.ssh\authorized_keys` ตามปกติ

3. บันทึกไฟล์แล้ว Restart sshd:
   ```powershell
   Restart-Service sshd
   ```

---

## 🌐 2. การตั้งค่า Tailscale

### 2.1 สร้าง Tailscale Auth Key
1. เข้าไปที่ [Tailscale Admin Console](https://login.tailscale.com/admin/settings/keys)
2. คลิก **Generate auth key...**
3. ติ๊กเปิด **Reusable** (ไม่จำเป็นหากใช้ Railway Volume แต่เปิดไว้ได้)
4. ติ๊กเปิด **Ephemeral** (เพื่อให้โหนดหลุดอัตโนมัติหาก container หยุดทำงานเป็นเวลานาน)
5. ในช่อง **Tags** ให้ใส่: `tag:hermes`
6. บันทึกคีย์ `tskey-auth-...` ไว้สำหรับตั้งเป็น `TS_AUTHKEY` บน Railway

### 2.2 ตัวอย่าง Tailscale ACL Policy
ไปที่เมนู **Access Controls** ใน Tailscale Admin Console เพื่อจำกัดสิทธิ์ให้ container `tag:hermes` เข้าถึงได้เฉพาะพอร์ต 22 ของ PC เท่านั้น:

```json
{
  "tagOwners": {
    "tag:hermes": ["autogroup:admin"]
  },
  "acls": [
    {
      "action": "accept",
      "src": ["tag:hermes"],
      "dst": ["100.x.y.z:22"]
    }
  ]
}
```
*(แทนที่ `100.x.y.z` ด้วย Tailscale IP ของเครื่อง Windows PC ของคุณ หรือใช้ชื่ออุปกรณ์)*

---

## 🚂 3. การ Deploy บน Railway

### 3.1 สร้าง Service บน Railway
1. ไปที่โปรเจกต์ของคุณบน Railway Dashboard
2. สร้าง Service ใหม่จาก GitHub Repo นี้
3. ในแท็บ **Settings**:
   - **Root Directory**: ให้ตั้งเป็น `hermes` (หรือเว้นไว้ถ้าเลือก service subpath ได้ถูกต้อง)
   - Railway จะตรวจพบ `railway.json` และ `Dockerfile` อัตโนมัติ

### 3.2 เชื่อมต่อ Persistent Volume (จำเป็นมาก ⚠️)
1. ในหน้า Service -> แท็บ **Volumes**
2. คลิก **Add Volume**
3. ตั้งค่า **Mount Path** เป็น: `/data`
4. ปริมาณเนื้อที่: 5 GB ก็เพียงพอ (ใช้เก็บ state ของ Tailscale, ข้อมูล session, memory, skills ของ Hermes และ SSH known_hosts)

### 3.3 ตั้งค่า Environment Variables
ในแท็บ **Variables** ให้เพิ่มค่าตัวแปรทั้งหมดตามไฟล์ `hermes/.env.example`:

| ตัวแปร | ตัวอย่างค่า | คำอธิบาย |
|---|---|---|
| `TS_AUTHKEY` | `tskey-auth-kXXXXXX-...` | Auth key จาก Tailscale (มี `tag:hermes`) |
| `TS_HOSTNAME` | `hermes-railway` | ชื่อโหนดที่จะแสดงใน Tailscale network |
| `PC_TAILSCALE_HOST` | `100.80.x.x` | Tailscale IP หรือ MagicDNS ของ Windows PC |
| `PC_USER` | `hermes` | ชื่อ Windows user ที่ใช้ SSH เข้าไป |
| `PC_SSH_PORT` | `22` | พอร์ต SSH (ค่าเริ่มต้น 22) |
| `SSH_PRIVATE_KEY` | `-----BEGIN OPENSSH PRIVATE KEY-----...` | Private Key ของ Ed25519 (วางทั้งบล็อกได้เลย) |
| `OPENROUTER_API_KEY` | `sk-or-v1-...` | API Key สำหรับ LLM (หรือ `NOUS_API_KEY`, `OPENAI_API_KEY`) |
| `DISCORD_BOT_TOKEN` | `MTE...` | Bot Token ของ Discord (หรือ `TELEGRAM_BOT_TOKEN`) |
| `DISCORD_ALLOWED_USERS`| `123456789012345678` | Discord User ID ของคุณ (ห้ามเว้นว่าง) |
| `TERMINAL_ENV` | `local` | ค่าเริ่มต้นที่แนะนำ (ดูหัวข้อ Terminal Backend ด้านล่าง) |

---

## ⚙️ 4. Hermes Terminal Backend: การตั้งค่าและการเลือกใช้งาน

### 4.1 ดีไซน์ที่แนะนำ (Preferred Design): `TERMINAL_ENV=local` (Default)
โดยค่าเริ่มต้น `TERMINAL_ENV` จะทำงานแบบ `local` (ภายใน Linux container ของ Railway)
- **ทำไมถึงแนะนำแบบนี้:**
  1. Hermes สามารถใช้เครื่องมือ internal ของตัวเองใน Linux container ได้อย่างสมบูรณ์ (เช่น ไฟล์ระบบ, สคริปต์, เครื่องมือเสริม)
  2. เมื่อผู้ใช้สั่งให้ควบคุมหรือทำงานบน PC, Hermes จะรันผ่านคำสั่ง:
     ```bash
     ssh mypc "<คำสั่งที่ต้องการรัน>"
     ```
  3. Container ได้ถูกคอนฟิก `~/.ssh/config` สำหรับ Host `mypc` ให้ใช้ `ProxyCommand tailscale --socket=/tmp/tailscaled.sock nc %h %p` อัตโนมัติ ทำให้การรัน `ssh mypc` เชื่อมต่อเข้า Windows PC ได้ทันที
  4. ป้องกันปัญหาความไม่เข้ากันของ Windows Pathing หรือ File Sync ของ Hermes

### 4.2 ทางเลือกเพิ่มเติม (Alternative): Full SSH Backend (`TERMINAL_ENV=ssh`)
หากคุณต้องการให้**ทุกคำสั่ง Terminal** ของ Hermes ส่งไปรันบน Windows PC โดยตรง ให้ตั้งค่าตัวแปรดังนี้:
- `TERMINAL_ENV=ssh`
- `TERMINAL_SSH_HOST=mypc` (หรือใช้ `$PC_TAILSCALE_HOST`)
- `TERMINAL_SSH_USER=hermes`
- `TERMINAL_SSH_PORT=22`
- `TERMINAL_SSH_KEY=/root/.ssh/id_ed25519`
- `TERMINAL_SSH_PERSISTENT=true`

*(หมายเหตุ: คีย์คอนฟิกเหล่านี้ได้รับการตรวจสอบตรงตามซอร์สโค้ด `tools/terminal_tool_backends.py` และ `tools/environments/ssh.py` ของ NousResearch/hermes-agent เรียบร้อยแล้ว)*

---

## 🧪 5. วิธีทดสอบการเชื่อมต่อ (Verification)

เมื่อ Deploy บน Railway สำเร็จ:
1. เปิด **Railway Shell** (ผ่าน CLI `railway shell` หรือผ่าน Web Console ของ Railway)
2. ทดสอบสั่ง SSH ไปยัง Windows PC ผ่าน Host alias `mypc`:
   ```bash
   ssh mypc "echo ok && uname -a"
   ```
3. หากผลลัพธ์แสดง `ok` พร้อมระบบของ Git Bash (MINGW64...) แสดงว่าการเชื่อมต่อเสร็จสมบูรณ์ 100%!
4. ทดสอบพิมพ์แชทหาบอทใน Discord หรือ Telegram เช่น:
   > *"ลองเช็ค disk space บน PC ผ่าน ssh mypc ให้หน่อย"*

---

## 🛡️ 6. Security Checklist (รายการตรวจสอบความปลอดภัย)

- [x] **Allowlist เฉพาะ User ID ของตนเอง**: ใส่ User ID ของคุณใน `DISCORD_ALLOWED_USERS` หรือ `TELEGRAM_ALLOWED_USERS` เสมอ เพื่อป้องกันไม่ให้คนอื่นใน Discord/Telegram สั่งบอทได้
- [x] **ปิด YOLO Mode (เปิด Command Approval ไว้)**: Hermes จะถามการยืนยันก่อนรันคำสั่งอันตราย (Dangerous Commands) เสมอ
- [x] **จำกัดสิทธิ์ผู้ใช้บน Windows**: ใช้ dedicated non-admin user (`hermes`) สำหรับรันคำสั่ง
- [x] **Tailscale ACL แคบที่สุด**: อนุญาตเฉพาะ `tag:hermes` เข้า `dst: Windows_PC:22` เท่านั้น ไม่เปิดสิทธิ์เข้าเครื่องอื่นๆ ใน Tailnet
- [x] **พอร์ต 22 ไม่เปิดสู่ Public Internet**: พอร์ต 22 ตอบสนองเฉพาะภายในวงเครือข่ายเสมือนของ Tailscale
- [x] **กรณี PC ปิดเครื่องอยู่ (Offline)**: การเชื่อมต่อจะ Timeout อย่างปลอดภัย Hermes จะแจ้งเตือนในแชทว่าไม่สามารถติดต่อ PC ได้ และ Container จะไม่ Crash
