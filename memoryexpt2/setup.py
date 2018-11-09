from setuptools import setup, find_packages


setup_args = dict(
    name='dlgr.memoryexp',
    version="5.0.0",
    description='Demonstration experiments for Dallinger',
    url='http://github.com/Dallinger/Dallinger',
    maintainer='Jordan Suchow',
    maintainer_email='suchow@berkeley.edu',
    license='MIT',
    keywords=['science', 'cultural evolution', 'experiments', 'psychology'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
    ],
    packages=find_packages('.'),
    package_dir={'': '.'},
    namespace_packages=[],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
    ],
    entry_points={
        'dallinger.experiments': [
            'CoordinationChatroom = experiment:CoordinationChatroom',
        ],
    },
)

setup(**setup_args)
