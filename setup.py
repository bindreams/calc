"""Install script for calc."""
from setuptools import setup

install_requires = [
    "lark-parser",
]

setup(
    name="calc",
    version="1.0.1",
    description="Safe eval-like function for mathematical expressions",
    author="Andrey Zhukov",
    author_email="andres.zhukov@gmail.com",
    license="MIT",
    install_requires=install_requires,
    py_modules=["calc"],
)
