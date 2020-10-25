## Tickets system

To run this project you should previously install all dependencies from `requirements.txt`. Then you probably
must run the following command `python manage.py crontab add` too (it's demanded for start up periodic automatic tasks
in the project).

### Project design

The project is implemented using Django and DRF frameworks. It's based on REST API architecture (all examples 
could be seen in `tickets_component.tests.py`). This project enables to reserving and buying tickets only for logged 
users.
