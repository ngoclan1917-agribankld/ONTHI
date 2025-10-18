# app.py
import streamlit as st
import pandas as pd

# ⚙️ Cấu hình giao diện
st.set_page_config(page_title="Chatbot Trắc Nghiệm", page_icon="📝", layout="wide")

st.title("🤖 Chatbot Trắc nghiệm")
st.markdown("📂 **Trái:** Quản lý file câu hỏi — 💬 **Phải:** Tra cứu đáp án đúng.")

# Khởi tạo session lưu file
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}  # {filename: DataFrame}

# 🧭 Bố cục 2 cột
col1, col2 = st.columns([1, 2])

# ========================
# 📂 CỘT TRÁI: QUẢN LÝ FILE
# ========================
with col1:
    st.subheader("📂 Tải & Quản lý file")

    uploaded_files = st.file_uploader(
        "Tải lên một hoặc nhiều file Excel",
        type=["xlsx", "xls"],
        accept_multiple_files=True
    )

    def read_file_from_header(file):
        """
        Tự động xác định dòng tiêu đề chứa 'CÂU HỎI'
        và đọc dữ liệu từ dòng đó trở xuống.
        """
        df_raw = pd.read_excel(file, header=None)
        header_row_idx = None
        for i, row in df_raw.iterrows():
            if any(str(cell).strip().upper() == "CÂU HỎI" for cell in row):
                header_row_idx = i
                break

        if header_row_idx is None:
            raise ValueError("❌ Không tìm thấy dòng tiêu đề có cột 'CÂU HỎI'.")

        # Đọc lại file từ dòng header tìm được
        df = pd.read_excel(file, header=header_row_idx)
        return df

    # ✅ Đọc dữ liệu từ file mới tải
    if uploaded_files:
        for file in uploaded_files:
            if file.name not in st.session_state.uploaded_files:
                try:
                    df = read_file_from_header(file)
                    st.session_state.uploaded_files[file.name] = df
                except Exception as e:
                    st.error(f"Lỗi đọc file {file.name}: {e}")

    # 📋 Danh sách file đã tải
    if st.session_state.uploaded_files:
        st.markdown("### 📄 Danh sách file đã tải:")
        for filename in list(st.session_state.uploaded_files.keys()):
            cols = st.columns([4, 1])
            with cols[0]:
                st.write(f"📎 {filename} ({len(st.session_state.uploaded_files[filename])} câu)")
            with cols[1]:
                if st.button("🗑️ Xóa", key=f"delete_{filename}"):
                    del st.session_state.uploaded_files[filename]
                    st.experimental_rerun()
    else:
        st.info("⚠️ Chưa có file nào được tải lên.")

# ==========================
# 💬 CỘT PHẢI: TRA CỨU CHATBOT
# ==========================
# Kẻ đường phân cách dọc
st.markdown(
    """
    <hr style="border: none; border-top: 2px solid #ccc; margin-top: -1rem; margin-bottom: 1rem;">
    """,
    unsafe_allow_html=True
)

with col2:
    st.subheader("💬 Chatbot tra cứu đáp án")

    if st.session_state.uploaded_files:
        combined_df = pd.concat(st.session_state.uploaded_files.values(), ignore_index=True)

        # Chuẩn hóa tên cột (tránh lỗi chữ hoa/thường)
        combined_df.columns = [str(c).strip().upper() for c in combined_df.columns]

        user_input = st.text_input("🔎 Nhập từ khóa câu hỏi:")

        def tim_cau_hoi(keyword, dataframe):
            keyword_lower = keyword.lower().strip()
            return dataframe[dataframe['CÂU HỎI'].str.lower().str.contains(keyword_lower, na=False)]

        if st.button("Tìm kiếm") and user_input:
            results = tim_cau_hoi(user_input, combined_df)
            if results.empty:
                st.warning("❌ Không tìm thấy câu hỏi nào phù hợp.")
            else:
                for _, row in results.iterrows():
                    dap_an_dung = int(row['ĐÁP ÁN ĐÚNG'])
                    noi_dung_dap_an = row[f'ĐÁP ÁN {dap_an_dung}']
                    st.markdown(f"**📌 Câu hỏi:** {row['CÂU HỎI']}")
                    st.success(f"✅ **Đáp án đúng:** {noi_dung_dap_an}")
                    st.divider()
    else:
        st.info("📌 Vui lòng tải ít nhất một file ở cột bên trái trước khi tra cứu.")

# ==========================
# 📘 HƯỚNG DẪN
# ==========================
with st.expander("📘 Hướng dẫn sử dụng"):
    st.write("- Có thể tải lên nhiều file Excel cùng lúc.")
    st.write("- Nếu file có các dòng dư ở đầu → chương trình sẽ tự xác định dòng có cột 'CÂU HỎI' để đọc đúng dữ liệu.")
    st.write("- Có thể 🗑️ xóa từng file không cần.")
    st.write("- Chatbot sẽ tìm kiếm trong tất cả các file còn lại.")
    st.write("- Cột bắt buộc: STT | CÂU HỎI | ĐÁP ÁN 1–4 | ĐÁP ÁN ĐÚNG.")
