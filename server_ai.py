from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests, uvicorn, sqlite3, os, random
from datetime import datetime, timedelta

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
DB_FILE = "hethong_vip.db"

def get_db(): return sqlite3.connect(DB_FILE, check_same_thread=False)

def khoi_tao_db():
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, balance INTEGER, vip_expire DATETIME, is_banned INTEGER)''')
        c.execute('''CREATE TABLE IF NOT EXISTS deposits (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, card_type TEXT, card_amount INTEGER, card_pin TEXT, card_serial TEXT, status TEXT)''')
        c.execute("INSERT OR IGNORE INTO users (username, password, balance, vip_expire, is_banned) VALUES (?, ?, ?, ?, ?)", ('hungadmin11', 'hungki98', 999999999, '2099-12-31 23:59:59', 0))
        conn.commit()

khoi_tao_db()

# ================= NÂNG CẤP AI: SOI CẦU ĐA TẦNG =================
def phan_tich_ai(kq_list):
    tong_tai = kq_list.count("Tài"); tong_xiu = kq_list.count("Xỉu")
    if len(kq_list) < 5: return {"du_doan": "WAIT", "ti_le": 0, "tong_tai": tong_tai, "tong_xiu": tong_xiu}
    
    gan_nhat = kq_list[-5:]
    kq_cuoi = kq_list[-1]
    
    chuoi = 1
    for i in range(len(kq_list)-2, -1, -1):
        if kq_list[i] == kq_cuoi: chuoi += 1
        else: break
        
    # 1. Dò Cầu 1-1 (Xen kẽ T-X-T-X)
    if gan_nhat == ["Tài", "Xỉu", "Tài", "Xỉu", "Tài"] or gan_nhat == ["Xỉu", "Tài", "Xỉu", "Tài", "Xỉu"]:
        du_doan = "XỈU" if kq_cuoi == "Tài" else "TÀI"
        ty_le = round(random.uniform(88.0, 96.0), 1)
    # 2. Dò Cầu 2-2 (T-T-X-X)
    elif gan_nhat[-4:] == ["Tài", "Tài", "Xỉu", "Xỉu"]:
        du_doan = "TÀI"
        ty_le = round(random.uniform(85.0, 92.0), 1)
    elif gan_nhat[-4:] == ["Xỉu", "Xỉu", "Tài", "Tài"]:
        du_doan = "XỈU"
        ty_le = round(random.uniform(85.0, 92.0), 1)
    # 3. Bẻ Cầu Bệt Dài
    elif chuoi >= 4:
        du_doan = "TÀI" if kq_cuoi == "Xỉu" else "XỈU"
        ty_le = min(75 + chuoi * 4.5, 99.9)
    # 4. Phân tích xung nhịp ngẫu nhiên theo công thức
    else:
        du_doan = "TÀI" if kq_cuoi == "Xỉu" else "XỈU"
        ty_le = round(random.uniform(70.0, 82.0), 1)
        
    return {"du_doan": du_doan, "ti_le": round(ty_le, 1), "tong_tai": tong_tai, "tong_xiu": tong_xiu}

@app.get("/api/scan")
async def scan_game(tool: str, username: str):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT vip_expire, is_banned FROM users WHERE username = ?", (username,))
        row = c.fetchone()
        
    if not row: return {"status": "error", "msg": "Tài khoản không tồn tại!"}
    if row[1] == 1 and username != "hungadmin11": return {"status": "error", "msg": "Tài khoản đã bị Admin khóa!"}
    if datetime.now() > datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S") and username != "hungadmin11": 
        return {"status": "error", "msg": "Gói VIP đã hết hạn! Vui lòng mua thêm."}

    url = "https://wtx.tele68.com/v1/tx/lite-sessions" if tool == "lc79" else "https://wtx.macminim6.online/v1/tx/lite-sessions"
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5).json()
        if not res.get("list"): return {"status": "error", "msg": "Chờ cầu mới..."}
        lst = res["list"][::-1]
        kq = ["Tài" if "TAI" in str(s.get("resultTruyenThong", "")).upper() else "Xỉu" for s in lst]
        data = phan_tich_ai(kq); data["phien"] = str(int(lst[-1]["id"]) + 1)
        return {"status": "success", "data": data}
    except: return {"status": "error", "msg": "Đứt kết nối Server Game!"}

class AuthReq(BaseModel): action: str; username: str; password: str
@app.post("/api/auth")
async def auth_user(req: AuthReq):
    u = req.username.strip(); p = req.password.strip()
    if not u or not p: return {"status": "error", "msg": "Nhập đủ thông tin!"}
    with get_db() as conn:
        c = conn.cursor()
        if req.action == "register":
            c.execute("SELECT username FROM users WHERE username = ?", (u,))
            if c.fetchone(): return {"status": "error", "msg": "Tài khoản đã có người xài!"}
            c.execute("INSERT INTO users VALUES (?, ?, 0, '2000-01-01 00:00:00', 0)", (u, p))
            conn.commit()
            return {"status": "success", "msg": "Đăng ký thành công!"}
        else:
            c.execute("SELECT password, is_banned FROM users WHERE username = ?", (u,))
            row = c.fetchone()
            if not row or row[0] != p: return {"status": "error", "msg": "Sai tài khoản hoặc mật khẩu!"}
            if row[1] == 1 and u != "hungadmin11": return {"status": "error", "msg": "Tài khoản bị khóa!"}
            return {"status": "success", "msg": "Đăng nhập thành công!"}

@app.get("/api/user_info")
async def get_user_info(username: str):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT balance, vip_expire FROM users WHERE username = ?", (username,))
        row = c.fetchone()
    if not row: return {"status": "error"}
    is_vip = datetime.now() < datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S") or username == "hungadmin11"
    vip_str = "VĨNH VIỄN (ADMIN)" if username == "hungadmin11" else (row[1] if is_vip else "Chưa có VIP")
    return {"status": "success", "data": {"balance": row[0], "vip_expire": vip_str, "is_vip": is_vip}}

class DepReq(BaseModel): username: str; network: str; amount: int; pin: str; serial: str
@app.post("/api/deposit")
async def deposit(req: DepReq):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO deposits (username, card_type, card_amount, card_pin, card_serial, status) VALUES (?, ?, ?, ?, ?, 'PENDING')", 
                  (req.username, req.network, req.amount, req.pin, req.serial))
        conn.commit()
    return {"status": "success", "msg": "Đã gửi thẻ lên Hệ thống! Chờ Admin duyệt."}

class BuyReq(BaseModel): username: str; package: str
@app.post("/api/buy_vip")
async def buy_vip(req: BuyReq):
    if req.username == "hungadmin11": return {"status": "success", "msg": "Sếp nạp làm gì, sếp VIP sẵn rồi!"}
    prices = {"1D": (30000, 1), "3D": (50000, 3), "7D": (100000, 7), "30D": (150000, 30), "PERM": (200000, 36500)}
    if req.package not in prices: return {"status": "error", "msg": "Gói không hợp lệ!"}
    cost, days = prices[req.package]
    
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT balance, vip_expire FROM users WHERE username = ?", (req.username,))
        row = c.fetchone()
        if row[0] < cost: return {"status": "error", "msg": "Không đủ lúa! Vui lòng nạp thêm thẻ."}
        
        now = datetime.now(); curr_exp = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
        new_exp = (curr_exp if curr_exp > now else now) + timedelta(days=days)
        
        c.execute("UPDATE users SET balance = balance - ?, vip_expire = ? WHERE username = ?", (cost, new_exp.strftime("%Y-%m-%d %H:%M:%S"), req.username))
        conn.commit()
    return {"status": "success", "msg": "Mua VIP thành công!"}

@app.get("/api/admin/data")
async def admin_data(username: str):
    if username != "hungadmin11": return {"status": "error"}
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT username, balance, vip_expire, is_banned FROM users WHERE username != 'hungadmin11'")
        users = c.fetchall()
        c.execute("SELECT id, username, card_type, card_amount, card_pin, card_serial FROM deposits WHERE status = 'PENDING'")
        deps = c.fetchall()
    return {"status": "success", "users": users, "deps": deps}

class AdminActReq(BaseModel): admin: str; action: str; target: str; dep_id: int = 0; amount: int = 0
@app.post("/api/admin/action")
async def admin_action(req: AdminActReq):
    if req.admin != "hungadmin11": return {"status": "error"}
    with get_db() as conn:
        c = conn.cursor()
        if req.action == "ban": c.execute("UPDATE users SET is_banned = 1 WHERE username = ?", (req.target,))
        elif req.action == "unban": c.execute("UPDATE users SET is_banned = 0 WHERE username = ?", (req.target,))
        elif req.action == "approve_dep":
            c.execute("UPDATE deposits SET status = 'APPROVED' WHERE id = ?", (req.dep_id,))
            c.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (req.amount, req.target))
        elif req.action == "reject_dep": c.execute("UPDATE deposits SET status = 'REJECTED' WHERE id = ?", (req.dep_id,))
        conn.commit()
    return {"status": "success"}

@app.get("/")
async def home(): return FileResponse("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("server_ai:app", host="0.0.0.0", port=port)
      
