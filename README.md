
Install

~~~
python3 -m venv venv
source venv/bin/activate
which python
pip install cython
export CWB_DIR=/Users/ltarrade/Documents/cwb-3.0.0-osx-10.5-universal/
pip install -r requirements.txt
# mv ./PyCQP_interface.py ./venv/lib/python3.7/site-packages/
export FLASK_APP=cqp.py
export FLASK_ENV=development
venv/bin/flask run
~~~
