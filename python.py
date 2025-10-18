# app.py
import streamlit as st
import pandas as pd
import io

# ⚙️ Cấu hình giao diện
st.set_page_config(page_title="Chatbot Trắc Nghiệm", page_icon="📝", layout="wide")

st.title("🤖 Chatbot Trắc nghiệm")
st.markdown("📂 **Trái:** Quản lý file câu hỏi — 💬 **Phải:** Tra cứu đáp án đúng.")

# Khởi tạo session lưu danh sách file đã tải
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}  # dict: {tên file: DataFrame}

# 🧭 Chia bố cục 2 cột có đường kẻ phân cách
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

    # ✅ Đọc dữ liệu từ các file mới tải
    if uploaded_files:
        for file in uploaded_files:
            if file.name not in st.session_state.uploaded_files:
                try:
                    df = pd.read_excel(file)
                    st.session_state.uploaded_files[file.name] = df
                except Exception as e:
                    st.error(f"❌ Lỗi đọc file {file.name}: {e}")

    # 📋 Danh sách file đã tải
    if st.session_state.uploaded_files:
        st.markdown("### 📄 Danh sách file đã tải:")
        for filename in list(st.session_state.uploaded_files.keys()):
            cols = st.columns([4, 1])
            with cols[0]:
                st.write(f"📎 {filename}")
            with cols[1]:
                # 🧹 Nút xóa file
                if st.button("🗑️ Xóa", key=f"delete_{filename}"):
                    del st.session_state.uploaded_files[filename]
                    st.experimental_rerun()
    else:
        st.info("⚠️ Chưa có file nào được tải lên.")

# ==========================
# 💬 CỘT PHẢI: TRA CỨU CHATBOT
# ==========================
# Kẻ đường phân cách dọc giữa 2 cột
st.markdown(
    """
    <hr style="border: none; border-top: 2px solid #ccc; margin-top: -1rem; margin-bottom: 1rem;">
    """,
    unsafe_allow_html=True
)

with col2:
    st.subheader("💬 Chatbot tra cứu đáp án")

    # Gộp dữ liệu từ tất cả các file đã tải
    if st.session_state.uploaded_files:
        combined_df = pd.concat(st.session_state.uploaded_files.values(), ignore_index=True)

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
    st.write("- Có thể tải lên **nhiều file Excel** cùng lúc.")
    st.write("- Sau khi tải, có thể 🗑️ **xóa** từng file không cần.")
    st.write("- Chatbot sẽ tìm kiếm trong **tất cả các file còn lại**.")
    st.write("- File Excel cần có cột: STT | CÂU HỎI | ĐÁP ÁN 1–4 | ĐÁP ÁN ĐÚNG.")
    st.write("- “ĐÁP ÁN ĐÚNG” là số thứ tự từ 1 đến 4.")
