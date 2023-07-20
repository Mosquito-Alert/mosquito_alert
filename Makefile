.PHONY: help

.DEFAULT_GOAL	:= help
SHELL			:= /bin/bash

APP_NAME 		:= 'mosquito_alert'
REGISTRY_SERVER	:= ghcr.io
REPOSITORY 		:= '$(REGISTRY_SERVER)/mosquito-alert/mosquito_alert'
TAG				:= $(shell git describe --tags)
RELEASE_TAG		?= latest

DOCKER_USER		?= ''

ENVIRONMENT		:= 'production'

DOCKER_COMPOSE_DEV=docker-compose-local.yml

help: # http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


# ===================================================
#  DEV ENVIRONMENT COMMANDS
# ===================================================

start:  ## Create and start containers.
	docker compose -f $(DOCKER_COMPOSE_DEV) up -d --force-recreate

restart:  ## Restart service containers.
	docker compose -f $(DOCKER_COMPOSE_DEV) restart

stop:  ## Stop all containers.
	docker compose -f $(DOCKER_COMPOSE_DEV) stop

down:  ## Stop and remove all containers, networks.
	docker compose -f $(DOCKER_COMPOSE_DEV) down --volumes --remove-orphans

ps:  ## List containers.
	docker compose -f $(DOCKER_COMPOSE_DEV) ps

kill:  # Force stop of containers.
	docker compose -f $(DOCKER_COMPOSE_DEV) kill

logs:  ## Show all containers logs.
	docker compose -f $(DOCKER_COMPOSE_DEV) logs -f

shell:  ## Run shell inside django container.
	docker compose -f $(DOCKER_COMPOSE_DEV) run --rm django /bin/bash

shell_plus:  ## Run shell_plus inside django container.
	docker compose -f $(DOCKER_COMPOSE_DEV) run --rm django python manage.py shell_plus

psql:  ## Start postgres command-line client.
	docker compose -f $(DOCKER_COMPOSE_DEV) exec postgres sh -c 'psql $$POSTGRES_DB $$POSTGRES_USER'

clean_docker:  ## Remove all container and images.
	docker rm $(docker ps -a -q)
	docker rmi $(docker image ls -q)

# ===================================================
# Docker images commands
# ===================================================

login: ## Login to container registry server.
	docker login -u $(DOCKER_USER) $(REGISTRY_SERVER)

build: ## Build the current image version for this app.
	docker build --tag $(APP_NAME)_$(ENVIRONMENT):$(TAG) --build-arg BUILD_ENVIRONMENT=$(ENVIRONMENT) .
	docker tag $(APP_NAME)_$(ENVIRONMENT):$(TAG) $(REPOSITORY):$(TAG)

push: login ## Push the latest image to the repository.
	docker push $(REPOSITORY):$(TAG)

deploy: build login push  ## Build and push a new image version to the reposistory.

release: login  ## Make current docker tag to be retagged as 'latest'.
	docker pull $(REPOSITORY):$(TAG)
	docker tag  $(REPOSITORY):$(TAG) $(REPOSITORY):$(RELEASE_TAG)
	docker push $(REPOSITORY):$(RELEASE_TAG)
