import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ------------------------
# SETUP GIAO DIỆN
# ------------------------
st.set_page_config(page_title="Chatbot Trắc nghiệm", layout="wide")
st.title("📚 Chatbot Trắc nghiệm - Tìm đáp án theo từ khóa")

# ------------------------
# PHẦN 1: TẢI FILE
# ------------------------
st.header("📤 Bước 1: Tải file câu hỏi (CSV/XLSX)")

uploaded_files = st.file_uploader(
    "Chọn file .csv hoặc .xlsx chứa câu hỏi trắc nghiệm", 
    type=["csv", "xlsx"], 
    accept_multiple_files=True
)

@st.cache_data
def load_data(files):
    dataframes = []
    for file in files:
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            required_cols = ['STT', 'Câu hỏi', 'Đáp án 1', 'Đáp án 2', 'Đáp án 3', 'Đáp án 4', 'Đáp án đúng', 'Trích dẫn nguồn câu hỏi']
            if all(col in df.columns for col in required_cols):
                df = df[required_cols]
                dataframes.append(df)
            else:
                st.error(f"❌ File {file.name} thiếu cột bắt buộc.")
        except Exception as e:
            st.error(f"❌ Lỗi khi đọc file {file.name}: {e}")
    
    if dataframes:
        return pd.concat(dataframes, ignore_index=True)
    return pd.DataFrame()

questions_df = load_data(uploaded_files)

if not questions_df.empty:
    st.success(f"✅ Đã nạp {len(questions_df)} câu hỏi.")
    st.dataframe(questions_df.head())

    # ------------------------
    # PHẦN 2: NHẬP TRUY VẤN
    # ------------------------
    st.header("🔍 Bước 2: Nhập từ khóa hoặc câu hỏi cần tìm")
    user_query = st.text_input("Nhập nội dung cần tìm kiếm")

    if user_query:
        try:
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform(questions_df['Câu hỏi'])
            query_vec = vectorizer.transform([user_query])
            similarity_scores = cosine_similarity(query_vec, tfidf_matrix).flatten()

            best_match_index = similarity_scores.argmax()
            best_score = similarity_scores[best_match_index]

            if best_score < 0.1:
                st.warning("❌ Không tìm thấy câu hỏi phù hợp.")
            else:
                # ------------------------
                # PHẦN 3: TRẢ LỜI
                # ------------------------
                st.header("📖 Kết quả tìm được")

                match = questions_df.iloc[best_match_index]

                st.subheader("📝 Câu hỏi:")
                st.write(match['Câu hỏi'])

                st.subheader("🔘 Các lựa chọn:")
                for i in range(1, 5):
                    st.write(f"{i}. {match[f'Đáp án {i}']}")

                try:
                    correct_index = int(str(match['Đáp án đúng']).strip())
                    correct_content = match[f'Đáp án {correct_index}']
                    st.subheader("✅ Đáp án đúng:")
                    st.success(f"{correct_index}. {correct_content}")
                except:
                    st.error("❌ Không thể xác định đáp án đúng do định dạng lỗi.")

                if pd.notna(match['Trích dẫn nguồn câu hỏi']):
                    st.caption(f"📚 Nguồn: {match['Trích dẫn nguồn câu hỏi']}")

                st.caption(f"🔍 Độ tương đồng: {best_score:.2f}")
        except Exception as e:
            st.error(f"❌ Lỗi xử lý truy vấn: {e}")
else:
    st.info("👆 Vui lòng tải lên ít nhất 1 file hợp lệ để bắt đầu.")
