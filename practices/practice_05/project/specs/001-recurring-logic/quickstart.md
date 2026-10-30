# Quickstart: проверка логики

```bash
python3 -m unittest discover tests && pyright
PORT=8001 DB_PATH=/tmp/sroki-rec.db python3 backend/server.py &
curl -s -XPOST localhost:8001/api/deadlines -H 'Content-Type: application/json' \
  -d '{"title":"Отчёт","due_at":"2027-01-31T18:00","recurrence":"monthly"}'      # recurrence, next_id: null
curl -s -XPATCH localhost:8001/api/deadlines/1 -H 'Content-Type: application/json' \
  -d '{"status":"done"}'                       # next_id: 2, next.due_at: 2027-02-28T18:00
curl -s -XPATCH localhost:8001/api/deadlines/1 -d '{"status":"todo"}'   # next: null, 2 остался
curl -s -XPATCH localhost:8001/api/deadlines/1 -d '{"status":"done"}'   # next: null, третьего нет
curl -s -XPATCH localhost:8001/api/deadlines/2 -d '{"recurrence":"hourly"}'  # 400, field recurrence
```
