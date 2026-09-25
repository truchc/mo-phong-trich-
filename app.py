import streamlit as st
import CoolProp.CoolProp as CP
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Thiết lập giao diện trang web rộng rãi
st.set_page_config(page_title="Mô phỏng Hệ Nhiệt động lực học", layout="wide")
st.title(" MÔ PHỎNG VÀ ĐỊNH VỊ ĐIỂM LÀM VIỆC CỦA HỆ DUNG MÔI")

# --- THANH ĐIỀU KHIỂN (SIDEBAR) ---
st.sidebar.header(" CẤU HÌNH ĐIỂM LÀM VIỆC")

# Lựa chọn loại hệ dung môi để tính toán
fluid_type = st.sidebar.selectbox(
    "Chọn hệ dung môi cần khảo sát:",
    ["1. Nước cận tới hạn (Thuần túy)", "2. Hỗn hợp Ethanol / Nước (0% - 99.5%)"]
)

# Cấu hình thanh trượt dựa trên hệ dung môi đã chọn
if fluid_type == "1. Nước cận tới hạn (Thuần túy)":
    T_work = st.sidebar.slider("Nhiệt độ làm việc T (°C)", 100.0, 374.0, 250.0, step=1.0)
    P_work = st.sidebar.slider("Áp suất làm việc P (MPa)", 0.1, 22.0, 10.0, step=0.1)
    eth_pct = 0.0
    fluid_string = "Water"
    
    # Mốc tới hạn của nước tinh khiết
    T_critical = 373.946  # °C
    P_critical = 22.064   # MPa
    st.subheader("Hệ thống: Nước cận tới hạn (Pure Subcritical Water)")
else:
    eth_pct = st.sidebar.slider("Nồng độ Ethanol (% khối lượng)", 0.0, 99.5, 50.0, step=0.5)
    T_work = st.sidebar.slider("Nhiệt độ làm việc T (°C)", 20.0, 240.0, 80.0, step=1.0)
    P_work = st.sidebar.slider("Áp suất làm việc P (MPa)", 0.1, 15.0, 5.0, step=0.1)
    
    st.subheader(f"Hệ thống: Chất lỏng áp suất Hỗn hợp Ethanol/Nước ({eth_pct}%)")
    
    # Quy đổi phần trăm khối lượng sang phần trăm mol (Mole fraction) để CoolProp hiểu
    M_eth, M_wat = 46.07, 18.02
    w_eth = eth_pct / 100.0
    w_wat = 1.0 - w_eth
    n_eth = w_eth / M_eth
    n_wat = w_wat / M_wat
    x_eth = n_eth / (n_eth + n_wat)
    fluid_string = f"Ethanol[{x_eth}]&Water[{1-x_eth}]"
    
    # Ước tính tuyến tính đường cong điểm tới hạn (Critical curve) dựa trên nồng độ mol
    # Điểm tới hạn Ethanol tinh khiết: Tc = 240.75 °C, Pc = 6.148 MPa
    # Điểm tới hạn Nước tinh khiết: Tc = 373.95 °C, Pc = 22.06 MPa
    T_critical = x_eth * 240.75 + (1 - x_eth) * 373.946
    P_critical = x_eth * 6.148 + (1 - x_eth) * 22.064

# --- HÀM TÍNH TOÁN NHIỆT ĐỘNG ---
def calculate_properties(T_celsius, P_mpa, fluid_str):
    T_kelvin = T_celsius + 273.15
    P_pascal = P_mpa * 1e6
    try:
        rho = CP.PropsSI('D', 'T', T_kelvin, 'P', P_pascal, fluid_str)
        h = CP.PropsSI('H', 'T', T_kelvin, 'P', P_pascal, fluid_str) / 1000
        s = CP.PropsSI('S', 'T', T_kelvin, 'P', P_pascal, fluid_str) / 1000
        phase = CP.PhaseSI('T', 'T', T_kelvin, 'P', P_pascal, fluid_str)
        
        if phase in [CP.iphase_liquid, CP.iphase_supercritical_liquid]:
            status = "Chất lỏng nén áp suất"
        else:
            status = "Hơi / Khí quá nhiệt"
            # Phá hủy dữ liệu hiển thị đồ thị nếu bị hóa hơi ở áp suất thấp
            rho, h, s = np.nan, np.nan, np.nan
        return rho, h, s, status
    except:
        return np.nan, np.nan, np.nan, "Ngoài dải tính toán"

# Tính toán giá trị tại điểm làm việc hiện tại
rho_work, h_work, s_work, status_work = calculate_properties(T_work, P_work, fluid_string)

# --- HIỂN THỊ THÔNG SỐ ĐIỂM HIỆN TẠI VÀ THÔNG SỐ TỚI HẠN THAM CHIẾU ---
col_m1, col_m2 = st.columns(2)
with col_m1:
    st.write("### 📊 Thông số vật lý tại điểm làm việc:")
    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
    metrics_col1.metric("Mật độ (Density)", f"{rho_work:.2f} kg/m³" if not np.isnan(rho_work) else "N/A")
    metrics_col2.metric("Enthalpy (h)", f"{h_work:.2f} kJ/kg" if not np.isnan(h_work) else "N/A")
    metrics_col3.metric("Entropy (s)", f"{s_work:.2f} kJ/kg·K" if not np.isnan(s_work) else "N/A")
    st.info(f"**Trạng thái pha thực tế:** {status_work}")

