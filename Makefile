DB_URL=postgresql://root:secret@localhost:5432/coach?sslmode=disable

pip-install-base:
	pip3 install -r requirements/base.txt

pip-install-local:
	pip3 install -r requirements/local.txt

run-postgres:
	docker run --name postgres15 -p 5432:5432 -e POSTGRES_USER=root -e POSTGRES_PASSWORD=secret -d postgres:15.10-alpine

start-postgres:
	docker start postgres15

stop-postgres:
	docker stop postgres15

remove-postgres:
	docker rm -f postgres15

create-database:
	docker exec -it postgres15 createdb --username=root --owner=root coach

drop-database:
	docker exec -it postgres15 dropdb coach

make-migrations:
	python3 manage.py makemigrations

apply-migrations:
	python3 manage.py migrate

rollback-migrations:
	python3 manage.py migrate <app_name> <migration_name>

delete-migrations:
	find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
	find . -path "*/migrations/*.pyc" -delete

run-server:
	python3 manage.py runserver
