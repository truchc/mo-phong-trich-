import CoolProp.CoolProp as CP
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

# Cấu hình giao diện Streamlit hiển thị tối ưu trên cả điện thoại và máy tính
st.set_page_config(page_title="SFE/SWE Thermophysical Tool", layout="centered")

st.title("🔬 Công Cụ Nhiệt Động Lực Học Dung Môi Siêu Tới Hạn & Chất lỏng áp suất")
st.caption("Phát triển bởi TS. Hồ Công Trực")


# =========================================================================
# HÀM ĐỘC LẬP: TÍNH TOÁN VÀ HIỂN THỊ BẢNG TRA CỨU
# =========================================================================
def hien_thi_bang_tra_cuu(P_input, P_Pa):
    st.write("---")
    st.subheader(f"📋 Bảng nhiệt độ sôi & hằng số điện môi hỗn hợp tại {P_input} bar")
    st.markdown(
        f"Bảng dưới đây liệt kê điểm sôi và tính chất phân cực (Hằng số điện môi $\\varepsilon$) "
        f"tại các mốc nồng độ khác nhau dưới áp suất không đổi **{P_input} bar**."
    )

    nong_do_list = [1.0, 5.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 95.0, 99.5]
    
    col_nong_do = []
    col_bubble = []
    col_dew = []
    col_eps = []
    
    try:
        state_vle = CP.AbstractState("HEOS", "Ethanol&Water")
        for pct in nong_do_list:
            w_e_t = pct / 100.0
            w_w_t = 1.0 - w_e_t
            col_nong_do.append(f"{pct}%")
            
            try:
                state_vle.set_mass_fractions([w_e_t, w_w_t])
                
                # 1. Tính điểm sôi (Bubble point)
                state_vle.update(CP.PQ_INPUTS, P_Pa, 0.0)
                T_b = state_vle.T() - 273.15
                col_bubble.append(f"{T_b:.2f} °C")
                
                # 2. Tính điểm sương (Dew point)
                state_vle.update(CP.PQ_INPUTS, P_Pa, 1.0)
                T_d = state_vle.T() - 273.15
                col_dew.append(f"{T_d:.2f} °C")
                
                # 3. Tính hằng số điện môi tại điểm sôi
                v_e_t = (w_e_t / 0.789) / ((w_e_t / 0.789) + (w_w_t / 1.0))
                eps_mix_table = max(1.0, v_e_t * (24.30 - 0.130 * (T_b - 25.0)) + (1.0 - v_e_t) * (78.54 - 0.360 * (T_b - 25.0)))
                col_eps.append(f"{eps_mix_table:.2f}")
                
            except:
                col_bubble.append("Vượt điểm tới hạn")
                col_dew.append("Vượt điểm tới hạn")
                col_eps.append("N/A")
                
        display_df = pd.DataFrame()
        display_df["Nồng độ Ethanol"] = col_nong_do
        display_df["Nhiệt độ bắt đầu sôi (Bubble Point)"] = col_bubble
        display_df["Nhiệt độ hóa hơi hoàn toàn (Dew Point)"] = col_dew
        display_df["Hằng số điện môi tại điểm sôi (ε)"] = col_eps
        
        st.dataframe(display_df, use_container_width=True)
    except Exception as e:
        st.error(f"Lỗi tạo bảng tra cứu hỗn hợp: {e}")


# =========================================================================
# 1. THANH ĐIỀU KHIỂN & NHẬP THÔNG SỐ VẬN HÀNH
# =========================================================================
st.header("⚙️ Thông số vận hành")

solvent = st.selectbox(
    "Chọn dung môi trích ly:",
    options=["CarbonDioxide", "Water", "Ethanol_Water"],
    format_func=lambda x: "1. CO2 (Trích ly siêu tới hạn - SFE)"
    if x == "CarbonDioxide"
    else (
        "2. Nước (Trích ly cận tới hạn - SWE)"
        if x == "Water"
        else "3. Hỗn hợp Ethanol & Nước (Chất lỏng siêu áp)"
    ),
)

