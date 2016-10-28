from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='uodm',
      version='0.1.1',
      description='Micro Object-document-mapper',
      long_description=readme(),
      classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Intended Audience :: Developers',
        'Topic :: Database :: Front-Ends'
      ],
      keywords='odm nosql mongodb persistence',
      url='https://bitbucket.org/eiwa_dev/uodm',
      author='Juan I Carrano <jc@eiwa.ag>, Diego Vazquez <dv@eiwa.ag>',
      author_email='jc@eiwa.ag',
      license='MIT',
      py_modules=['uodm'],
      include_package_data=True,
      zip_safe=True
    )
