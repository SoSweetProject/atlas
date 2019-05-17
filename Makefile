build:
	docker build -t sosweet/atlas -f Dockerfile .
test:
	docker run -ti --rm --name atlas -p 5000:5000 -v /corpora/data/:/corpora/data/ -v /usr/local/share/cwb/registry:/usr/local/share/cwb/registry sosweet/atlas
enter:
	docker run -ti --rm  --name atlas -p 5000:5000 -v /corpora/data/:/corpora/data/ -v /usr/local/share/cwb/registry:/usr/local/share/cwb/registry --entrypoint=bash sosweet/atlas

enter_container:
	docker exec -ti atlas bash
