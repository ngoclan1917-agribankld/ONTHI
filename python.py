# python.py

import streamlit as st
import pandas as pd
from google import genai
from google.genai.errors import APIError

# --- Cấu hình Trang Streamlit ---
st.set_page_config(
    page_title="App Phân Tích Báo Cáo Tài Chính",
    layout="wide"
)

# --- Cập nhật Tiêu đề và Styling Nổi Bật ---
st.markdown(
    """
    <div style="text-align: center;">
        <h1 style="color: red; font-size: 2.5em; text-transform: uppercase; border-bottom: 3px solid red; padding-bottom: 10px; margin-bottom: 30px;">
            ỨNG DỤNG PHÂN TÍCH BÁO CÁO TÀI CHÍNH 📊
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Hàm hỗ trợ định dạng subheader ---
def styled_subheader(text, number):
    """Tạo subheader với màu xanh, in đậm, và font lớn hơn."""
    st.markdown(f'<h3 style="color: #1E90FF; font-weight: bold;">{number}. {text}</h3>', unsafe_allow_html=True)


# --- Hàm tính toán chính (Sử dụng Caching để Tối ưu hiệu suất) ---
@st.cache_data
def process_financial_data(df):
    """Thực hiện các phép tính Tăng trưởng và Tỷ trọng."""
    
    # Đảm bảo các giá trị là số để tính toán
    numeric_cols = ['Năm trước', 'Năm sau']
    for col in numeric_cols:
        # Sử dụng errors='coerce' để chuyển đổi các chuỗi không phải số thành NaN, sau đó fillna(0)
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # 1. Tính Tốc độ Tăng trưởng
    # Dùng .replace(0, 1e-9) cho Series Pandas để tránh lỗi chia cho 0
    df['Tốc độ tăng trưởng (%)'] = (
        (df['Năm sau'] - df['Năm trước']) / df['Năm trước'].replace(0, 1e-9)
    ) * 100

    # 2. Tính Tỷ trọng theo Tổng Tài sản
    # Lọc chỉ tiêu "TỔNG CỘNG TÀI SẢN"
    tong_tai_san_row = df[df['Chỉ tiêu'].str.contains('TỔNG CỘNG TÀI SẢN', case=False, na=False)]
    
    if tong_tai_san_row.empty:
        # Xử lý trường hợp không tìm thấy TỔNG CỘNG TÀI SẢN
        # Có thể giả định tổng là 1 nếu file rỗng, nhưng tốt nhất là báo lỗi rõ ràng
        # Để code hoạt động, nếu không tìm thấy, ta sẽ dùng 1e-9 để tránh chia cho 0
        tong_tai_san_N_1 = 1e-9
        tong_tai_san_N = 1e-9
        # raise ValueError("Không tìm thấy chỉ tiêu 'TỔNG CỘNG TÀI SẢN'.") 
    else:
        tong_tai_san_N_1 = tong_tai_san_row['Năm trước'].iloc[0]
        tong_tai_san_N = tong_tai_san_row['Năm sau'].iloc[0]

    
    # ******************************* PHẦN SỬA LỖI BẮT ĐẦU *******************************
    # Xử lý giá trị 0 thủ công cho mẫu số để tính tỷ trọng.
    
    divisor_N_1 = tong_tai_san_N_1 if tong_tai_san_N_1 != 0 else 1e-9
    divisor_N = tong_tai_san_N if tong_tai_san_N != 0 else 1e-9

    # Tính tỷ trọng với mẫu số đã được xử lý
    df['Tỷ trọng Năm trước (%)'] = (df['Năm trước'] / divisor_N_1) * 100
    df['Tỷ trọng Năm sau (%)'] = (df['Năm sau'] / divisor_N) * 100
    # ******************************* PHẦN SỬA LỖI KẾT THÚC *******************************
    
    return df

# --- Hàm gọi API Gemini cho Phân Tích Báo Cáo ---
def get_ai_analysis(data_for_ai, api_key):
    """Gửi dữ liệu phân tích đến Gemini API và nhận nhận xét."""
    try:
        client = genai.Client(api_key=api_key)
        model_name = 'gemini-2.5-flash' 

        prompt = f"""
        Bạn là một chuyên gia phân tích tài chính chuyên nghiệp. Dựa trên các chỉ số tài chính sau, hãy đưa ra một nhận xét khách quan, ngắn gọn (khoảng 3-4 đoạn) về tình hình tài chính của doanh nghiệp. Đánh giá tập trung vào tốc độ tăng trưởng, thay đổi cơ cấu tài sản, khả năng thanh toán hiện hành, và vốn lưu động ròng.
        
        Dữ liệu thô và chỉ số:
        {data_for_ai}
        """

        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        return response.text

    except APIError as e:
        return f"Lỗi gọi Gemini API: Vui lòng kiểm tra Khóa API hoặc giới hạn sử dụng. Chi tiết lỗi: {e}"
    except KeyError:
        return "Lỗi: Không tìm thấy Khóa API 'GEMINI_API_KEY'. Vui lòng kiểm tra cấu hình Secrets trên Streamlit Cloud."
    except Exception as e:
        return f"Đã xảy ra lỗi không xác định: {e}"

# --- BẮT ĐẦU THÊM KHUNG CHAT GEMINI MỚI ---
# Khởi tạo state chat
if "messages" not in st.session_state:
    st.session_state.messages = []
    
# Hàm gọi API Gemini cho tương tác Chat (ĐÃ FIX LỖI VALIDATION)
def get_chat_response(prompt, api_key):
    """Tương tác với Gemini trong chế độ chat."""
    try:
        client = genai.Client(api_key=api_key)
        
        # Lấy lịch sử tin nhắn và CHUYỂN ĐỔI sang định dạng API mong muốn (thêm key 'text')
        history = [
            {
                "role": "user" if msg["role"] == "user" else "model", 
                "parts": [{"text": msg["content"]}] # FIX: 'parts' cần là list chứa dict với key 'text'
            } 
            for msg in st.session_state.messages
        ]
        
        # Khởi tạo chat session
        chat = client.chats.create(
            model="gemini-2.5-flash", 
            history=history
        )
        
        # Gửi tin nhắn mới
        response = chat.send_message(prompt)
        return response.text
    
    except APIError as e:
        return f"Lỗi gọi Gemini API: Vui lòng kiểm tra Khóa API hoặc giới hạn sử dụng. Chi tiết lỗi: {e}"
    except Exception as e:
        return f"Đã xảy ra lỗi không xác định trong chat: {e}"
# --- KẾT THÚC KHUNG CHAT GEMINI MỚI ---


# --- Chức năng 1: Tải File ---
styled_subheader("Tải File", 1)
uploaded_file = st.file_uploader(
    "Tải file Excel Báo cáo Tài chính (Chỉ tiêu | Năm trước | Năm sau)",
    type=['xlsx', 'xls']
)

if uploaded_file is not None:
    try:
        df_raw = pd.read_excel(uploaded_file)
        
        # Tiền xử lý: Đảm bảo chỉ có 3 cột quan trọng
        df_raw.columns = ['Chỉ tiêu', 'Năm trước', 'Năm sau']
        
        # Xử lý dữ liệu
        df_processed = process_financial_data(df_raw.copy())

        if df_processed is not None:
            
            # --- Chức năng 2 & 3: Hiển thị Kết quả ---
            styled_subheader("Tốc độ Tăng trưởng & Tỷ trọng Cơ cấu Tài sản", 2)
            st.dataframe(df_processed.style.format({
                'Năm trước': '{:,.0f}',
                'Năm sau': '{:,.0f}',
                'Tốc độ tăng trưởng (%)': '{:.2f}%',
                'Tỷ trọng Năm trước (%)': '{:.2f}%',
                'Tỷ trọng Năm sau (%)': '{:.2f}%'
            }), use_container_width=True)
            
            # --- Chức năng 4: Tính Chỉ số Tài chính ---
            styled_subheader("Các Chỉ số Tài chính Cơ bản", 4)
            
            # Khởi tạo các biến để tránh lỗi UnboundLocalError trong phần except và Chức năng 5
            thanh_toan_hien_hanh_N = "N/A"
            thanh_toan_hien_hanh_N_1 = "N/A"
            von_luu_dong_rong_N = "N/A"
            von_luu_dong_rong_N_1 = "N/A"
            htk_n = "N/A"
            htk_n_1 = "N/A"

            try:
                # Lấy Tài sản ngắn hạn
                tsnh_n = df_processed[df_processed['Chỉ tiêu'].str.contains('TÀI SẢN NGẮN HẠN', case=False, na=False)]['Năm sau'].iloc[0]
                tsnh_n_1 = df_processed[df_processed['Chỉ tiêu'].str.contains('TÀI SẢN NGẮN HẠN', case=False, na=False)]['Năm trước'].iloc[0]

                # Lấy Nợ ngắn hạn
                no_ngan_han_N = df_processed[df_processed['Chỉ tiêu'].str.contains('NỢ NGẮN HẠN', case=False, na=False)]['Năm sau'].iloc[0]  
                no_ngan_han_N_1 = df_processed[df_processed['Chỉ tiêu'].str.contains('NỢ NGẮN HẠN', case=False, na=False)]['Năm trước'].iloc[0]
                
                # Lấy Hàng Tồn Kho (HTK)
                htk_n_raw = df_processed[df_processed['Chỉ tiêu'].str.contains('HÀNG TỒN KHO', case=False, na=False)]['Năm sau'].iloc[0]
                htk_n_1_raw = df_processed[df_processed['Chỉ tiêu'].str.contains('HÀNG TỒN KHO', case=False, na=False)]['Năm trước'].iloc[0]

                # Tính toán
                # 1. Chỉ số Thanh toán Hiện hành
                thanh_toan_hien_hanh_N = tsnh_n / no_ngan_han_N
                thanh_toan_hien_hanh_N_1 = tsnh_n_1 / no_ngan_han_N_1
                
                # 2. Vốn lưu động ròng (MỚI)
                von_luu_dong_rong_N = tsnh_n - no_ngan_han_N
                von_luu_dong_rong_N_1 = tsnh_n_1 - no_ngan_han_N_1
                
                # 3. Giá trị Hàng tồn kho
                htk_n = htk_n_raw
                htk_n_1 = htk_n_1_raw
                
                # --- Hiển thị Metrics ---
                col1, col2, col3 = st.columns(3)
                
                # Metric 1: Thanh toán Hiện hành
                with col1:
                    st.metric(
                        label="Chỉ số Thanh toán Hiện hành (Năm trước)",
                        value=f"{thanh_toan_hien_hanh_N_1:.2f} lần"
                    )
                    st.metric(
                        label="Chỉ số Thanh toán Hiện hành (Năm sau)",
                        value=f"{thanh_toan_hien_hanh_N:.2f} lần",
                        delta=f"{thanh_toan_hien_hanh_N - thanh_toan_hien_hanh_N_1:.2f}"
                    )
                
                # Metric 2: Vốn lưu động ròng (MỚI)
                with col2:
                    st.metric(
                        label="Vốn lưu động ròng (Năm trước)",
                        value=f"{von_luu_dong_rong_N_1:,.0f}"
                    )
                    st.metric(
                        label="Vốn lưu động ròng (Năm sau)",
                        value=f"{von_luu_dong_rong_N:,.0f}",
                        delta=f"{von_luu_dong_rong_N - von_luu_dong_rong_N_1:,.0f}"
                    )
                    
                # Metric 3: Hàng tồn kho & Vòng quay (MỚI)
                with col3:
                    st.info("**Vòng quay Hàng tồn kho** và **Vòng quay Vốn lưu động** cần dữ liệu **DOANH THU/GIÁ VỐN** (từ báo cáo kết quả kinh doanh). Vui lòng đảm bảo file excel có các chỉ tiêu này.")
                    
                    st.metric(
                        label="Hàng tồn kho (Năm sau)",
                        value=f"{htk_n:,.0f}",
                        delta=f"{htk_n - htk_n_1:,.0f}" if isinstance(htk_n, (int, float)) and isinstance(htk_n_1, (int, float)) else "N/A"
                    )
                    
                    st.metric(
                        label="Vòng quay Vốn lưu động (Năm sau)",
                        value="N/A",
                        delta="Thiếu Doanh thu"
                    )

                    
            except IndexError:
                 st.warning("Thiếu một hoặc nhiều chỉ tiêu cần thiết ('TÀI SẢN NGẮN HẠN', 'NỢ NGẮN HẠN', 'HÀNG TỒN KHO') để tính chỉ số.")
                 # Gán lại các biến về N/A để Chức năng 5 không bị lỗi
                 thanh_toan_hien_hanh_N = "N/A" 
                 thanh_toan_hien_hanh_N_1 = "N/A"
                 von_luu_dong_rong_N = "N/A"
                 von_luu_dong_rong_N_1 = "N/A"
                 
            
            # --- Chức năng 5: Nhận xét AI ---
            styled_subheader("Nhận xét Tình hình Tài chính (AI)", 5)
            
            # Chuẩn bị dữ liệu để gửi cho AI (ĐÃ BỔ SUNG VỐN LƯU ĐỘNG RÒNG)
            data_for_ai = pd.DataFrame({
                'Chỉ tiêu': [
                    'Toàn bộ Bảng phân tích (dữ liệu thô)', 
                    'Tăng trưởng Tài sản ngắn hạn (%)', 
                    'Thanh toán hiện hành (N-1)', 
                    'Thanh toán hiện hành (N)',
                    'Vốn lưu động ròng (N-1)', 
                    'Vốn lưu động ròng (N)' 
                ],
                'Giá trị': [
                    df_processed.to_markdown(index=False),
                    f"{df_processed[df_processed['Chỉ tiêu'].str.contains('TÀI SẢN NGẮN HẠN', case=False, na=False)]['Tốc độ tăng trưởng (%)'].iloc[0]:.2f}%" if not isinstance(thanh_toan_hien_hanh_N, str) else "N/A", 
                    f"{thanh_toan_hien_hanh_N}", 
                    f"{thanh_toan_hien_hanh_N}",
                    f"{von_luu_dong_rong_N_1:,.0f}" if isinstance(von_luu_dong_rong_N_1, (int, float)) else f"{von_luu_dong_rong_N_1}", 
                    f"{von_luu_dong_rong_N:,.0f}" if isinstance(von_luu_dong_rong_N, (int, float)) else f"{von_luu_dong_rong_N}" 
                ]
            }).to_markdown(index=False) 

            if st.button("Yêu cầu AI Phân tích"):
                api_key = st.secrets.get("GEMINI_API_KEY") 
                
                if api_key:
                    with st.spinner('Đang gửi dữ liệu và chờ Gemini phân tích...'):
                        ai_result = get_ai_analysis(data_for_ai, api_key)
                        st.markdown("**Kết quả Phân tích từ Gemini AI:**")
                        st.info(ai_result)
                else:
                     st.error("Lỗi: Không tìm thấy Khóa API. Vui lòng cấu hình Khóa 'GEMINI_API_KEY' trong Streamlit Secrets.")

    except ValueError as ve:
        st.error(f"Lỗi cấu trúc dữ liệu: {ve}")
    except Exception as e:
        st.error(f"Có lỗi xảy ra khi đọc hoặc xử lý file: {e}. Vui lòng kiểm tra định dạng file.")

else:
    st.info("Vui lòng tải lên file Excel để bắt đầu phân tích.")

st.divider()

# --- BẮT ĐẦU KHUNG CHAT TƯƠNG TÁC MỚI (MỤC 6) ---

styled_subheader("Chat với Gemini AI 💬", 6)
st.caption("Hãy hỏi Gemini về các thuật ngữ tài chính, hoặc yêu cầu nó giải thích thêm về kết quả phân tích ở trên.")

# Hiển thị lịch sử chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Xử lý input từ người dùng
if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
    
    # 1. Lưu và hiển thị tin nhắn của người dùng
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 2. Gọi API và hiển thị phản hồi của Gemini
    api_key = st.secrets.get("GEMINI_API_KEY")
    
    if not api_key:
        st.error("Không tìm thấy Khóa API để khởi tạo Chat.")
        ai_response = "Xin lỗi, tôi không thể trả lời. Vui lòng kiểm tra Khóa API 'GEMINI_API_KEY' trong Streamlit Secrets."
    else:
        with st.chat_message("assistant"):
            with st.spinner("Đang nghĩ..."):
                ai_response = get_chat_response(prompt, api_key)
                st.markdown(ai_response)
                
    # 3. Lưu phản hồi của Gemini vào lịch sử
    st.session_state.messages.append({"role": "assistant", "content": ai_response})
    
# --- KẾT THÚC KHUNG CHAT TƯƠNG TÁC MỚI ---
