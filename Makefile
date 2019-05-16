build:
	docker build -t ltar/sosweet -f Dockerfile .
test:
	docker run -ti --rm --name sosweet -p 5000:5000 -v /corpora/data/:/corpora/data/ -v /usr/local/share/cwb/registry:/usr/local/share/cwb/registry ltar/sosweet
enter:
	docker run -ti --rm  --name sosweet -p 5000:5000 -v /corpora/data/:/corpora/data/ -v /usr/local/share/cwb/registry:/usr/local/share/cwb/registry --entrypoint=bash ltar/sosweet

enter_container:
	docker exec -ti sosweet bash
