PYTHON := python
COMPOSE := docker-compose
DOCKER := docker

.SILENT: help install-dev lint type build start stop clean

.PHONY: help
help:
	echo Makefile for Python Project Formatting and Dependency Management
	echo Usage:
	echo   make install-dev     Install development dependencies
	echo   make lint            Lint all .py code using flake8
	echo   make type            Type check code using pyright
	echo   make build           Build Docker environment using docker-compose
	echo   make start           Start the Docker environment
	echo   make stop            Stop the Docker environment
	echo   make docs            View documentation
	echo   make clean           Clean the project based on .dockerignore

.PHONY: install-dev
install-dev:
	$(PYTHON) -m pip install --upgrade flake8 pyright

.PHONY: lint
lint:
	$(PYTHON) -m flake8
	echo Linting complete!

.PHONY: type
type:
	$(PYTHON) -m pyright

.PHONY: build
build:
	$(COMPOSE) up -d --build

.PHONY: start
start:
	$(COMPOSE) up -d

.PHONY: stop
stop:
	$(COMPOSE) down -v

.PHONY: clean
clean:
	$(PYTHON) make/clean.py
	echo Project cleaned!
