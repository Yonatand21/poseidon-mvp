from setuptools import find_packages, setup

package_name = "poseidon_ssv_sim"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", ["launch/ssv_vrx.launch.py"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="POSEIDON MVP contributors",
    maintainer_email="contributors@poseidon-mvp.local",
    description="SSV runtime package for VRX-backed Gazebo Harmonic integration.",
    license="TBD",
    entry_points={
        "console_scripts": [
            "mock_ssv_runtime = poseidon_ssv_sim.mock_ssv_runtime:main",
            "ssv_contract_shim = poseidon_ssv_sim.ssv_contract_shim:main",
            "ssv_state_adapter = poseidon_ssv_sim.ssv_state_adapter:main",
        ],
    },
)
