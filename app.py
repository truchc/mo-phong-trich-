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
# HÀM 1: TÍNH TOÁN VÀ HIỂN THỊ BẢNG TRA CỨU CHO HỖN HỢP
# =========================================================================
def hien_thi_bang_tra_cuu(P_input, P_Pa):
    st.write("---")
    st.subheader(f"📋 Bảng nhiệt độ sôi & hằng số điện môi hỗn hợp tại {P_input} bar")
    st.markdown(
        f"Bảng dưới đây liệt kê điểm sôi và tính chất phân cực (Hằng số điện môi $\\varepsilon$) "
        f"tại các mốc nồng độ khác nhau dưới áp suất không đổi **{P_input} bar**."
    )

    nong_do_list = [1.0, 5.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 95.0, 99.5]
    col_nong_do, col_bubble, col_dew, col_eps = [], [], [], []
    
    try:
        state_vle = CP.AbstractState("HEOS", "Ethanol&Water")
        for pct in nong_do_list:
            w_e_t = pct / 100.0
            w_w_t = 1.0 - w_e_t
            col_nong_do.append(f"{pct}%")
            
            try:
                state_vle.set_mass_fractions([w_e_t, w_w_t])
                state_vle.update(CP.PQ_INPUTS, P_Pa, 0.0)
                T_b = state_vle.T() - 273.15
                col_bubble.append(f"{T_b:.2f} °C")
                
                state_vle.update(CP.PQ_INPUTS, P_Pa, 1.0)
                T_d = state_vle.T() - 273.15
                col_dew.append(f"{T_d:.2f} °C")
                
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
# HÀM 2: VẼ ĐỒ THỊ GIẢN ĐỒ PHA ĐỘC LẬP
# =========================================================================
def ve_gian_do_pha(solvent, T_input, P_input, critical_T, critical_P, t_min, t_max, p_min, p_max, w_ethanol, nong_do_percent):
    fig, ax = plt.subplots(figsize=(6, 4.5))

    if solvent != "Ethanol_Water":
        try:
            T_triple = CP.PropsSI("Tmin", "T", 0, "P", 0, solvent)
            T_crit = CP.PropsSI("Tcrit", "T", 0, "P", 0, solvent)
            T_space = np.linspace(T_triple, T_crit - 0.05, 200)
            P_sat = [CP.PropsSI("P", "T", t, "Q", 0, solvent) / 1e5 for t in T_space]
            ax.plot(T_space - 273.15, P_sat, "r-", linewidth=2, label="Đường bão hòa Lỏng - Hơi")
        except:
            pass
        ax.plot(critical_T, critical_P, "go", markersize=8, label=f"Điểm tới hạn ({critical_T:.1f}°C, {critical_P:.1f} bar)")
        ax.set_title(f"Giản đồ Pha Áp suất - Nhiệt độ của {solvent}", fontsize=11)
    else:
        mix_T_crit = 373.95 - (373.95 - 240.75) * w_ethanol
        mix_P_crit = 220.64 - (220.64 - 61.48) * w_ethanol
        ax.plot(mix_T_crit, mix_P_crit, "go", markersize=9, label=f"Điểm tới hạn hỗn hợp ({mix_T_crit:.1f}°C, {mix_P_crit:.1f} bar)")
        ax.set_title(f"Vị trí vận hành hỗn hợp Ethanol/Nước ({nong_do_percent}%)", fontsize=11)

    ax.plot(T_input, P_input, "bX", markersize=11, label="Điểm vận hành")
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


# =========================================================================
# 3. GIAO DIỆN KHỞI TẠO ĐẦU VÀO
# =========================================================================
st.header("⚙️ Thông số vận hành")

solvent = st.selectbox(
    "Chọn dung môi trích ly:",
    options=["CarbonDioxide", "Water", "Ethanol_Water"],
    format_func=lambda x: "1. CO2 (Trích ly siêu tới hạn - SFE)" if x == "CarbonDioxide"
    else ("2. Nước (Trích ly cận tới hạn - SWE)" if x == "Water" else "3. Hỗn hợp Ethanol & Nước (Chất lỏng siêu áp)"),
)

w_ethanol, w_water, nong_do_percent = 0.0, 1.0, 0.0

