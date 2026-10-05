"""Сделки amoCRM без открытых задач или с просроченными задачами (API v4)."""
import os
import time
import requests

BASE = f"https://{os.environ['AMO_SUBDOMAIN']}.amocrm.ru/api/v4"
HEADERS = {"Authorization": f"Bearer {os.environ['AMO_TOKEN']}"}
CLOSED_STATUSES = {142, 143}  # «Успешно реализовано» и «Закрыто и не реализовано»


def get_all(path, key, params=None):
    items, page = [], 1
    while True:
        r = requests.get(f"{BASE}/{path}", headers=HEADERS,
                         params={**(params or {}), "page": page, "limit": 250})
        if r.status_code == 204:  # пустая страница — данных больше нет
            break
        r.raise_for_status()
        items += r.json()["_embedded"][key]
        page += 1
        time.sleep(0.2)  # лимит amoCRM — до 7 запросов в секунду; до 250 записей на страницу
    return items


def problem_deals():
    leads = [l for l in get_all("leads", "leads")
             if l["status_id"] not in CLOSED_STATUSES]
    tasks = get_all("tasks", "tasks",
                    {"filter[entity_type]": "leads", "filter[is_completed]": 0})
    now, open_tasks = int(time.time()), {}
    for t in tasks:
        open_tasks.setdefault(t["entity_id"], []).append(t)

    result = []
    for lead in leads:
        lt = open_tasks.get(lead["id"], [])
        overdue = [t for t in lt if t["complete_till"] < now]
        if not lt or overdue:
            result.append({
                "id": lead["id"],
                "name": lead["name"],
                "manager_id": lead["responsible_user_id"],
                "problem": "нет задач" if not lt else f"просрочено задач: {len(overdue)}",
            })
    return result


if __name__ == "__main__":
    for d in problem_deals():
        print(d)
