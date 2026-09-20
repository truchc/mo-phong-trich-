import CoolProp.CoolProp as CP
import matplotlib.pyplot as plt
import numpy as np
import streamlit as stream

# Cấu hình giao diện Streamlit hiển thị tối ưu trên cả điện thoại và máy tính
stream.set_page_config(page_title="SFE/SWE Thermophysical Tool", layout="centered")

stream.title("🔬 Công Cụ Nhiệt Động Lực Học Dung Môi Tới Hạn")
stream.caption(
    "Phát triển bởi TS. Chuyên gia Công nghệ Thực phẩm & Thiết bị Hóa học"
)

# 1. THANH ĐIỀU KHIỂN (SIDEBAR / TOP PANEL TRÊN ĐIỆN THOẠI)
stream.header("⚙️ Thông số vận hành")

# Lựa chọn dung môi
solvent = stream.selectbox(
    "Chọn dung môi trích ly:",
    options=["CarbonDioxide", "Water"],
    format_func=lambda x: "CO2 (Trích ly siêu tới hạn - SFE)"
    if x == "CarbonDioxide"
    else "Nước (Trích ly cận tới hạn - SWE)",
)

# Định nghĩa giới hạn kéo-thả dựa trên loại dung môi
if solvent == "CarbonDioxide":
    t_min, t_max, t_default = 20.0, 100.0, 45.0
    p_min, p_max, p_default = 50.0, 500.0, 250.0
    critical_T = 304.13 - 273.15  # ~30.98 °C
    critical_P = 73.77  # bar
else:  # Water
    t_min, t_max, t_default = 25.0, 300.0, 150.0
    p_min, p_max, p_default = 1.0, 150.0, 15.0
    critical_T = 647.096 - 273.15  # ~373.95 °C
    critical_P = 220.64  # bar

# Thanh kéo chọn Nhiệt độ và Áp suất
T_input = stream.slider(
    "Nhiệt độ vận hành (°C):", min_value=t_min, max_value=t_max, value=t_default
)
P_input = stream.slider(
    "Áp suất vận hành (bar):", min_value=p_min, max_value=p_max, value=p_default
)

# 2. XỬ LÝ DỮ LIỆU NHIỆT ĐỘNG
T_K = T_input + 273.15
P_Pa = P_input * 1e5

try:
    # Tính toán thông số bằng CoolProp
    density = CP.PropsSI("D", "T", T_K, "P", P_Pa, solvent)
    viscosity = CP.PropsSI("V", "T", T_K, "P", P_Pa, solvent)
    enthalpy = CP.PropsSI("H", "T", T_K, "P", P_Pa, solvent) / 1000  # kJ/kg
    phase_idx = CP.PhaseSI("T", T_K, "P", P_Pa, solvent)

    # Từ điển dịch trạng thái pha sang tiếng Việt cho trực quan
    phase_dict = {
        0: "Lỏng bão hòa",
        1: "Hơi bão hòa",
        2: "Lỏng (Liquid)",
        3: "Vùng lưỡng pha (Vapor-Liquid)",
        4: "Khí (Gas)",
        5: "Siêu tới hạn (Supercritical Fluid)",
        6: "Quá nhiệt",
        7: "Cận tới hạn (Subcritical Liquid)",
    }
    phase_vn = phase_dict.get(phase_idx, f"Mã pha: {phase_idx}")
    if solvent == "Water" and T_input > 100 and phase_idx == 2:
        phase_vn = "Cận tới hạn (Subcritical Water)"

    # 3. HIỂN THỊ KẾT QUẢ SỐ LIỆU ĐẸP MẮT (METRICS)
    stream.subheader("📊 Kết quả tính toán trạng thái")
    stream.info(f"**Trạng thái pha:** {phase_vn}")

    col1, col2 = stream.columns(2)
    with col1:
        stream.metric(
            label="Khối lượng riêng (Density)", value=f"{density:.1f} kg/m³"
        )
        stream.metric(
            label="Độ nhớt (Viscosity)", value=f"{viscosity * 1e6:.3f} x 10⁻⁶ Pa·s"
        )
    with col2:
        stream.metric(label="Nhiệt nội năng (Enthalpy)", value=f"{enthalpy:.1f} kJ/kg")
        stream.metric(
            label="Điểm vận hành thực tế", value=f"{T_input}°C, {P_input} bar"
        )

    # 4. THUẬT TOÁN VẼ GIẢN ĐỒ PHA TỰ ĐỘNG
    stream.subheader("📈 Giản đồ pha trực quan")

    fig, ax = plt.subplots(figsize=(6, 4.5))

    # Vẽ đường bão hòa (Saturation line) từ điểm Ba (Triple point) đến Điểm tới hạn (Critical point)
    T_triple = CP.PropsSI(solvent, "Tmin")
    T_crit = CP.PropsSI(solvent, "Tcrit")
    T_space = np.linspace(T_triple, T_crit, 200)
    P_sat = [CP.PropsSI("P", "T", t, "Q", 0, solvent) / 1e5 for t in T_space]

    T_space_C = T_space - 273.15

    # Vẽ đường ranh giới pha
    ax.plot(
        T_space_C,
        P_sat,
        "r-",
        linewidth=2,
        label="Đường bão hòa Lỏng - Hơi",
    )

    # Đánh dấu điểm tới hạn (Critical Point)
    ax.plot(
        critical_T,
        critical_P,
        "go",
        markersize=8,
        label=f"Điểm tới hạn ({critical_T:.1f}°C, {critical_P:.1f} bar)",
    )

    # Đánh dấu ĐIỂM VẬN HÀNH HIỆN TẠI (Khách hàng đang kéo thanh chọn)
    ax.plot(
        T_input, P_input, "bX", markersize=11, label="Điểm vận hành của bạn"
    )

    # Kẻ đường dóng nét đứt trợ giúp trực quan
    ax.axvline(x=T_input, color="gray", linestyle="--", linewidth=0.8)
    ax.axhline(y=P_input, color="gray", linestyle="--", linewidth=0.8)

    # Trang trí đồ thị
    ax.set_title(f"Giản đồ Pha Áp suất - Nhiệt độ của {solvent}", fontsize=11)
    ax.set_xlabel("Nhiệt độ T (°C)", fontsize=10)
    ax.set_ylabel("Áp suất P (bar)", fontsize=10)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper left", fontsize=9)

    # Giới hạn khung đồ thị bao quanh điểm vận hành cho dễ nhìn
    ax.set_xlim(t_min, t_max)
    ax.set_ylim(p_min, p_max)

    # Đưa đồ thị hiển thị lên giao diện Web Streamlit
    stream.pyplot(fig)

except Exception as e:
    stream.error(f"Không thể mô phỏng tại vùng thông số này. Lỗi: {e}")
