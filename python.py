# app.py
import streamlit as st
import pandas as pd

# ⚙️ Cấu hình giao diện
st.set_page_config(page_title="Chatbot Trắc Nghiệm", page_icon="📝", layout="wide")

st.title("🤖 Chatbot Trắc nghiệm")
st.markdown("Giao diện gồm **2 cột**: 📂 bên trái tải file câu hỏi – 💬 bên phải nhập từ khóa để tìm đáp án.")

# 🧭 Chia bố cục 2 cột: Trái - Phải
col1, col2 = st.columns([1, 2])  # [tỉ lệ cột trái, cột phải]

# --- 📂 CỘT TRÁI: TẢI FILE EXCEL ---
with col1:
    st.subheader("📂 Tải file câu hỏi")
    uploaded_file = st.file_uploader("Chọn file Excel", type=["xlsx", "xls"])

    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            st.success(f"✅ Đã tải thành công {len(df)} câu hỏi.")
        except Exception as e:
            st.error(f"Lỗi khi đọc file: {e}")
            st.stop()
    else:
        st.info("⏳ Vui lòng tải file Excel để bắt đầu.")
        df = None

# --- 💬 CỘT PHẢI: CHATBOT TÌM CÂU HỎI ---
with col2:
    st.subheader("💬 Chatbot tra cứu đáp án")

    if df is not None:
        user_input = st.text_input("🔎 Nhập từ khóa câu hỏi:")

        def tim_cau_hoi(keyword, dataframe):
            keyword_lower = keyword.lower().strip()
            return dataframe[dataframe['CÂU HỎI'].str.lower().str.contains(keyword_lower, na=False)]

        if st.button("Tìm kiếm") and user_input:
            results = tim_cau_hoi(user_input, df)
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
        st.info("📌 Vui lòng tải file ở cột bên trái trước khi tra cứu.")

# --- 📖 HƯỚNG DẪN ---
with st.expander("📘 Hướng dẫn sử dụng"):
    st.write("- Tải file Excel có cấu trúc: STT | CÂU HỎI | ĐÁP ÁN 1–4 | ĐÁP ÁN ĐÚNG (là số thứ tự 1–4).")
    st.write("- Sau khi tải file → nhập từ khóa → bot trả về Câu hỏi & Đáp án đúng.")
    st.write("- Giao diện chia 2 vùng: Trái để tải file, Phải để tìm kiếm.")
