Installation Guide
==================

Baconian is easy to install. We offer the pip requirement file to install required packages. Make sure
your machine have python 3.5.


1. We recommend you to use anaconda to manage your package and environment, since installing the required packages may
overwrites some of already installed packages with a different version.

.. code-block:: bash

    source activate your_env

2. Clone the source code and install the packages with requirement file:

.. code-block:: bash

    git clone git@github.com:Lukeeeeee/baconian-project.git baconian
    cd path/to/baconian
    pip install -e .

The ``-e`` means "editable", so changes you make to files in the Ray
directory will take effect without reinstalling the package. In contrast, if
you do ``python setup.py install``, files will be copied from the Baconian
directory to a directory of Python packages (often something like
``/home/ubuntu/anaconda3/lib/python3.5/site-packages/baconian``). This means that
changes you make to files in the Baconian directory will not have any effect.


Then you are free to go. You can either use the Baconian as a third party package and import into your own project, or
directly modify it. If you want to use the full environments of gym, e.g., `Mujoco <http://www.mujoco.org>`_,
please refer to its  page to obtain the license and library. Then install the requirements
(you may need to re-install gym after that.)

3. We have implemented many examples, you may try them first at :code:`examples`
