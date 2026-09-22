import CoolProp.CoolProp as CP
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

# Cấu hình giao diện Streamlit hiển thị tối ưu trên cả điện thoại và máy tính
st.set_page_config(page_title="SFE/SWE Thermophysical Tool", layout="centered")

st.title("🔬 Công Cụ Nhiệt Động Lực Học Dung Môi Siêu Tới Hạn & Chất lỏng áp ")
st.caption(
    "Phát triển bởi TS. Hồ Công Trực"
)

# =========================================================================
# HÀM ĐỘC LẬP: TÍNH TOÁN VÀ HIỂN THỊ BẢNG TRA CỨU (TRÁNH LỖI THỤT LỀ TRONG TRY)
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
            
    # Tạo bảng hiển thị bằng DataFrame pandas an toàn
    display_df = pd.DataFrame()
    display_df["Nồng độ Ethanol"] = col_nong_do
    display_df["Nhiệt độ bắt đầu sôi (Bubble Point)"] = col_bubble
    display_df["Nhiệt độ hóa hơi hoàn toàn (Dew Point)"] = col_dew
    display_df["Hằng số điện môi tại điểm sôi (ε)"] = col_eps
    
    st.dataframe(display_df, use_container_width=True)


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
        critical_T = 304.13 - 273.15
        critical_P = 73.77
    else:
        t_min, t_max, t_default = 25.0, 300.0, 150.0
        p_min, p_max, p_default = 1.0, 150.0, 15.0
        critical_T = 647.096 - 273.15
        critical_P = 220.64

T_input = st.slider("Nhiệt độ vận hành (°C):", min_value=t_min, max_value=t_max, value=t_default)
P_input = st.slider("Áp suất vận hành (bar):", min_value=p_min, max_value=p_max, value=p_default)

T_K = T_input + 273.15
P_Pa = P_input * 1e5

# =========================================================================
# 2. XỬ LÝ TOÁN NHIỆT ĐỘNG TRONG KHỐI TRY/EXCEPT LỚN (ĐÃ CHUẨN HÓA)
# =========================================================================
try:
    if solvent == "Ethanol_Water":
        state = CP.AbstractState("HEOS", "Ethanol&Water")
        state.set_mass_fractions([w_ethanol, w_water])
        state.update(CP.PT_INPUTS, P_Pa, T_K)
        density = state.rhomass()
        viscosity = state.viscosity()
        enthalpy = state.hmass() / 1000
        phase_vn = "Chất lỏng siêu áp nén (Compressed Liquid Mixture)"
    else:
        density = CP.PropsSI("D", "T", T_K, "P", P_Pa, solvent)
        viscosity = CP.PropsSI("V", "T", T_K, "P", P_Pa, solvent)
        enthalpy = CP.PropsSI("H", "T", T_K, "P", P_Pa, solvent) / 1000
        phase_idx = CP.PhaseSI("T", T_K, "P", P_Pa, solvent)
        phase_dict = {
            0: "Lỏng bão hòa", 1: "Hơi bão hòa", 2: "Lỏng (Liquid)",
            3: "Vùng lưỡng pha (Vapor-Liquid)", 4: "Khí (Gas)",
            5: "Siêu tới hạn (Supercritical Fluid)", 6: "Quá nhiệt",
            7: "Cận tới hạn (Subcritical Liquid)"
        }
        phase_vn = phase_dict.get(phase_idx, f"Mã pha: {phase_idx}")
        if solvent == "Water" and T_input > 100 and phase_idx == 2:
            phase_vn = "Cận tới hạn (Subcritical Water)"

    # --- TÍNH HẰNG SỐ ĐIỆN MÔI ---
    epsilon_water_base = 78.54 - 0.360 * (T_input - 25.0)
    epsilon_ethanol_base = 24.30 - 0.130 * (T_input - 25.0)

    if solvent == "Water":
        dielectric_const = max(1.0, epsilon_water_base)
        polarity_desc = "Phân cực mạnh (Hòa tan tốt chất vô cơ/muối/ion)"
    elif solvent == "CarbonDioxide":
        dielectric_const = 1.01 if P_input < 73 else 1.25
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
        st.metric(label="Nhiệt nội năng (Enthalpy)", value=f"{enthalpy:.1f} kJ/kg")
        st.metric(label="Điểm vận hành thực tế", value=f"{T_input}°C, {P_input} bar")

    # =========================================================================
    # 4. VẼ ĐỒ THỊ GIẢN ĐỒ PHA TRỰC QUAN
    # =========================================================================
    st.subheader("📈 Giản đồ pha trực quan")
    fig, ax = plt.subplots(figsize=(6, 4.5))

    if solvent != "Ethanol_Water":
        T_triple = CP.PropsSI(solvent, "Tmin")
        T_crit = CP.PropsSI(solvent, "Tcrit")
        T_space = np.linspace(T_triple, T_crit, 200)
        P_sat = [CP.PropsSI("P", "T", t, "Q", 0, solvent) / 1e5 for t in T_space]
        ax.plot(T_space - 273.15, P_sat, "r-", linewidth=2, label="Đường bão hòa Lỏng - Hơi")
        ax.plot(critical_T, critical_P, "go", markersize=8, label=f"Điểm tới hạn ({critical_T:.1f}°C, {critical_P:.1f} bar)")
        ax.set_title(f"Giản đồ Pha Áp suất - Nhiệt độ của {solvent}", fontsize=11)
    else:
        mix_T_crit = 373.95 - (373.95 - 240.75) * w_ethanol
        mix_P_crit = 220.64 - (220.64 - 61.48) * w_ethanol
        ax.plot(mix_T_crit, mix_P_crit, "go", markersize=9, label=f"Điểm tới hạn hỗn hợp ({mix_T_crit:.1f}°C, {mix_P_crit:.1f} bar)")
        ax.set_title(f"Vị trí vận hành hỗn hợp Ethanol/Nước ({nong_do_percent}%)", fontsize=11)

    ax.plot(T_input, P_input, "bX", markersize=11, label="Điểm vận hành hiện tại")
    ax.axvline(x=T_input, color="gray", linestyle="--", linewidth=0.8)
    ax.axhline(y=P_input, color="gray", linestyle="--", linewidth=0.8)
    ax.set_xlabel("Nhiệt độ T (°C)")
    ax.set_ylabel("Áp suất P (bar)")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper left", fontsize=9)
    
    if solvent == "Ethanol_Water":
        ax.set_xlim(20.0, 400.0)
        ax.set_ylim(1.0, 240.0)
    else:
        ax.set_xlim(t_min, t_max)
        ax.set_ylim(p_min, p_max)

    st.pyplot(fig)

    # Gọi hàm hiển thị bảng tra cứu một cách an toàn
    if solvent == "Ethanol_Water":
        hien_thi_bang_tra_cuu(P_input, P_Pa)

except Exception as e:
    st.error(f"⚠️ Vùng áp suất/nhiệt độ này vượt quá giới hạn bão hòa thực nghiệm. Chi tiết: {e}")
