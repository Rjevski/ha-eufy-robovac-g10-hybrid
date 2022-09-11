# Home Assistant integration for Eufy Robovac

This is a crude Home Assistant integration for the Eufy Robovac G10 Hybrid.

It is not "good" code by any means as it's mostly an amalgamation of various previous attempts by the community coupled with my terrible experience at developing Hass addons.

However, it works well enough for my purposes with the G10 Hybrid. Maybe one day I'll have time to polish this up or contribute to other integrations such as LocalTuya, but in the meantime, here is the code as-is with no warranty.


## How to use

* Install the integration using your favorite method
* Set up the integration in your Home Assistant and provide your Eufy credentials
* All vacuums from the account that are reachable on the local network will be added into HA

The integration will dump all the Tuya "DPs" in the "attributes" of the vacuum entity, so you can observe them and infer their meaning, modifying the integration based on your findings if necessary.

It also exposes some other entities such as setting the volume or resetting the consumables (filters, etc) change reminders.


## To do

* move "eufy_local_id_grabber" (another one of my project) into a PyPi package and install it at runtime
* resolve device names & models instead of assuming a G10 Hybrid all the time
* support for other models?
* somehow inherit from LocalTuya's much more polished Tuya implementation?


# Credits / thanks

* [rospogrigio](https://github.com/rospogrigio)'s [localtuya](https://github.com/rospogrigio/localtuya)
* [mitchellrj](https://github.com/mitchellrj)'s [eufy_robovac](https://github.com/mitchellrj/eufy_robovac)
* [bmccluskey](https://github.com/bmccluskey)'s [eufy_vacuum](https://github.com/bmccluskey/eufy_vacuum)
