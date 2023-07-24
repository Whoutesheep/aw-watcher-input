.PHONY: build test package clean

build:
	poetry install

typecheck:
	poetry run mypy aw_watcher_input --ignore-missing-imports

package:
	pyinstaller aw-watcher-input.spec --clean --noconfirm

clean:
	rm -rf build dist
	rm -rf aw_watcher_input/__pycache__
