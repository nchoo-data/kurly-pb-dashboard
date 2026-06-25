import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

st.set_page_config(
    page_title="마켓컬리 PB 모니터링",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────
# CSS (예시 HTML 디자인 기준)
# ─────────────────────────────────────────
st.markdown("""
<style>
:root {
  --bg: #f5f7fb;
  --card: #ffffff;
  --border: #e5e7eb;
  --text: #111827;
  --muted: #6b7280;
  --primary: #7c3aed;
  --primary-soft: #f3e8ff;
  --danger: #dc2626;
  --danger-soft: #fee2e2;
  --warning: #d97706;
  --warning-soft: #fef3c7;
  --success: #059669;
  --success-soft: #d1fae5;
  --shadow: 0 1px 2px rgba(16,24,40,.04), 0 8px 24px rgba(16,24,40,.06);
  --radius: 16px;
}

/* 전체 배경 */
[data-testid="stAppViewContainer"],
[data-testid="stMain"] { background: var(--bg) !important; }
[data-testid="stHeader"] { background: transparent !important; }

/* 사이드바 화이트 */
[data-testid="stSidebar"] {
  background: #ffffff !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* radio → nav 스타일 */
[data-testid="stSidebar"] .stRadio > div { gap: 2px !important; }
[data-testid="stSidebar"] .stRadio label {
  padding: 10px 12px !important;
  border-radius: 10px !important;
  width: 100% !important;
  cursor: pointer !important;
  font-size: 14px !important;
  transition: background .15s !important;
}
[data-testid="stSidebar"] .stRadio label:hover { background: #f9fafb !important; }
/* 선택된 항목 */
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"][aria-checked="true"] ~ div,
[data-testid="stSidebar"] .stRadio input:checked ~ div { color: var(--primary) !important; }

/* radio 원 숨기기 */
[data-testid="stSidebar"] [data-baseweb="radio"] > div:first-child { display: none !important; }
[data-testid="stSidebar"] .stRadio [role="radio"] { display: none !important; }

/* 카드 공통 */
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 18px 20px;
  margin-bottom: 0;
}

/* KPI */
.kpi-label { font-size: 13px; color: var(--muted); margin-bottom: 10px; }
.kpi-value { font-size: 30px; font-weight: 800; letter-spacing: -.04em; margin-bottom: 8px; }
.kpi-foot  { font-size: 12px; color: var(--muted); }
.kpi-delta-neg { font-size: 12px; color: var(--danger); }
.kpi-delta-pos { font-size: 12px; color: var(--success); }

/* 뱃지 */
.badge {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 4px 10px; border-radius: 999px;
  font-size: 12px; font-weight: 600; white-space: nowrap;
}
.badge.danger  { background: var(--danger-soft);  color: var(--danger); }
.badge.warning { background: var(--warning-soft); color: var(--warning); }
.badge.success { background: var(--success-soft); color: var(--success); }
.badge.purple  { background: var(--primary-soft); color: var(--primary); }

/* 테이블 */
.table-wrap { overflow: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { padding: 12px 10px; border-bottom: 1px solid var(--border);
         text-align: left; vertical-align: middle; white-space: nowrap; }
th { color: var(--muted); font-weight: 600; font-size: 12px;
     background: #fafafa; position: sticky; top: 0; }
tr:last-child td { border-bottom: none; }

/* 알림 카드 */
.alert-item {
  border: 1px solid var(--border); border-radius: 14px;
  padding: 14px; background: #fcfcfd; margin-bottom: 10px;
}
.alert-item.critical { border-left: 3px solid var(--danger); }
.alert-item.warning  { border-left: 3px solid var(--warning); }
.alert-title { font-weight: 700; font-size: 14px; margin: 0; }
.alert-meta  { font-size: 12px; color: var(--muted); margin-top: 4px; }
.chip { font-size: 12px; padding: 5px 10px; border-radius: 999px;
        background: #f3f4f6; color: #374151; display: inline-block; margin: 3px 3px 0 0; }

/* 액션 카드 */
.action-card {
  border-radius: 14px; padding: 16px 18px; margin-bottom: 10px;
}

/* LLM 로그 */
.log-entry {
  background: white; border: 1px solid var(--border);
  border-radius: 12px; padding: 16px; margin-bottom: 12px;
}
.log-ts { font-size: 12px; color: var(--muted); margin-bottom: 6px; }
.log-body { font-size: 14px; color: var(--text); line-height: 1.7; }
.log-insight {
  background: var(--primary-soft); border-radius: 8px;
  padding: 10px 14px; margin-top: 10px; font-size: 13px;
  color: #4c1d95; line-height: 1.6;
}

/* section header */
.sec-title { font-size: 16px; font-weight: 700; letter-spacing: -.02em; margin-bottom: 4px; }
.sec-sub   { font-size: 12px; color: var(--muted); margin-bottom: 14px; }

/* Streamlit 기본 요소 최소화 */
div[data-testid="stMetric"] { display: none; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# 데이터 로드
# ─────────────────────────────────────────
@st.cache_data
def load_data():
    prod  = pd.read_csv("prod.csv")
    kurly = pd.read_csv("kurly.csv")

    def parse_date(s):
        try:
            return pd.to_datetime(str(s).rstrip("."), format="%y.%m.%d")
        except Exception:
            return pd.NaT

    kurly["날짜_dt"] = kurly["날짜"].apply(parse_date)
    kurly = kurly.dropna(subset=["날짜_dt"])
    prod["상품ID"]  = prod["상품ID"].astype("int64")
    kurly["상품ID"] = kurly["상품ID"].astype("int64")
    return prod, kurly


@st.cache_data
def build_df_risk(prod, kurly):
    max_date = kurly["날짜_dt"].max()
    curr = kurly[kurly["날짜_dt"] >= max_date - timedelta(days=13)]
    prev = kurly[
        (kurly["날짜_dt"] >= max_date - timedelta(days=27)) &
        (kurly["날짜_dt"] <  max_date - timedelta(days=13))
    ]

    curr_agg = curr.groupby("상품ID").agg(
        최근별점=("별점","mean"),
        최근부정비율=("리뷰유형", lambda x: (x=="부정").mean()),
        최근저평점비율=("별점", lambda x: (x<=2).mean()),
    ).reset_index()
    prev_agg = prev.groupby("상품ID").agg(
        이전별점=("별점","mean"),
        이전부정비율=("리뷰유형", lambda x: (x=="부정").mean()),
    ).reset_index()

    df = prod.copy()
    df = df.merge(curr_agg, on="상품ID", how="left")
    df = df.merge(prev_agg, on="상품ID", how="left")

    df["7일 변화"]       = (df["최근별점"] - df["이전별점"]).round(2).fillna(0.0)
    df["평균별점_curr"]  = df["최근별점"].fillna(df["평균별점"])
    df["부정비율_curr"]  = df["최근부정비율"].fillna(df["부정리뷰비율"])
    df["저평점비율_curr"]= df["최근저평점비율"].fillna(df["저평점비율"])
    df["평균감성점수"]   = (df["평균별점_curr"] - 1) / 4 * 2
    df["반응량"]         = (df["평균감성점수"] * np.log1p(df["리뷰수"])).round(1)

    decline_pen = df["7일 변화"].clip(-1, 0).abs() * 10
    df["위험 점수"] = (
        df["부정비율_curr"]*45 + df["저평점비율_curr"]*45 + decline_pen
    ).clip(0, 100).round().astype(int)

    _no = {"nan","키워드 없음","없음","","NaN"}
    def get_neg_kw(row):
        kws = [str(row.get(c,"")) for c in ["품질(부정)","구성/가성비(부정)","배송(부정)"]]
        return ", ".join(k.strip() for k in kws if k not in _no)[:60] or "-"

    df["주요 부정 키워드"] = df.apply(get_neg_kw, axis=1)
    df["상태"] = df["위험 점수"].apply(
        lambda x: "심각" if x>=70 else ("경고" if x>=40 else "주의")
    )

    # 이전 기간 기준 df_prev
    df_prev = prod.copy()
    df_prev = df_prev.merge(prev_agg, on="상품ID", how="left")
    df_prev["부정비율_prev"] = df_prev["이전부정비율"].fillna(df_prev["부정리뷰비율"])
    df_prev["위험 점수"] = (
        df_prev["부정비율_prev"]*45 + df_prev["저평점비율"]*45
    ).clip(0,100).round().astype(int)
    df_prev["상태"] = df_prev["위험 점수"].apply(
        lambda x: "심각" if x>=70 else ("경고" if x>=40 else "주의")
    )
    return df, df_prev


@st.cache_data
def build_timeseries(kurly):
    df_ts = kurly.copy()
    df_ts["주차"] = df_ts["날짜_dt"].dt.to_period("W").dt.start_time
    weekly = df_ts.groupby("주차").agg(
        평균별점=("별점","mean"),
        부정비율=("리뷰유형", lambda x: (x=="부정").mean()),
        리뷰수=("별점","count"),
    ).reset_index()
    weekly["반응량"]  = (((weekly["평균별점"]-1)/4*2) * np.log1p(weekly["리뷰수"])).round(2)
    weekly["주차_str"] = weekly["주차"].dt.strftime("%y.%m.%d")
    return weekly


# ─────────────────────────────────────────
# 공통 헬퍼
# ─────────────────────────────────────────
def badge_html(status):
    cls = {"심각":"danger","경고":"warning","주의":"success"}.get(status,"purple")
    return f'<span class="badge {cls}">{status}</span>'


def risk_table_html(df, top_n=20):
    priority = (df["상태"] != "주의").sum()
    rows_df  = df.sort_values("위험 점수", ascending=False).head(top_n)

    rows_html = ""
    for _, r in rows_df.iterrows():
        rating = f"{r['평균별점_curr']:.1f}"
        ch = r["7일 변화"]
        if ch < 0:
            ch_html = f'<span style="color:#dc2626;font-weight:600;">{ch:+.1f}</span>'
        elif ch > 0:
            ch_html = f'<span style="color:#059669;font-weight:600;">{ch:+.1f}</span>'
        else:
            ch_html = f'<span style="color:#9ca3af;">0.0</span>'

        rs = int(r["위험 점수"])
        if rs >= 70:
            rs_html = f'<span style="color:#dc2626;font-weight:700;">{rs}</span>'
        elif rs >= 40:
            rs_html = f'<span style="color:#d97706;font-weight:700;">{rs}</span>'
        else:
            rs_html = f'<span style="color:#374151;">{rs}</span>'

        rows_html += f"""
        <tr>
          <td style="font-weight:500;color:#111827;max-width:200px;overflow:hidden;text-overflow:ellipsis;">{r['상품명']}</td>
          <td>{r['브랜드']}</td>
          <td>{r['분류']}</td>
          <td style="text-align:center;">{rating}</td>
          <td style="text-align:center;">{ch_html}</td>
          <td style="text-align:center;">{r['반응량']:.1f}</td>
          <td style="text-align:center;">{rs_html}</td>
          <td style="color:#6b7280;max-width:180px;">{r['주요 부정 키워드']}</td>
          <td style="text-align:center;">{badge_html(r['상태'])}</td>
        </tr>"""

    return f"""
<div class="card">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px;">
    <div>
      <div class="sec-title">① 위험 상품 랭킹</div>
      <div class="sec-sub">평점 하락 위험도와 반응량을 종합한 우선 확인 목록</div>
    </div>
    <span class="badge purple">우선 검토 {priority}개</span>
  </div>
  <div class="table-wrap" style="max-height:420px;overflow-y:auto;">
  <table>
    <thead><tr>
      <th>상품명</th><th>브랜드</th><th>분류</th>
      <th style="text-align:center;">평균별점</th>
      <th style="text-align:center;">7일 변화</th>
      <th style="text-align:center;">반응량</th>
      <th style="text-align:center;">위험 점수</th>
      <th>주요 부정 키워드</th>
      <th style="text-align:center;">상태</th>
    </tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
  </div>
</div>"""


# ─────────────────────────────────────────
# 페이지별 렌더 함수
# ─────────────────────────────────────────
def page_overview(df_risk, df_risk_prev, weekly):
    _no = {"nan","키워드 없음","없음","","NaN"}

    # KPI
    critical_cnt  = (df_risk["상태"]=="심각").sum()
    warning_cnt   = (df_risk["상태"]=="경고").sum()
    total_items   = len(df_risk)
    avg_risk      = df_risk["위험 점수"].mean()
    prev_critical = (df_risk_prev["상태"]=="심각").sum()
    delta_c       = int(critical_cnt - prev_critical)
    delta_cls     = "kpi-delta-neg" if delta_c > 0 else "kpi-delta-pos"
    delta_str     = f"전주 대비 {delta_c:+d}건"

    k1,k2,k3,k4 = st.columns(4)
    k1.markdown(f"""<div class="card">
      <div class="kpi-label">모니터링 상품 수</div>
      <div class="kpi-value">{total_items}개</div>
      <div class="kpi-foot">전체 PB 상품 기준</div>
    </div>""", unsafe_allow_html=True)
    k2.markdown(f"""<div class="card" style="border-left:3px solid #dc2626;">
      <div class="kpi-label">평점 하락 위험 상품</div>
      <div class="kpi-value" style="color:#dc2626;">{critical_cnt}개</div>
      <div class="{delta_cls}">{delta_str}</div>
    </div>""", unsafe_allow_html=True)
    k3.markdown(f"""<div class="card" style="border-left:3px solid #d97706;">
      <div class="kpi-label">경고 상품</div>
      <div class="kpi-value" style="color:#d97706;">{warning_cnt}개</div>
      <div class="kpi-foot">14일 내 부정 리뷰 급증</div>
    </div>""", unsafe_allow_html=True)
    k4.markdown(f"""<div class="card" style="border-left:3px solid #7c3aed;">
      <div class="kpi-label">평균 위험 점수</div>
      <div class="kpi-value">{avg_risk:.1f}</div>
      <div class="kpi-foot">0~100 기준</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 위험 상품 랭킹 + 부정 요인 도넛
    배송_cnt  = df_risk[~df_risk["배송(부정)"].astype(str).isin(_no)].shape[0]
    품질_cnt  = df_risk[~df_risk["품질(부정)"].astype(str).isin(_no)].shape[0]
    가성비_cnt = df_risk[~df_risk["구성/가성비(부정)"].astype(str).isin(_no)].shape[0]

    col_tbl, col_donut = st.columns([1.7, 1])
    with col_tbl:
        st.markdown(risk_table_html(df_risk), unsafe_allow_html=True)

    with col_donut:
        st.markdown("""<div class="card">
          <div class="sec-title">② 부정 요인 분포</div>
          <div class="sec-sub">최근 14일 · 부정 키워드 존재 상품 수 기준</div>
        </div>""", unsafe_allow_html=True)

        total_neg = 배송_cnt + 품질_cnt + 가성비_cnt
        if total_neg > 0:
            fig = go.Figure(go.Pie(
                labels=["배송", "품질", "구성/가성비"],
                values=[배송_cnt, 품질_cnt, 가성비_cnt],
                hole=0.55,
                marker_colors=["#7c3aed","#dc2626","#f59e0b"],
                textinfo="label+percent",
                textfont_size=13,
            ))
            fig.update_layout(
                showlegend=True,
                legend=dict(orientation="h", y=-0.1, font_size=12),
                height=260, margin=dict(t=4,b=4,l=0,r=0),
                paper_bgcolor="white", plot_bgcolor="white",
            )
            st.plotly_chart(fig, use_container_width=True)

        c1, c2 = st.columns(2)
        c1.markdown(f"""<div style="background:#f9f5ff;border:1px solid #e9d5ff;border-radius:12px;padding:14px;text-align:center;">
          <div style="font-size:11px;color:#7e22ce;margin-bottom:4px;">위험 브랜드 수</div>
          <div style="font-size:24px;font-weight:800;color:#7c3aed;">{df_risk[df_risk['상태']!='주의']['브랜드'].nunique()}</div>
          <div style="font-size:11px;color:#9ca3af;">개</div>
        </div>""", unsafe_allow_html=True)
        c2.markdown(f"""<div style="background:#fee2e2;border:1px solid #fecaca;border-radius:12px;padding:14px;text-align:center;">
          <div style="font-size:11px;color:#dc2626;margin-bottom:4px;">심각 알림</div>
          <div style="font-size:24px;font-weight:800;color:#dc2626;">{critical_cnt}</div>
          <div style="font-size:11px;color:#9ca3af;">건</div>
        </div>""", unsafe_allow_html=True)


def page_brand(df_risk):
    st.markdown("### 브랜드 모니터링")
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        brand_health = df_risk.groupby("브랜드").agg(
            평균위험점수=("위험 점수","mean"),
            심각상품수=("상태", lambda x:(x=="심각").sum()),
            평균별점=("평균별점_curr","mean"),
            상품수=("상품ID","count"),
        ).reset_index().sort_values("평균위험점수", ascending=True)

        fig = px.bar(
            brand_health, x="평균위험점수", y="브랜드",
            orientation="h",
            color="평균위험점수",
            color_continuous_scale=[(0,"#d1fae5"),(0.4,"#fef3c7"),(1,"#fee2e2")],
            text=brand_health["평균위험점수"].round(1),
            title="<b>브랜드별 평균 위험 점수</b>",
            hover_data={"심각상품수":True,"평균별점":":.2f","상품수":True},
        )
        fig.update_layout(height=380, margin=dict(t=40,b=10,l=0,r=60),
                          coloraxis_showscale=False,
                          paper_bgcolor="white", plot_bgcolor="white")
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        cat_perf = df_risk.groupby("분류").agg(
            평균별점=("평균별점_curr","mean"),
            부정비율=("부정비율_curr","mean"),
            위험상품수=("상태", lambda x:(x=="심각").sum()),
            상품수=("상품ID","count"),
        ).reset_index().sort_values("부정비율", ascending=False).head(12)

        fig2 = px.bar(
            cat_perf, x="부정비율", y="분류",
            orientation="h",
            color="부정비율",
            color_continuous_scale=[(0,"#f0e6ff"),(0.5,"#7c3aed"),(1,"#3D0066")],
            text=cat_perf["부정비율"].apply(lambda x: f"{x:.0%}"),
            title="<b>카테고리별 부정 리뷰 비율</b>",
            hover_data={"평균별점":":.2f","위험상품수":True,"상품수":True},
        )
        fig2.update_layout(height=380, margin=dict(t=40,b=10,l=0,r=60),
                           coloraxis_showscale=False, xaxis_tickformat=".0%",
                           paper_bgcolor="white", plot_bgcolor="white")
        fig2.update_traces(textposition="outside")
        st.plotly_chart(fig2, use_container_width=True)


def page_products(df_risk, weekly):
    st.markdown("### 상품 상세 분석")

    f1, f2, f3 = st.columns(3)
    brands = ["전체"] + sorted(df_risk["브랜드"].dropna().unique().tolist())
    cats   = ["전체"] + sorted(df_risk["분류"].dropna().unique().tolist())
    status_opts = ["심각","경고","주의"]

    sel_brand  = f1.selectbox("브랜드", brands)
    sel_cat    = f2.selectbox("분류", cats)
    sel_status = f3.multiselect("상태", status_opts, default=status_opts)

    df = df_risk.copy()
    if sel_brand != "전체": df = df[df["브랜드"]==sel_brand]
    if sel_cat   != "전체": df = df[df["분류"]==sel_cat]
    if sel_status: df = df[df["상태"].isin(sel_status)]

    st.markdown(f"<div style='font-size:13px;color:#6b7280;margin:8px 0;'>총 {len(df)}개 상품</div>",
                unsafe_allow_html=True)
    st.markdown(risk_table_html(df, top_n=len(df)), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 주간 추이 분석")

    t1, t2, t3 = st.columns(3)
    ly = dict(height=240, margin=dict(t=36,b=20,l=0,r=0),
              paper_bgcolor="white", plot_bgcolor="white")
    with t1:
        fig = px.line(weekly, x="주차_str", y="평균별점", title="<b>평균 별점 추이</b>",
                      markers=True, color_discrete_sequence=["#7c3aed"])
        fig.update_traces(line_width=2.5, marker_size=6)
        fig.update_layout(**ly); fig.update_xaxes(tickangle=-30, tickfont_size=10)
        st.plotly_chart(fig, use_container_width=True)
    with t2:
        fig = px.line(weekly, x="주차_str", y="부정비율", title="<b>부정 리뷰 비율 추이</b>",
                      markers=True, color_discrete_sequence=["#dc2626"])
        fig.update_traces(line_width=2.5, marker_size=6)
        fig.update_yaxes(tickformat=".1%")
        fig.update_layout(**ly); fig.update_xaxes(tickangle=-30, tickfont_size=10)
        st.plotly_chart(fig, use_container_width=True)
    with t3:
        fig = px.line(weekly, x="주차_str", y="반응량", title="<b>주간 반응량</b>",
                      markers=True, color_discrete_sequence=["#f59e0b"])
        fig.update_traces(line_width=2.5, marker_size=6)
        fig.update_layout(**ly); fig.update_xaxes(tickangle=-30, tickfont_size=10)
        st.plotly_chart(fig, use_container_width=True)


def page_alerts(df_risk):
    st.markdown("### 부정 알림 센터")

    a_col, b_col = st.columns(2)

    with a_col:
        st.markdown('<div class="sec-title">심각 상품 알림</div>'
                    '<div class="sec-sub">위험 점수 70 이상 · 즉각 조치 권장</div>',
                    unsafe_allow_html=True)
        critical_df = df_risk[df_risk["상태"]=="심각"].sort_values("위험 점수", ascending=False)
        if len(critical_df) == 0:
            st.success("현재 심각 위험 상품이 없습니다.")
        for _, r in critical_df.iterrows():
            kw_chips = "".join(f'<span class="chip">{k.strip()}</span>'
                               for k in r["주요 부정 키워드"].split(",") if k.strip() and k.strip()!="-")
            st.markdown(f"""
            <div class="alert-item critical">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                  <div class="alert-title">{r['상품명']}</div>
                  <div class="alert-meta">{r['브랜드']} · {r['분류']}</div>
                </div>
                <span class="badge danger">심각</span>
              </div>
              <div style="font-size:13px;color:#374151;margin-top:8px;">
                별점 <b>{r['평균별점_curr']:.1f}</b> &nbsp;|&nbsp;
                7일 변화 <b style="color:#dc2626;">{r['7일 변화']:+.1f}</b> &nbsp;|&nbsp;
                위험점수 <b>{r['위험 점수']}</b>
              </div>
              <div style="margin-top:8px;">{kw_chips}</div>
            </div>""", unsafe_allow_html=True)

    with b_col:
        st.markdown('<div class="sec-title">경고 상품 알림</div>'
                    '<div class="sec-sub">위험 점수 40~69 · 모니터링 강화 권장</div>',
                    unsafe_allow_html=True)
        warn_df = df_risk[df_risk["상태"]=="경고"].sort_values("위험 점수", ascending=False)
        if len(warn_df) == 0:
            st.info("현재 경고 상품이 없습니다.")
        for _, r in warn_df.iterrows():
            kw_chips = "".join(f'<span class="chip">{k.strip()}</span>'
                               for k in r["주요 부정 키워드"].split(",") if k.strip() and k.strip()!="-")
            st.markdown(f"""
            <div class="alert-item warning">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                  <div class="alert-title">{r['상품명']}</div>
                  <div class="alert-meta">{r['브랜드']} · {r['분류']}</div>
                </div>
                <span class="badge warning">경고</span>
              </div>
              <div style="font-size:13px;color:#374151;margin-top:8px;">
                별점 <b>{r['평균별점_curr']:.1f}</b> &nbsp;|&nbsp;
                7일 변화 <b style="color:#d97706;">{r['7일 변화']:+.1f}</b> &nbsp;|&nbsp;
                위험점수 <b>{r['위험 점수']}</b>
              </div>
              <div style="margin-top:8px;">{kw_chips}</div>
            </div>""", unsafe_allow_html=True)


def page_risk(df_risk):
    _no = {"nan","키워드 없음","없음","","NaN"}
    배송_cnt   = df_risk[~df_risk["배송(부정)"].astype(str).isin(_no)].shape[0]
    품질_cnt   = df_risk[~df_risk["품질(부정)"].astype(str).isin(_no)].shape[0]
    가성비_cnt  = df_risk[~df_risk["구성/가성비(부정)"].astype(str).isin(_no)].shape[0]

    st.markdown("### 예측 리스크")

    col1, col2 = st.columns([1.2, 1])

    with col1:
        # 위험 점수 분포
        fig = px.histogram(
            df_risk, x="위험 점수", nbins=20,
            title="<b>위험 점수 분포</b>",
            color_discrete_sequence=["#7c3aed"],
        )
        fig.add_vline(x=40, line_dash="dash", line_color="#d97706", annotation_text="경고")
        fig.add_vline(x=70, line_dash="dash", line_color="#dc2626", annotation_text="심각")
        fig.update_layout(height=300, margin=dict(t=40,b=10,l=0,r=0),
                          paper_bgcolor="white", plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # 별점 vs 위험점수 scatter
        fig2 = px.scatter(
            df_risk, x="평균별점_curr", y="위험 점수",
            color="상태",
            color_discrete_map={"심각":"#dc2626","경고":"#d97706","주의":"#059669"},
            title="<b>별점 vs 위험 점수</b>",
            hover_data={"상품명":True,"브랜드":True,"분류":True},
        )
        fig2.update_layout(height=300, margin=dict(t=40,b=10,l=0,r=0),
                           paper_bgcolor="white", plot_bgcolor="white")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="sec-title">운영 액션 제안</div>'
                '<div class="sec-sub">부정 요인 빈도 기준 · 자동 우선순위 정렬</div>',
                unsafe_allow_html=True)

    actions = sorted([
        ("🚚 배송 이슈 대응", "#fee2e2",
         f"포장 파손·지연 배송 이슈 상품 {배송_cnt}개를 우선 추출해 물류·포장 프로세스를 점검하세요. 7일 변화 −0.2 이하 상품은 즉각 조치가 필요합니다.",
         배송_cnt),
        ("🔍 품질 점검 대상 지정", "#fff7ed",
         f"신선도·맛 관련 부정 키워드가 급증한 {품질_cnt}개 상품의 원재료·보관·유통기한 관리 이슈를 점검하세요. 동일 분류 내 저평점 상품과 비교 분석을 권장합니다.",
         품질_cnt),
        ("📦 상세페이지 기대치 보정", "#f3e8ff",
         f"구성·가성비 불만이 집중된 {가성비_cnt}개 상품의 상세페이지 내 용량·구성·가격 설명을 보정하세요. 기대치와 실제 제품 간 간극을 줄이는 것이 재구매율에 직접 영향을 줍니다.",
         가성비_cnt),
    ], key=lambda x: -x[3])

    for title, color, desc, cnt in actions:
        st.markdown(f"""
        <div class="action-card" style="background:{color};border-radius:14px;">
          <div style="font-size:14px;font-weight:700;color:#111827;margin-bottom:6px;">
            {title} <span style="font-size:12px;color:#6b7280;font-weight:400;">({cnt}개 상품)</span>
          </div>
          <div style="font-size:13px;color:#374151;line-height:1.6;">{desc}</div>
        </div>""", unsafe_allow_html=True)


def page_llm(df_risk):
    st.markdown("### LLM 요약 로그")
    st.markdown('<div class="sec-sub">AI가 리뷰 데이터를 분석해 생성한 주간 요약 · 인사이트</div>',
                unsafe_allow_html=True)

    critical_products = df_risk[df_risk["상태"]=="심각"]["상품명"].head(3).tolist()
    top_brand = df_risk.groupby("브랜드")["위험 점수"].mean().idxmax() if len(df_risk) else "N/A"
    top_brand_score = df_risk.groupby("브랜드")["위험 점수"].mean().max() if len(df_risk) else 0
    top_cat = df_risk.groupby("분류")["부정비율_curr"].mean().idxmax() if len(df_risk) else "N/A"

    sample_logs = [
        {
            "ts": "2026.03.23 09:00 · 자동 생성",
            "label": "주간 위험 요약",
            "label_cls": "danger",
            "body": f"""이번 주 전체 PB 상품 {len(df_risk)}개 중 위험 점수 70 이상의 '심각' 상태 상품이 {(df_risk['상태']=='심각').sum()}개로 집계되었습니다. 특히 <b>{', '.join(critical_products)}</b> 등의 상품에서 평균 별점이 전주 대비 큰 폭으로 하락했습니다.""",
            "insight": f"💡 인사이트: '{top_brand}' 브랜드 전체 평균 위험 점수가 {top_brand_score:.1f}점으로 가장 높아 긴급 점검이 필요합니다. 특히 배송 관련 부정 키워드가 전주 대비 증가 추세를 보이고 있습니다.",
        },
        {
            "ts": "2026.03.23 09:01 · 자동 생성",
            "label": "카테고리 인사이트",
            "label_cls": "warning",
            "body": f"'{top_cat}' 카테고리의 부정 리뷰 비율이 전체 평균 대비 높게 나타났습니다. 해당 카테고리 내 신선도 및 포장 관련 키워드 빈도가 증가하고 있으며, 소비자 기대 수준과 실제 상품 품질 간 간극이 발생하고 있는 것으로 분석됩니다.",
            "insight": "💡 인사이트: 해당 카테고리의 상세페이지 용량·구성 표기 방식을 재검토하고, 신선 배송 프로세스 점검을 통해 불만 원인을 선제적으로 제거할 것을 권장합니다.",
        },
        {
            "ts": "2026.03.23 09:02 · 자동 생성",
            "label": "반응량 예측",
            "label_cls": "purple",
            "body": "회귀 모델 분석 결과, 가성비순 반응 증가 시 반응량이 유의미하게 상승(+5.29)하는 반면, 품질순 반응(-3.06) 및 배송순 반응(-1.74)은 반응량에 부정적 영향을 미치는 것으로 확인되었습니다. 현재 위험 상품 중 배송 불만 비중이 높아, 이를 개선할 경우 반응량 회복 가능성이 높습니다.",
            "insight": "💡 인사이트: 배송 품질 개선을 통해 부정 리뷰 유형을 '배송'에서 '가성비' 긍정으로 전환하는 것이 반응량 회복에 가장 효과적인 방향으로 예측됩니다.",
        },
    ]

    for log in sample_logs:
        st.markdown(f"""
        <div class="log-entry">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <span class="badge {log['label_cls']}">{log['label']}</span>
            <span class="log-ts">{log['ts']}</span>
          </div>
          <div class="log-body">{log['body']}</div>
          <div class="log-insight">{log['insight']}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin-top:8px;">
      <div style="font-size:13px;color:#6b7280;line-height:1.8;">
        ⚙️ <b>분석 모델 정보</b><br>
        • 위험 점수: 부정리뷰비율×45 + 저평점비율×45 + 평점하락패널티<br>
        • 반응량 모델: OLS 회귀 (R²=0.639) — 가성비순반응, 품질순반응, 배송순반응, 할인가 유효<br>
        • 데이터 기준: 최근 14일 vs 이전 14일 비교
      </div>
    </div>""", unsafe_allow_html=True)


def page_settings():
    st.markdown("### 설정")
    st.info("현재 데이터 소스 및 임계값 설정 기능은 준비 중입니다.")
    st.markdown("""
    <div class="card">
      <div class="sec-title">현재 설정값</div>
      <table>
        <tr><th>항목</th><th>값</th></tr>
        <tr><td>심각 임계값</td><td>위험 점수 ≥ 70</td></tr>
        <tr><td>경고 임계값</td><td>위험 점수 40~69</td></tr>
        <tr><td>분석 기간</td><td>최근 14일 vs 이전 14일</td></tr>
        <tr><td>데이터 소스</td><td>prod.csv / kurly.csv</td></tr>
      </table>
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
def main():
    prod, kurly      = load_data()
    df_risk, df_risk_prev = build_df_risk(prod, kurly)
    weekly           = build_timeseries(kurly)

    # ── 사이드바 ──
    with st.sidebar:
        st.markdown("""
        <div style="margin-bottom:24px;">
          <div style="font-size:20px;font-weight:700;letter-spacing:-.02em;color:#111827;">마켓컬리PB 모니터링</div>
          <div style="font-size:13px;color:#6b7280;line-height:1.5;margin-top:6px;">
            PB 브랜드 반응량, 평점 하락 위험,<br>부정 키워드 알림을 한 화면에서 확인하는 운영 대시보드
          </div>
        </div>
        <hr style="border:none;border-top:1px solid #e5e7eb;margin-bottom:16px;">
        """, unsafe_allow_html=True)

        page = st.radio(
            "navigation",
            options=["Overview", "브랜드 모니터링", "상품 상세 분석",
                     "부정 알림 센터", "예측 리스크", "LLM 요약 로그", "설정"],
            label_visibility="collapsed",
        )

    # ── 페이지 렌더 ──
    if page == "Overview":
        page_overview(df_risk, df_risk_prev, weekly)
    elif page == "브랜드 모니터링":
        page_brand(df_risk)
    elif page == "상품 상세 분석":
        page_products(df_risk, weekly)
    elif page == "부정 알림 센터":
        page_alerts(df_risk)
    elif page == "예측 리스크":
        page_risk(df_risk)
    elif page == "LLM 요약 로그":
        page_llm(df_risk)
    elif page == "설정":
        page_settings()


if __name__ == "__main__":
    main()
