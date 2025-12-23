
import json
from pathlib import Path

import streamlit as st
import pandas as pd

DATA_PATH = Path(__file__).parent / "student_records.json"
PW_PATH = Path(__file__).parent / "class_passwords.json"

@st.cache_data
def load_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    classes = sorted(data.keys(), key=lambda x: (int(x.split("-")[0]), int(x.split("-")[1])))
    return data, classes

@st.cache_data
def load_passwords(classes):
    if PW_PATH.exists():
        with open(PW_PATH, "r", encoding="utf-8") as f:
            pw_map = json.load(f)
    else:
        pw_map = {}
    for c in classes:
        pw_map.setdefault(c, "")
    return pw_map

def main():
    st.set_page_config(
        page_title="2025-1 진로독서 세특(창체 진로활동): 2학년 6~10반",
        layout="wide",
    )
    st.title("2025-1 진로독서 세특(창체 진로활동): 2학년 6~10반")

    data, classes = load_data()
    pw_map = load_passwords(classes)

    st.info(
        "이 페이지는 **2학년 6~10반 진로독서 활동** 기반의 세특(창체 진로활동) 기재 내용을 확인하기 위한 페이지입니다.\n\n"
        "1) 상단에서 **반을 선택**하고\n"
        "2) 해당 반의 **비밀번호를 입력**한 뒤\n"
        "3) **확인** 버튼을 눌러 주세요.\n\n"
        "※ **비고**에 '보고서 미제출' 등이 표시된 학생은, 보고서 기반 진로 연계 기록이 어려워 수업 활동 중심으로 기재되어 있습니다."
    )

    if "auth_class" not in st.session_state:
        st.session_state["auth_class"] = None

    query_params = st.query_params
    default_class = None
    if "class" in query_params:
        q = query_params["class"]
        if isinstance(q, list):
            q = q[0]
        if q in classes:
            default_class = q

    col_top = st.columns([2, 3, 2])
    with col_top[1]:
        selected_class = st.selectbox(
            "반 선택",
            options=classes,
            index=classes.index(default_class) if default_class in classes else 0,
            format_func=lambda x: f"{x}반",
        )
        pw_input = st.text_input("해당 반 비밀번호", type="password", max_chars=30)
        confirm = st.button("확인")

    if st.session_state.get("auth_class") and st.session_state["auth_class"] != selected_class:
        st.session_state["auth_class"] = None

    auth_ok = False
    if confirm:
        real_pw = pw_map.get(selected_class, "")
        if real_pw and pw_input == real_pw:
            st.session_state["auth_class"] = selected_class
            auth_ok = True
            st.success(f"{selected_class}반 인증이 완료되었습니다.")
        else:
            st.session_state["auth_class"] = None
            st.error("비밀번호가 올바르지 않습니다. 다시 확인해 주세요.")
    elif st.session_state.get("auth_class") == selected_class:
        auth_ok = True

    st.write("---")
    if not auth_ok:
        st.warning("반과 비밀번호를 입력한 뒤 **확인** 버튼을 눌러야 목록을 볼 수 있습니다.")
        return

    students = data.get(selected_class, [])
    if not students:
        st.info("해당 반의 데이터가 없습니다.")
        return

    rows=[]
    for s in students:
        rows.append({
            "번호": s.get("number"),
            "이름": s.get("name"),
            "학번": s.get("student_id"),
            "비고": s.get("remark",""),
            "글자수": s.get("record",{}).get("length",0),
        })
    df_summary = pd.DataFrame(rows).sort_values(["번호"]).reset_index(drop=True)

    left, right = st.columns([2, 3])

    with left:
        st.subheader(f"{selected_class}반 학생 목록")
        name_filter = st.text_input("이름 또는 학번 검색", placeholder="예: 김OO 또는 20106")
        only_missing = st.checkbox("비고(보고서 미제출 등) 표시된 학생만 보기", value=False)

        df_view = df_summary.copy()
        if name_filter.strip():
            key = name_filter.strip().lower()
            df_view = df_view[
                df_view["이름"].astype(str).str.contains(key, case=False)
                | df_view["학번"].astype(str).str.contains(key)
            ]
        if only_missing:
            df_view = df_view[df_view["비고"].astype(str).str.strip() != ""]

        st.dataframe(df_view, hide_index=True, use_container_width=True, height=420)

    with right:
        st.subheader("학생 세부 내용")
        st.write("학생을 클릭하면 세특 문구와 비고를 확인할 수 있습니다. (복사 기능 포함)")

        filtered_ids = set(df_view["학번"].astype(str).tolist())
        for s in students:
            if str(s.get("student_id")) not in filtered_ids:
                continue
            num = s.get("number"); name = s.get("name"); sid = s.get("student_id")
            remark = s.get("remark","")
            rec = s.get("record",{})
            length = rec.get("length",0)

            label = f"{num}번 {name} (학번 {sid}, {length}자)"
            if remark:
                label += f"  •  비고: {remark}"

            with st.expander(label, expanded=False):
                if remark:
                    st.warning(f"비고: {remark}")
                content = rec.get("content","")
                st.write(content)
                st.caption(f"글자수(공백 포함): {length}자")
                with st.expander("이 문구만 복사하기"):
                    st.text_area("Ctrl + A, Ctrl + C로 복사하세요.", value=content, height=160)

    st.write("---")
    with st.expander("ℹ️ 사용 안내"):
        st.markdown(
            """
            **사용 방법 요약**

            1. 상단에서 **반을 선택**합니다.
            2. 해당 반 **비밀번호를 입력**한 뒤, **확인 버튼**을 누릅니다.
            3. 왼쪽 표에서 **번호 / 이름 / 학번 / 비고 / 글자수**를 확인합니다.
            4. 비고가 있는 학생만 보고 싶다면 **체크박스**를 선택합니다.
            5. 오른쪽에서 학생을 클릭해 세특 문구를 확인하고, **복사**하여 붙여넣습니다.
            """
        )

if __name__ == "__main__":
    main()
