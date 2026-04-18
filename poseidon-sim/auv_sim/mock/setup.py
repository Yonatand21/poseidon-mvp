from setuptools import find_packages, setup

package_name = "poseidon_sim_mock"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="POSEIDON MVP contributors",
    maintainer_email="contributors@poseidon-mvp.local",
    description="Mock sim world publisher for ARM64 hosts without Stonefish.",
    license="TBD",
    entry_points={
        "console_scripts": [
            "mock_world = poseidon_sim_mock.mock_world:main",
        ],
    },
)
