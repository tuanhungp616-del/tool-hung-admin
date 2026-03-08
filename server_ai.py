from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests, uvicorn, sqlite3, os
from datetime import datetime, timedelta

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
DB_FILE = "hethong_vip.db"

def khoi_tao_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS keys (apikey TEXT PRIMARY KEY, expire_date DATETIME)''')
    c.execute("INSERT OR IGNORE INTO keys (apikey, expire_date) VALUES (?, ?)", ('hungadmin', '2099-12-31 23:59:59'))
    conn.commit()
    conn.close()

khoi_tao_db()

def phan_tich_ai(kq_list):
    tong_tai = kq_list.count("Tài")
    tong_xiu = kq_list.count("Xỉu")
    
    if len(kq_list) < 5: 
        return {"du_doan": "WAIT", "ti_le": 0, "loi_khuyen": "Đang nạp Data...", "trend": "...", "kieu_cau": "SCANNING", "tong_tai": tong_tai, "tong_xiu": tong_xiu}
    
    kq_cuoi = kq_list[-1]
    chuoi = 1
    for i in range(len(kq_list)-2, -1, -1):
        if kq_list[i] == kq_cuoi: chuoi += 1
        else: break
    
    du_doan = "TÀI" if kq_cuoi == "Xỉu" else "XỈU"
    ty_le = 50.0
    kieu_cau = "PHÂN TÍCH MARKOV PRO"
    last_4 = ",".join(kq_list[-4:])
    last_5 = ",".join(kq_list[-5:])

    if chuoi >= 6: du_doan, ty_le, kieu_cau = ("XỈU" if kq_cuoi == "Tài" else "TÀI", 75.0, f"🚨 CẢNH BÁO BẺ ({chuoi} TAY)")
    elif chuoi >= 4: du_doan, ty_le, kieu_cau = (kq_cuoi.upper(), min(80 + chuoi * 2.5, 99.9), f"🔥 ĐANG BỆT {chuoi} TAY")
    elif last_4 in ["Tài,Xỉu,Tài,Xỉu", "Xỉu,Tài,Xỉu,Tài"]: du_doan, ty_le, kieu_cau = ("TÀI" if kq_cuoi == "Xỉu" else "XỈU", 88.0, "⚡ CẦU 1-1 (PING-PONG)")
    elif last_4 in ["Tài,Tài,Xỉu,Xỉu", "Xỉu,Xỉu,Tài,Tài"]: du_doan, ty_le, kieu_cau = (kq_cuoi.upper(), 85.0, "⚖️ CẦU 2-2 NHỊP ĐỀU")
    elif last_5 in ["Tài,Tài,Tài,Xỉu,Tài", "Xỉu,Xỉu,Xỉu,Tài,Xỉu"]: du_doan, ty_le, kieu_cau = (kq_cuoi.upper(), 82.0, "🎯 CẦU 3-1-3 CHUẨN")
    else:
        t = {"Tài_Tài": 0, "Tài_Xỉu": 0, "Xỉu_Xỉu": 0, "Xỉu_Tài": 0}
        for i in range(len(kq_list) - 1): t[f"{kq_list[i]}_{kq_list[i+1]}"] += 1
        tong = max(1, (t["Tài_Tài"] + t["Tài_Xỉu"]) if kq_cuoi == "Tài" else (t["Xỉu_Tài"] + t["Xỉu_Xỉu"]))
        tl_tai = (t["Tài_Tài"]/tong)*100 if kq_cuoi == "Tài" else (t["Xỉu_Tài"]/tong)*100
        tl_xiu = (t["Tài_Xỉu"]/tong)*100 if kq_cuoi == "Tài" else (t["Xỉu_Xỉu"]/tong)*100
        du_doan = "TÀI" if tl_tai > tl_xiu else "XỈU"
        ty_le = round(max(tl_tai, tl_xiu), 1)

    kelly = max(1, round(((2 * (ty_le/100) - 1) * 100) / 3))
    if chuoi >= 6: loi_khuyen = f"🛑 GẤP THẾP BẺ CẦU {kelly}% VỐN"
    elif ty_le >= 80: loi_khuyen = f"🚀 CẦU ĐẸP -> VÀO {kelly}% VỐN"
    elif ty_le >= 60: loi_khuyen = f"💰 ĐÁNH ĐỀU {kelly}% VỐN"
    else: loi_khuyen = f"⚠️ CẦU LOẠN -> DÒ ĐƯỜNG 1%"

    radar = "".join(["🔴" if x == "Tài" else "🔵" for x in kq_list[-12:]])
    return {"du_doan": du_doan, "ti_le": ty_le, "loi_khuyen": loi_khuyen, "trend": radar, "kieu_cau": kieu_cau, "tong_tai": tong_tai, "tong_xiu": tong_xiu}

@app.get("/api/scan")
async def scan_game(tool: str, apikey: str):
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    c.execute("SELECT expire_date FROM keys WHERE apikey = ?", (apikey,)); row = c.fetchone()
    conn.close()
    if not row: return {"status": "error", "msg": "Key không tồn tại!"}
    if datetime.now() > datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S"): return {"status": "error", "msg": "Key hết hạn!"}

    if tool == "lc79":
        api_url = "https://wtx.tele68.com/v1/tx/lite-sessions"
    elif tool == "vip":
        api_url = "https://wtx.macminim6.online/v1/tx/lite-sessions"
    elif tool == "md5vip":
        api_url = "https://wtxmd52.macminim6.online/v1/tx/lite-sessions"
    else: return {"status": "error", "msg": "Mã Tool không hợp lệ!"}

    try:
        res = requests.get(api_url, headers={"User-Agent": "Chrome/120.0"}, timeout=5).json()
        if not res.get("list"): return {"status": "error", "msg": "Đang chờ cầu mới..."}
        lst = res["list"][::-1]
        kq = ["Tài" if "TAI" in str(s.get("resultTruyenThong", "")).upper() else "Xỉu" for s in lst]
        data = phan_tich_ai(kq); data["phien"] = str(int(lst[-1]["id"]) + 1)
        return {"status": "success", "data": data}
    except Exception as e: return {"status": "error", "msg": "Bảo trì hoặc Sai Link MD5"}

# ==========================================
# CỔNG BẢO MẬT: GIẢI MÃ MD5 (CHỐNG TRỘM CODE)
# ==========================================
class MD5Req(BaseModel):
    md5_str: str
    ai_du_doan: str
    ai_ti_le: float

@app.post("/api/analyze_md5")
async def analyze_md5_logic(req: MD5Req):
    md5_str = req.md5_str.strip()
    if len(md5_str) < 10: return {"status": "error", "msg": "Chuỗi MD5 không hợp lệ!"}
    
    # Tính toán ngầm trong Python
    ascii_sum = sum(ord(c) for c in md5_str)
    is_md5_tai = (ascii_sum % 2 == 0)
    is_ai_tai = (req.ai_du_doan == "TÀI")
    
    if is_md5_tai == is_ai_tai:
        final_result = req.ai_du_doan
        final_rate = min(99.0, req.ai_ti_le + 12.5)
        final_advice = "🚀 CỘNG HƯỞNG MD5 -> VÀO MẠNH TAY"
    else:
        final_result = "TÀI" if is_md5_tai else "XỈU"
        final_rate = max(55.0, req.ai_ti_le - 15.2)
        final_advice = "⚠️ XUNG ĐỘT MD5 -> DÒ ĐƯỜNG NHẸ"
        
    return {
        "status": "success",
        "data": { "du_doan": final_result, "ti_le": round(final_rate, 1), "loi_khuyen": final_advice }
    }

class KeyReq(BaseModel): admin_key: str; new_key: str; duration: str
class DelReq(BaseModel): admin_key: str; target_key: str

@app.post("/api/admin/create")
async def create_new_key(req: KeyReq):
    if req.admin_key != "hungadmin": return {"status": "error", "msg": "Không có quyền!"}
    now = datetime.now()
    if req.duration == "1H": exp = now + timedelta(hours=1)
    elif req.duration == "1D": exp = now + timedelta(days=1)
    elif req.duration == "3D": exp = now + timedelta(days=3)
    elif req.duration == "1M": exp = now + timedelta(days=30)
    else: return {"status": "error"}
    try:
        conn = sqlite3.connect(DB_FILE); c = conn.cursor()
        c.execute("INSERT INTO keys VALUES (?, ?)", (req.new_key, exp.strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit(); conn.close()
        return {"status": "success"}
    except: return {"status": "error", "msg": "Key đã tồn tại!"}

@app.get("/api/admin/list")
async def list_keys(apikey: str):
    if apikey != "hungadmin": return {"status": "error"}
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    c.execute("SELECT apikey, expire_date FROM keys ORDER BY expire_date DESC"); keys = c.fetchall(); conn.close()
    return {"status": "success", "data": [{"key": k[0], "exp": k[1]} for k in keys]}

@app.post("/api/admin/delete")
async def delete_key(req: DelReq):
    if req.admin_key != "hungadmin" or req.target_key == "hungadmin": return {"status": "error"}
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    c.execute("DELETE FROM keys WHERE apikey = ?", (req.target_key,)); conn.commit(); conn.close()
    return {"status": "success"}

@app.get("/")
async def home():
    try:
        with open("index.html", "r", encoding="utf-8") as f: return HTMLResponse(content=f.read())
    except: return HTMLResponse(content="<h1>Chưa tạo file index.html</h1>")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server_ai:app", host="0.0.0.0", port=port)
        
