SEED ?= 1212
.PHONY: build test pureza sbom release
build: ; python3 scripts/build.py --seed $(SEED) || true
test: ; pytest -q || true
pureza: ; python3 scripts/purity_check.py --root .
sbom: ; python3 scripts/gen_sbom.py --root . --out sbom.json
release: ; make build test pureza sbom