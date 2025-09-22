from setuptools import setup, find_packages

setup(
    name='faciliter-lib',
    version='0.2.8',
    description='Shared library for MCP agent tools (internal use only)',
    author='Julien Nadaud',
    author_email='jnadaud@faciliter.ai',
    url='https://github.com/Aiuj/faciliter-lib',
    packages=find_packages(),
    install_requires=[
        'fast-langdetect>=1.0.0',
        'fastmcp>=2.10.6',
        'google-genai>=0.6.0',
        'ollama>=0.3.1',
        'langfuse>=3.2.1',
        'openinference-instrumentation-google-genai>=0.1.5',
        'redis>=6.2.0',
        'openai>=1.41.0',
        'openpyxl>=3.1.5',
        'markdown>=3.8.2',
        'tabulate>=0.9.0',
        'numpy>=2.3.3',

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
