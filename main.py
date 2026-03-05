from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI(title="Hưng Admin Auto Web")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def get_ai_prediction():
    try:
        res = requests.get("https://wtx.tele68.com/v1/tx/lite-sessions", timeout=5).json()
        danh_sach = res.get("list", [])
        if not danh_sach: return {"du_doan": "WAIT", "ti_le": 0, "loi_khuyen": "Lỗi nạp Data", "trend": "---", "phien": "..."}
        
        danh_sach.reverse()
        phien_hien_tai = str(danh_sach[-1]["id"])
        phien_tiep = str(int(phien_hien_tai) + 1)
        
        kq_list = ["Tài" if s["resultTruyenThong"] == "TAI" else "Xỉu" for s in danh_sach]
        kq_cuoi = kq_list[-1]
        trend = "".join(["🔴" if x == "Tài" else "🔵" for x in kq_list[-15:]])
        
        chuoi_hien_tai = 1
        for i in range(len(kq_list)-2, -1, -1):
            if kq_list[i] == kq_cuoi: chuoi_hien_tai += 1
            else: break
            
        if chuoi_hien_tai >= 4:
            return {"du_doan": kq_cuoi.upper(), "ti_le": 85 + chuoi_hien_tai, "loi_khuyen": f"🔥 ĐANG BỆT {chuoi_hien_tai} TAY - VÀO MẠNH 10%", "trend": trend, "phien": phien_tiep}
            
        trans = {"Tài_Tài": 0, "Tài_Xỉu": 0, "Xỉu_Xỉu": 0, "Xỉu_Tài": 0}
        for i in range(len(kq_list) - 1): trans[f"{kq_list[i]}_{kq_list[i+1]}"] += 1
            
        tong = (trans["Tài_Tài"] + trans["Tài_Xỉu"]) if kq_cuoi == "Tài" else (trans["Xỉu_Tài"] + trans["Xỉu_Xỉu"])
        if tong == 0: tong = 1
        
        tl_tai = (trans["Tài_Tài"]/tong)*100 if kq_cuoi == "Tài" else (trans["Xỉu_Tài"]/tong)*100
        tl_xiu = (trans["Tài_Xỉu"]/tong)*100 if kq_cuoi == "Tài" else (trans["Xỉu_Xỉu"]/tong)*100
        
        du_doan = "TÀI" if tl_tai > tl_xiu else "XỈU"
        ty_le_max = round(max(tl_tai, tl_xiu), 1)
        
        if ty_le_max >= 75: loi_khuyen = "✅ CẦU ĐẸP - VÀO TỰ TIN 5%"
        elif ty_le_max >= 60: loi_khuyen = "⚖️ CẦU ỔN - ĐÁNH ĐỀU 2%"
        else: loi_khuyen = "⚠️ CẦU LOẠN - ĐÁNH DÒ ĐƯỜNG"
        
        return {"du_doan": du_doan, "ti_le": ty_le_max, "loi_khuyen": loi_khuyen, "trend": trend, "phien": phien_tiep}
    except:
        return {"du_doan": "SCAN", "ti_le": 50, "loi_khuyen": "Đang kết nối lại...", "trend": "---", "phien": "..."}

@app.get("/api/data")
async def api_data():
    return get_ai_prediction()

