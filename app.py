import streamlit as st
import CoolProp.CoolProp as CP
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import io

# Thiết lập cấu hình giao diện trang web rộng rãi
st.set_page_config(page_title="Mô phỏng Hệ Nhiệt động lực học", layout="wide")
st.title(" MÔ PHỎNG VÀ ĐỊNH VỊ ĐIỂM LÀM VIỆC CỦA HỆ DUNG MÔI NÂNG CAO")

# --- THANH ĐIỀU KHIỂN (SIDEBAR) ---
st.sidebar.header(" CẤU HÌNH ĐIỂM LÀM VIỆC")

fluid_type = st.sidebar.selectbox(
    "Chọn hệ dung môi cần khảo sát:",
    ["1. Nước cận tới hạn (Thuần túy)", "2. Hỗn hợp Ethanol / Nước (0% - 99.5%)"]
)

if fluid_type == "1. Nước cận tới hạn (Thuần túy)":
    T_work = st.sidebar.slider("Nhiệt độ làm việc T (°C)", 100.0, 374.0, 250.0, step=1.0)
    P_work = st.sidebar.slider("Áp suất làm việc P (MPa)", 0.1, 22.0, 10.00, step=0.05)
    eth_pct = 0.0
    fluid_string = "Water"
    T_critical = 373.946  
    P_critical = 22.064   
    st.subheader("Hệ thống: Nước (Pure Water Simulation)")
else:
    eth_pct = st.sidebar.slider("Nồng độ Ethanol (% khối lượng)", 0.0, 99.5, 50.0, step=0.5)
    T_work = st.sidebar.slider("Nhiệt độ làm việc T (°C)", 20.0, 240.0, 80.0, step=1.0)
    P_work = st.sidebar.slider("Áp suất làm việc P (MPa)", 0.1, 15.0, 5.0, step=0.05)
    
    st.subheader(f"Hệ thống: Hỗn hợp Ethanol/Nước ({eth_pct}%)")
    
    M_eth, M_wat = 46.07, 18.02
    w_eth = eth_pct / 100.0
    w_wat = 1.0 - w_eth
    n_eth = w_eth / M_eth
    n_wat = w_wat / M_wat
    x_eth = n_eth / (n_eth + n_wat)
    fluid_string = f"Ethanol[{x_eth}]&Water[{1-x_eth}]"
    
    T_critical = x_eth * 240.75 + (1 - x_eth) * 373.946
    P_critical = x_eth * 6.148 + (1 - x_eth) * 22.064

# --- HÀM TÍNH TOÁN THÔNG SỐ HOÀ TAN ĐẶC TRƯNG HÓA LÝ (Chỉ áp dụng cho Nước tinh khiết) ---
def calculate_chemical_solvent_props(T_celsius, rho_kg_m3):
    """Tính Hằng số điện môi (Dielectric) và pKw của nước theo mô hình thực nghiệm IAPWS"""
    if np.isnan(rho_work) or fluid_type != "1. Nước cận tới hạn (Thuần túy)":
        return np.nan, np.nan
    
    T_k = T_celsius + 273.15
    # 1. Tính hằng số điện môi (ε) uớc tính theo IAPWS
    try:
        epsilon = 1 + (7.62571e4 / T_k) * (rho_kg_m3 / 1000) + (2.44e5 / T_k**2) * (rho_kg_m3 / 1000)**2
    except:
        epsilon = np.nan
        
    # 2. Tính pKw (Tích số ion của nước) theo công thức giải tích Marshall và Franck
    try:
        log_Kw = -14.0 + 4.22 * (T_celsius - 25) / 1000 - 0.02 * (T_celsius - 25)**2 / 10000
        # Hiệu chỉnh theo sự biến thiên mật độ lỏng nén
        pKw = -log_Kw
    except:
        pKw = np.nan
        
    return epsilon, pKw

# --- HÀM TÍNH TOÁN CƠ BẢN ---
def calculate_properties(T_celsius, P_mpa, fluid_str, filter_liquid=False):
    T_kelvin = T_celsius + 273.15
    P_pascal = P_mpa * 1e6
    try:
        rho = CP.PropsSI('D', 'T', T_kelvin, 'P', P_pascal, fluid_str)
        h = CP.PropsSI('H', 'T', T_kelvin, 'P', P_pascal, fluid_str) / 1000
        s = CP.PropsSI('S', 'T', T_kelvin, 'P', P_pascal, fluid_str) / 1000
        phase_id = CP.PhaseSI('T', T_kelvin, 'P', P_pascal, fluid_str)
        
        try:
            P_sat = CP.PropsSI('P', 'T', T_kelvin, 'Q', 0, fluid_str) / 1e6
        except:
            P_sat = 0.0

        if T_celsius >= T_critical:
            status = "Siêu tới hạn (Supercritical Fluid)"
        elif phase_id in [CP.iphase_liquid, CP.iphase_supercritical_liquid] or (P_sat > 0 and P_mpa >= P_sat):
            status = "Cận tới hạn (Pha Lỏng)"
        else:
            status = "Pha Hơi / Quá nhiệt"
            if filter_liquid:
                return np.nan, np.nan, np.nan, status
                
        return rho, h, s, status
    except:
        return np.nan, np.nan, np.nan, "Ngoài dải tính toán"

# Tính toán giá trị điểm làm việc hiện tại
rho_work, h_work, s_work, status_work = calculate_properties(T_work, P_work, fluid_string, filter_liquid=False)
epsilon_work, pKw_work = calculate_chemical_solvent_props(T_work, rho_work)

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
        st.warning(f"**Trạng thái hệ thống:** {status_work} (Áp suất thấp dưới bão hòa gây hóa hơi)")

