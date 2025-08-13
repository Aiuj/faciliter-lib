from setuptools import setup, find_packages

setup(
    name='faciliter-lib',
    version='0.2.2',
    description='Shared library for MCP agent tools (internal use only)',
    author='Julien Nadaud',
    author_email='jnadaud@faciliter.ai',
    url='https://github.com/Aiuj/faciliter-lib',
    packages=find_packages(),
    install_requires=[
        'fast-langdetect>=0.3.2',
        'fastmcp>=2.10.6',
        'langfuse>=3.2.1',
        'redis>=6.2.0',
    ],
    python_requires='>=3.12',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],
    license='MIT',
)
