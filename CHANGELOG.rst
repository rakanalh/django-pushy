v0.1.0 (2014-10-09)
===================
* Initial release

v0.1.1 (2014-10-09)
===================
* Bug fixes

v0.1.2 (2014-10-10)
===================
* Django 1.7 Support

v0.1.3 (2014-10-12)
===================
* Added device queryset filters

v0.1.4 (2014-10-21)
===================
* Added Dict Payload

v0.1.5 (2015-02-10)
===================
* Added APNS support

v0.1.6 (2015-04-22)
===================
* Changed the default payload dispatch to use gcm.json_request as a default. See README.rst for config to change default.

v0.1.7 (2015-05-05)
===================
* Bug fixes in json response handling

v0.1.8 (2015-05-27)
===================
* Changed landscape lint problems / Changed license to MIT

v0.1.9 (2015-10-06)
===================
* Added new database fields date_started and date_finished for push notification
* Notification are started using a chord with a group of tasks and a callback

v0.1.10 (2016-02-22)
====================
* Dropped Python 2.6 support
* Added Restful APIs to create & destroy devices using DRF

v0.1.11 (2016-03-01)
====================
* Fixed a bug in migrations

v0.1.12 (2016-11-19)
====================
* Fixed issue with existing canonical keys
* Removed south migrations completely
* Dropped support for Django 1.6

v0.1.13 (2017-01-05)
====================
* GCMMismatchsenderidexception is caught and an error is reported

v1.0.0 (2017-08-06)
====================
* Migrated from GCM and APNS libraries into pushjack
* Python 3 support