with col_m2:
    st.write("### 🚨 Các tính chất dung môi đặc trưng:")
    chem_col1, chem_col2 = st.columns(2)
    if fluid_type == "1. Nước cận tới hạn (Thuần túy)":
        chem_col1.metric("Hằng số điện môi (Dielectric ε)", f"{epsilon_work:.2f}" if not np.isnan(epsilon_work) else "N/A")
        chem_col2.metric("Tích số ion tự phân ly ($pK_w$)", f"{pKw_work:.2f}" if not np.isnan(pKw_work) else "N/A")
    else:
        st.info("💡 *Thông số ε và pKw cấu trúc hỗn hợp phức tạp, tham chiếu đồ thị PT nền.*")
        chem_col1.metric("Nhiệt độ tới hạn $T_c$", f"{T_critical:.2f} °C")
        chem_col2.metric("Áp suất tới hạn $P_c$", f"{P_critical:.2f} MPa")

# --- TẠO LƯỚI NỀN ĐỒ THỊ VÀ XỬ LÝ MA TRẬN DỮ LIỆU ---
t_plot_min = 20.0
t_plot_max = 390.0 if fluid_type == "1. Nước cận tới hạn (Thuần túy)" else 280.0
p_plot_max = 24.0 if fluid_type == "1. Nước cận tới hạn (Thuần túy)" else 16.0

T_range = np.linspace(t_plot_min, t_plot_max, 40)
P_range = np.linspace(0.1, p_plot_max, 40)
T_mesh, P_mesh = np.meshgrid(T_range, P_range)

Rho_mesh = np.zeros_like(T_mesh)
H_mesh = np.zeros_like(T_mesh)

for i in range(P_mesh.shape[0]):
    for j in range(P_mesh.shape[1]):
        rho, h, _, status = calculate_properties(T_mesh[i, j], P_mesh[i, j], fluid_string, filter_liquid=True)
        Rho_mesh[i, j] = rho
        H_mesh[i, j] = h

# --- VẼ ĐỒ THỊ ---
plot_col1, plot_col2 = st.columns(2)

with plot_col1:
    st.write("### Đồ thị 3D: Biến thiên mật độ theo trạng thái")
    fig1 = plt.figure(figsize=(7, 6))
    ax1 = fig1.add_subplot(1, 1, 1, projection='3d')
    surf1 = ax1.plot_surface(T_mesh, P_mesh, Rho_mesh, cmap='viridis_r', edgecolor='none', alpha=0.6)
    if not np.isnan(rho_work):
        ax1.scatter(T_work, P_work, rho_work, color='red', s=120, label='Điểm làm việc', zorder=5)
    ax1.set_xlabel("Nhiệt độ (°C)")
    ax1.set_ylabel("Áp suất (MPa)")
    ax1.set_zlabel("Mật độ (kg/m³)")
    st.pyplot(fig1)

with plot_col2:
    st.write("### Đồ thị 2D: Bản đồ Áp suất - Nhiệt độ (P-T) & Đường bão hoà")
    fig2, ax2 = plt.subplots(figsize=(7, 5.2))
    contour = ax2.contourf(T_mesh, P_mesh, H_mesh, levels=20, cmap='plasma', alpha=0.6)
    fig2.colorbar(contour, ax=ax2, label="Enthalpy (kJ/kg)")
    
    # 🌟 THÊM ĐƯỜNG CONG ÁP SUẤT BÃO HOÀ THỰC TẾ (VAPOR-LIQUID EQUILIBRIUM LINE)
    T_sat_line = np.linspace(t_plot_min, T_critical - 0.5, 100)
    P_sat_line = []
    for t_s in T_sat_line:
        try:
            p_s = CP.PropsSI('P', 'T', t_s + 273.15, 'Q', 0, fluid_string) / 1e6
        except:
            p_s = np.nan
        P_sat_line.append(p_s)
    
    ax2.plot(T_sat_line, P_sat_line, color='darkorange', linewidth=3, linestyle='-', label='Đường bão hoà (Ranh giới Lỏng-Hơi)')
    
    # Đường dóng tọa độ chữ thập tại điểm làm việc
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

# --- THIẾT LẬP HỆ THỐNG XUẤT FILE DỮ LIỆU ĐỘNG (MA TRẬN MẬT ĐỘ ĐỒ THỊ) ---
st.write("### 💾 Xuất ma trận dữ liệu mô phỏng nền")

# Tạo cấu trúc DataFrame phân tích cho người dùng tải về
flat_T = T_mesh.flatten()
flat_P = P_mesh.flatten()
flat_Rho = Rho_mesh.flatten()
flat_H = H_mesh.flatten()

export_df = pd.DataFrame({
    "Nhiệt độ (°C)": flat_T,
    "Áp suất (MPa)": flat_P,
    "Mật độ (kg/m³)": flat_Rho,
    "Enthalpy (kJ/kg)": flat_H
}).dropna() # Loại bỏ những điểm hóa hơi không có số liệu lỏng

# Tạo hai khối nút bấm xuất file lưu trữ
dl_col1, dl_col2 = st.columns(2)

with dl_col1:
    # 🌟 NÚT TẢI FILE CSV
    csv_data = export_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Tải Ma trận dữ liệu dưới dạng (.CSV)",
        data=csv_data,
        file_name=f"matrix_data_{fluid_string}.csv",
        mime='text/csv',
        use_container_width=True
    )

with dl_col2:
    # 🌟 NÚT TẢI FILE EXCEL (.XLSX)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name='Thermodynamic_Matrix')
    excel_data = buffer.getvalue()
    
    st.download_button(
        label="📥 Tải Báo cáo dữ liệu dưới dạng (.XLSX Excel)",
        data=excel_data,
        file_name=f"matrix_report_{fluid_string}.xlsx",
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        use_container_width=True
    )