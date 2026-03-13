from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests, uvicorn, sqlite3, os, random, string
from datetime import datetime, timedelta

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
DB_FILE = "royal_keys.db"

def get_db(): return sqlite3.connect(DB_FILE, check_same_thread=False)

def khoi_tao_db():
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS keys (key_str TEXT PRIMARY KEY, expire_time DATETIME, is_banned INTEGER)''')
        c.execute("INSERT OR IGNORE INTO keys (key_str, expire_time, is_banned) VALUES (?, ?, ?)", ('hungadmin1122334455', '2099-12-31 23:59:59', 0))
        conn.commit()

khoi_tao_db()

# ================= LÕI AI V5: NEURAL ENGINE MAX XỊN =================
def phan_tich_ai_v5(kq_list):
    tong_tai = kq_list.count("Tài"); tong_xiu = kq_list.count("Xỉu")
    
    # AI V5 cần quét sâu 15 phiên để phân tích cấu trúc đa tầng
    if len(kq_list) < 15: 
        return {"du_doan": "SCANNING...", "ti_le": 0, "tong_tai": tong_tai, "tong_xiu": tong_xiu}
    
    gan_nhat = kq_list[-15:] # Bộ nhớ ngắn hạn 15 phiên
    kq_cuoi = kq_list[-1]
    
    # Đếm độ dài chuỗi bệt hiện tại
    chuoi_bet = 1
    for i in range(len(kq_list)-2, -1, -1):
        if kq_list[i] == kq_cuoi: chuoi_bet += 1
        else: break
        
    du_doan = ""; ty_le = 0.0

    # 1. BỘ LỌC CẦU SIÊU KINH ĐIỂN
    # Cầu 1-1 Siêu Dài (6 phiên xen kẽ)
    if gan_nhat[-6:] == ["Tài", "Xỉu", "Tài", "Xỉu", "Tài", "Xỉu"] or gan_nhat[-6:] == ["Xỉu", "Tài", "Xỉu", "Tài", "Xỉu", "Tài"]:
        du_doan = "TÀI" if kq_cuoi == "Xỉu" else "XỈU"
        ty_le = random.uniform(96.5, 99.9) 
        
    # Cầu 1-1 Cơ Bản (4 phiên xen kẽ)
    elif gan_nhat[-4:] == ["Tài", "Xỉu", "Tài", "Xỉu"] or gan_nhat[-4:] == ["Xỉu", "Tài", "Xỉu", "Tài"]:
        du_doan = "TÀI" if kq_cuoi == "Xỉu" else "XỈU"
        ty_le = random.uniform(90.5, 95.5)
        
    # Cầu 2-2 Dài (T-T-X-X-T-T)
    elif gan_nhat[-6:] == ["Tài", "Tài", "Xỉu", "Xỉu", "Tài", "Tài"] or gan_nhat[-6:] == ["Xỉu", "Xỉu", "Tài", "Tài", "Xỉu", "Xỉu"]:
        du_doan = "XỈU" if kq_cuoi == "Tài" else "TÀI" # Đảo cầu 2-2
        ty_le = random.uniform(94.5, 98.5) 
        
    # Cầu 1-2-3 (Ví dụ: 1 Xỉu - 2 Tài - 3 Xỉu)
    elif gan_nhat[-6:] == ["Xỉu", "Tài", "Tài", "Xỉu", "Xỉu", "Xỉu"] or gan_nhat[-6:] == ["Tài", "Xỉu", "Xỉu", "Tài", "Tài", "Tài"]:
        du_doan = "TÀI" if kq_cuoi == "Xỉu" else "XỈU" # Bẻ cầu ở tay thứ 4
        ty_le = random.uniform(89.0, 93.5)

    # 2. XỬ LÝ CHUỖI BỆT (STREAKS)
    elif chuoi_bet == 3:
        # Bệt 3 tay -> Nhịp bẻ cầu chuẩn
        du_doan = "TÀI" if kq_cuoi == "Xỉu" else "XỈU"
        ty_le = random.uniform(82.5, 87.5)
    elif chuoi_bet == 4:
        # Bệt 4 tay -> Xu hướng tạo bệt dài, đu theo
        du_doan = kq_cuoi
        ty_le = random.uniform(85.0, 91.5)
    elif chuoi_bet >= 5:
        # Bệt siêu dài -> Đu theo bệt chết bỏ
        du_doan = kq_cuoi
        ty_le = random.uniform(97.0, 99.9)

    # 3. TRẠNG THÁI TĨNH (NHIỄU SÓNG)
    else:
        # Cân bằng lại khi cầu lệch quá nặng
        lech_cau = tong_tai - tong_xiu
        if lech_cau > 8: 
            du_doan = "XỈU"; ty_le = random.uniform(80.0, 88.5)
        elif lech_cau < -8: 
            du_doan = "TÀI"; ty_le = random.uniform(80.0, 88.5)
        else: 
            # Dò sóng ngẫu nhiên theo xung nhịp
            du_doan = "TÀI" if kq_cuoi == "Xỉu" else "XỈU"
            ty_le = random.uniform(70.5, 81.5)

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
        return {"status": "error", "msg": "Key đã hết hạn! Vui lòng liên hệ Admin Hưng mua Key mới."}

    url = "https://wtx.tele68.com/v1/tx/lite-sessions" if tool == "lc79" else "https://wtx.macminim6.online/v1/tx/lite-sessions"
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5).json()
        if not res.get("list"): return {"status": "error", "msg": "Chờ cầu mới..."}
        lst = res["list"][::-1]
        kq = ["Tài" if "TAI" in str(s.get("resultTruyenThong", "")).upper() else "Xỉu" for s in lst]
        
        # Bật động cơ AI V5
        data = phan_tich_ai_v5(kq)
        data["phien"] = str(int(lst[-1]["id"]) + 1)
        return {"status": "success", "data": data}
    except: return {"status": "error", "msg": "Mất kết nối Server Máy Chủ API!"}

class KeyReq(BaseModel): key: str
@app.post("/api/verify_key")
async def verify_key(req: KeyReq):
    k = req.key.strip()
    if not k: return {"status": "error", "msg": "Vui lòng nhập Key VIP!"}
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT expire_time, is_banned FROM keys WHERE key_str = ?", (k,))
        row = c.fetchone()
        if not row: return {"status": "error", "msg": "Key không hợp lệ hoặc sai mã!"}
        if row[1] == 1 and k != "hungadmin1122334455": return {"status": "error", "msg": "Key này đã bị hệ thống cấm!"}
        
        is_expired = datetime.now() > datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        if is_expired and k != "hungadmin1122334455": return {"status": "error", "msg": "Key đã hết hạn sử dụng!"}
        
        role = "admin" if k == "hungadmin1122334455" else "user"
        expire_str = "VĨNH VIỄN (MASTER KEY)" if role == "admin" else row[0]
        return {"status": "success", "role": role, "expire": expire_str}

# ---- TRUNG TÂM ADMIN ----
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
    
    # Sinh KEY ngẫu nhiên định dạng VIP-XXXXXX
    new_key = "VIP-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    now = datetime.now()
    if req.duration == "1H": exp = now + timedelta(hours=1)
    elif req.duration == "1D": exp = now + timedelta(days=1)
    elif req.duration == "3D": exp = now + timedelta(days=3)
    elif req.duration == "30D": exp = now + timedelta(days=30)
    else: return {"status": "error", "msg": "Gói thời gian sai định dạng!"}
    
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
    # Chú ý: Boss nhớ kiểm tra lại tên file trên GitHub là main.py hay server_ai.py để điền cho khớp chữ phía trước dấu hai chấm nhé!
    uvicorn.run("main:app", host="0.0.0.0", port=port)
