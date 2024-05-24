from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in torre_jp_xi/__init__.py
from torre_jp_xi import __version__ as version

setup(
	name="torre_jp_xi",
	version=version,
	description="Custom App for a Condo",
	author="Lewin Villar",
	author_email="lewin.villar@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
