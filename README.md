# Herestapis

[![Binder](https://mybinder.org/badge_logo.svg)](http://mybinder.org/v2/gh/deeplook/herestapis/master?filepath=index.ipynb)
[![Nbviewer](https://github.com/jupyter/design/blob/master/logos/Badges/nbviewer_badge.svg)](http://nbviewer.jupyter.org/github/deeplook/herestapis/tree/master/)

This is a collection of notebooks presented at a ["Geocoding and Mapping" special PyData Berlin meetup](https://www.meetup.com/PyData-Berlin/events/255574946/) on 2018-11-08. They can be executed inside a Jupyter environment kindly hosted by [mybinder.org](mybinder.org). You only need to click the "launch binder" button and wait anywhere between 30 seconds and two minutes.

Of course, you could also download or clone this repo and install the dependencies in `binder/apt.txt` and `binder/environment.yml` locally (the latter with `conda`)... For now the former is recommended, as everything should work (except the `ipyearth` bits, which will be hopefully fixed, soon, too). 

For getting the full experience a registration with https://developer.here.com is needed, together with APP_CODE and APP_ID credentials, which need to be stored in the file `credentials.py.template` (with the `.template` extension removed). 
