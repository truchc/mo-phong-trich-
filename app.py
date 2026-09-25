import CoolProp.CoolProp as CP
import numpy as np
import matplotlib.pyplot as plt
from tabulate import tabulate

class SubcriticalWaterCalculator:
    def __init__(self):
        self.fluid = "Water"
        
    def calculate_properties(self, T_celsius, P_mpa):
        """
        Tính toán thông số nhiệt động của nước tại T (°C) và P (MPa).
        Tự động xác định xem có đạt trạng thái lỏng/cận tới hạn hay không.
        """
        T_kelvin = T_celsius + 273.15
        P_pascal = P_mpa * 1e6  # Chuyển MPa sang Pascal
        
        try:
            # Lấy trạng thái pha
            phase = CP.PhaseSI('T', T_kelvin, 'P', P_pascal, self.fluid)
            
            # Tính toán thông số
            rho = CP.PropsSI('D', 'T', T_kelvin, 'P', P_pascal, self.fluid)      # Mật độ (kg/m3)
            h = CP.PropsSI('H', 'T', T_kelvin, 'P', P_pascal, self.fluid) / 1000  # Enthalpy (kJ/kg)
            s = CP.PropsSI('S', 'T', T_kelvin, 'P', P_pascal, self.fluid) / 1000  # Entropy (kJ/kg.K)
            
            # Gắn nhãn phân loại trạng thái để người dùng dễ theo dõi
            status = "Cận tới hạn (Lỏng)" if phase in [CP.iphase_liquid, CP.iphase_supercritical_liquid] else "Hơi/Quá nhiệt"
            
            return {
                "T": T_celsius, "P": P_mpa, "Rho": rho, "H": h, "S": s, "Phase": phase, "Status": status
            }
        except Exception as e:
            # Trả về N/A nếu vượt quá ranh giới toán học của thư viện
            return {"T": T_celsius, "P": P_mpa, "Rho": np.nan, "H": np.nan, "S": np.nan, "Phase": "Unknown", "Status": "Lỗi dữ liệu"}

    def generate_mesh_data(self, T_range, P_range):
        """Tạo lưới dữ liệu để vẽ đồ thị"""
        T_mesh, P_mesh = np.meshgrid(T_range, P_range)
        Rho_mesh = np.zeros_like(T_mesh)
        H_mesh = np.zeros_like(T_mesh)
        
        for i in range(P_mesh.shape[0]):
            for j in range(P_mesh.shape[1]):
                res = self.calculate_properties(T_mesh[i, j], P_mesh[i, j])
                # Nếu là hơi quá nhiệt, ta gán np.nan để đồ thị chỉ tập trung hiển thị vùng chất lỏng cận tới hạn
                if res["Status"] == "Cận tới hạn (Lỏng)":
                    Rho_mesh[i, j] = res["Rho"]
                    H_mesh[i, j] = res["H"]
                else:
                    Rho_mesh[i, j] = np.nan
                    H_mesh[i, j] = np.nan
                    
        return T_mesh, P_mesh, Rho_mesh, H_mesh

# --- CHẠY CHƯƠNG TRÌNH VÀ VẼ ĐỒ THỊ ---
if __name__ == "__main__":
    calc = SubcriticalWaterCalculator()
    
    # 1. In một số điểm dữ liệu mẫu ra bảng để kiểm tra nhanh
    sample_points = [
        (100, 0.1),  # Điểm sôi chuẩn
        (150, 1.0),  # Lỏng nén
        (250, 5.0),  # Cận tới hạn điển hình
        (300, 15.0), # Cận tới hạn áp suất cao
        (350, 22.0), # Sát điểm tới hạn (374°C, 22.06 MPa)
        (350, 0.1)   # Vùng này sẽ hóa hơi (Áp suất quá thấp)
    ]
    
    table_data = []
    for T, P in sample_points:
        res = calc.calculate_properties(T, P)
        table_data.append([
            f"{res['T']} °C", f"{res['P']} MPa", 
            f"{res['Rho']:.2f}" if not np.isnan(res['Rho']) else "N/A",
            f"{res['H']:.2f}" if not np.isnan(res['H']) else "N/A",
            f"{res['S']:.2f}" if not np.isnan(res['S']) else "N/A",
            res['Status']
        ])
        
    headers = ["Nhiệt độ", "Áp suất", "Mật độ (kg/m³)", "Enthalpy (kJ/kg)", "Entropy (kJ/kg·K)", "Đánh giá trạng thái"]
    print("\n=== BẢNG TRA CỨU MẪU NƯỚC CẬN TỚI HẠN ===")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

    # 2. Tạo ma trận dữ liệu quét toàn bộ dải (100-374°C, 0.1-22 MPa)
    T_range = np.linspace(100, 374, 50)
    P_range = np.linspace(0.1, 22.0, 50)
    T_mesh, P_mesh, Rho_mesh, H_mesh = calc.generate_mesh_data(T_range, P_range)

    # 3. Vẽ đồ thị biểu diễn trực quan
    fig = plt.figure(figsize=(14, 6))

    # Đồ thị 1: Biến thiên Mật độ (Density) dạng 3D bề mặt
    ax1 = fig.add_subplot(1, 2, 1, projection='3d')
    surf1 = ax1.plot_surface(T_mesh, P_mesh, Rho_mesh, cmap='viridis_r', edgecolor='none', alpha=0.9)
    ax1.set_title("Mật độ của Nước cận tới hạn ($\lambda$)", fontsize=12, pad=10)
    ax1.set_xlabel("Nhiệt độ (°C)")
    ax1.set_ylabel("Áp suất (MPa)")
    ax1.set_zlabel("Mật độ (kg/m³)")
    fig.colorbar(surf1, ax=ax1, shrink=0.5, aspect=10, label="kg/m³")

    # Đồ thị 2: Bản đồ đường đẳng nhiệt/đẳng áp của Enthalpy (2D Contour)
    ax2 = fig.add_subplot(1, 2, 2)
    contour = ax2.contourf(T_mesh, P_mesh, H_mesh, levels=20, cmap='plasma')
    ax2.set_title("Bản đồ Nhiệt động Enthalpy ($h$)", fontsize=12)
    ax2.set_xlabel("Nhiệt độ (°C)")
    ax2.set_ylabel("Áp suất (MPa)")
    cbar = fig.colorbar(contour, ax=ax2, label="Enthalpy (kJ/kg)")
    
    # Vẽ thêm đường ranh giới tượng trưng (vùng màu trắng trống là vùng nước đã bị hóa hơi)
    ax2.text(120, 2, "Vùng Hơi\n(Bị loại bỏ)", color='red', fontsize=10, weight='bold')
    ax2.text(250, 15, "Vùng Chất lỏng\nCận tới hạn", color='white', fontsize=10, weight='bold')

    plt.tight_layout()
    print("\n[Hệ thống] Đang hiển thị đồ thị mô phỏng...")
    plt.show()