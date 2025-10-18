# app.py
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Chatbot Trắc Nghiệm", page_icon="📝", layout="centered")

st.title("🤖 Chatbot Trắc nghiệm")
st.write("Nhập từ khóa để chatbot tìm câu hỏi liên quan và trả lời đáp án đúng.")

# --- Bước 1: Upload hoặc đọc sẵn file Excel ---
uploaded_file = st.file_uploader("📂 Tải lên file Excel câu hỏi trắc nghiệm", type=["xlsx", "xls"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        st.success(f"✅ Đã tải {len(df)} câu hỏi.")
        st.dataframe(df.head())  # Xem trước dữ liệu
    except Exception as e:
        st.error(f"Lỗi khi đọc file: {e}")
        st.stop()
else:
    st.info("⏳ Vui lòng tải file Excel để bắt đầu.")
    st.stop()

# --- Bước 2: Hàm tìm câu hỏi ---
def tim_cau_hoi(keyword, dataframe):
    # chuyển về lowercase để tìm kiếm không phân biệt hoa thường
    keyword_lower = keyword.lower().strip()
    # lọc câu hỏi chứa từ khóa
    ket_qua = dataframe[dataframe['CÂU HỎI'].str.lower().str.contains(keyword_lower, na=False)]
    return ket_qua

# --- Bước 3: Giao diện chat ---
user_input = st.text_input("💬 Nhập từ khóa câu hỏi:")

if st.button("Tìm kiếm") and user_input:
    results = tim_cau_hoi(user_input, df)
    if results.empty:
        st.warning("❌ Không tìm thấy câu hỏi nào phù hợp.")
    else:
        for idx, row in results.iterrows():
            st.markdown(f"**📌 Câu hỏi:** {row['CÂU HỎI']}")
            st.write(f"1️⃣ {row['ĐÁP ÁN 1']}")
            st.write(f"2️⃣ {row['ĐÁP ÁN 2']}")
            st.write(f"3️⃣ {row['ĐÁP ÁN 3']}")
            st.write(f"4️⃣ {row['ĐÁP ÁN 4']}")
            dap_an_dung = int(row['ĐÁP ÁN ĐÚNG'])
            noi_dung_dap_an = row[f'ĐÁP ÁN {dap_an_dung}']
            st.success(f"✅ **Đáp án đúng:** {dap_an_dung} — {noi_dung_dap_an}")
            st.divider()

# --- Gợi ý tìm kiếm ---
with st.expander("📖 Gợi ý sử dụng"):
    st.write("- Nhập từ khóa ngắn gọn (vd: *Việt Nam*, *thủ đô*, *GDP*...)")
    st.write("- Chatbot sẽ trả về tất cả câu hỏi có chứa từ khóa.")
    st.write("- Cột “ĐÁP ÁN ĐÚNG” trong Excel phải là số thứ tự của đáp án (1–4).")
