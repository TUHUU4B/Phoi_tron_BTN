import streamlit as st
import numpy as np
import pandas as pd
import pulp
import matplotlib.pyplot as plt


# --- Gradation limits from TCVN 13567-1:2022, Bảng 1 (người dùng có thể chỉnh lại) ---
# Lưu ý: Các giá trị dưới đây chỉ là ví dụ/giá trị tạm, bạn nên đối chiếu và chỉnh
# lại cho khớp hoàn toàn với tiêu chuẩn TCVN 13567-1:2022, Bảng 1.


def get_default_limits():
    # Mỗi phần tử: {loai_BTN: {cỡ sàng (mm): (Cận dưới, Cận trên)}}
    # Chỉ cần khai báo các cỡ sàng thực sự có trong Bảng 1 cho từng loại BTN;
    # ứng dụng sẽ tự động ẩn các cỡ sàng không liên quan.
    return {
        "BTN C25": {
            31.5: (100, 100),
            25: (90, 100),
            19: (75, 90),
            16: (65, 83),
            12.5: (57, 74),
            9.5: (45, 65),
            4.75: (24, 52),
            2.36: (16, 42),
            1.18: (12, 33),
            0.6: (8, 24),
            0.3: (5, 17),
            0.15: (3, 13),
            0.075: (3, 7),
        },
        "BTN C19": {
            25: (100, 100),
            19: (90, 100),
            16: (78, 92),
            12.5: (62, 78),
            9.5: (50, 72),
            4.75: (26, 56),
            2.36: (18, 46),
            1.18: (12, 33),
            0.6: (8, 24),
            0.3: (5, 17),
            0.15: (3, 13),
            0.075: (3, 7),
        },
        "BTN C16": {
            19: (100, 100),
            16: (90, 100),
            12.5: (76, 92),
            9.5: (60, 80),
            4.75: (34, 62),
            2.36: (22, 48),
            1.18: (13, 36),
            0.6: (9, 24),
            0.3: (7, 18),
            0.15: (5, 14),
            0.075: (4, 8),
        },
        "BTN C12,5": {
            16: (100, 100),
            12.5: (92, 100),
            9.5: (68, 85),
            4.75: (38, 70),
            2.36: (24, 50),
            1.18: (15, 38),
            0.6: (10, 30),
            0.3: (7, 20),
            0.15: (4, 15),
            0.075: (4, 8),
        },
        "BTN C9,5": {
            12.5: (90, 100),
            9.5: (80, 100),
            4.75: (45, 75),
            2.36: (30, 58),
            1.18: (20, 44),
            0.6: (13, 35),
            0.3: (9, 27),
            0.15: (6, 18),
            0.075: (4, 8),
        },
        "BTN C4,75": {
            9.5: (100, 100),
            4.75: (95, 100),
            2.36: (55, 75),
            1.18: (35, 55),
            0.6: (24, 45),
            0.3: (14, 30),
            0.15: (7, 18),
            0.075: (5, 10),
        },
    }


def solve_blend(aggregate_df: pd.DataFrame, limits_df: pd.DataFrame):
    """
    aggregate_df: rows = sieve sizes, columns = each aggregate (% passing)
    limits_df: rows = sieve sizes, columns = ['Lower', 'Upper']
    Returns: weights (Series) and resulting gradation (Series) or (None, None) if infeasible.
    """
    sieves = limits_df.index.tolist()
    agg_names = aggregate_df.columns.tolist()

    # Define LP
    prob = pulp.LpProblem("AggregateBlending", pulp.LpMinimize)

    # Tỷ lệ mỗi cốt liệu
    x_vars = {name: pulp.LpVariable(name, lowBound=0) for name in agg_names}

    # Biến độ lệch so với giá trị giữa (Lower + Upper)/2 tại mỗi cỡ sàng
    d_plus = {s: pulp.LpVariable(f"d_plus_{s}", lowBound=0) for s in sieves}
    d_minus = {s: pulp.LpVariable(f"d_minus_{s}", lowBound=0) for s in sieves}

    # Mục tiêu: tối thiểu tổng độ lệch tuyệt đối so với giá trị giữa dải cho mọi sàng
    prob += pulp.lpSum(d_plus[s] + d_minus[s] for s in sieves), "MinimizeDeviation"

    # Sum of proportions = 1
    prob += pulp.lpSum(x_vars.values()) == 1, "SumOfFractions"

    # Gradation constraints
    for sieve in sieves:
        lower = limits_df.loc[sieve, "Lower"]
        upper = limits_df.loc[sieve, "Upper"]
        mid = (lower + upper) / 2.0
        blend_expr = pulp.lpSum(
            aggregate_df.loc[sieve, agg] * x_vars[agg] for agg in agg_names
        )
        prob += blend_expr >= lower, f"Lower_{sieve}"
        prob += blend_expr <= upper, f"Upper_{sieve}"

        # Ràng buộc độ lệch tuyệt đối: blend - mid = d_plus - d_minus
        prob += blend_expr - mid == d_plus[sieve] - d_minus[sieve], f"Deviation_{sieve}"

    # Solve
    status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
    if pulp.LpStatus[status] != "Optimal":
        return None, None

    weights = pd.Series({name: x_vars[name].value() for name in agg_names})
    blend_gradation = (aggregate_df * weights).sum(axis=1)
    return weights, blend_gradation


