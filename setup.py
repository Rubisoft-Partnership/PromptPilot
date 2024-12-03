from setuptools import setup, find_packages

setup(
    name='promptpilot',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        # List your package dependencies here
        # For example:
        # 'flask',
        # 'langfuse',
    ],
    author='Federico Rubbi',
    description='A package for prompt optimization',
    url='https://github.com/Rubisoft-Partnership/PromptPilot',
    classifiers=[
        'Programming Language :: Python :: 3.9',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',
)