import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Tra cứu câu hỏi từ file Excel", layout="wide")

# ==========================
# Khởi tạo session state
# ==========================
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}

# ==========================
# Hàm đọc dữ liệu từ file Excel
# ==========================
def read_excel_skip_header(file_data):
    df = pd.read_excel(file_data, header=None)
    header_row = None
    for i in range(len(df)):
        if df.iloc[i].notna().sum() > 1:
            header_row = i
            break
    if header_row is not None:
        df = pd.read_excel(file_data, header=header_row)
    else:
        df = pd.read_excel(file_data)
    return df

# ==========================
# Giao diện tải file (Cột trái)
# ==========================
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📁 Chọn file Excel (có thể nhiều)")
    uploaded = st.file_uploader(
        " ",  # Không hiển thị label
        type=["xlsx", "xls"],
        accept_multiple_files=True
    )

    # Lưu file vào session_state
    if uploaded:
        for file in uploaded:
            st.session_state.uploaded_files[file.name] = file

    # Hiển thị danh sách file đã tải + nút xóa
    for filename in list(st.session_state.uploaded_files.keys()):
        file_col1, file_col2 = st.columns([5, 1])
        file_col1.write(filename)
        if file_col2.button("❌", key=f"delete_{filename}"):
            del st.session_state.uploaded_files[filename]

    if st.session_state.uploaded_files:
        if st.button("🧹 Xóa tất cả file đã tải"):
            st.session_state.uploaded_files.clear()

# ==========================
# Giao diện tra cứu (Cột phải)
# ==========================
with col2:
    st.subheader("🔍 Tra cứu câu hỏi")
    keyword = st.text_input("Nhập từ khóa và nhấn Enter hoặc bấm Tìm kiếm", "")
    search_btn = st.button("Tìm kiếm")

    st.markdown("<div style='margin-top: 60px;'></div>", unsafe_allow_html=True)  # Tăng khoảng cách gấp 3

    if (search_btn or keyword) and st.session_state.uploaded_files:
        results = []
        for filename, file in st.session_state.uploaded_files.items():
            try:
                df = read_excel_skip_header(BytesIO(file.getvalue()))
                for col in df.columns:
                    matches = df[df[col].astype(str).str.contains(keyword, case=False, na=False)]
                    if not matches.empty:
                        results.append((filename, matches))
            except Exception as e:
                st.error(f"Lỗi khi đọc file {filename}: {e}")

        if results:
            for filename, matches in results:
                st.write(f"📌 **Kết quả trong file:** `{filename}`")
                st.dataframe(matches, use_container_width=True)
        else:
            st.warning("❌ Không tìm thấy kết quả nào.")
    elif (search_btn or keyword) and not st.session_state.uploaded_files:
        st.warning("⚠️ Vui lòng tải lên ít nhất một file Excel trước khi tra cứu.")
