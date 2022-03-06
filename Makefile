.PHONY: fmt

fmt:
	black .

build:
	flit build

clean:
	rm --recursive dist
	find . --name __pycache__ -exec rm --recursive '{}' +
