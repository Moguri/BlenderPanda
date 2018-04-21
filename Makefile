.PHONEY: lint, lint_templates, todos

# TODO build this from bl_info['version']
ver_str := v0.3.0

lint:
	pylint *.py

todos:
	pylint -d all -e fixme *.py

zip:
	git-archive-all --force-submodules --prefix BlenderPanda BlenderPanda-$(ver_str).zip