if solvent == "Ethanol_Water":
    nong_do_percent = st.slider(
        "Nồng độ Ethanol trong hỗn hợp (% khối lượng):",
        min_value=0.0,
        max_value=100.0,
        value=70.0,
        step=1.0,
    )
    w_ethanol = nong_do_percent / 100.0
    w_water = 1.0 - w_ethanol
    t_min, t_max, t_default = 20.0, 250.0, 150.0
    p_min, p_max, p_default = 1.0, 150.0, 25.0
else:
    if solvent == "CarbonDioxide":
        t_min, t_max, t_default = 20.0, 100.0, 45.0
        p_min, p_max, p_default = 50.0, 500.0, 250.0
        critical_T = 31.06  # Giá trị chuẩn NIST cho CO2
        critical_P = 73.77
    else:
        t_min, t_max, t_default = 25.0, 370.0, 150.0
        p_min, p_max, p_default = 1.0, 250.0, 15.0
        critical_T = 373.95
        critical_P = 220.64

T_input = st.slider("Nhiệt độ vận hành (°C):", min_value=t_min, max_value=t_max, value=t_default)
P_input = st.slider("Áp suất vận hành (bar):", min_value=p_min, max_value=p_max, value=p_default)

T_K = T_input + 273.15
P_Pa = P_input * 1e5

