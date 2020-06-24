import os

from setuptools import find_packages, setup
import versioneer

install_requires = [
    line.rstrip()
    for line in open(os.path.join(os.path.dirname(__file__), "requirements.txt"))
]

setup(
    name="jobcreator",
    install_requires=install_requires,
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="Imaging database and storage",
    url="https://github.com/donatolab/jobcreator",
    license="MIT",
    packages=find_packages(),
    entry_points={"console_scripts": ["jobcreator=jobcreator.__main__:main"],},
    zip_safe=False,
)
