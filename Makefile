.PHONY: install run test demo bundle

install:
	python -m pip install -U pip
	pip install -r requirements.txt

run:
	export PYTHONPATH=$$(pwd) && bin/rlxd

test:
	pytest -q

demo:
	bash scripts/seed_demo.sh && bash scripts/run_demo.sh

bundle:
	bash scripts/build_offline_bundle.sh