from setuptools import setup, find_packages

setup(
    name="backlog_manager",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    entry_points={
        "console_scripts": [
            "backlog-manager=backlog_manager.main:run_cli",
        ],
    },
)