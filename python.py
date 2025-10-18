import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---- Đọc và chuẩn hóa dữ liệu ----
@st.cache_data
def load_questions(files):
    all_data = []

    for file in files:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            st.warning(f"❌ File không hợp lệ: {file.name}")
            continue

        required_columns = ['STT', 'Câu hỏi', 'Đáp án 1', 'Đáp án 2', 'Đáp án 3', 'Đáp án 4', 'Đáp án đúng', 'Trích dẫn nguồn câu hỏi']
        if all(col in df.columns for col in required_columns):
            all_data.append(df[required_columns])
        else:
            st.warning(f"⚠️ File {file.name} thiếu cột cần thiết.")
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    else:
        return pd.DataFrame(columns=required_columns)

# ---- Tìm kiếm câu hỏi gần giống ----
def search_best_match(df, query):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(df['Câu hỏi'])
    query_vec = vectorizer.transform([query])

    similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
    best_idx = similarities.argmax()
    best_score = similarities[best_idx]

    if best_score < 0.1:
        return None, 0.0
    return df.iloc[best_idx], best_score

# ---- Streamlit UI ----
st.set_page_config(page_title="📚 Trắc nghiệm Bot", layout="wide")
st.title("🤖 Chatbot Trắc Nghiệm theo Từ Khóa")

uploaded_files = st.file_uploader("📤 Tải lên file câu hỏi (CSV hoặc Excel)", type=['csv', 'xls', 'xlsx'], accept_multiple_files=True)

if uploaded_files:
    df = load_questions(uploaded_files)
    st.success(f"✅ Đã tải {len(df)} câu hỏi hợp lệ.")

    query = st.text_input("🔍 Nhập từ khóa hoặc nội dung câu hỏi:")
    if query:
        matched_question, score = search_best_match(df, query)
        
        if matched_question is not None:
            st.markdown("### ✅ Câu hỏi khớp nhất:")
            st.write(matched_question['Câu hỏi'])

            st.markdown("### 🔘 Các lựa chọn:")
            for i in range(1, 5):
                st.write(f"{i}. {matched_question[f'Đáp án {i}']}")

            # Lấy đáp án đúng và nội dung
            correct_letter = str(matched_question['Đáp án đúng']).strip()
            try:
                correct_index = int(correct_letter)
                correct_content = matched_question[f'Đáp án {correct_index}']
                st.markdown("### 🟢 Đáp án đúng:")
                st.success(f"{correct_letter}. {correct_content}")
            except:
                st.error("⚠️ Không thể xác định đáp án đúng (định dạng lỗi).")

            # Trích dẫn nguồn nếu có
            if pd.notna(matched_question['Trích dẫn nguồn câu hỏi']):
                st.caption(f"📚 Nguồn: {matched_question['Trích dẫn nguồn câu hỏi']}")

            st.caption(f"🔍 Mức độ tương đồng: {score:.2f}")
        else:
            st.warning("❌ Không tìm thấy câu hỏi phù hợp.")
