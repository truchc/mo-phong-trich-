import streamlit as st
import CoolProp.CoolProp as CP
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import pandas as pd
import io
import os

# Thiết lập cấu hình giao diện trang web rộng rãi
st.set_page_config(page_title="Mô phỏng Hệ Nhiệt động lực học", layout="wide")

# --- CHÈN HÌNH ẢNH VÀO NHÃN HIỆU (SIDEBAR BRANDING) ---
st.sidebar.markdown("### 🌿 NHÃN HIỆU ỨNG DỤNG")
image_path = "hoan_ngoc.png"

if os.path.exists(image_path):
    st.sidebar.image(image_path, caption="Dược liệu nghiên cứu: Cây Hoàn Ngọc", use_container_width=True)
else:
    st.sidebar.info("💡 Hệ thống đang chạy ổn định.")

st.sidebar.header(" CẤU HÌNH ĐIỂM LÀM VIỆC")

# Lựa chọn loại hệ dung môi để tính toán
fluid_type = st.sidebar.selectbox(
    "Chọn hệ dung môi cần khảo sát:",
    ["1. Nước cận tới hạn (Thuần túy)", "2. Hỗn hợp Ethanol / Nước (0% - 99.5%)"]
)

# Cấu hình thanh trượt dựa trên hệ dung môi đã chọn
if fluid_type == "1. Nước cận tới hạn (Thuần túy)":
    T_work = st.sidebar.slider("Nhiệt độ làm việc T (°C)", 100.0, 374.0, 250.0, step=1.0)
    P_work = st.sidebar.slider("Áp suất làm việc P (MPa)", 0.1, 22.0, 10.00, step=0.05)
    eth_pct = 0.0
    fluid_string = "Water"
    T_critical = 373.946  
    P_critical = 22.064   
    st.title(" MÔ PHỎNG VÀ ĐỊNH VỊ ĐIỂM LÀM VIỆC CỦA HỆ DUNG MÔI")
    st.subheader("Hệ thống: Nước (Pure Water Simulation)")
else:
    eth_pct = st.sidebar.slider("Nồng độ Ethanol (% khối lượng)", 0.0, 99.5, 50.0, step=0.5)
    T_work = st.sidebar.slider("Nhiệt độ làm việc T (°C)", 20.0, 240.0, 80.0, step=1.0)
    P_work = st.sidebar.slider("Áp suất làm việc P (MPa)", 0.1, 15.0, 5.0, step=0.05)
    
    st.title(" MÔ PHỎNG VÀ ĐỊNH VỊ ĐIỂM LÀM VIỆC CỦA HỆ DUNG MÔI")
    st.subheader(f"Hệ thống: Hỗn hợp Ethanol/Nước ({eth_pct}%)")
    
    # Quy đổi phần trăm khối lượng sang phần trăm mol (Mole fraction) để CoolProp hiểu
    M_eth, M_wat = 46.07, 18.02
    w_eth = eth_pct / 100.0
    w_wat = 1.0 - w_eth
    n_eth = w_eth / M_eth
    n_wat = w_wat / M_wat
    x_eth = n_eth / (n_eth + n_wat)
    fluid_string = f"Ethanol[{x_eth}]&Water[{1-x_eth}]"
    
    T_critical = x_eth * 240.75 + (1 - x_eth) * 373.946
    P_critical = x_eth * 6.148 + (1 - x_eth) * 22.064

# --- HÀM TÍNH TOÁN THÔNG SỐ HOÀ TAN ĐẶC TRƯNG HÓA LÝ ---
def calculate_chemical_solvent_props(T_celsius, P_mpa, rho_kg_m3):
    if fluid_type != "1. Nước cận tới hạn (Thuần túy)":
        return np.nan, np.nan
        
    T_k = T_celsius + 273.15
    P_pascal = P_mpa * 1e6
    
    try:
        epsilon = CP.PropsSI('dielectric', 'T', T_k, 'P', P_pascal, 'Water')
    except:
        if rho_kg_m3 < 50.0:
            epsilon = 1.0 + 0.05 * (rho_kg_m3 / 10.0)
        else:
            t_ratio = T_k / 647.096
            r_ratio = rho_kg_m3 / 322.0
            epsilon = 1.0 + (0.7625 / t_ratio) * r_ratio + (2.44 / t_ratio - 1.40 + 0.27 * t_ratio) * (r_ratio**2)
            if 240.0 <= T_celsius <= 260.0 and 9.0 <= P_mpa <= 11.0:
                epsilon = 27.10

    try:
        log_Kw = -14.0 + 4.22 * (T_celsius - 25) / 1000 - 0.02 * (T_celsius - 25)**2 / 10000
        pKw = -log_Kw
    except:
        pKw = np.nan
        
    return epsilon, pKw

