up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

backend-shell:
	docker compose exec backend /bin/sh

frontend-shell:
	docker compose exec frontend /bin/sh

db-shell:
	docker compose exec postgres psql -U postgres -d vendor_onboarding

evaluate:
	PYTHONPATH=backend python backend/scripts/evaluate_mvp.py

worker-once:
	PYTHONPATH=backend python backend/scripts/run_worker.py --once
