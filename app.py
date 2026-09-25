import streamlit as st
import CoolProp.CoolProp as CP
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Thiết lập tiêu đề trang web
st.set_page_config(page_title="Mô phỏng Nhiệt động lực học", layout="wide")
st.title(" MÔ PHỎNG THÔNG SỐ NHIỆT ĐỘNG LỰC HỌC")
st.subheader("Hệ thống: Nước cận tới hạn (Subcritical Water)")

# --- THANH ĐIỀU KHIỂN (SIDEBAR) ---
st.sidebar.header("Cấu hình dải mô phỏng")
t_min, t_max = st.sidebar.slider("Dải nhiệt độ (°C)", 100.0, 374.0, (100.0, 374.0))
p_min, p_max = st.sidebar.slider("Dải áp suất (MPa)", 0.1, 22.0, (0.1, 22.0))

# --- HÀM TÍNH TOÁN NHIỆT ĐỘNG ---
def calculate_properties(T_celsius, P_mpa):
    T_kelvin = T_celsius + 273.15
    P_pascal = P_mpa * 1e6
    try:
        phase = CP.PhaseSI('T', T_kelvin, 'P', P_pascal, 'Water')
        rho = CP.PropsSI('D', 'T', T_kelvin, 'P', P_pascal, 'Water')
        h = CP.PropsSI('H', 'T', T_kelvin, 'P', P_pascal, 'Water') / 1000
        s = CP.PropsSI('S', 'T', T_kelvin, 'P', P_pascal, 'Water') / 1000
        
        if phase in [CP.iphase_liquid, CP.iphase_supercritical_liquid]:
            status = "Cận tới hạn (Lỏng)"
        else:
            status = "Hơi/Quá nhiệt"
            rho, h, s = np.nan, np.nan, np.nan
        return rho, h, s, status
    except:
        return np.nan, np.nan, np.nan, "Lỗi dữ liệu"

# --- TẠO DỮ LIỆU VÀ ĐỒ THỊ ---
T_range = np.linspace(t_min, t_max, 30)
P_range = np.linspace(p_min, p_max, 30)
T_mesh, P_mesh = np.meshgrid(T_range, P_range)

Rho_mesh = np.zeros_like(T_mesh)
H_mesh = np.zeros_like(T_mesh)

# Quét ma trận
for i in range(P_mesh.shape[0]):
    for j in range(P_mesh.shape[1]):
        rho, h, _, status = calculate_properties(T_mesh[i, j], P_mesh[i, j])
        Rho_mesh[i, j] = rho
        H_mesh[i, j] = h

# --- HIỂN THỊ KẾT QUẢ LÊN WEB ---
col1, col2 = st.columns(2)

with col1:
    st.write("### Đồ thị 3D: Biến thiên Mật độ (kg/m³)")
    fig1 = plt.figure(figsize=(6, 5))
    ax1 = fig1.add_subplot(1, 1, 1, projection='3d')
    surf1 = ax1.plot_surface(T_mesh, P_mesh, Rho_mesh, cmap='viridis_r', edgecolor='none', alpha=0.9)
    ax1.set_xlabel("Nhiệt độ (°C)")
    ax1.set_ylabel("Áp suất (MPa)")
    ax1.set_zlabel("Mật độ")
    fig1.colorbar(surf1, ax=ax1, shrink=0.5, aspect=10)
    st.pyplot(fig1)

with col2:
    st.write("### Bản đồ 2D: Trường nhiệt Enthalpy (kJ/kg)")
    fig2, ax2 = plt.subplots(figsize=(6, 4.3))
    contour = ax2.contourf(T_mesh, P_mesh, H_mesh, levels=20, cmap='plasma')
    ax2.set_xlabel("Nhiệt độ (°C)")
    ax2.set_ylabel("Áp suất (MPa)")
    fig2.colorbar(contour, ax=ax2)
    st.pyplot(fig2)

# Hiển thị bảng tra cứu mẫu nhanh
st.write("### Bảng dữ liệu tra cứu nhanh tại một số điểm mẫu")
samples = [
    (100, 0.1), (150, 1.0), (250, 5.0), (300, 15.0), (350, 22.0)
]
df_list = []
for t, p in samples:
    rho, h, s, stat = calculate_properties(t, p)
    df_list.append({"Nhiệt độ (°C)": t, "Áp suất (MPa)": p, "Mật độ (kg/m³)": rho, "Enthalpy (kJ/kg)": h, "Trạng thái": stat})

st.dataframe(pd.DataFrame(df_list), use_container_width=True)