# =========================================================================
# 2. XỬ LÝ TOÁN NHIỆT ĐỘNG
# =========================================================================
try:
    if solvent == "Ethanol_Water":
        state = CP.AbstractState("HEOS", "Ethanol&Water")
        state.set_mass_fractions([w_ethanol, w_water])
        state.update(CP.PT_INPUTS, P_Pa, T_K)
        density = state.rhomass()
        viscosity = state.viscosity()
        enthalpy = state.hmass() / 1000
        
        # Xác định pha cho hỗn hợp dựa trên bộ tạo cập nhật trạng thái thực tế
        try:
            # Lấy thông số pha từ cấu trúc trừu tượng của hỗn hợp nhị phân
            p_idx = state.phase()
            phase_dict = {
                CP.iphase_liquid: "Chất lỏng dưới hạn / Áp suất cao (Compressed Liquid Mixture)",
                CP.iphase_gas: "Pha khí (Gas Mixture)",
                CP.iphase_twophase: "Vùng lưỡng pha Lỏng - Hơi (VLE - Two Phase)",
                CP.iphase_supercritical: "Hỗn hợp trạng thái Siêu tới hạn (Supercritical Mixture)",
                CP.iphase_supercritical_liquid: "Chất lỏng siêu tới hạn (Supercritical Liquid)",
                CP.iphase_supercritical_gas: "Khí siêu tới hạn (Supercritical Gas)"
            }
            phase_vn = phase_dict.get(p_idx, "Không xác định rõ pha")
        except:
            phase_vn = "Chất lỏng hỗn hợp nén áp suất"
    else:
        density = CP.PropsSI("D", "T", T_K, "P", P_Pa, solvent)
        viscosity = CP.PropsSI("V", "T", T_K, "P", P_Pa, solvent)
        enthalpy = CP.PropsSI("H", "T", T_K, "P", P_Pa, solvent) / 1000
        
        # SỬA LỖI CHÍNH: Mã pha trả về từ PhaseSI là dạng chuỗi string trong phiên bản CoolProp mới, không phải số nguyên!
        phase_str = CP.PhaseSI("T", T_K, "P", P_Pa, solvent)
        phase_dict = {
            "liquid": "Chất lỏng (Liquid)",
            "supercritical_fluid": "Siêu tới hạn (Supercritical Fluid)",
            "supercritical_liquid": "Chất lỏng siêu tới hạn (Supercritical Liquid)",
            "supercritical_gas": "Khí siêu tới hạn (Supercritical Gas)",
            "gas": "Pha Khí (Gas)",
            "twophase": "Vùng lưỡng pha (Vapor-Liquid Region)",
            "subcritical": "Cận tới hạn (Subcritical)"
        }
        phase_vn = phase_dict.get(phase_str, f"Mã pha: {phase_str}")
        
        if solvent == "Water" and T_input >= 100 and T_input < critical_T and "liquid" in phase_str.lower():
            phase_vn = "Nước cận tới hạn (Subcritical Hot Water - SWE)"

    # --- TÍNH HẰNG SỐ ĐIỆN MÔI CHUẨN XÁC ---
    epsilon_water_base = 78.54 - 0.360 * (T_input - 25.0)
    epsilon_ethanol_base = 24.30 - 0.130 * (T_input - 25.0)

    if solvent == "Water":
        dielectric_const = max(1.0, epsilon_water_base)
        polarity_desc = "Phân cực mạnh (Hòa tan tốt chất vô cơ/muối/ion)"
    elif solvent == "CarbonDioxide":
        # SỬA LỖI CHÍNH: Tính hằng số điện môi của CO2 theo phương trình thực nghiệm bậc hai dựa trên khối lượng riêng (density)
        # Công thức chuẩn khoa học: epsilon = 1 + A*rho + B*rho^2 (rho tính bằng g/cm3)
        rho_g_cm3 = density / 1000.0
        dielectric_const = 1.0 + 0.423 * rho_g_cm3 + 0.052 * (rho_g_cm3 ** 2)
        polarity_desc = "Không phân cực (Hòa tan tốt lipid, chất béo, tinh dầu)"
    else:
        v_eth = (w_ethanol / 0.789) / ((w_ethanol / 0.789) + (w_water / 1.0))
        dielectric_const = max(1.0, v_eth * epsilon_ethanol_base + (1.0 - v_eth) * epsilon_water_base)
        if dielectric_const > 50:
            polarity_desc = "Phân cực mạnh (Hệ dung môi chứa nhiều nước)"
        elif dielectric_const > 35:
            polarity_desc = "Phân cực trung bình (Vùng tối ưu trích hoạt chất hữu cơ)"
        else:
            polarity_desc = "Phân cực yếu (Hệ dung môi chứa nhiều cồn)"

    # =========================================================================
    # 3. HIỂN THỊ KẾT QUẢ ĐẸP MẮT
    # =========================================================================
    st.subheader("📊 Kết quả tính toán trạng thái")
    st.info(f"**Trạng thái pha:** {phase_vn}")
    st.warning(f"⚡ **Tính chất phân cực:** Hằng số điện môi $\\varepsilon$ = {dielectric_const:.2f} | {polarity_desc}")

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Khối lượng riêng (Density)", value=f"{density:.1f} kg/m³")
        st.metric(label="Độ nhớt (Viscosity)", value=f"{viscosity * 1e6:.3f} x 10⁻⁶ Pa·s")
    with col2:
        st.metric(label="Enthalpy hỗn hợp", value=f"{enthalpy:.1f} kJ/kg")
        st.metric(label="Điểm vận hành thực tế", value=f"{T_input}°C, {P_input} bar")

    # =========================================================================
    # 4. VẼ ĐỒ THỊ GIẢN ĐỒ PHA TRỰC QUAN
    # =========================================================================
    st.subheader("📈 Giản đồ pha trực quan")
    fig, ax = plt.subplots(figsize=(6, 4.5))

    if solvent != "Ethanol_Water":
        # SỬA LỖI CHÍNH: Thay đổi cách lấy giá trị Tmin tránh lỗi sập thư viện
        T_triple = CP.PropsSI("Tmin", "T", 0, "P", 0, solvent)
        T_crit = CP.PropsSI("Tcrit", "T", 0, "P", 0, solvent)
        T_space = np.linspace(T_triple, T_crit - 0.05, 200)
        P_sat = [CP.PropsSI("P", "T", t, "Q", 0, solvent) / 1e5 for t in T_space]
        
        ax.plot(T_space - 273.15, P_sat, "r-", linewidth=2, label="Đường bão hòa Lỏng - Hơi")