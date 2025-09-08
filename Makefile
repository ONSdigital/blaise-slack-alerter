mkfile_dir := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

.PHONY: help
## This help screen
help:
	@echo "$$(tput bold)Available commands:$$(tput sgr0)";echo;sed -ne"/^## /{h;s/.*//;:d" -e"H;n;s/^## //;td" -e"s/:.*//;G;s/\\n## /---/;s/\\n/ /g;p;}" ${MAKEFILE_LIST}|LC_ALL='C' sort -f|awk -F --- -v n=$$(tput cols) -v i=29 -v a="$$(tput setaf 6)" -v z="$$(tput sgr0)" '{printf"%s%*s%s ",a,-i,$$1,z;m=split($$2,w," ");l=n-i;for(j=1;j<=m;j++){l-=length(w[j])+1;if(l<= 0){l=n-i-length(w[j])-1;printf"\n%*s ",-i," ";}printf"%s ",w[j];}printf"\n";}'

.PHONY=format
## Format python
format:
	@poetry run isort .
	@poetry run black .

.PHONY=lint
## Run styling checks for python
lint: format
	@poetry run flake8 --ignore=E501,W503,E203 .
	@poetry run mypy --config-file ${mkfile_dir}mypy.ini .

.PHONY=test
## Run unit tests
test: format lint
	@poetry run python -m pytest

requirements.txt:
	@poetry export -f requirements.txt --without-hashes --output requirements.txt
