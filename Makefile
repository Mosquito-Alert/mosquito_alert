.PHONY: help

.DEFAULT_GOAL	:= help
SHELL			:= /bin/bash

DOCKER_COMPOSE_DEV=docker-compose-local.yml
DOCKER_COMPOSE_DEV_SSL=docker-compose-local-ssl.yml

DOCKER_COMPOSE_FLAGS := -f $(DOCKER_COMPOSE_DEV)

ifdef SSL
    # If SSL is set, append the SSL compose file
    DOCKER_COMPOSE_FLAGS += -f $(DOCKER_COMPOSE_DEV_SSL)
endif

help: # http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


# ===================================================
#  DEV ENVIRONMENT COMMANDS
# ===================================================

start:  ## Create and start containers.
	docker compose $(DOCKER_COMPOSE_FLAGS) up -d --force-recreate

restart:  ## Restart service containers.
	docker compose $(DOCKER_COMPOSE_FLAGS) restart

stop:  ## Stop all containers.
	docker compose $(DOCKER_COMPOSE_FLAGS) stop

down:  ## Stop all containers.
	docker compose $(DOCKER_COMPOSE_FLAGS) down

ps:  ## List containers.
	docker compose $(DOCKER_COMPOSE_FLAGS) ps

kill:  # Force stop of containers.
	docker compose $(DOCKER_COMPOSE_FLAGS) kill

logs:  ## Show all containers logs.
	docker compose $(DOCKER_COMPOSE_FLAGS) logs -f

shell:  ## Run shell inside django container.
	docker compose $(DOCKER_COMPOSE_FLAGS) run --rm django /bin/bash

psql:  ## Start postgres command-line client.
	docker compose $(DOCKER_COMPOSE_FLAGS) run --rm django python3 manage.py dbshell

db_restore:  ## Restore data to postgres
	docker compose $(DOCKER_COMPOSE_FLAGS) exec -T postgres bash -c "while ! pg_isready -U postgres -d postgres; do sleep 1; done && pg_restore -Fc -U postgres -d postgres" < $(file)

clean_data:  ## Remove any data
	docker compose $(DOCKER_COMPOSE_FLAGS) down postgres --volumes

clean_docker:  ## Remove all container and images.
	docker rm $(docker ps -a -q)
	docker rmi $(docker image ls -q)
