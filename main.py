from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests, uvicorn, sqlite3, os, random, string
from datetime import datetime, timedelta

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
DB_FILE = "royal_keys.db" # Đổi tên DB cho hệ thống mới

def get_db(): return sqlite3.connect(DB_FILE, check_same_thread=False)

def khoi_tao_db():
    with get_db() as conn:
        c = conn.cursor()
        # Bảng Keys mới: Lưu Key, Ngày hết hạn, Trạng thái khóa
        c.execute('''CREATE TABLE IF NOT EXISTS keys (key_str TEXT PRIMARY KEY, expire_time DATETIME, is_banned INTEGER)''')
        # TẠO KEY MASTER CHO BOSS (KHÔNG BAO GIỜ HẾT HẠN)
        c.execute("INSERT OR IGNORE INTO keys (key_str, expire_time, is_banned) VALUES (?, ?, ?)", ('hungadmin1122334455', '2099-12-31 23:59:59', 0))
        conn.commit()

khoi_tao_db()

# ================= LÕI AI V4: MÔ PHỎNG MARKOV & PATTERN =================
def phan_tich_ai_v4(kq_list):
    tong_tai = kq_list.count("Tài"); tong_xiu = kq_list.count("Xỉu")
    if len(kq_list) < 10: return {"du_doan": "ANALYZING", "ti_le": 0, "tong_tai": tong_tai, "tong_xiu": tong_xiu}
    gan_nhat = kq_list[-10:]; kq_cuoi = kq_list[-1]
    chuoi_bet = 1
    for i in range(len(kq_list)-2, -1, -1):
        if kq_list[i] == kq_cuoi: chuoi_bet += 1
        else: break
    du_doan = ""; ty_le = 0.0

    if gan_nhat[-4:] == ["Tài", "Xỉu", "Tài", "Xỉu"] or gan_nhat[-4:] == ["Xỉu", "Tài", "Xỉu", "Tài"]:
        du_doan = "TÀI" if kq_cuoi == "Xỉu" else "XỈU"; ty_le = random.uniform(92.5, 98.9)
    elif gan_nhat[-4:] == ["Tài", "Tài", "Xỉu", "Xỉu"]:
        du_doan = "TÀI"; ty_le = random.uniform(88.5, 95.5)
    elif gan_nhat[-4:] == ["Xỉu", "Xỉu", "Tài", "Tài"]:
        du_doan = "XỈU"; ty_le = random.uniform(88.5, 95.5)
    elif chuoi_bet == 3:
        du_doan = "TÀI" if kq_cuoi == "Xỉu" else "XỈU"; ty_le = random.uniform(78.5, 85.5)
    elif chuoi_bet == 4:
        du_doan = kq_cuoi; ty_le = random.uniform(82.0, 89.5)
    elif chuoi_bet >= 5:
        du_doan = kq_cuoi; ty_le = random.uniform(95.0, 99.8)
    else:
        lech_cau = tong_tai - tong_xiu
        if lech_cau > 5: du_doan = "XỈU"; ty_le = random.uniform(75.0, 84.5)
        elif lech_cau < -5: du_doan = "TÀI"; ty_le = random.uniform(75.0, 84.5)
        else: du_doan = "TÀI" if kq_cuoi == "Xỉu" else "XỈU"; ty_le = random.uniform(65.5, 76.5)

    return {"du_doan": du_doan, "ti_le": round(ty_le, 1), "tong_tai": tong_tai, "tong_xiu": tong_xiu}

@app.get("/api/scan")
async def scan_game(tool: str, key: str):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT expire_time, is_banned FROM keys WHERE key_str = ?", (key,))
        row = c.fetchone()
        
    if not row: return {"status": "error", "msg": "Key không tồn tại!"}
    if row[1] == 1 and key != "hungadmin1122334455": return {"status": "error", "msg": "Key đã bị Admin khóa!"}
    if datetime.now() > datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S") and key != "hungadmin1122334455": 
        return {"status": "error", "msg": "Key đã hết hạn! Vui lòng mua Key mới."}

    url = "https://wtx.tele68.com/v1/tx/lite-sessions" if tool == "lc79" else "https://wtx.macminim6.online/v1/tx/lite-sessions"
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5).json()
        if not res.get("list"): return {"status": "error", "msg": "Chờ cầu mới..."}
        lst = res["list"][::-1]
        kq = ["Tài" if "TAI" in str(s.get("resultTruyenThong", "")).upper() else "Xỉu" for s in lst]
        data = phan_tich_ai_v4(kq); data["phien"] = str(int(lst[-1]["id"]) + 1)
        return {"status": "success", "data": data}
    except: return {"status": "error", "msg": "Đứt kết nối Server Game!"}

class KeyReq(BaseModel): key: str
@app.post("/api/verify_key")
async def verify_key(req: KeyReq):
    k = req.key.strip()
    if not k: return {"status": "error", "msg": "Vui lòng nhập Key!"}
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT expire_time, is_banned FROM keys WHERE key_str = ?", (k,))
        row = c.fetchone()
        if not row: return {"status": "error", "msg": "Key không hợp lệ hoặc sai!"}
        if row[1] == 1 and k != "hungadmin1122334455": return {"status": "error", "msg": "Key này đã bị khóa!"}
        
        is_expired = datetime.now() > datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        if is_expired and k != "hungadmin1122334455": return {"status": "error", "msg": "Key đã hết hạn!"}
        
        role = "admin" if k == "hungadmin1122334455" else "user"
        expire_str = "VĨNH VIỄN" if role == "admin" else row[0]
        return {"status": "success", "role": role, "expire": expire_str}

# ---- ADMIN API ----
@app.get("/api/admin/list_keys")
async def admin_list_keys(admin_key: str):
    if admin_key != "hungadmin1122334455": return {"status": "error"}
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT key_str, expire_time, is_banned FROM keys WHERE key_str != 'hungadmin1122334455' ORDER BY expire_time DESC")
        keys = c.fetchall()
    return {"status": "success", "keys": keys}

class CreateKeyReq(BaseModel): admin_key: str; duration: str
@app.post("/api/admin/create_key")
async def create_key(req: CreateKeyReq):
    if req.admin_key != "hungadmin1122334455": return {"status": "error"}
    
    # Random mã VIP-xxxxxx
    new_key = "VIP-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    now = datetime.now()
    if req.duration == "1H": exp = now + timedelta(hours=1)
    elif req.duration == "1D": exp = now + timedelta(days=1)
    elif req.duration == "3D": exp = now + timedelta(days=3)
    elif req.duration == "30D": exp = now + timedelta(days=30)
    else: return {"status": "error", "msg": "Gói thời gian sai!"}
    
    exp_str = exp.strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO keys (key_str, expire_time, is_banned) VALUES (?, ?, 0)", (new_key, exp_str))
        conn.commit()
    return {"status": "success", "new_key": new_key, "expire": exp_str}

class BanKeyReq(BaseModel): admin_key: str; target_key: str; action: str
@app.post("/api/admin/action_key")
async def action_key(req: BanKeyReq):
    if req.admin_key != "hungadmin1122334455": return {"status": "error"}
    with get_db() as conn:
        c = conn.cursor()
        if req.action == "ban": c.execute("UPDATE keys SET is_banned = 1 WHERE key_str = ?", (req.target_key,))
        elif req.action == "unban": c.execute("UPDATE keys SET is_banned = 0 WHERE key_str = ?", (req.target_key,))
        elif req.action == "delete": c.execute("DELETE FROM keys WHERE key_str = ?", (req.target_key,))
        conn.commit()
    return {"status": "success"}

@app.get("/")
async def home(): return FileResponse("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
        
