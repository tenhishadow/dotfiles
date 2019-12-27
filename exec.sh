virtualenv ansible_venv
source ansible_venv/bin/activate
pip install -r requirements.txt

ansible-playbook playbook_install.yml