def format_vn_number(x, digits: int = 2) -> str:
    """Định dạng số theo quy cách Việt Nam: phần nghìn dùng '.', phần thập phân dùng ','."""
    try:
        value = float(x)
    except (TypeError, ValueError):
        return str(x)
    fmt = f"{{:,.{digits}f}}".format(value)
    # Mặc định Python dùng ',' cho nghìn, '.' cho thập phân → đảo lại
    return fmt.replace(",", "X").replace(".", ",").replace("X", ".")


def format_vn_sieve_label(x) -> str:
    """Định dạng nhãn cỡ sàng kiểu Việt Nam (31,5; 4,75; 0,075...)."""
    try:
        return str(float(x)).replace(".", ",")
    except (TypeError, ValueError):
        return str(x)


def get_gradation_classification(mix_type: str, blend_gradation: pd.Series) -> dict:
    """
    Xác định loại cấp phối (thô/mịn) theo TCVN 13567-1:2022, Bảng 2.
    
    Args:
        mix_type: Loại BTN (ví dụ: "BTN C9,5", "BTN C12,5", ...)
        blend_gradation: Series với index là cỡ sàng (mm), giá trị là % lọt qua sàng
    
    Returns:
        dict với keys: 'control_sieve', 'passing_value', 'gradation_type', 'threshold'
    """
    # Bảng 2: Cỡ sàng khống chế và ngưỡng phân loại
    classification_rules = {
        "BTN C9,5": {"control_sieve": 2.36, "threshold": 45.0},
        "BTN C12,5": {"control_sieve": 2.36, "threshold": 40.0},
        "BTN C16": {"control_sieve": 2.36, "threshold": 38.0},
        "BTN C19": {"control_sieve": 4.75, "threshold": 45.0},
        "BTN C25": {"control_sieve": 4.75, "threshold": 40.0},
    }
    
    if mix_type not in classification_rules:
        return None
    
    rule = classification_rules[mix_type]
    control_sieve = rule["control_sieve"]
    threshold = rule["threshold"]
    
    # Lấy giá trị % lọt qua cỡ sàng khống chế
    if control_sieve not in blend_gradation.index:
        return None
    
    passing_value = blend_gradation.loc[control_sieve]
    
    # Xác định loại cấp phối
    if passing_value < threshold:
        gradation_type = "Cấp phối thô"
    else:
        gradation_type = "Cấp phối mịn"
    
    return {
        "control_sieve": control_sieve,
        "passing_value": passing_value,
        "gradation_type": gradation_type,
        "threshold": threshold,
    }


