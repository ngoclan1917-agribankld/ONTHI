# app.py
import streamlit as st
import pandas as pd

# Cấu hình giao diện
st.set_page_config(page_title="Chatbot Trắc Nghiệm", page_icon="📝", layout="centered")

st.title("🤖 Chatbot Trắc nghiệm")
st.write("Nhập từ khóa để chatbot tìm câu hỏi liên quan và trả về đáp án đúng.")

# --- Bước 1: Upload file Excel ---
uploaded_file = st.file_uploader("📂 Tải lên file Excel câu hỏi trắc nghiệm", type=["xlsx", "xls"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        st.success(f"✅ Đã tải thành công {len(df)} câu hỏi.")
    except Exception as e:
        st.error(f"Lỗi khi đọc file: {e}")
        st.stop()
else:
    st.info("⏳ Vui lòng tải file Excel để bắt đầu.")
    st.stop()

# --- Bước 2: Hàm tìm câu hỏi theo từ khóa ---
def tim_cau_hoi(keyword, dataframe):
    keyword_lower = keyword.lower().strip()
    ket_qua = dataframe[dataframe['CÂU HỎI'].str.lower().str.contains(keyword_lower, na=False)]
    return ket_qua

# --- Bước 3: Giao diện chat ---
user_input = st.text_input("💬 Nhập từ khóa câu hỏi:")

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

# --- Gợi ý sử dụng ---
with st.expander("📖 Hướng dẫn sử dụng"):
    st.write("- Nhập từ khóa ngắn gọn (vd: *Việt Nam*, *thủ đô*...).")
    st.write("- Chatbot sẽ trả về Câu hỏi và Đáp án đúng tương ứng.")
    st.write("- Cột “ĐÁP ÁN ĐÚNG” trong Excel phải là số thứ tự (1–4).")
