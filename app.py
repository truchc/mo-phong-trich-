import CoolProp.CoolProp as CP
import numpy as np
import pandas as pd
import plotly.graph_objects as go
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
# HÀM 2: VẼ GIẢN ĐỒ PHA TƯƠNG TÁC (PLOTLY) - ĐÃ KHẮC PHỤC LỖI HIỂN THỊ
# =========================================================================
def ve_gian_do_pha(solvent, T_input, P_input, critical_T, critical_P, t_min, t_max, p_min, p_max, w_ethanol, nong_do_percent):
    fig = go.Figure()

    if solvent != "Ethanol_Water":
        try:
            # Lấy giới hạn nhiệt độ chuẩn của chất từ CoolProp
            T_triple = CP.PropsSI("Tmin", "T", 0, "P", 0, solvent)
            T_crit = CP.PropsSI("Tcrit", "T", 0, "P", 0, solvent)
            
            # Quét an toàn: Tránh điểm kỳ dị tại chính xác Tmin và Tcrit
            T_space = np.linspace(T_triple + 0.1, T_crit - 0.1, 150)
            T_degC = T_space - 273.15
            P_sat_bar = []
            
            for t in T_space:
                try:
                    p_pa = CP.PropsSI("P", "T", t, "Q", 0, solvent)
                    P_sat_bar.append(p_pa / 1e5)
                except:
                    P_sat_bar.append(None)
            
            # Vẽ đường bão hòa lỏng - hơi
            fig.add_trace(go.Scatter(
                x=T_degC, y=P_sat_bar,
                mode='lines',
                name='Đường bão hòa Lỏng - Hơi',
                line=dict(color='red', width=3)
            ))
            
        except Exception as e:
            st.warning(f"Không thể dựng đường bão hòa tự động: {e}")
            
        # Thêm điểm tới hạn cố định của chất
        fig.add_trace(go.Scatter(
            x=[critical_T], y=[critical_P],
            mode='markers+text',
            name='Điểm tới hạn',
            text=[f" Critical Point ({critical_T:.1f}°C, {critical_P:.1f} bar)"],
            textposition="top right",
            marker=dict(color='green', size=12, symbol='circle')
        ))
    else:
        # Đối với hỗn hợp Ethanol_Water
        mix_T_crit = 373.95 - (373.95 - 240.75) * w_ethanol
        mix_P_crit = 220.64 - (220.64 - 61.48) * w_ethanol
        fig.add_trace(go.Scatter(
            x=[mix_T_crit], y=[mix_P_crit],
            mode='markers+text',
            name='Điểm tới hạn hỗn hợp',
            text=[f" Mixture Critical Point ({mix_T_crit:.1f}°C, {mix_P_crit:.1f} bar)"],
            textposition="top right",
            marker=dict(color='green', size=12, symbol='circle')
        ))

    # Thêm điểm vận hành thực tế mà người dùng đang chọn trên thanh trượt
    fig.add_trace(go.Scatter(
        x=[T_input], y=[P_input],
        mode='markers+text',
        name='Điểm vận hành',
        text=[" Vị trí đang chọn"],
        textposition="bottom center",
        marker=dict(color='blue', size=14, symbol='x')
    ))

    # Cấu hình Layout cho đồ thị thích ứng lưới nét đứt
    fig.update_layout(
        title=f"Giản đồ Pha Áp suất - Nhiệt độ ({solvent if solvent != 'Ethanol_Water' else 'Hỗn hợp'})",
        xaxis_title="Nhiệt độ T (°C)",
        yaxis_title="Áp suất P (bar)",
        xaxis=dict(range=[t_min, t_max], gridcolor='rgba(200,200,200,0.4)', showgrid=True),
        yaxis=dict(range=[p_min, p_max], gridcolor='rgba(200,200,200,0.4)', showgrid=True),
        template="plotly_white",
        hovermode="closest",
        height=500
    )

    # Đưa đường nét đứt định vị điểm vận hành vào đồ thị
    fig.add_vline(x=T_input, line_width=1, line_dash="dash", line_color="gray")
    fig.add_hline(y=P_input, line_width=1, line_dash="dash", line_color="gray")

    st.plotly_chart(fig, use_container_width=True)


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
    t_min, t_max, t_default = 20.0, 400.0, 150.0
    p_min, p_max, p_default = 1.0, 240.0, 25.0
    critical_T = 373.95 - (373.95 - 240.75) * w_ethanol
    critical_P = 220.64 - (220.64 - 61.48) * w_ethanol
else:
    if solvent == "CarbonDioxide":
        t_min, t_max, t_default = -20.0, 100.0, 35.0
        p_min, p_max, p_default = 1.0, 300.0, 80.0
        critical_T = 31.06
        critical_P = 73.77
    else:
        t_min, t_max, t_default = 25.0, 400.0, 150.0
        p_min, p_max, p_default = 1.0, 250.0, 15.0
        critical_T = 373.95
        critical_P = 220.64

T_input = st.slider("Nhiệt độ vận hành (°C):", min_value=float(t_min), max_value=float(t_max), value=float(t_default))
P_input = st.slider("Áp suất vận hành (bar):", min_value=float(p_min), max_value=float(p_max), value=float(p_default))

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