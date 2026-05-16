import sys
import types
import datetime

# Strong patch for Python 3.12+ distutils compatibility
from packaging.version import parse as parse_version
class LooseVersion:
    def __init__(self, vstring):
        self.vstring = str(vstring)
        self.v = parse_version(self.vstring)
    def __str__(self): return self.vstring
    def __repr__(self): return f"LooseVersion('{self.vstring}')"
    def _to_v(self, other):
        if isinstance(other, LooseVersion): return other.v
        if isinstance(other, str): return parse_version(other)
        return other
    def __lt__(self, other): return self.v < self._to_v(other)
    def __le__(self, other): return self.v <= self._to_v(other)
    def __gt__(self, other): return self.v > self._to_v(other)
    def __ge__(self, other): return self.v >= self._to_v(other)
    def __eq__(self, other): return self.v == self._to_v(other)
    def __ne__(self, other): return self.v != self._to_v(other)

dv = types.ModuleType('distutils.version')
dv.LooseVersion = LooseVersion
d = types.ModuleType('distutils')
d.version = dv
sys.modules['distutils'] = d
sys.modules['distutils.version'] = dv

import streamlit as st
from google.cloud import bigquery
import pandas as pd
import koreanize_matplotlib

# --- [설정] ---
PROJECT_ID = 'lunar-alpha-332721'
DATASET_ID = 'sales_intelligence'
TABLE_ID = 'daily_summary'
# -------------

# st.set_page_config(page_title="1101 MUSEUM", layout="wide") 