def main():
    st.set_page_config(page_title="Thiết kế phối trộn cốt liệu BTN", layout="wide")
    st.title("Thiết kế phối trộn cốt liệu BTN theo TCVN 13567-1:2022")

    st.markdown(
        "Ứng dụng này giúp tính **tỷ lệ phối trộn cốt liệu** sao cho đường cong hạt "
        "của hỗn hợp nằm **trong giới hạn yêu cầu** theo TCVN 13567-1:2022 (Bảng 1). "
        "Bạn có thể chỉnh sửa lại giới hạn hoặc số liệu thành phần cốt liệu nếu cần."
    )

    limits_data = get_default_limits()

    # --- Sidebar: chọn loại BTN và số lượng cốt liệu ---
    with st.sidebar:
        # Logo và thông tin công ty
        try:
            st.image("logo.png", use_container_width=True)
        except FileNotFoundError:
            st.warning("Không tìm thấy file logo.png")

        st.markdown(
            "<div style='text-align: center; margin-top: 10px; margin-bottom: 10px;'>"
            "<h4>CÔNG TY TỨ HỮU</h4>"
            "<p style='font-size: 0.9em; color: #666;'>Tác giả: MR Tuấn - 0946135156</p>"
            "</div>",
            unsafe_allow_html=True,
        )

        st.header("Thông số thiết kế")
        mix_type = st.selectbox("Chọn loại BTN", list(limits_data.keys()))
        n_agg = st.number_input("Số lượng cốt liệu tham gia phối trộn", 2, 6, 3, 1)

    # --- Bảng giới hạn yêu cầu ---
    st.subheader("Giới hạn cấp phối yêu cầu")
    mix_limits_dict = limits_data[mix_type]
    # Chỉ dùng các cỡ sàng được khai báo cho loại BTN đang chọn
    sieves_for_mix = sorted(mix_limits_dict.keys(), reverse=True)
    limits_df = pd.DataFrame(
        [(s, *mix_limits_dict[s]) for s in sieves_for_mix],
        columns=["Sieve (mm)", "Lower", "Upper"],
    ).set_index("Sieve (mm)")

    # Hiển thị giới hạn theo định dạng số Việt Nam + nhãn cỡ sàng kiểu Việt Nam
    limits_display = limits_df.copy()
    limits_display["Lower"] = limits_display["Lower"].apply(
        lambda v: format_vn_number(v, 2)
    )
    limits_display["Upper"] = limits_display["Upper"].apply(
        lambda v: format_vn_number(v, 2)
    )
    limits_display.index = [format_vn_sieve_label(s) for s in sieves_for_mix]
    limits_display.index.name = "Cỡ sàng (mm)"

    edited_limits_df = st.data_editor(
        limits_display,
        num_rows="fixed",
        use_container_width=True,
        # Key phụ thuộc vào loại BTN để Streamlit tạo bảng mới,
        # tránh giữ lại các cỡ sàng của loại trước đó.
        key=f"limits_editor_{mix_type}",
    )

    # --- Bảng cấp phối từng cốt liệu ---
    st.subheader("Cấp phối từng loại cốt liệu (% lọt sàng tích lũy)")

    default_agg_cols = {
        f"Cốt liệu {i+1}": [0.0] * len(sieves_for_mix) for i in range(n_agg)
    }
    agg_df = pd.DataFrame(
        default_agg_cols,
        index=pd.Index(sieves_for_mix, name="Sieve (mm)"),
    )
    # Hiển thị theo định dạng Việt Nam (ban đầu là 0,00) + nhãn cỡ sàng kiểu Việt Nam
    agg_display = agg_df.applymap(lambda v: format_vn_number(v, 2))
    agg_display.index = [format_vn_sieve_label(s) for s in sieves_for_mix]
    agg_display.index.name = "Cỡ sàng (mm)"

    st.markdown(
        "Nhập **% lọt sàng tích lũy** cho từng cỡ sàng và từng cốt liệu. "
        "Ví dụ: đá dăm, cát, bột khoáng,..."
    )

    edited_agg_df = st.data_editor(
        agg_display,
        use_container_width=True,
        key=f"agg_editor_{mix_type}",
    )

    # Điều khiển nút tính để sau khi bấm, người dùng vẫn chỉnh sửa được tỷ lệ
    if "calc_clicked" not in st.session_state:
        st.session_state["calc_clicked"] = False

    if st.button("Tính phối trộn", type="primary"):
        st.session_state["calc_clicked"] = True

    if st.session_state["calc_clicked"]:
        # Kiểm tra dữ liệu
        try:
            # Chuyển chuỗi dạng Việt Nam (12,5) -> float
            cleaned_agg = edited_agg_df.applymap(
                lambda v: str(v).replace(".", "").replace(",", ".")
            )
            cleaned_limits = edited_limits_df.applymap(
                lambda v: str(v).replace(".", "").replace(",", ".")
            )
            # Phục hồi lại index cỡ sàng dạng số cho tính toán
            cleaned_agg.index = sieves_for_mix
            cleaned_limits.index = sieves_for_mix
            aggregate_df = cleaned_agg.astype(float)
            limits_clean = cleaned_limits.astype(float)
        except ValueError:
            st.error("Vui lòng nhập số hợp lệ cho tất cả ô trong bảng.")
            return

        # Giữ thứ tự cỡ sàng theo sieves_for_mix (từ lớn đến nhỏ)
        aggregate_df = aggregate_df.loc[sieves_for_mix]
        limits_clean = limits_clean.loc[sieves_for_mix]

        weights, blend_gradation = solve_blend(aggregate_df, limits_clean)

        if weights is None:
            st.error(
                "Không tìm được phương án phối trộn thỏa mãn tất cả giới hạn. "
                "Hãy kiểm tra lại giới hạn hoặc cấp phối từng cốt liệu."
            )
            return

        st.success("Đã tìm được tỷ lệ phối trộn thỏa mãn yêu cầu giới hạn.")

        # Hiển thị và cho phép điều chỉnh tỷ lệ phối trộn
        st.subheader("Tỷ lệ phối trộn tối ưu (có thể chỉnh sửa)")
        # Làm tròn đến 0,1% để hiển thị
        percent_init = (weights * 100).round(1)
        percent_df = percent_init.to_frame("Tỷ lệ (%)").T

        st.markdown(
            "Bạn có thể **chỉnh sửa lại tỷ lệ (%)** cho từng cốt liệu bên dưới. "
            "Chương trình sẽ tự động **chuẩn hóa** tổng bằng 100% và cập nhật lại đường cong cấp phối."
        )

        # Hiển thị theo định dạng số Việt Nam trong bảng chỉnh sửa
        percent_display = percent_df.applymap(lambda v: format_vn_number(v, 1))
        edited_percent_df = st.data_editor(
            percent_display,
            num_rows="fixed",
            use_container_width=True,
            key=f"weights_editor_{mix_type}",
        )

        # Lấy tỷ lệ sau khi người dùng chỉnh sửa (dạng Việt Nam) và chuyển về float
        try:
            edited_percent_clean = edited_percent_df.applymap(
                lambda v: str(v).replace(".", "").replace(",", ".")
            )
            edited_percent_series = edited_percent_clean.iloc[0].astype(float)
        except Exception:
            st.error("Tỷ lệ phối trộn phải là số. Vui lòng kiểm tra lại các ô trong bảng.")
            return

        # Chuẩn hóa tổng về 100%
        edited_percent_series = edited_percent_series.clip(lower=0)
        total = edited_percent_series.sum()
        if total == 0:
            st.error("Tổng tỷ lệ các cốt liệu đang bằng 0. Vui lòng nhập lại.")
            return
        edited_percent_series = edited_percent_series * (100.0 / total)

        # Lưu lại dạng phần trăm đã chuẩn hóa (làm tròn 0,1%) để hiển thị đẹp, kèm màu sắc
        percent_df_norm = edited_percent_series.round(1).to_frame("Tỷ lệ (%)").T
        styled_percent = (
            percent_df_norm.style.format(lambda v: format_vn_number(v, 1))
            .set_properties(**{"color": "#1f77b4", "font-weight": "bold"})
        )
        st.dataframe(styled_percent, use_container_width=True)

        # Hiển thị tổng tỷ lệ (luôn 100%) để người dùng tiện theo dõi
        st.markdown(
            f"**Tổng tỷ lệ:** <span style='color:#d62728;font-weight:bold;'>{format_vn_number(percent_df_norm.values.sum(), 1)} %</span>",
            unsafe_allow_html=True,
        )

        # Chuyển về dạng tỷ lệ (1.0 = 100%) để tính toán
        edited_weights = edited_percent_series / 100.0
        # Đường cong hỗn hợp tương ứng với tỷ lệ đã chỉnh, làm tròn đến 0,1%
        blend_gradation = (aggregate_df * edited_weights).sum(axis=1).round(1)

        # Phân loại cấp phối theo TCVN 13567-1:2022, Bảng 2
        classification = get_gradation_classification(mix_type, blend_gradation)
        if classification:
            st.subheader("Phân loại cấp phối (TCVN 13567-1:2022, Bảng 2)")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(
                    f"**Cỡ sàng khống chế:** {format_vn_sieve_label(classification['control_sieve'])} mm"
                )
                st.markdown(
                    f"**Lượng lọt qua cỡ sàng khống chế:** {format_vn_number(classification['passing_value'], 2)} %"
                )
            with col2:
                st.markdown(
                    f"**Ngưỡng phân loại:** {format_vn_number(classification['threshold'], 2)} %"
                )
                gradation_type = classification['gradation_type']
                if gradation_type == "Cấp phối thô":
                    color = "#ff7f0e"  # cam
                else:
                    color = "#2ca02c"  # xanh lá
                st.markdown(
                    f"**Loại cấp phối:** <span style='color:{color};font-weight:bold;font-size:1.1em;'>{gradation_type}</span>",
                    unsafe_allow_html=True,
                )
            
            # Hiển thị bảng tóm tắt
            summary_data = {
                "Loại BTN": [mix_type],
                "Cỡ sàng khống chế (mm)": [format_vn_sieve_label(classification['control_sieve'])],
                "Lượng lọt qua sàng khống chế (%)": [format_vn_number(classification['passing_value'], 2)],
                "Ngưỡng phân loại (%)": [format_vn_number(classification['threshold'], 2)],
                "Loại cấp phối": [gradation_type],
            }
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

        # Bảng so sánh đường cong hạt
        st.subheader("Đường cong cấp phối hỗn hợp so với giới hạn")
        result_df = pd.DataFrame(
            {
                "Lower": limits_clean["Lower"],
                "Upper": limits_clean["Upper"],
                "Hỗn hợp": blend_gradation,  # Đã làm tròn đến 0,1% ở trên
            },
            index=limits_clean.index,
        )
        # Bảng hiển thị với định dạng số Việt Nam
        result_display = result_df.copy()
        result_display["Lower"] = result_display["Lower"].apply(lambda v: format_vn_number(v, 2))
        result_display["Upper"] = result_display["Upper"].apply(lambda v: format_vn_number(v, 2))
        result_display["Hỗn hợp"] = result_display["Hỗn hợp"].apply(lambda v: format_vn_number(v, 1))  # 0,1%
        # Đổi nhãn cỡ sàng sang dạng 31,5; 4,75; 0,075...
        vn_index = [format_vn_sieve_label(i) for i in result_display.index]
        result_display.index = vn_index
        result_display.index.name = "Cỡ sàng (mm)"
        st.dataframe(result_display, use_container_width=True)

        # Biểu đồ thành phần hạt theo trục logarit (giống mẫu)
        st.subheader("Biểu đồ thành phần hạt bê tông nhựa")
        sieves_mm = np.array(limits_clean.index.tolist(), dtype=float)
        lower_vals = limits_clean["Lower"].values
        upper_vals = limits_clean["Upper"].values
        blend_vals = blend_gradation.values

        # Thiết lập style và màu sắc hiện đại, dễ nhìn
        plt.style.use("seaborn-v0_8-whitegrid")
        fig, ax = plt.subplots(figsize=(7, 4))

        # Trục x logarit, đảo chiều từ lớn (trái) sang nhỏ (phải)
        ax.set_xscale("log")
        ax.invert_xaxis()

        # Vẽ đường bao và đường cấp phối hỗn hợp với màu sắc phân biệt rõ
        ax.plot(
            sieves_mm,
            blend_vals,
            "-o",
            color="#1f77b4",  # xanh dương
            linewidth=2.2,
            markersize=5,
            label="Kết quả phối trộn",
        )
        ax.plot(
            sieves_mm,
            upper_vals,
            "--",
            color="#ff7f0e",  # cam
            marker="s",
            markersize=4,
            label="Đường bao cận trên",
        )
        ax.plot(
            sieves_mm,
            lower_vals,
            "--",
            color="#2ca02c",  # xanh lá
            marker="d",
            markersize=4,
            label="Đường bao cận dưới",
        )

        ax.set_xlabel("Cỡ hạt theo logarit (mm)")
        ax.set_ylabel("Lượng lọt qua sàng (%)")
        ax.set_title(
            "BIỂU ĐỒ THÀNH PHẦN HẠT BÊ TÔNG NHỰA",
            fontsize=12,
            fontweight="bold",
        )
        ax.set_ylim(0, 100)
        ax.grid(True, which="both", linestyle=":", linewidth=0.6, alpha=0.7)
        ax.legend(loc="upper right", frameon=True, facecolor="white", framealpha=0.9)

        st.pyplot(fig)

        st.caption(
            "Lưu ý: Nếu có sai khác nhỏ so với bảng TCVN 13567-1:2022, bạn có thể chỉnh sửa lại giới hạn "
            "trong bảng trên cho phù hợp với tài liệu thiết kế thực tế."
        )


if __name__ == "__main__":
    main()


