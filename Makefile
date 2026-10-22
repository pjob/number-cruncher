.PHONY: run test deb install uninstall clean

run:
	python3 -m number_cruncher

test:
	python3 -m unittest

deb:
	./build-deb.sh

install: deb
	sudo apt install --reinstall ./build/number-cruncher_*_all.deb

uninstall:
	sudo apt remove number-cruncher

clean:
	rm -rf build