if solvent == "Ethanol_Water":
    nong_do_percent = st.slider("Nồng độ Ethanol trong hỗn hợp (% khối lượng):", min_value=0.0, max_value=100.0, value=70.0, step=1.0)
    w_ethanol = nong_do_percent / 100.0
    w_water = 1.0 - w_ethanol
    t_min, t_max, t_default = 20.0, 250.0, 150.0
    p_min, p_max, p_default = 1.0, 150.0, 25.0
    critical_T = 373.95 - (373.95 - 240.75) * w_ethanol
    critical_P = 220.64 - (220.64 - 61.48) * w_ethanol
else:
    if solvent == "CarbonDioxide":
        t_min, t_max, t_default = 20.0, 100.0, 27.98
        p_min, p_max, p_default = 50.0, 500.0, 79.91
        critical_T = 31.06
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

# Khởi tạo các giá trị nhiệt động mặc định phòng ngừa lỗi tính toán
density, viscosity, enthalpy = 0.0, 0.0, 0.0
phase_vn = "Chưa xác định"
dielectric_const, polarity_desc = 1.0, "Chưa xác định"


# =========================================================================
# 4. LUỒNG TÍNH TOÁN VÀ HIỂN THỊ KẾT QUẢ
# =========================================================================
if solvent == "Ethanol_Water":
    try:
        state = CP.AbstractState("HEOS", "Ethanol&Water")
        state.set_mass_fractions([w_ethanol, w_water])
        state.update(CP.PT_INPUTS, P_Pa, T_K)
        density = state.rhomass()
        viscosity = state.viscosity()
        enthalpy = state.hmass() / 1000
        
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
        
        # Tính toán hằng số điện môi gần đúng cho hỗn hợp lỏng
        v_e = (w_ethanol / 0.789) / ((w_ethanol / 0.789) + (w_water / 1.0))
        dielectric_const = max(1.0, v_e * (24.30 - 0.130 * (T_input - 25.0)) + (1.0 - v_e) * (78.54 - 0.360 * (T_input - 25.0)))
    except Exception as e:
        st.error(f"Lỗi tính chất hỗn hợp Ethanol/Nước: {e}")
else:
    try:
        density = CP.PropsSI("D", "T", T_K, "P", P_Pa, solvent)
        viscosity = CP.PropsSI("V", "T", T_K, "P", P_Pa, solvent)
        enthalpy = CP.PropsSI("H", "T", T_K, "P", P_Pa, solvent) / 1000
        
        try:
            phase_str = CP.PhaseSI("T", T_K, "P", P_Pa, solvent)
            phase_dict = {
                "liquid": "Chất lỏng (Liquid)",
                "gas": "Pha khí (Gas)",
                "twophase": "Vùng lưỡng pha Lỏng - Hơi (Two-Phase)",
                "supercritical": "Trạng thái Siêu tới hạn (Supercritical)",
                "supercritical_liquid": "Chất lỏng siêu tới hạn (Supercritical Liquid)",
                "supercritical_gas": "Khí siêu tới hạn (Supercritical Gas)"
            }
            phase_vn = phase_dict.get(phase_str, f"Pha: {phase_str}")
        except:
            phase_vn = "Siêu tới hạn / Cận tới hạn đặc biệt"
            
        if solvent == "Water":
            # Công thức thực nghiệm tính hằng số điện môi của nước theo T
            dielectric_const = 87.74 - 0.4008 * T_input + 9.398e-4 * (T_input**2) - 1.41e-6 * (T_input**3)
            dielectric_const = max(1.0, dielectric_const)
    except Exception as e:
        st.error(f"Lỗi tính toán thuộc tính của {solvent}: {e}")

# Đánh giá độ phân cực dựa trên hằng số điện môi
if dielectric_const > 50:
    polarity_desc = "Phân cực mạnh (Strongly Polar)"
elif 20 <= dielectric_const <= 50:
    polarity_desc = "Phân cực trung bình (Moderately Polar)"
else:
    polarity_desc = "Kém phân cực / Không phân cực (Non-polar / Weakly Polar)"

# Hiển thị kết quả ra màn hình UI
st.write("---")
st.header("📊 Kết quả thuộc tính nhiệt động")

col_res1, col_res2 = st.columns(2)
with col_res1:
    st.metric("Khối lượng riêng (Density)", f"{density:.2f} kg/m³")
    st.metric("Độ nhớt động lực (Viscosity)", f"{viscosity*1e6:.3f} μPa·s")
    st.metric("Enthalpy", f"{enthalpy:.2f} kJ/kg")

with col_res2:
    st.subheader("🔍 Trạng thái Pha & Phân cực")