with col_m2:
    st.write("### 🚨 Thông số giới hạn tới hạn tương ứng:")
    crit_col1, crit_col2 = st.columns(2)
    crit_col1.metric("Nhiệt độ tới hạn ước tính ($T_c$)", f"{T_critical:.2f} °C")
    crit_col2.metric("Áp suất tới hạn ước tính ($P_c$)", f"{P_critical:.2f} MPa")
    st.warning("⚠️ *Lưu ý: Với hỗn hợp, điểm tới hạn dịch chuyển liên tục theo tỷ lệ trộn.*")

# --- TẠO LƯỚI NỀN ĐO ĐẠC ĐỒ THỊ ---
# Tự động thay đổi trục tọa độ của đồ thị sao cho ôm sát dải nhiệt độ của từng chất
t_plot_max = 390 if fluid_type == "1. Nước cận tới hạn (Thuần túy)" else 280
p_plot_max = 24 if fluid_type == "1. Nước cận tới hạn (Thuần túy)" else 16

T_range = np.linspace(20, t_plot_max, 35)
P_range = np.linspace(0.1, p_plot_max, 35)
T_mesh, P_mesh = np.meshgrid(T_range, P_range)

Rho_mesh = np.zeros_like(T_mesh)
H_mesh = np.zeros_like(T_mesh)

for i in range(P_mesh.shape[0]):
    for j in range(P_mesh.shape[1]):
        rho, h, _, status = calculate_properties(T_mesh[i, j], P_mesh[i, j], fluid_string)
        if status == "Chất lỏng nén áp suất":
            Rho_mesh[i, j] = rho
            H_mesh[i, j] = h
        else:
            Rho_mesh[i, j] = np.nan
            H_mesh[i, j] = np.nan

# --- VẼ ĐỒ THỊ ---
plot_col1, plot_col2 = st.columns(2)

with plot_col1:
    st.write("### Đồ thị 3D: Biến thiên mật độ theo trạng thái")
    fig1 = plt.figure(figsize=(7, 6))
    ax1 = fig1.add_subplot(1, 1, 1, projection='3d')
    surf1 = ax1.plot_surface(T_mesh, P_mesh, Rho_mesh, cmap='viridis_r', edgecolor='none', alpha=0.6)
    
    # Chấm điểm làm việc hiện tại
    if not np.isnan(rho_work):
        ax1.scatter(T_work, P_work, rho_work, color='red', s=120, label='Điểm làm việc hiện tại', zorder=5)
    
    ax1.set_xlabel("Nhiệt độ (°C)")
    ax1.set_ylabel("Áp suất (MPa)")
    ax1.set_zlabel("Mật độ (kg/m³)")
    ax1.set_xlim(20, t_plot_max)
    ax1.set_ylim(0, p_plot_max)
    ax1.legend()
    st.pyplot(fig1)

with plot_col2:
    st.write("### Đồ thị 2D: Bản đồ Áp suất - Nhiệt độ (P-T)")
    fig2, ax2 = plt.subplots(figsize=(7, 5.2))
    contour = ax2.contourf(T_mesh, P_mesh, H_mesh, levels=20, cmap='plasma', alpha=0.7)
    fig2.colorbar(contour, ax=ax2, label="Enthalpy (kJ/kg)")
    
    # Đường dóng tọa độ
    ax2.axvline(x=T_work, color='red', linestyle='--', alpha=0.4)
    ax2.axhline(y=P_work, color='red', linestyle='--', alpha=0.4)
    
    # Vẽ điểm làm việc di động
    ax2.scatter(T_work, P_work, color='red', edgecolor='black', s=130, label=f'Điểm làm việc ({T_work}°C, {P_work}MPa)', zorder=5)
    
    # Vẽ mốc giới hạn tới hạn tương ứng với nồng độ đó
    ax2.scatter(T_critical, P_critical, color='cyan', marker='X', s=160, edgecolor='black', label=f'Mốc tới hạn chất trộn ({T_critical:.1f}°C)', zorder=5)
    
    ax2.set_xlim(20, t_plot_max)
    ax2.set_ylim(0, p_plot_max)
    ax2.set_xlabel("Nhiệt độ (°C)")
    ax2.set_ylabel("Áp suất (MPa)")
    ax2.legend(loc='upper left')
    ax2.grid(True, linestyle=':', alpha=0.6)
    st.pyplot(fig2)

# --- BẢNG DỮ LIỆU ĐỘNG THEO NỒNG ĐỘ ĐANG CHỌN ---
st.write(f"### 📋 Bảng tra cứu thông số nhiệt động của hệ tại các mức áp suất khác nhau (ở {T_work} °C)")
pressures_sample = [0.1, 1.0, 5.0, 10.0, 15.0, 20.0]
df_list = []
for p_s in pressures_sample:
    if p_s <= p_plot_max:
        rho, h, s, stat = calculate_properties(T_work, p_s, fluid_string)
        df_list.append({
            "Nhiệt độ khảo sát (°C)": T_work,
            "Áp suất thử nghiệm (MPa)": p_s,
            "Mật độ (kg/m³)": f"{rho:.2f}" if not np.isnan(rho) else "Bị hóa hơii / Pha Khí",
            "Enthalpy (kJ/kg)": f"{h:.2f}" if not np.isnan(h) else "N/A",
            "Entropy (kJ/kg·K)": f"{s:.2f}" if not np.isnan(s) else "N/A",
            "Đánh giá cấu trúc pha": stat
        })
st.dataframe(pd.DataFrame(df_list), use_container_width=True)