# 콤팩트 다크 테마 CSS (글자 크기 이전 버전으로 축소)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    [data-testid="stAppViewContainer"], [data-testid="stHeader"], .main {
        background-color: #0f172a !important;
    }
    
    html, body, [class*="css"] {
        font-family: 'Inter', 'Apple SD Gothic Neo', sans-serif;
        color: #e2e8f0 !important;
    }
    
    .main .block-container { 
        padding: 0.2rem 1.2rem !important; 
        max-width: 98.5%; 
    }
    
    /* 제목 크기 축소 (기존 버전 기준) */
    .dashboard-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #ffffff;
        padding: 8px 0 8px 12px;
        border-left: 5px solid #3b82f6;
        margin-bottom: 0.2rem;
    }
    
    /* 탭 디자인 및 크기 축소 */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 36px;
        padding: 0 14px;
        font-size: 0.85rem;
        background-color: #1e293b !important;
        color: #94a3b8 !important;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6 !important;
        color: #ffffff !important;
    }
    
    /* 지표 카드 크기 축소 */
    .metric-grid { display: flex; gap: 8px; margin-bottom: 10px; }
    .metric-container {
        flex: 1;
        background-color: #1e293b;
        border-radius: 8px;
        padding: 10px 12px;
        border: 1px solid #334155;
    }
    .metric-label { font-size: 0.75rem; color: #94a3b8; margin-bottom: 2px; font-weight: 600; }
    .metric-value { font-size: 1.15rem; font-weight: 700; color: #ffffff; }
    
    .kakao-text { color: #facc15 !important; }
    .naver-text { color: #22c55e !important; }
    .interpark-text { color: #f43f5e !important; }
    .ticketlink-text { color: #60a5fa !important; }
    
    /* 테이블 가독성 및 글자 크기 축소 */
    .scroll-container {
        max-height: 74vh;
        overflow-y: auto;
        border: 1px solid #334155;
        border-radius: 8px;
        background-color: #0f172a;
    }
    
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9rem; /* 이전 흰색 버전의 콤팩트한 크기 */
    }
    
    .custom-table thead th {
        position: sticky;
        top: 0;
        background-color: #1e293b;
        color: #f1f5f9;
        z-index: 100;
        padding: 10px;
        text-align: center;
        border-bottom: 2px solid #3b82f6;
    }
    
    .custom-table td {
        border-bottom: 1px solid #1e293b;
        padding: 8px 12px;
        text-align: right;
        color: #cbd5e1;
    }
    
    .custom-table tr:hover { background-color: #1e293b; }
    
    .custom-table .date-col {
        text-align: center;
        background-color: #1e293b;
        font-weight: 600;
        color: #ffffff;
        position: sticky;
        left: 0;
        z-index: 5;
    }
    
    .total-row {
        background-color: #1e3a8a !important;
        color: #facc15 !important;
        font-weight: 700;
    }
    
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-thumb { background: #3b82f6; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=1)
def load_data():
    # Streamlit Cloud 배포를 위한 Secrets 인증 로직 추가
    if "gcp_service_account" in st.secrets:
        from google.oauth2 import service_account
        info = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(info)
        client = bigquery.Client(credentials=credentials, project=PROJECT_ID)
    else:
        # 로컬 환경용 (key.json 또는 기본 인증 사용)
        client = bigquery.Client(project=PROJECT_ID)
    
    query = f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`"
    df = client.query(query).to_dataframe()
    
    def normalize_date(d):
        d = str(d).strip()
        if not d or "합계" in d: return "1900-01-01"
        return d.replace('.', '-').replace(' ', '')
    
    df['date_norm'] = df['date'].apply(normalize_date)
    df['date_obj'] = pd.to_datetime(df['date_norm'], errors='coerce').dt.date
    return df

def format_num(val):
    try:
        n = int(float(str(val).replace(',', '')))
        return f"{n:,}"
    except:
        return "0"

def main():
    st.markdown('<div class="dashboard-title">🏛️ BW Sales Intelligence Dashboard</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📊 판매 요약", "📋 상세 내역"])
    
    try:
        df = load_data()
        
        total_row_df = df[df['date_obj'] == datetime.date(1900, 1, 1)]
        total_row = total_row_df.iloc[0] if not total_row_df.empty else df.iloc[0]
        
        daily_df = df[
            (df['date_obj'] > datetime.date(1900, 1, 1)) & 
            (df['total_rev'] > 0)
        ].sort_values('date_obj', ascending=False)

        with tab1:
            # --- [지표 섹션] ---
            st.markdown(f"""
            <div class="metric-grid">
                <div class="metric-container">
                    <div class="metric-label">🏛️ 누적 총 매출</div>
                    <div class="metric-value">{format_num(total_row['total_rev'])} <span style="font-size:0.75rem; font-weight:400;">원</span></div>
                </div>
                <div class="metric-container">
                    <div class="metric-label kakao-text">🟡 Kakao 매출</div>
                    <div class="metric-value kakao-text">{format_num(total_row['k_rev'])} <span style="font-size:0.75rem; font-weight:400;">원</span></div>
                </div>
                <div class="metric-container">
                    <div class="metric-label naver-text">🟢 Naver 매출</div>
                    <div class="metric-value naver-text">{format_num(total_row['n_rev'])} <span style="font-size:0.75rem; font-weight:400;">원</span></div>
                </div>
                <div class="metric-container">
                    <div class="metric-label interpark-text">🔴 Interpark 매출</div>
                    <div class="metric-value interpark-text">{format_num(total_row['i_rev'])} <span style="font-size:0.75rem; font-weight:400;">원</span></div>
                </div>
                <div class="metric-container">
                    <div class="metric-label ticketlink-text">🔵 티켓링크 매출</div>
                    <div class="metric-value ticketlink-text">{format_num(total_row.get('t_rev', 0))} <span style="font-size:0.75rem; font-weight:400;">원</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # --- [테이블 섹션] ---
            st.markdown('<div class="scroll-container">', unsafe_allow_html=True)
            
            html = '<table class="custom-table"><thead>'
            html += '<tr>'
            html += '<th rowspan="2">날짜</th>'
            html += '<th colspan="2">전체 합계</th>'
            html += '<th colspan="2" class="kakao-text">Kakao</th>'
            html += '<th colspan="2" class="naver-text">Naver</th>'
            html += '<th colspan="2" class="interpark-text">Interpark</th>'
            html += '<th colspan="2" class="ticketlink-text">티켓링크</th>'
            html += '</tr>'
            html += '<tr>'
            html += '<th>금액</th><th>수량</th>'
            html += '<th>금액</th><th>수량</th>'
            html += '<th>금액</th><th>수량</th>'
            html += '<th>금액</th><th>수량</th>'
            html += '<th>금액</th><th>수량</th>'
            html += '</tr></thead><tbody>'

            # 전체 합계 행
            html += '<tr class="total-row">'
            html += '<td class="date-col" style="background-color:#1e3a8a;">전체 합계</td>'
            html += f'<td>{format_num(total_row["total_rev"])}</td><td>{format_num(total_row["total_qty"])}</td>'
            html += f'<td>{format_num(total_row["k_rev"])}</td><td>{format_num(total_row["k_qty"])}</td>'
            html += f'<td>{format_num(total_row["n_rev"])}</td><td>{format_num(total_row["n_qty"])}</td>'
            html += f'<td>{format_num(total_row["i_rev"])}</td><td>{format_num(total_row["i_qty"])}</td>'
            html += f'<td>{format_num(total_row.get("t_rev", 0))}</td><td>{format_num(total_row.get("t_qty", 0))}</td>'
            html += '</tr>'

            # 일별 데이터
            for _, row in daily_df.iterrows():
                dt_str = str(row['date']).replace(' ', '')
                html += '<tr>'
                html += f'<td class="date-col">{dt_str}</td>'
                html += f'<td>{format_num(row["total_rev"])}</td><td>{format_num(row["total_qty"])}</td>'
                html += f'<td>{format_num(row["k_rev"])}</td><td>{format_num(row["k_qty"])}</td>'
                html += f'<td>{format_num(row["n_rev"])}</td><td>{format_num(row["n_qty"])}</td>'
                html += f'<td>{format_num(row["i_rev"])}</td><td>{format_num(row["i_qty"])}</td>'
                html += f'<td>{format_num(row.get("t_rev", 0))}</td><td>{format_num(row.get("t_qty", 0))}</td>'
                html += '</tr>'
            
            html += '</tbody></table></div>'
            st.markdown(html, unsafe_allow_html=True)

        with tab2:
            st.markdown("### 📋 상세 내역")
            st.dataframe(daily_df, use_container_width=True)

    except Exception as e:
        st.error(f"오류: {e}")

if __name__ == "__main__":
    main()