HTML_CODE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HƯNG ADMIN | AI PREDICTION</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #050505; color: #fff; font-family: 'Orbitron', sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        body::before { content: ''; position: absolute; width: 100%; height: 100%; background: linear-gradient(rgba(0, 255, 170, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 255, 170, 0.05) 1px, transparent 1px); background-size: 30px 30px; z-index: -1; }
        .dashboard { width: 95%; max-width: 450px; background: rgba(10, 15, 10, 0.85); backdrop-filter: blur(10px); border: 2px solid #00ffaa; border-radius: 15px; padding: 20px; box-shadow: 0 0 30px rgba(0,255,170,0.2); }
        .header { text-align: center; border-bottom: 1px dashed #00ffaa; padding-bottom: 15px; margin-bottom: 20px; }
        .header h1 { color: #00ffaa; font-size: 24px; text-shadow: 0 0 10px #00ffaa; letter-spacing: 3px; }
        .signal-box { background: rgba(0,0,0,0.6); border: 1px solid #333; border-radius: 10px; padding: 20px; text-align: center; margin-bottom: 20px; position: relative; }
        .phien-text { position: absolute; top: 10px; left: 15px; color: #aaa; font-size: 12px; }
        .status-dot { position: absolute; top: 10px; right: 15px; width: 12px; height: 12px; background: #00ffaa; border-radius: 50%; box-shadow: 0 0 10px #00ffaa; animation: blink 1s infinite; }
        .result-text { font-size: 55px; font-weight: 900; margin: 15px 0; letter-spacing: 5px; }
        .txt-tai { color: #ff3366; text-shadow: 0 0 20px #ff3366; }
        .txt-xiu { color: #00ccff; text-shadow: 0 0 20px #00ccff; }
        .txt-wait { color: #ffaa00; text-shadow: 0 0 20px #ffaa00; font-size: 40px; }
        .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; }
        .stat-card { background: linear-gradient(45deg, rgba(0,255,170,0.1), transparent); border: 1px solid #00ffaa; border-radius: 8px; padding: 15px; text-align: center; }
        .stat-title { color: #aaa; font-size: 11px; margin-bottom: 8px; }
        .stat-value { font-size: 20px; font-weight: bold; color: #fff; }
        .stat-khuyen { grid-column: 1 / span 2; background: rgba(255,170,0,0.1); border-color: #ffaa00; color: #ffaa00; }
        .radar-box { background: #000; border: 1px solid #222; border-radius: 8px; padding: 15px; text-align: center; }
        .radar-balls { font-size: 22px; letter-spacing: 8px; font-family: sans-serif;}
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
    </style>
</head>
<body>
<div class="dashboard">
    <div class="header"><h1>👑 HƯNG ADMIN 👑</h1><p>HỆ THỐNG TRÍ TUỆ NHÂN TẠO PRO</p></div>
    <div class="signal-box">
        <div class="phien-text" id="ui-phien">PHIÊN: Đang tải...</div>
        <div class="status-dot"></div>
        <div style="color:#aaa; font-size:12px; margin-top:20px;">CHỈ THỊ VÁN SAU</div>
        <div class="result-text txt-wait" id="ui-result">LOADING</div>
    </div>
    <div class="stats-grid">
        <div class="stat-card"><div class="stat-title">TỶ LỆ WIN (AI)</div><div class="stat-value" id="ui-tile">--%</div></div>
        <div class="stat-card"><div class="stat-title">TRẠNG THÁI</div><div class="stat-value" style="color:#00ffaa;">ONLINE</div></div>
        <div class="stat-card stat-khuyen"><div class="stat-title" style="color:#ffaa00;">QUẢN LÝ VỐN KELLY</div><div class="stat-value" id="ui-khuyen" style="font-size:16px;">Đang kết nối...</div></div>
    </div>
    <div class="radar-box"><div class="stat-title">RADAR CẦU (15 TAY GẦN NHẤT)</div><div class="radar-balls" id="ui-trend">...</div></div>
</div>
<script>
    async function fetchData() {
        try {
            const res = await fetch('/api/data'); const data = await res.json();
            document.getElementById('ui-phien').innerText = "PHIÊN KẾ: #" + data.phien;
            document.getElementById('ui-tile').innerText = data.ti_le + "%";
            document.getElementById('ui-khuyen').innerText = data.loi_khuyen;
            document.getElementById('ui-trend').innerText = data.trend;
            const resEl = document.getElementById('ui-result');
            resEl.innerText = data.du_doan; resEl.className = "result-text";
            if (data.du_doan === "TÀI") resEl.classList.add("txt-tai");
            else if (data.du_doan === "XỈU") resEl.classList.add("txt-xiu");
            else resEl.classList.add("txt-wait");
        } catch (e) {}
    }
    setInterval(fetchData, 2500); fetchData();
</script>
</body>
</html>
"""
@app.get("/")
async def home(): return HTMLResponse(content=HTML_CODE)
  