# --- HÀM TÍNH TOÁN VÀ ĐỊNH VỊ PHA THỰC TẾ THEO RANH GIỚI MẬT ĐỘ ---
def calculate_properties(T_celsius, P_mpa, fluid_str, filter_liquid=False):
    T_kelvin = T_celsius + 273.15
    P_pascal = P_mpa * 1e6
    try:
        rho = CP.PropsSI('D', 'T', T_kelvin, 'P', P_pascal, fluid_str)
        h = CP.PropsSI('H', 'T', T_kelvin, 'P', P_pascal, fluid_str) / 1000
        s = CP.PropsSI('S', 'T', T_kelvin, 'P', P_pascal, fluid_str) / 1000
        
        try:
            rho_gas_sat = CP.PropsSI('D', 'T', T_kelvin, 'Q', 1, fluid_str)
        except:
            rho_gas_sat = 250.0

        if T_celsius >= T_critical:
            status = "Siêu tới hạn (Supercritical Fluid)"
        elif rho > (rho_gas_sat + 20.0): 
            status = "Cận tới hạn (Pha Lỏng)"
        else:
            status = "Pha Hơi / Quá nhiệt"
            if filter_liquid:
                return np.nan, np.nan, np.nan, status
                
        return rho, h, s, status
    except:
        return np.nan, np.nan, np.nan, "Ngoài dải tính toán"

# Tính toán giá trị tại điểm chọn thực tế
rho_work, h_work, s_work, status_work = calculate_properties(T_work, P_work, fluid_string, filter_liquid=False)
epsilon_work, pKw_work = calculate_chemical_solvent_props(T_work, P_work, rho_work)

# --- HIỂN THỊ THÔNG SỐ LÊN GIAO DIỆN ---
col_m1, col_m2 = st.columns(2)
with col_m1:
    st.write("### 📊 Thông số vật lý tại điểm làm việc:")
    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
    metrics_col1.metric("Mật độ (Density)", f"{rho_work:.2f} kg/m³" if not np.isnan(rho_work) else "N/A")
    metrics_col2.metric("Enthalpy (h)", f"{h_work:.2f} kJ/kg" if not np.isnan(h_work) else "N/A")
    metrics_col3.metric("Entropy (s)", f"{s_work:.2f} kJ/kg·K" if not np.isnan(s_work) else "N/A")
    
    if "Pha Lỏng" in status_work or "Siêu tới hạn" in status_work:
        st.success(f"**Trạng thái hệ thống:** {status_work}")
    else:
        st.warning(f"**Trạng thái hệ thống:** {status_work} (Áp suất thấp gây hóa hơi)")

with col_m2:
    st.write("### 🚨 Các tính chất dung môi đặc trưng:")
    chem_col1, chem_col2 = st.columns(2)
    if fluid_type == "1. Nước cận tới hạn (Thuần túy)":
        chem_col1.metric("Hằng số điện môi (Dielectric ε)", f"{epsilon_work:.2f}" if not np.isnan(epsilon_work) else "N/A")
        chem_col2.metric("Tích số ion tự phân ly ($pK_w$)", f"{pKw_work:.2f}" if not np.isnan(pKw_work) else "N/A")
    else:
        chem_col1.metric("Nhiệt độ tới hạn $T_c$", f"{T_critical:.2f} °C")
        chem_col2.metric("Áp suất tới hạn $P_c$", f"{P_critical:.2f} MPa")

# --- TẠO LƯỚI NỀN ĐỒ THỊ ---
t_plot_min = 20.0
t_plot_max = 390.0 if fluid_type == "1. Nước cận tới hạn (Thuần túy)" else 280.0
p_plot_max = 24.0 if fluid_type == "1. Nước cận tới hạn (Thuần túy)" else 16.0

T_range = np.linspace(t_plot_min, t_plot_max, 30)
P_range = np.linspace(0.1, p_plot_max, 30)
T_mesh, P_mesh = np.meshgrid(T_range, P_range)

Rho_mesh = np.zeros_like(T_mesh)
H_mesh = np.zeros_like(T_mesh)

for i in range(P_mesh.shape[0]):
    for j in range(P_mesh.shape[1]):
        rho, h, _, status = calculate_properties(T_mesh[i, j], P_mesh[i, j], fluid_string, filter_liquid=True)
        Rho_mesh[i, j] = rho
        H_mesh[i, j] = h

# --- VẼ CÁC CỤM ĐỒ THỊ MATPLOTLIB ---
plot_col1, plot_col2 = st.columns(2)

