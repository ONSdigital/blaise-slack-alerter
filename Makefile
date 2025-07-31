.DEFAULT_GOAL := help

.PHONY: help
## This help screen
help:
	@echo "$$(tput bold)Available commands:$$(tput sgr0)";echo;sed -ne"/^## /{h;s/.*//;:d" -e"H;n;s/^## //;td" -e"s/:.*//;G;s/\\n## /---/;s/\\n/ /g;p;}" ${MAKEFILE_LIST}|LC_ALL='C' sort -f|awk -F --- -v n=$$(tput cols) -v i=29 -v a="$$(tput setaf 6)" -v z="$$(tput sgr0)" '{printf"%s%*s%s ",a,-i,$$1,z;m=split($$2,w," ");l=n-i;for(j=1;j<=m;j++){l-=length(w[j])+1;if(l<= 0){l=n-i-length(w[j])-1;printf"\n%*s ",-i," ";}printf"%s ",w[j];}printf"\n";}'

.PHONY=lint
## Run code style linter
lint:
	@poetry run black --check .

.PHONY=format
## Apply code style fixes
format:
	@poetry run black .

.PHONY=check-types
## Run the typechecker
check-types:
	@poetry run mypy .

.PHONY=test
## Run the tests (includes linter and typechecker)
test: lint check-types
	@poetry run python -m pytest

.PHONY=test-bail
test-bail: lint check-types
	@poetry run python -m pytest -x

requirements.txt:
	@poetry export -f requirements.txt --without-hashes --output requirements.txt
