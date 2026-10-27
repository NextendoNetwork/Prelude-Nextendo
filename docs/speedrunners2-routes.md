# SpeedRunners 2 routes

The generated Nextendo hosts list routes ns.photonengine.io to the configured
Nextendo IP. The independent server advertises its own master/game endpoints.
api.braincloudservers.com was already routed for the shared UCH login service.
api.gameanalytics.com also goes to Nextendo's internal accept-and-close sink.

Atmosphere hosts are global while Nextendo mode is selected: Photon and analytics
hosts are shared by other games. Nintendo mode uses the existing restoration path.
User-owned custom hosts keep the existing ownership/refresh behavior.

Update1.2.0, South America, crossplay off: physical Switch and Ryujinx completed
a race and displayed results with equivalent checked hosts routes in the LAN test.
The hosts refresh decision test passes. No NRO was built; this PR changes no release
version, payload, sysmodule, firmware patch or release asset.

Tournaments, friend invitations and durable ranked statistics remain pending.
