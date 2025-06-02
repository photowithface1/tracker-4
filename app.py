import streamlit as st
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import calendar

DATA_FILE = "habit_web_data.json"

# 預設資料
def default_data():
    return {
        "habits": {},
        "rewards": {},
        "score": 0,
        "checked": {}  # 新增每日打卡紀錄
    }

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return default_data()

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 初始化資料
data = load_data()
today = datetime.now().strftime("%Y-%m-%d")
if "checked" not in data:
    data["checked"] = {}
if today not in data["checked"]:
    data["checked"][today] = []

st.title("🎯 每日習慣與獎勵追蹤")

# ==== 設定習慣 ====
st.sidebar.header("📝 新增或修改習慣")
new_habit = st.sidebar.text_input("習慣名稱")
new_score = st.sidebar.number_input("習慣分數", min_value=1, step=1)
if st.sidebar.button("➕ 加入習慣"):
    if new_habit:
        data["habits"][new_habit] = new_score
        save_data(data)
        st.sidebar.success(f"已新增習慣「{new_habit}」")

# 顯示與刪除習慣
st.sidebar.subheader("🗑 刪除習慣")
habit_to_delete = st.sidebar.selectbox("選擇要刪除的習慣", [""] + list(data["habits"].keys()))
if st.sidebar.button("❌ 刪除習慣"):
    if habit_to_delete:
        data["habits"].pop(habit_to_delete)
        save_data(data)
        st.sidebar.success(f"已刪除習慣「{habit_to_delete}」")

# ==== 設定獎勵 ====
st.sidebar.header("🎁 新增或修改獎勵")
new_reward = st.sidebar.text_input("獎勵名稱")
reward_cost = st.sidebar.number_input("所需分數", min_value=1, step=1)
if st.sidebar.button("🎯 加入獎勵"):
    if new_reward:
        data["rewards"][new_reward] = reward_cost
        save_data(data)
        st.sidebar.success(f"已新增獎勵「{new_reward}」")

# 顯示與刪除獎勵
st.sidebar.subheader("🗑 刪除獎勵")
reward_to_delete = st.sidebar.selectbox("選擇要刪除的獎勵", [""] + list(data["rewards"].keys()))
if st.sidebar.button("❌ 刪除獎勵"):
    if reward_to_delete:
        data["rewards"].pop(reward_to_delete)
        save_data(data)
        st.sidebar.success(f"已刪除獎勵「{reward_to_delete}」")

# ==== 完成習慣打卡 ====
st.header("✅ 今天完成的習慣")
total_score = 0
completed = []

for habit, point in data["habits"].items():
    already_checked = habit in data["checked"][today]
    disabled = already_checked
    label = f"{habit}（+{point}分）"
    if disabled:
        st.checkbox(label + "（已完成）", value=True, disabled=True)
    else:
        if st.checkbox(label):
            total_score += point
            completed.append(habit)

if st.button("👉 完成打卡"):
    if completed:
        data["score"] += total_score
        data["checked"][today].extend(completed)
        save_data(data)
        st.success(f"已新增 {total_score} 分，目前總分為 {data['score']} 分！")
    else:
        st.info("今天的習慣都已完成或尚未勾選")

st.divider()

# ==== 兌換獎勵 ====
st.header("🎁 兌換獎勵")
for reward, cost in data["rewards"].items():
    if st.button(f"兌換：{reward}（{cost} 分）"):
        if data["score"] >= cost:
            data["score"] -= cost
            save_data(data)
            st.success(f"你成功兌換了「{reward}」，剩餘 {data['score']} 分。")
        else:
            st.warning("分數不足，請繼續努力！")

st.divider()
st.metric("⭐ 目前累積總分：", f"{data['score']} 分")

# ==== 額外統計與圖表 ====
st.header("📈 習慣打卡歷史統計")
habit_totals = {habit: 0 for habit in data["habits"]}
daily_scores = {}

for day, habits in data["checked"].items():
    day_score = 0
    for h in habits:
        if h in habit_totals:
            habit_totals[h] += 1
            day_score += data["habits"].get(h, 0)
    daily_scores[day] = day_score

if habit_totals:
    st.subheader("📊 習慣完成次數統計圖")
    fig, ax = plt.subplots()
    ax.bar(habit_totals.keys(), habit_totals.values())
    ax.set_ylabel("完成次數")
    ax.set_title("習慣完成統計")
    st.pyplot(fig)

    st.subheader("📈 每日得分折線圖")
    score_df = pd.DataFrame.from_dict(daily_scores, orient="index", columns=["分數"])
    score_df = score_df.sort_index()
    st.line_chart(score_df)

    st.subheader("🗓️ 每日打卡情況")
    for date in sorted(data["checked"].keys(), reverse=True):
        st.markdown(f"**{date}**：{'、'.join(data['checked'][date]) if data['checked'][date] else '（無打卡）'}")

    st.subheader("📌 習慣完成率（%）")
    total_days = len(data["checked"])
    for habit, count in habit_totals.items():
        percent = (count / total_days) * 100 if total_days > 0 else 0
        st.write(f"{habit}：{percent:.1f}% 完成率")

    st.subheader("🗓️ 打卡月曆視圖")
    selected_month = st.selectbox("選擇月份：", sorted(set([d[:7] for d in data["checked"]]), reverse=True))
    cal = calendar.Calendar()
    days_in_month = [d for d in data["checked"] if d.startswith(selected_month)]
    marked = {d[-2:]: data["checked"][d] for d in days_in_month}

    st.markdown("### ✅ 有打卡日期")
    for day in sorted(marked):
        habits_done = '、'.join(marked[day]) if marked[day] else '（無打卡）'
        st.write(f"{selected_month}-{day}：{habits_done}")
else:
    st.info("尚未有打卡資料可供統計")