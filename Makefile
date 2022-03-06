.PHONY: fmt

fmt:
	black tools forgehub

build:
	flit build

clean:
	rm --recursive dist
	find . --name __pycache__ -exec rm --recursive '{}' +
