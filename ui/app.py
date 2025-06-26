import os
import pandas as pd
import streamlit as st
import requests
import st_file_uploader as stf
from streamlit_autorefresh import st_autorefresh
import streamlit_authenticator as stauth

st.markdown(
    """
    <style>
    .block-container {
        max-width: 70%;
        margin-left: auto;
        margin-right: auto;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

password = os.environ.get("STREAMLIT_PASS", "admin")
env_key = os.environ.get("STREAMLIT_KEY", "some_random_key_string")

users = {
    "admin": {"name": "Администратор", "password": password},
}

credentials = {
    "usernames": {
        user: {"name": info["name"], "password": info["password"]}
        for user, info in users.items()
    }
}

authenticator = stauth.Authenticate(
    credentials,
    cookie_name="my_app_auth",
    key=env_key,
    cookie_expiry_days=1,
)




col1, col2, col3 = st.columns([3, 5, 3])
with col2:
    authenticator.login(
        location='main',
        fields={
            "Form name":       "Авторизация",
            "Username":        "Имя пользователя",
            "Password":        "Пароль",
            "Login":           "Войти",
        }
    )

    auth_status = st.session_state.get("authentication_status")
    name = st.session_state.get("name")

    if auth_status is False:
        st.error("❌ Неверное имя пользователя или пароль")
        st.stop()
    if auth_status is None:
        st.warning("🔒 Пожалуйста, войдите")
        st.stop()



col1, col2 = st.sidebar.columns([4,1])
col1.markdown(f"Привет, **{st.session_state['name']}**!")

if col2.button("Выход"):
    authenticator.logout("unused", location="unrendered")
    st.rerun()


# ——————————————
# Авто-обновление каждые 30 секунд
# ——————————————
st.set_page_config(layout="wide")
st_autorefresh(interval=30_000, key="auto_refresh")


API_BASE = os.environ.get("STREAMLIT_API_BASE_URL", "http://localhost:8080/api/v1")

# ——————————————
# Простые функции для API (без кеша!)
# ——————————————
def fetch_sidebar(status: str):
    resp = requests.get(
        f"{API_BASE}/convert",
        params={"status": status, "sort": "desc"},
        timeout=5,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("items", data) if isinstance(data, dict) else data

def fetch_conversions(
    status: str,
    file_name: str | None,
    sort_field: str,
    sort_asc: bool,
):
    resp = requests.get(
        f"{API_BASE}/convert",
        params={"status": status, "file_name": file_name, "sort": "desc"},
        timeout=5,
    )
    resp.raise_for_status()
    data = resp.json()
    items = data.get("items", data) if isinstance(data, dict) else data

    items = sorted(
        items,
        key=lambda x: x.get(sort_field) or "",
        reverse=not sort_asc
    )

    total = len(items)
    start = (page - 1) * page_size
    return items[start : start + page_size], total

# ——————————————
# Sidebar: задачи (каждые 10 сек обновляется)
# ——————————————
st.sidebar.header("Задачи")
for code, title in [("processing", "В обработке"), ("pending", "В очереди")]:
    st.sidebar.subheader(title)
    items = fetch_sidebar(code)
    if not items:
        st.sidebar.info("Пусто")
    else:
        # Заголовок
        c1, c2 = st.sidebar.columns([3, 2])
        c1.markdown("**Файл**")
        c2.markdown("**Создано**")
        # Каждая пара колонок — для одной строки
        for itm in items:
            ts: pd.Timestamp = pd.to_datetime(itm["created_at"], utc=True)
            ts = ts.tz_convert(None)
            formatted = ts.strftime("%Y.%m.%d %H:%M")
            r1, r2 = st.sidebar.columns([3, 2])
            r1.text(itm["file_name"])
            r2.text(formatted)

# ——————————————
# MAIN: загрузка и отправка PDF
# ——————————————
st.title("Конвертация файлов")
custom = stf.create_custom_uploader(
    uploader_msg="Перетащите PDF сюда",
    limit_msg="Максимум 100 МБ",
    button_msg="Выбрать файл",
)
uploaded_file = custom.file_uploader(
    "Выберите PDF для конвертации",
    type=["pdf"],
    key="pdf_uploader",
)
if uploaded_file:
    if uploaded_file.type != "application/pdf":
        st.error("Можно загружать только PDF-файлы!")
    elif uploaded_file.size > 100 * 1024 * 1024:
        st.error("Максимальный размер файла — 100 МБ.")
    elif st.button("Начать конвертацию", key="start_convert"):
        with st.spinner("Отправляю в очередь..."):
            files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
            r = requests.post(f"{API_BASE}/convert", files=files, timeout=10)
        if r.status_code != 202:
            st.error(f"Не удалось создать задачу: {r.text}")
        else:
            st.success("Задача поставлена")
            st.rerun()

st.markdown("---")
st.header("Файлы")

status_opts = [
    ("all", "Все"),
    ("pending", "В очереди"),
    ("processing", "В обработке"),
    ("completed", "Готово"),
    ("failed", "Ошибка"),
]
status_dict = {label: code for code, label in status_opts}
sel_status  = status_dict[st.selectbox("Статус", [lab for _, lab in status_opts], key="f_status")]
name_filter = st.text_input("Название файла содержит", key="f_name")

if "sort_field" not in st.session_state:
    st.session_state.sort_field = "created_at"
    st.session_state.sort_asc   = False
if "page" not in st.session_state:
    st.session_state.page = 1

def on_sort(field):
    if st.session_state.sort_field == field:
        st.session_state.sort_asc = not st.session_state.sort_asc
    else:
        st.session_state.sort_field = field
        st.session_state.sort_asc = True
    st.session_state.page = 1

page_size = 8
page      = st.session_state.page

with st.spinner("Загружаем данные..."):
    page_items, total_items = fetch_conversions(
        sel_status,
        name_filter or None,
        st.session_state.sort_field,
        st.session_state.sort_asc,
    )

c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
def header(col, text, field):
    icon = ""
    if st.session_state.sort_field == field:
        icon = " ▲" if st.session_state.sort_asc else " ▼"
    if col.button(text + icon, key="sort_"+field):
        on_sort(field)

header(c1, "Имя файла",   "file_name")
header(c2, "Статус",      "status")
header(c3, "Создано",     "created_at")
c4.markdown("**Скачать**")

for itm in page_items:
    r1, r2, r3, r4 = st.columns([4, 2, 2, 1])
    r1.write(itm["file_name"])
    r2.write({
        "pending":    "В очереди",
        "processing": "В обработке",
        "completed":  "Готово",
        "failed":     "Ошибка",
    }.get(itm["status"], itm["status"]))
    r3.write(
        pd.to_datetime(itm["created_at"], utc=True)
          .to_pydatetime()
          .astimezone()
          .strftime("%Y.%m.%d %H:%M")
    )
    if itm.get("download_url"):
        url = f"{API_BASE}/{itm['download_url']}"
        r4.markdown(f"[Скачать]({url})")

# ——————————————
# Пагинация
# ——————————————
total_pages = max(1, (total_items - 1) // page_size + 1)
o1, o2, o3, o4, o5 = st.columns([3, 2, 2, 2, 3])
with o2:
    if st.button("◀ Предыдущая", disabled=page<=1, key="pag_prev"):
        st.session_state.page = page - 1
        st.rerun()
with o3:
    st.markdown(f"**Страница {page} из {total_pages}**")
with o4:
    if st.button("Следующая ▶", disabled=page>=total_pages, key="pag_next"):
        st.session_state.page = page + 1
        st.rerun()