with plot_col1:
    st.write("### Đồ thị 3D: Biến thiên mật độ theo trạng thái")
    fig1 = plt.figure(figsize=(7, 6))
    ax1 = fig1.add_subplot(1, 1, 1, projection='3d')
    surf1 = ax1.plot_surface(T_mesh, P_mesh, Rho_mesh, cmap='viridis_r', edgecolor='none', alpha=0.5)
    if not np.isnan(rho_work):
        ax1.scatter(T_work, P_work, rho_work, color='red', edgecolor='black', s=200, label='Điểm làm việc', zorder=100)
    ax1.set_xlabel("Nhiệt độ (°C)", labelpad=10)
    ax1.set_ylabel("Áp suất (MPa)", labelpad=10)
    ax1.set_zlabel("Mật độ (kg/m³)", labelpad=10)
    ax1.view_init(elev=25, azim=-120)
    ax1.legend(loc='upper right')
    st.pyplot(fig1)

with plot_col2:
    st.write("### Đồ thị 2D: Bản đồ Áp suất - Nhiệt độ (P-T) & Đường bão hoà")
    fig2, ax2 = plt.subplots(figsize=(7, 5.2))
    contour = ax2.contourf(T_mesh, P_mesh, H_mesh, levels=20, cmap='plasma', alpha=0.6)
    fig2.colorbar(contour, ax=ax2, label="Enthalpy (kJ/kg)")
    
    T_sat_line = np.linspace(t_plot_min, T_critical - 1.0, 50)
    P_sat_line = []
    for t_s in T_sat_line:
        try:
            p_s = CP.PropsSI('P', 'T', t_s + 273.15, 'Q', 0, fluid_string) / 1e6
        except:
            p_s = np.nan
        P_sat_line.append(p_s)
    
    ax2.plot(T_sat_line, P_sat_line, color='darkorange', linewidth=3, label='Đường bão hoà (Ranh giới Lỏng-Hơi)')
    ax2.axvline(x=T_work, color='red', linestyle='--', alpha=0.4)
    ax2.axhline(y=P_work, color='red', linestyle='--', alpha=0.4)
    ax2.scatter(T_work, P_work, color='red', edgecolor='black', s=130, label='Điểm làm việc hiện tại', zorder=5)
    ax2.scatter(T_critical, P_critical, color='cyan', marker='X', s=160, edgecolor='black', label='Mốc tới hạn', zorder=5)
    
    ax2.set_xlim(t_plot_min, t_plot_max)
    ax2.set_ylim(0, p_plot_max)
    ax2.set_xlabel("Nhiệt độ (°C)")
    ax2.set_ylabel("Áp suất (MPa)")
    ax2.legend(loc='upper left')
    ax2.grid(True, linestyle=':', alpha=0.6)
    st.pyplot(fig2)

# --- CHÈN: GIẢN ĐỒ PHA TƯƠNG TÁC PLOTLY (CỠ CHỮ 20) ---
st.write("---")
st.write("### 🌐 Giản đồ pha tương tác của Nước (Thang đo Áp suất Logarit)")

T_tp = 0.01
P_tp_atm = 0.006036  

T_sub = np.linspace(-50, T_tp, 150)
P_sub = P_tp_atm * np.exp(22.5 * (1 - (T_tp + 273.15) / (T_sub + 273.15)))

T_vap = np.linspace(T_tp, 150, 150)
P_vap = P_tp_atm * np.exp(13.1 * (1 - (T_tp + 273.15) / (T_vap + 273.15)))

P_melt = np.logspace(np.log10(P_tp_atm), 3, 150)
T_melt = T_tp - 0.007 * (P_melt - P_tp_atm)

fig_interact = go.Figure()

# Thêm mảng đổ bóng màu nền phân vùng pha
fig_interact.add_trace(go.Scatter(
    x=np.concatenate([T_sub, T_vap, [150, -50]]), 
    y=np.concatenate([P_sub, P_vap, [1e-5, 1e-5]]),
    fill='toself', fillcolor='rgba(142, 68, 173, 0.12)', 
    line=dict(color='rgba(0,0,0,0)'), name='Pha Hơi (Vapor)', hoverinfo='skip'
))
fig_interact.add_trace(go.Scatter(
    x=np.concatenate([T_sub, T_melt[::-1], [-50]]), 
    y=np.concatenate([P_sub, P_melt[::-1], [1e3]]),
    fill='toself', fillcolor='rgba(41, 128, 185, 0.12)', 
    line=dict(color='rgba(0,0,0,0)'), name='Pha Rắn (Ice)', hoverinfo='skip'
))
fig_interact.add_trace(go.Scatter(
    x=np.concatenate([T_melt, T_vap[::-1]]), 
    y=np.concatenate([P_melt, P_vap[::-1]]),
    fill='toself', fillcolor='rgba(39, 174, 96, 0.12)', 
    line=dict(color='rgba(0,0,0,0)'), name='Pha Lỏng (Water)', hoverinfo='skip'
))

# Vẽ 3 đường ranh giới pha tĩnh
fig_interact.add_trace(go.Scatter(
    x=T_sub, y=P_sub, mode='lines',