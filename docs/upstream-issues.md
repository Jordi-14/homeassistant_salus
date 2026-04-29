# Upstream issues from `epoplavskis/homeassistant_salus`

Exported with GitHub CLI.

This is a maintainer backlog and historical reference for issues left in the
upstream Home Assistant integration. It is intentionally not a normal support
document. Use it when looking for old bug reports, device requests, gateway
firmware problems, or collaboration context that may still be useful for future
work.

---

## #85: Can UGE600 stay offline with this integration?

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/85
- State: closed
- Author: @Euron3xt
- Created: 2026-01-09T16:44:40Z
- Updated: 2026-01-18T06:16:26Z
- Labels: none

### Issue body

Quick question.

My plumber is proposing to install Salus devices in my home. From what I've read last year were some problems after an update of the Salus gateways.

If I get the UGE600 as a gateway. Can I take it offline after initial setup and still run the system with this integration? Or does Salus not allow the device to run without their cloud?

If I can't run it without their cloud I will look for a plumber that can also provide other systems.

Thanks for the help!

### Conversation

#### @mkrum001 commented at 2026-01-12T14:29:28Z

Well, if you restrict it's internet access from the router, may be it will not be updated. But do you have guarantee that the new device will came with the old, working firmware?   What will be the heat source ? 

#### @Euron3xt commented at 2026-01-18T06:16:26Z

Currently the heat source is a woody pellet burner. In the future a ground sourced heatpump might be added. But the plumber just told me he can also get Wavin products and those are easily integrated via modbus! :)

---

## #84: The value of the infloor temperature sensors not displayed in HA

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/84
- State: open
- Author: @RazvanRaul666
- Created: 2025-11-19T10:12:07Z
- Updated: 2026-04-22T09:43:13Z
- Labels: none

### Issue body

Hi, 

I have a UGE600 gateway with 10 SQ610 thermostats.  I also have installed some infloor temperature sensors that display the temperature of the floor.  They are installed on the S1/S2 ports. I can see those in the Salus app but not in HA. Am i doing something wrong or is this not supported by the integration? 

Thank you!

<img width="373" height="260" alt="Image" src="https://github.com/user-attachments/assets/539401ec-c899-4f2b-a75c-1f188270637e" />

<img width="564" height="583" alt="Image" src="https://github.com/user-attachments/assets/091a27ca-a91a-4339-adba-3fb3ed5f1212" />

### Conversation

#### @wizake commented at 2026-01-07T19:18:44Z

mine is the same. always has been. I dont think its supported by the integration

#### @daschiOnGitHub commented at 2026-01-08T21:36:31Z

I‘d love to have his feature as well - I assume it needs to be added in the underlying pyit600 library?

#### @leonardpitzu commented at 2026-03-27T10:44:15Z

I might be able to help with that - check my fork, make an issue there and give me as many details as you can. If you feel comfortable install my fork, enable debug mode and give me the logs with or without the under-floor sensors. I do not have the hardware but it might find the data I need in the logs/debug info you can share with me.

#### @daschiOnGitHub commented at 2026-03-27T11:04:49Z

Hi @leonardpitzu, thanks for your offer!
I'm a little bit confused: I think I'm using already your fork in HA...
I also made a log file, but there are not enough details in it I assume - can I get to another log level?

2026-03-27 11:58:56.523 DEBUG (MainThread) [custom_components.salus.gateway] Gateway write → HTTP 200 (128 bytes)
2026-03-27 11:58:56.529 DEBUG (MainThread) [custom_components.salus.gateway] Gateway read → HTTP 200 (25120 bytes)
2026-03-27 11:58:56.537 DEBUG (MainThread) [custom_components.salus.gateway] Gateway read → HTTP 200 (2832 bytes)
2026-03-27 11:58:56.572 DEBUG (MainThread) [custom_components.salus.gateway] Gateway read → HTTP 200 (21744 bytes)
2026-03-27 11:58:56.574 DEBUG (MainThread) [custom_components.salus] Finished fetching salus data in 0.051 seconds (success: True)
2026-03-27 11:58:57.505 DEBUG (MainThread) [custom_components.salus.gateway] Gateway write → HTTP 200 (128 bytes)
2026-03-27 11:59:06.585 DEBUG (MainThread) [custom_components.salus.gateway] Gateway read → HTTP 200 (25168 bytes)
2026-03-27 11:59:06.592 DEBUG (MainThread) [custom_components.salus.gateway] Gateway read → HTTP 200 (2832 bytes)
2026-03-27 11:59:06.618 DEBUG (MainThread) [custom_components.salus.gateway] Gateway read → HTTP 200 (21776 bytes)
2026-03-27 11:59:06.620 DEBUG (MainThread) [custom_components.salus] Finished fetching salus data in 0.043 seconds (success: True)
2026-03-27 11:59:09.801 DEBUG (MainThread) [custom_components.salus.gateway] Gateway write → HTTP 200 (128 bytes)
2026-03-27 11:59:16.638 DEBUG (MainThread) [custom_components.salus.gateway] Gateway read → HTTP 200 (25168 bytes)
2026-03-27 11:59:16.645 DEBUG (MainThread) [custom_components.salus.gateway] Gateway read → HTTP 200 (2832 bytes)
2026-03-27 11:59:16.698 DEBUG (MainThread) [custom_components.salus.gateway] Gateway read → HTTP 200 (21776 bytes)
2026-03-27 11:59:16.700 DEBUG (MainThread) [custom_components.salus] Finished fetching salus data in 0.076 seconds (success: True)

#### @daschiOnGitHub commented at 2026-04-22T09:43:13Z

solved in https://github.com/leonardpitzu/homeassistant_salus/issues/6

---

## #83: SD600 salus

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/83
- State: open
- Author: @digitaldds-sk
- Created: 2025-11-14T10:14:41Z
- Updated: 2025-11-14T10:14:41Z
- Labels: none

### Issue body

Hello from 23 Salus UGE600 gateways connected to Home Assistant via it600 integration.
I use SD600 smoke sensors on about 12 gateways, which were previously available via the local API, but after the latest updates they are no longer fully visible in the API and integration.

In the Salus Smart Home application, the SD600 sensors are displayed correctly, so both the sensors and the gateways themselves are working.
However, the local UGE600 API has stopped providing their data, and therefore it is not possible to obtain information about the sensor status in any local solution. Can you help me with this?

### Conversation

_No comments._

---

## #82: salus ug800 after update can no longer be integrated into iT600 integration

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/82
- State: open
- Author: @spetrupaul
- Created: 2025-11-08T04:44:14Z
- Updated: 2025-12-18T15:07:40Z
- Labels: none

### Issue body

Hello everyone, I have a UG800 gateway that worked perfectly with the Salus iT600 integration. After the last update to the Salus gateway, the integration no longer works.
in the logs I have the following error.
File “/usr/local/lib/python3.13/site-packages/pyit600/encryptor.py”, line 25, in decrypt
padded_data: bytes = decryptor.update(cypher) + decryptor.finalize()
~~~~~~~~~~~~~~~~~~^^
ValueError: The length of the provided data is not a multiple of the block length.

Logger: pyit600
Sursa: custom_components/salus/config_flow.py:44
integrare: Salus iT600 (documentația, probleme)
Prima dată când a avut loc: 06:22:10 (2 occurrences)
Ultima înregistrare: 06:22:12

Bad logger message: Exception. %s / %s ((<class 'ValueError'>, "('The length of the provided data is not a multiple of the block length.',)", ValueError('The length of the provided data is not a multiple of the block length.')))

-unfortunately I can’t downgrade the gateway, is there a solution to this problem?



### Conversation

#### @doriangh commented at 2025-11-14T15:58:35Z

Can confirm that with v020300250804 UG800 is not connecting to HA. All I get is "Unknown error occured"

#### @Macrisu commented at 2025-11-19T17:05:42Z

[home-assistant_salus_2025-11-19T17-08-42.320Z.log](https://github.com/user-attachments/files/23633877/home-assistant_salus_2025-11-19T17-08-42.320Z.log)

Hello! Same problem here, after HA update ;(
UG800 does not work anymore.

#### @ifalex commented at 2025-11-26T22:27:00Z

Same thing.

#### @mlaurids commented at 2025-12-13T08:23:27Z

Same error for me. 

#### @alexconstantin commented at 2025-12-16T11:01:51Z

same here. is this fixable somehow?

#### @doriangh commented at 2025-12-18T14:48:43Z

I have successfully integrated all my salus thermostats using https://github.com/Peterka35/salus-it600-cloud

#### @spetrupaul commented at 2025-12-18T15:07:40Z

functioneaza perfect .Merci de informatie.

---

## #81: UG800 support?

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/81
- State: open
- Author: @vampywiz17
- Created: 2025-10-13T20:21:51Z
- Updated: 2026-03-12T18:48:27Z
- Labels: none

### Issue body

Hello there!

these component are support UG800 gateway?

https://saluscontrols.com/gb/product/ug800-universal-gateway/

### Conversation

#### @mkrum001 commented at 2025-10-20T14:07:50Z

I also got the UG800 and wondering if the support will be added?

#### @vyagi commented at 2025-10-30T12:46:12Z

+1 

#### @digitaldds-sk commented at 2025-11-06T08:59:58Z

I have a SALUS UG800 gateway added via HACS iT600 integration and after the last update of the UG800 gateway, current software version 020300250804, the gateway stopped communicating with HA. Do you have experience with this? If so, how did you solve it? I can't do dawngred on the SALUS Gateway.

#### @mkrum001 commented at 2025-11-10T09:14:13Z

@digitaldds-sk How did you manage to add the iT800 over the HACS iT600?

#### @spetrupaul commented at 2025-11-10T11:55:11Z

i use the ip adress and EUID from ug800 gateway in iT600 integration and the integration worked . I didn't do anything else.

#### @vyagi commented at 2025-11-10T11:58:53Z

Thanks... although I waited so long for the answer that I bought UGE600 ;-). Thank you anyway. 
But I got confirmation from official Salus technical support that the ONLY differences between UGE600 and UG800 are:
1) UG800 supports more devices (like 200 instead 100 or something like this)
2) UG800 initial configuration can be performed wierelessly

None of them are critical for me - so I am glad I bought UGE600 because it was quite cheaper

#### @digitaldds-sk commented at 2025-11-11T06:44:29Z

mkrum001 It didn't work. I added the UG800 gateway through the it600 integration, which worked for me for over half a year. After the last update of the UG800 gateway, this integration stopped working for me.

#### @digitaldds-sk commented at 2025-11-11T06:49:07Z

I basically have the same problem as described in this link. https://github.com/epoplavskis/homeassistant_salus/issues/82



#### @mkrum001 commented at 2025-11-11T10:13:14Z

I just was able to add the UG800 to the Salus iT600 integration and now I can see and control my all 4 thermostats - 3x FC600 and 1x SQ610.

Just added the integration from scratch and enter the IP + EUID. I don't remember if I added them before (I think no), or the integration was already added before receiving the device and so without entering the device info. Anyway it is working now.

<img width="401" height="776" alt="Image" src="https://github.com/user-attachments/assets/64041a9c-fe24-4e63-a8b8-945d71bcb81a" />

#### @spetrupaul commented at 2025-11-11T10:22:41Z

What software version is the gateway?
-if you have a version below version 20250715, do not update because your iT600 integration will no longer work

#### @mkrum001 commented at 2025-11-11T13:23:24Z

Software Version: 020270250303
Coordinator Version: 20250225

#### @spetrupaul commented at 2025-11-11T13:29:13Z

don't update it until a solution is found in the new version

#### @mkrum001 commented at 2025-11-12T16:36:40Z

Looks like my Gateway got updated last night without asking me and now is with 20250715 version. Meanwhile I found that the integration in HACS came from [this](https://github.com/leonardpitzu/homeassistant_salus) repo, but the issues are disabled there.

#### @digitaldds-sk commented at 2025-11-13T07:24:39Z

@mkrum001 mkrum001 and now when you restart the Home assistant abrana from Salus you have ug800 with coordinator version 20250715 or software version 020300250804 so it stops communicating with you. On the Salus ug800 gateway you cannot turn off automatic updates

#### @awhitwam commented at 2025-11-16T23:52:20Z

Since the upgrade, the payload for the web service is now encrypted, hence the HA Integration fails.  I'm currently trying to reverse engineer their flutter app to see if I can crack it.

#### @mkrum001 commented at 2025-11-17T13:36:07Z

I'm also on it but with no dev experience and some AI help so far I know this:
`<html><head></head><body>
Aspect | Old firmware | New firmware
-- | -- | --
Handshake | none | binary /read → /write
Cipher | AES-CBC (static MD5(EUID)) | RC4
Session key | static | per-session MD5(EUID + HS2_first12)
Frame terminator | N/A | 0x16 / 0x17
Payload | JSON | framed binary RC4 ciphertext
Decryption | AES-CBC decryptor | RC4 keystream XOR

</body></html>`

It's verified after I have traced the traffic between mobile device and Gateway in local mode. Afterwards with few test scripts I was able to communicate with the Gateway:

```
python3 local_example.py
Will save frame data to: /home/user/IdeaProjects/pyit600_mk/frame_dumpsLocal Gateway initialized for http://192.168.52.152:80
Using AES-128 (MD5) key: <some_key>
ClientSession created.
[HS1] POST http://192.168.52.152:80/deviceid/read (41B)
[HS1] status=200 len=12985 frames=51
[HS2] POST http://192.168.52.152:80/deviceid/write (174B)
[HS2] status=200 len=33 tail=0x17
Handshake complete.
```

I have no time for now to proceed further...


#### @digitaldds-sk commented at 2026-01-07T09:41:39Z

Good day, even after the update, the UG800 gateway still does not communicate with HA, can anyone help me with this?

#### @mkrum001 commented at 2026-03-12T10:17:06Z

@digitaldds-sk check this out: https://github.com/leonardpitzu/homeassistant_salus


#### @awhitwam commented at 2026-03-12T18:48:27Z

> [@digitaldds-sk](https://github.com/digitaldds-sk) check this out: https://github.com/leonardpitzu/homeassistant_salus

Great job, well done.  

---

## #80: Problem with Salus FC600NH

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/80
- State: open
- Author: @haegele100
- Created: 2025-09-23T17:52:38Z
- Updated: 2025-09-23T17:52:38Z
- Labels: none

### Issue body

Hello, I have a problem with the Salus FC600NH.
I'm getting an error message and can't access the FC600NH.
The system also has an FC600 installed. It's accessible and controllable. The gateway is the UG800.
Please help.

Dieser Fehler stammt von einer benutzerdefinierten Integration

Logger: pyit600
Quelle: custom_components/salus/climate.py:208
Integration: Salus iT600 (Dokumentation, Probleme)
Erstmals aufgetreten: 17:42:43 (12 Vorkommnisse)
Zuletzt protokolliert: 18:53:50

Bad logger message: Exception. %s / %s ((<class 'pyit600.exceptions.IT600CommandError'>, '("iT600 gateway rejected 'write' command with content '{'requestAttr': 'write', 'id': [{'data': {'DeviceType': 100, 'Endpoint': 9, 'UniID': '001e5e09090d8691'}, 'sIT600TH': {'SetHeatingSetpoint_x100': 2450}}]}'",)', IT600CommandError("iT600 gateway rejected 'write' command with content '{'requestAttr': 'write', 'id': [{'data': {'DeviceType': 100, 'Endpoint': 9, 'UniID': '001e5e09090d8691'}, 'sIT600TH': {'SetHeatingSetpoint_x100': 2450}}]}'")))
write failed: {'requestAttr': 'write', 'id': [{'data': {'DeviceType': 100, 'Endpoint': 9, 'UniID': '001e5e09090d8691'}, 'sIT600TH': {'SetHeatingSetpoint_x100': 2600}}]}
Bad logger message: Exception. %s / %s ((<class 'pyit600.exceptions.IT600CommandError'>, '("iT600 gateway rejected 'write' command with content '{'requestAttr': 'write', 'id': [{'data': {'DeviceType': 100, 'Endpoint': 9, 'UniID': '001e5e09090d8691'}, 'sIT600TH': {'SetHeatingSetpoint_x100': 2600}}]}'",)', IT600CommandError("iT600 gateway rejected 'write' command with content '{'requestAttr': 'write', 'id': [{'data': {'DeviceType': 100, 'Endpoint': 9, 'UniID': '001e5e09090d8691'}, 'sIT600TH': {'SetHeatingSetpoint_x100': 2600}}]}'")))
write failed: {'requestAttr': 'write', 'id': [{'data': {'DeviceType': 100, 'Endpoint': 9, 'UniID': '001e5e09090d8691'}, 'sIT600TH': {'SetHeatingSetpoint_x100': 2650}}]}
Bad logger message: Exception. %s / %s ((<class 'pyit600.exceptions.IT600CommandError'>, '("iT600 gateway rejected 'write' command with content '{'requestAttr': 'write', 'id': [{'data': {'DeviceType': 100, 'Endpoint': 9, 'UniID': '001e5e09090d8691'}, 'sIT600TH': {'SetHeatingSetpoint_x100': 2650}}]}'",)', IT600CommandError("iT600 gateway rejected 'write' command with content '{'requestAttr': 'write', 'id': [{'data': {'DeviceType': 100, 'Endpoint': 9, 'UniID': '001e5e09090d8691'}, 'sIT600TH': {'SetHeatingSetpoint_x100': 2650}}]}'")))



### Conversation

_No comments._

---

## #79: Failed to connect, please check IP address 2025.9.1

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/79
- State: open
- Author: @IonutGrigorut
- Created: 2025-09-10T03:06:12Z
- Updated: 2025-09-11T03:36:52Z
- Labels: none

### Issue body

Hello again, anybody has this issue with the 2025.9.1 core update. After this update i can't log in my Salus gateway anymore. Please can anybody help. 
I redownloaded the salus integration from HACS and when i try to connect with the ip adress an coordonator EUID i get this message  : 
"Failed to connect, please check IP address "

### Conversation

#### @andreizancu commented at 2025-09-10T18:36:14Z

Try for euid with 16 of 0. My problem I can see gateway but I can't see thermostats

#### @IonutGrigorut commented at 2025-09-11T03:36:52Z

i tried with the 16 of 0 and it didn't worked, and after that i tried again  with my EUID and now it worked ..... i don't understand .... yesterday i've tried to log in for a dozen of time and i couldn't log in, and today it worked.  

---

## #77: Can't fetch integration files

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/77
- State: closed
- Author: @maxpavlov
- Created: 2025-04-07T08:36:44Z
- Updated: 2025-04-07T11:56:54Z
- Labels: none

### Issue body

Since this morning, way past the 2025.1 update started to see the problem with integration. Don't know exactly why my thermostats dissapeared in the first place but went to hacs and tried to re-download the integration. Logs shows this:

Failed to fetch: `https://files.pythonhosted.org/packages/67/54/777a6562421565e57d89ac0612e0a33a6d0e283b1d55a80278b150df9a48/pyit600-0.5.1-py3-none-any.whl.metadata`

If I manually try to download the file via that link - everything works well and I am able to pull down the file on the same network. 

Without it salus integration obviously can't start. 

### Conversation

#### @maxpavlov commented at 2025-04-07T11:56:53Z

Was able to resolve this by feeding in the fallback DNS servers to my HAOS instance. 

---

## #76: Faild to connect, please check EUID.

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/76
- State: open
- Author: @IonutGrigorut
- Created: 2025-03-03T06:18:26Z
- Updated: 2025-03-25T04:14:49Z
- Labels: none

### Issue body

Hello, i have a new problem since today. 
2025-03-03 07:24:27.073 ERROR (MainThread) [custom_components.salus] Authentication error: check if you have specified gateway's EUID correctly.
 I've tried to delete and reconnect my gateway but i get the error Faild to connect, please check EUID. 
I have to mention that i have the new UG800 Gateway from Salus that worked fine until today in home assistant. 


### Conversation

#### @IonutGrigorut commented at 2025-03-06T05:46:06Z

Hi guys , nobody with this issue? I've tried to redownload Salus from hacs and tried to enable/disable Wi-Fi local  with the Local Wi-Fi Disabled i get the error Cannot connect to IP. with the local wi-fi enabled i stil get the Failed to connect, please check EUID. I've tried several times and still i get that issue . Please somebody help me.... 

#### @nordleuchte commented at 2025-03-09T07:14:59Z

Did you try with EUID 0000000000000000 as described in the readme?

#### @IonutGrigorut commented at 2025-03-09T07:26:54Z

Yes, i did. When i did try EUID 0000000000000000 i get the same message. i do think the problem could be my new UGE800 gateway. Maybe i'm going to change back to the old UGE600 Gateway.  

#### @blebel commented at 2025-03-24T15:24:59Z

I have (well had) the same issue. 
After discussing the issue with Salus support, they said that they dont have any support for HA, no local API at all, just an Alexa and Google Home integration.
They said "it works as it should" when they logged in to my setup.
So to you who got it to work dont "upgrade" anything!
I ditched the Salus hardware and moved on...
I had a UGE600, problem started for me when the old app got replaced with the premium app.
running a portscanner against the gateway shows no open ports at all, and digging in the firewall logs makes you think if they know what they are doing... 

#### @IonutGrigorut commented at 2025-03-25T04:14:49Z

After i updated to 2025.3.4 deleted the Salus iT600 Gateway integration and redownloaded it, it works again. All my salus devices are fully operational in HA. 

---

## #75: SD600 disappearing after a while

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/75
- State: open
- Author: @samuellazea
- Created: 2025-02-26T14:39:26Z
- Updated: 2025-02-26T14:41:13Z
- Labels: none

### Issue body

Hello,

First of all I want to say that this is really a nice integration and it's really appreciated.
In my case I have a UGE600 with multiple thermostats, door sensors and smoke sensors. All works fine for the thermostats, door sensors but for the smoke sensors ( I have 3 ) I was able to discover them and they were ok for a while but now they are unavailable in the integration. I tried to reload the integration, reinstall the integration but without success. On reinstall of the integration they are not available anymore in HA but they are online and visible in the Salus APP.

I did search for a solution and I saw that I am not the only one with this issue. Is there anything that can be done to have them persisted? Was thinking that it might be something like a keep alive or something.

https://github.com/epoplavskis/homeassistant_salus/issues/9#issuecomment-813273374

Thank you lots in advance and again, kudos for the nice work

### Conversation

_No comments._

---

## #74: Setting Preset/Target-Temperature via HA?

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/74
- State: open
- Author: @stvogel
- Created: 2025-02-09T16:10:22Z
- Updated: 2025-02-10T07:56:10Z
- Labels: none

### Issue body

Thanks a lot for this HA-integration. I have a Salus SQ610
and I see I have different actions in HA, e.g. change HVAC mode or change Preset mode

What I would really like to do is to set the preset-temperature.
To reduce the temperature when everybody is gone (e.g. in office-hours) for example.
This is currenlty not possible? Or am I missing something?

### Conversation

#### @stvogel commented at 2025-02-10T07:55:41Z

Seems to be related to #58 

---

## #73: Is there any way to get running state for a thermostat-connected valve

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/73
- State: open
- Author: @maxpavlov
- Created: 2025-01-25T20:55:07Z
- Updated: 2026-01-08T21:44:48Z
- Labels: none

### Issue body

Salus app shows the running state for both TRVs and underfloor heating zones. It looks like this in the app:

![Image](https://github.com/user-attachments/assets/cbca2afd-d5cb-4220-9c48-f9eed0413da7)

Is there a way to get this running state via salus integration so that I can somehow project the running state on the HA dashboard?

### Conversation

#### @zylxpl commented at 2025-01-28T12:07:37Z

Hi,
I’ve made some modifications to enable reading values such as TRV temperature, TRV mode, and valve open status (in %). However, I’m not sure what the "running state" represents in this context. If it’s something reported by the device, there’s likely a way to read it. But if it’s calculated by the cloud, it’s probably not possible.

Let me know what you think!

#### @mariussoica commented at 2025-01-28T12:53:18Z

Hey, 
I think what @maxpavlov  wants to say is that the binary_sensors from this integration are not reporting correct. 
Like for example the TRV is shown as an Binary_sensors with true / false (open / close), but for no reason some of them are report as open although are closed. If they changes the state in HA they remain with the same state as before. 

#### @daschiOnGitHub commented at 2026-01-08T21:41:09Z

Hi,
From my observations on a underfloor heating valve (on/off only) I assume „Running State“ is basically a duty cycle of the binary valve in a given period of time. So the „on“ time divided by the total time. This should easily be added in HA by creating a Virtual Sensor.

---

## #72: mqtt2 integration

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/72
- State: open
- Author: @mjrybarski
- Created: 2025-01-14T00:17:31Z
- Updated: 2025-04-08T13:50:28Z
- Labels: none

### Issue body

Guys maybe i am a noob but is there some integration/way of connecting our saluses (or at least fc600) via MQTT2. 



### Conversation

#### @nordleuchte commented at 2025-01-16T19:20:57Z

You mean Zigbee2MQTT? The FC600 is listed as a supported device: https://www.zigbee2mqtt.io/devices/FC600.html


#### @mharizanov commented at 2025-01-17T06:06:30Z

> You mean Zigbee2MQTT? The FC600 is listed as a supported device: https://www.zigbee2mqtt.io/devices/FC600.html
> 

Interesting, this is relatively new. If this works, we don't need the barely supported Salus integration and the gateway. I will investigate it and switch 

#### @nordleuchte commented at 2025-01-17T08:25:55Z

Let us know how it worked out. I have the SQ610RF thermostats which seem unsupported by Z2M for now. But maybe there's a chance to get rid of that otherwise useless Salus gateway.

#### @mharizanov commented at 2025-01-18T15:28:04Z

I could not get the FC600 to work with zigbee2mqtt, it is a cursed device in my opinion :) It seems to pair with z2m, and z2m shows it, but the device itself is stuck with "FC app" on the screen and no buttons work. I don't have time to dig further, hard resetting it and back to the old mode of operation 

#### @efenex commented at 2025-04-08T13:50:27Z

can confirm the exact same behaviour with my FC600 units: pairs correctly but the unit is stuck on FC app. From the manual, this should disappear once it is configured in the app; I suppose zigbee2mqtt does not confirm the pairing in the way that the FC600 expects.

---

## #71: Support for Salus iT800?

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/71
- State: open
- Author: @Aelbaert
- Created: 2025-01-07T11:34:13Z
- Updated: 2025-01-07T11:34:13Z
- Labels: none

### Issue body

Hello, I received a IT800 thermostat with my newly installed heatpump. 
I tried to use the iT600 custom component, but I get error: 'Failed to connect, please check IP address'. 
Looking at section 'troubleshooting'; option 'Disable Local WiFi Mode' isn't available in the Salus Premium Lite app.

Does anybody have a solution (update?) for this.

Kind regards,
Albert



### Conversation

_No comments._

---

## #70: 2025.1 Salus HA integration stopped working

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/70
- State: open
- Author: @IonutGrigorut
- Created: 2025-01-04T06:46:58Z
- Updated: 2025-04-16T08:58:26Z
- Labels: none

### Issue body

After my 2025.1 update my Salus thermostats stopped working in Home Assistant. Interesting is  after my re-enable my Salus integration i can see my switches  and plugs entities from Salus, but cant see my Thermostats entities. Can somebody help, please 

### Conversation

#### @nanoBit93 commented at 2025-01-04T07:20:58Z

Same issue, it‘s a general issue it seems since the integration is using a deprecated function. Here‘s the relevant part of my logs:

2025-01-04 07:46:36.075 WARNING (MainThread) [homeassistant.helpers.frame] Detected code that calls async_forward_entry_setup for integration salus with title: Salus Gateway and entry_id: ###(censored my EID)###, during setup without awaiting async_forward_entry_setup, which can cause the setup lock to be released before the setup is done. This will stop working in Home Assistant 2025.1, please report this issue
Stack (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/usr/src/homeassistant/homeassistant/__main__.py", line 227, in <module>
    sys.exit(main())
  File "/usr/src/homeassistant/homeassistant/__main__.py", line 213, in main
    exit_code = runner.run(runtime_conf)
  File "/usr/src/homeassistant/homeassistant/runner.py", line 154, in run
    return loop.run_until_complete(setup_and_run_hass(runtime_config))
  File "/usr/local/lib/python3.13/asyncio/base_events.py", line 707, in run_until_complete
    self.run_forever()
  File "/usr/local/lib/python3.13/asyncio/base_events.py", line 678, in run_forever
    self._run_once()
  File "/usr/local/lib/python3.13/asyncio/base_events.py", line 2033, in _run_once
    handle._run()
  File "/usr/local/lib/python3.13/asyncio/events.py", line 89, in _run
    self._context.run(self._callback, *self._args)
  File "/usr/src/homeassistant/homeassistant/config_entries.py", line 2353, in async_forward_entry_setup
    _report_non_awaited_platform_forwards(entry, "async_forward_entry_setup")
  File "/usr/src/homeassistant/homeassistant/config_entries.py", line 1199, in _report_non_awaited_platform_forwards
    report_usage(
  File "/usr/src/homeassistant/homeassistant/helpers/frame.py", line 234, in report_usage
    _LOGGER.warning(msg, stack_info=True)


EDIT: The issue was actually reported months ago, I guess the integration is not being maintained anymore.

#### @uzzitm commented at 2025-01-04T09:28:30Z

Same issue here.After 2025.1 update it stopped working

#### @IonutGrigorut commented at 2025-01-04T11:00:37Z

maybe somebody can help us with this ... Please

#### @palsbo commented at 2025-01-04T11:27:32Z

Same problem. Some functions are unsupported in 2025.1. There was a warning a few month ago, but what to do about it?

#### @bm123456 commented at 2025-01-04T12:05:31Z

I replaced my current instalation

\config\custom_components\salus

with

https://github.com/leonardpitzu/homeassistant_salus/tree/master/custom_components/salus

and restarted the Home Assistant.
The problem was solved and integration is working again like before.
Thank you @leonardpitzu


#### @nanoBit93 commented at 2025-01-04T13:12:38Z

Worked perfectly, thank you so much!!

For the others, in case you don't find the fork, that @bm123456 posted, in HACS (for me it didn't show there):

1. Remove the existing Salus integration + restart HA
2. Add a custom repository in HACS using the link above + restart HA
3. Add your Salus hub again

EDIT: By the way - if you don't change the names of your devices in the Salus app in the mean time (and assuming you didn't rename them in HA), HA will recognize the devices as the old ones... meaning all automations and visuals will work without and further action and you'll be able to see the historic data of the thermostats.

#### @sorenfisker commented at 2025-01-04T15:43:47Z

Is this repository unsupported?

There have been numerous reports of this error over the last 6 months but absolutely no response from @epoplavskis.

#### @nmatei commented at 2025-01-04T15:47:55Z

I dit a rollback HA back to 2024.12.5 (hard to imagine reconfiguring from scratch, i'll do it if that PR is not merged :( )
I'm glad there are multiple contributors, but is hard to change entire integration... maybe that could be a next step to HA - replace integration URL? :)

#### @palsbo commented at 2025-01-04T17:39:50Z

Worked for me. Thank you!

<http://www.e-julemaerket.dk/?b43be142-3678-476b-ba11-dded21173369>


lør. 4. jan. 2025 kl. 13.05 skrev bm123456 ***@***.***>:

> I replaced my current instalation
>
> \config\custom_components\salus
>
> with
>
>
> https://github.com/leonardpitzu/homeassistant_salus/tree/master/custom_components/salus
>
> and restarted the Home Assistant.
> The problem was solved and integration is working again like before.
> Thank you @leonardpitzu <https://github.com/leonardpitzu>
>
> —
> Reply to this email directly, view it on GitHub
> <https://github.com/epoplavskis/homeassistant_salus/issues/70#issuecomment-2571268591>,
> or unsubscribe
> <https://github.com/notifications/unsubscribe-auth/AAYJU475W6D2Y3GRRHVJSJT2I7FCFAVCNFSM6AAAAABUS2NPQSVHI2DSMVQWIX3LMV43OSLTON2WKQ3PNVWWK3TUHMZDKNZRGI3DQNJZGE>
> .
> You are receiving this because you commented.Message ID:
> ***@***.***>
>


#### @redbass commented at 2025-01-04T18:05:37Z

[bm123456](https://github.com/bm123456)
Could you please add more steps on how to solve this issue?

[nanoBit93](https://github.com/nanoBit93)
when I click on remove integration this message appears:

```
Integration is configured
The Salus iT600 integration is configured or ignored. You need to delete the configuration for it before removing it from HACS.

                         IGNORE   NAVIGATE
```

What should I do if I want to preserve all my data?

Sorry both, I'm new in HA community

#### @cflansbaum commented at 2025-01-04T20:29:55Z

@redbass 
1. Under the HACS Integration page, remove the current Salus repository (you can choose the Ignore option - i.e. not removing your integration setup under the Devices and Services page.  Restart HA.
2. Add a custom repository in HACS (using the 3 dots in the upper corner of the page) Use the URL - https://github.com/leonardpitzu/homeassistant_salus
3. After step 2 - click on the 3 dots to the right of this entry and click download (I ALWAYS forget this step and wonder why the repository didn't load...) Restart HA
4. Go back into your Devices and Services page and confirm everything is as it should be

#### @bm123456 commented at 2025-01-04T20:55:52Z

Hi @redbass ,

I'm not using HACS.
I have installed the "Samba share" Add-on, in order to have access to Home Assiatnt files from my Windows machine.
So from "Windows Explorer" the path to the "salus" integration is (in my case the Home Asistant IP address is 182.160.50.30):
\\182.160.50.30\config\custom_components\salus
You just need to delete the "salus" foder.
Aftre that download the @leonardpitzu version from here:
https://github.com/leonardpitzu/homeassistant_salus/archive/refs/heads/master.zip
From the ZIP file you need to get the "salus" folder and copy it to the place of the old one.
Restart the Home Asistan and all will work like before.

Regards

#### @redbass commented at 2025-01-04T21:19:55Z

[cflansbaum](https://github.com/cflansbaum)
It did work as you suggested. Thanks

[bm123456](https://github.com/bm123456)
I will surely try to install the SAMBA share

As a side note, To save some money I'm using a Salus Smart Home Gateway UG600 to manage an OMNIE underfloor heating system (https://omnie.co.uk/omnie-home-smart-thermostat/)
It seems that are both perfectly compatible (I guess just a rebranding)

#### @IonutGrigorut commented at 2025-01-05T06:48:22Z

Thank you every one of you. This morning i've done it. All thermostats work again with the HA. Thanks again and have a good day

#### @larrybml commented at 2025-01-08T11:24:13Z

> Hi @redbass ,
> 
> I'm not using HACS. I have installed the "Samba share" Add-on, in order to have access to Home Assiatnt files from my Windows machine. So from "Windows Explorer" the path to the "salus" integration is (in my case the Home Asistant IP address is 182.160.50.30): \182.160.50.30\config\custom_components\salus You just need to delete the "salus" foder. Aftre that download the @leonardpitzu version from here: https://github.com/leonardpitzu/homeassistant_salus/archive/refs/heads/master.zip From the ZIP file you need to get the "salus" folder and copy it to the place of the old one. Restart the Home Asistan and all will work like before.
> 
> Regards

I did like this, worked right after restart of HA.

Thank you everyone for support!!!

#### @IonutGrigorut commented at 2025-01-09T16:30:11Z

hi ... after updating to core 2025.1.1 salus gateway doesn't work anymore. @leonardpitzu can you please help me ? Because i am a complete newbie to HA

#### @IonutGrigorut commented at 2025-01-10T19:04:43Z

i've deleted the Salus gateway and re-integrated the salus gateway  and now everything works again ... i think i'm not going to update the HA anymore :) 

#### @parost666 commented at 2025-01-10T19:24:50Z

@IonutGrigorut if you start at the beginning of this thread you will get information on how to solve this problem. Take a look at the post by @cflansbaum that will help you I think.

#### @fastvd commented at 2025-01-10T20:40:40Z

i have a weird problem that i couldn't remove my device at all in the integrations....it just hung for a long time and never removed the device.
removing the old 0.51 integration didn't help either. then i just deleted the whole folder in custom_components and after that all my devices are gone. then I installed your new 0.53, restarted HA and tried to re-add the integration by default ...but at this point HA doesn't even open the form where you need to enter the ip and serial number.
![image](https://github.com/user-attachments/assets/533e67f6-a5eb-4000-b9b7-cfefaefcd052)


#### @nordleuchte commented at 2025-01-24T10:01:11Z

PR has been merged and there is a new release.
I think this can be closed now.
@epoplavskis 

#### @hawkpd commented at 2025-04-15T11:48:10Z

This has been working fine for me for many months now but one of my room thermostat entities dropped out on Sunday night.  I think I applying other HA updates at the time so there may have been an HA restart but the other 5 thermostats are working fine! 
 The thermostat that is not showing up in HA from physical inspection is fine and shows up and is controllable fine in the Salus App.

The error I get in HA is:

![Image](https://github.com/user-attachments/assets/4a058582-8fef-49fb-91cb-a1cadfcf604a)

I've tried all the usual - restart HA, apply HA updates, restarted the Salus hub, etc but no joy.

![Image](https://github.com/user-attachments/assets/c3fec55f-3ff2-4b4e-828e-c039e939dd76)



Any ideas anyone? @leonardpitzu



#### @leonardpitzu commented at 2025-04-15T12:04:50Z

Manually, that is using the physical buttons on the device, change the thermostat set temperature by something and validate it. It should come up.

#### @hawkpd commented at 2025-04-15T12:45:48Z

> Manually, that is using the physical buttons on the device, change the thermostat set temperature by something and validate it. It should come up.

It shows as unavailable.

![Image](https://github.com/user-attachments/assets/dc1dac85-d84d-40f5-b71e-4e9e89f7864a)

  

#### @hawkpd commented at 2025-04-16T08:58:24Z

@leonardpitzu are there any log files I can share to assist with trying to diagnose this?


---

## #69: HomeKit

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/69
- State: open
- Author: @raympestana
- Created: 2024-12-16T14:28:04Z
- Updated: 2024-12-16T14:28:04Z
- Labels: none

### Issue body

Hi
Love this tech!

Anyway we could please have HomeKit recognise some of the "OneTouch" settings on the Salus app as perhaps a scene in HomeKit? Thank you

### Conversation

_No comments._

---

## #68: Will stop working at 2025.1 - "code that calls async_forward_entry_setup" and "deprecated supported features values"

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/68
- State: closed
- Author: @snigehere
- Created: 2024-11-11T14:51:19Z
- Updated: 2025-01-24T11:35:42Z
- Labels: none

### Issue body

I see multiple issues reported in the logs where support for deprecated stuff is ending 

The next critical ones for me stop in 2025.1 - two issues reported:

2024-11-11 14:34:40.794 WARNING (MainThread) [homeassistant.helpers.frame] Detected code that calls async_forward_entry_setup for integration salus with title: xxxxxx and entry_id: yyyyyyyyyyyyyyyyyyyyy, during setup without awaiting async_forward_entry_setup, which can cause the setup lock to be released before the setup is done. This will stop working in Home Assistant 2025.1. Please report this issue.

2024-11-11 14:34:40.786 WARNING (MainThread) [homeassistant.helpers.entity] Entity None (<class 'custom_components.salus.climate.SalusThermostat'>) is using deprecated supported features values which will be removed in HA Core 2025.1. Instead it should use <ClimateEntityFeature.TARGET_TEMPERATURE|PRESET_MODE: 17>, please create a bug report at https://github.com/jvitkauskas/homeassistant_salus/issues and reference https://developers.home-assistant.io/blog/2023/12/28/support-feature-magic-numbers-deprecation

### Conversation

#### @mdelalan commented at 2024-12-08T19:25:38Z

Hi,
I have the same warning in my HA logs :

WARNING (MainThread) [homeassistant.helpers.frame] Detected that custom integration 'salus' calls async_forward_entry_setup for integration, salus with title: Salus iT600 Gateway and entry_id: xxxxxxxx, which is deprecated and will stop working in Home Assistant 2025.6, await async_forward_entry_setups instead at custom_components/salus/__init__.py, line 80: hass.async_create_task(, please create a bug report at https://github.com/jvitkauskas/homeassistant_salus/issues

WARNING (ImportExecutor_0) [homeassistant.components.climate.const] HVAC_MODE_HEAT was used from salus, this is a deprecated constant which will be removed in HA Core 2025.1. Use HVACMode.HEAT instead, please report it to the author of the 'salus' custom integration

WARNING (ImportExecutor_0) [homeassistant.components.climate.const] HVAC_MODE_COOL was used from salus, this is a deprecated constant which will be removed in HA Core 2025.1. Use HVACMode.COOL instead, please report it to the author of the 'salus' custom integration

WARNING (ImportExecutor_0) [homeassistant.components.climate.const] HVAC_MODE_OFF was used from salus, this is a deprecated constant which will be removed in HA Core 2025.1. Use HVACMode.OFF instead, please report it to the author of the 'salus' custom integration

WARNING (MainThread) [homeassistant.helpers.entity] Entity None (<class 'custom_components.salus.climate.SalusThermostat'>) is using deprecated supported features values which will be removed in HA Core 2025.1. Instead it should use <ClimateEntityFeature.TARGET_TEMPERATURE|PRESET_MODE: 17>, please create a bug report at https://github.com/jvitkauskas/homeassistant_salus/issues and reference https://developers.home-assistant.io/blog/2023/12/28/support-feature-magic-numbers-deprecation

WARNING (MainThread) [homeassistant.components.climate] Entity None (<class 'custom_components.salus.climate.SalusThermostat'>) implements HVACMode(s): off, heat, auto and therefore implicitly supports the turn_on/turn_off methods without setting the proper ClimateEntityFeature. Please create a bug report at https://github.com/jvitkauskas/homeassistant_salus/issues

@epoplavskis have you planed to update the code in order to work with HA 2025.1 version ?

#### @nordleuchte commented at 2024-12-16T19:50:03Z

There is an (untested?) pull request to deal with this: https://github.com/epoplavskis/homeassistant_salus/pull/61

#### @StLukesLivestream commented at 2025-01-02T21:37:11Z

@leonardpitzu 
Thanks for your work, its really appreciated - I installed your branch and now everything is working without warnings.  If the code gets merged I will switch back but its been outstanding for a while so maybe you are stuck with people hanging on your code!

#### @nmatei commented at 2025-01-04T15:45:40Z

for now, i think is easy for me to rollback HA back to 2024.12.5 (hard to imagine reconfiguring from scratch, i'll do it if that PR is not merged :( )

#### @nordleuchte commented at 2025-01-24T10:00:36Z

PR has been merged and there is a new release.
I think this can be closed now.

---

## #67: Salus iT600 Fahrenheit to Celsius

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/67
- State: closed
- Author: @yzarc7
- Created: 2024-11-05T12:08:12Z
- Updated: 2024-11-06T09:31:11Z
- Labels: none

### Issue body

Is there an easy way to change degrees Fahrenheit to Celsius?

Solved.
Wrong config in my home assistant system.

### Conversation

_No comments._

---

## #66: pyit600.exceptions.IT600CommandError: Unknown error occurred while communicating with iT600 gateway

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/66
- State: open
- Author: @prupert
- Created: 2024-11-03T12:11:18Z
- Updated: 2024-11-03T12:12:01Z
- Labels: none

### Issue body

While trying to add the Salus integration I instantaneously get "Unknown error occured" in the Home Assistant web interface. Upon investigation the logs I see the following errors.

When trying to add the gateway using the real EUID:
```
2024-11-03 13:04:00.179 ERROR (MainThread) [aiohttp.server] Error handling request
Traceback (most recent call last):
File "/usr/local/lib/python3.12/site-packages/pyit600/gateway.py", line 922, in _make_encrypted_request
with async_timeout.timeout(self._request_timeout):
TypeError: 'Timeout' object does not support the context manager protocol
The above exception was the direct cause of the following exception:
Traceback (most recent call last):
File "/usr/local/lib/python3.12/site-packages/aiohttp/web_protocol.py", line 477, in _handle_request
resp = await request_handler(request)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.12/site-packages/aiohttp/web_app.py", line 559, in _handle
return await handler(request)
^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.12/site-packages/aiohttp/web_middlewares.py", line 117, in impl
return await handler(request)
^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/components/http/security_filter.py", line 92, in security_filter_middleware
return await handler(request)
^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/components/http/forwarded.py", line 83, in forwarded_middleware
return await handler(request)
^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/components/http/request_context.py", line 26, in request_context_middleware
return await handler(request)
^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/components/http/ban.py", line 85, in ban_middleware
return await handler(request)
^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/components/http/auth.py", line 242, in auth_middleware
return await handler(request)
^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/components/http/headers.py", line 32, in headers_middleware
response = await handler(request)
^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/helpers/http.py", line 73, in handle
result = await handler(request, **request.match_info)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/components/http/decorators.py", line 81, in with_admin
return await func(self, request, *args, **kwargs)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/components/config/config_entries.py", line 222, in post
return await super().post(request, flow_id)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/components/http/data_validator.py", line 74, in wrapper
return await method(view, request, data, *args, **kwargs)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/helpers/data_entry_flow.py", line 122, in post
result = await self._flow_mgr.async_configure(flow_id, data)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/data_entry_flow.py", line 370, in async_configure
result = await self._async_configure(flow_id, user_input)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/data_entry_flow.py", line 417, in _async_configure
result = await self._async_handle_step(
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/data_entry_flow.py", line 520, in _async_handle_step
result: _FlowResultT = await getattr(flow, method)(user_input)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/config/custom_components/salus/config_flow.py", line 44, in async_step_user
unique_id = await gateway.connect()
^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.12/site-packages/pyit600/gateway.py", line 101, in connect
all_devices = await self._make_encrypted_request(
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.12/site-packages/pyit600/gateway.py", line 957, in _make_encrypted_request
raise IT600CommandError(
pyit600.exceptions.IT600CommandError: Unknown error occurred while communicating with iT600 gateway
2024-11-03 13:04:00.188 ERROR (MainThread) [homeassistant] Error doing job: Unclosed client session (None)
```

When trying to add the gateway using the EUID `0000000000000000`
```
2024-11-03 13:04:40.960 ERROR (MainThread) [aiohttp.server] Error handling request
Traceback (most recent call last):
File "/usr/local/lib/python3.12/site-packages/pyit600/gateway.py", line 922, in _make_encrypted_request
with async_timeout.timeout(self._request_timeout):
TypeError: 'Timeout' object does not support the context manager protocol
The above exception was the direct cause of the following exception:
Traceback (most recent call last):
File "/usr/local/lib/python3.12/site-packages/aiohttp/web_protocol.py", line 477, in _handle_request
resp = await request_handler(request)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.12/site-packages/aiohttp/web_app.py", line 559, in _handle
return await handler(request)
^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.12/site-packages/aiohttp/web_middlewares.py", line 117, in impl
return await handler(request)
^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/components/http/security_filter.py", line 92, in security_filter_middleware
return await handler(request)
^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/components/http/forwarded.py", line 83, in forwarded_middleware
return await handler(request)
^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/components/http/request_context.py", line 26, in request_context_middleware
return await handler(request)
^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/components/http/ban.py", line 85, in ban_middleware
return await handler(request)
^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/components/http/auth.py", line 242, in auth_middleware
return await handler(request)
^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/components/http/headers.py", line 32, in headers_middleware
response = await handler(request)
^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/helpers/http.py", line 73, in handle
result = await handler(request, **request.match_info)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/components/http/decorators.py", line 81, in with_admin
return await func(self, request, *args, **kwargs)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/components/config/config_entries.py", line 222, in post
return await super().post(request, flow_id)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/components/http/data_validator.py", line 74, in wrapper
return await method(view, request, data, *args, **kwargs)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/helpers/data_entry_flow.py", line 122, in post
result = await self._flow_mgr.async_configure(flow_id, data)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/data_entry_flow.py", line 370, in async_configure
result = await self._async_configure(flow_id, user_input)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/data_entry_flow.py", line 417, in _async_configure
result = await self._async_handle_step(
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/data_entry_flow.py", line 520, in _async_handle_step
result: _FlowResultT = await getattr(flow, method)(user_input)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/config/custom_components/salus/config_flow.py", line 44, in async_step_user
unique_id = await gateway.connect()
^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.12/site-packages/pyit600/gateway.py", line 101, in connect
all_devices = await self._make_encrypted_request(
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.12/site-packages/pyit600/gateway.py", line 957, in _make_encrypted_request
raise IT600CommandError(
pyit600.exceptions.IT600CommandError: Unknown error occurred while communicating with iT600 gateway
2024-11-03 13:04:40.966 ERROR (MainThread) [homeassistant] Error doing job: Unclosed client session (None)
```

I have confirmed that the settings are correct (local WiFi is NOT disabled), I can ping the gateway device IP address and it gives HTTP responses. 

### Conversation

_No comments._

---

## #65: New HTR-RF(20) without climate entity

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/65
- State: open
- Author: @marithpl
- Created: 2024-10-28T10:03:25Z
- Updated: 2024-10-28T10:03:25Z
- Labels: none

### Issue body

HTR-RF(20)
producent: SALUS
firmware: 00160501

After few years I had warranty replaced an HTR-RF(20) thermostat. Old one was integrated with custom_component, the new one shows in integration but without any entity (including climate type) so I am not able to set/read temperature .

<img width="1035" alt="image" src="https://github.com/user-attachments/assets/65994bb5-9dbc-4cd1-b84d-197b72b78714">


### Conversation

_No comments._

---

## #64: HA 2025.1 SalusThermostat is using deprecated features

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/64
- State: open
- Author: @peter4200
- Created: 2024-09-11T17:13:01Z
- Updated: 2025-01-24T10:04:21Z
- Labels: none

### Issue body

My home-assistant.log has many entries like these:

```
2024-09-11 18:52:52.314 WARNING (MainThread) [homeassistant.helpers.entity] Entity None (<class 'custom_components.salus.climate.SalusThermostat'>) is using deprecated supported features values which will be removed in HA Core 2025.1. Instead it should use <ClimateEntityFeature.TARGET_TEMPERATURE|PRESET_MODE: 17>, please create a bug report at https://github.com/jvitkauskas/homeassistant_salus/issues and reference https://developers.home-assistant.io/blog/2023/12/28/support-feature-magic-numbers-deprecation
2024-09-11 18:52:52.314 WARNING (MainThread) [homeassistant.components.climate] Entity None (<class 'custom_components.salus.climate.SalusThermostat'>) implements HVACMode(s): off, heat, auto and therefore implicitly supports the turn_on/turn_off methods without setting the proper ClimateEntityFeature. Please create a bug report at https://github.com/jvitkauskas/homeassistant_salus/issues

```

### Conversation

#### @nordleuchte commented at 2025-01-24T10:04:20Z

This should be closed as a duplicate of #68 
@epoplavskis 

---

## #63: HA 2025.6 problem

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/63
- State: open
- Author: @peter4200
- Created: 2024-09-11T17:03:18Z
- Updated: 2024-12-18T10:55:57Z
- Labels: none

### Issue body

My home-assistant.log has some of these entries:

2024-09-11 18:52:37.768 WARNING (MainThread) [homeassistant.helpers.frame] Detected that custom integration 'salus' calls async_forward_entry_setup for integration, salus with title: Salus iT600 Gateway and entry_id: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx, which is deprecated and will stop working in Home Assistant 2025.6, await async_forward_entry_setups instead at custom_components/salus/__init__.py, line 80: hass.async_create_task(, please create a bug report at https://github.com/jvitkauskas/homeassistant_salus/issues



### Conversation

#### @212850a commented at 2024-12-18T10:55:56Z

Looks like it is solved by PR which is suggested in #68.
Just need to wait until PR is merged.

---

## #62: AttributeError: 'NoneType' object has no attribute 'available'

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/62
- State: open
- Author: @peter4200
- Created: 2024-08-28T15:08:42Z
- Updated: 2025-06-09T16:28:59Z
- Labels: none

### Issue body

My home-assistant.log are filled with the error below and then, after some time, my HA stops working. I don't if the Salus integration is the problem, bur I'm trying to find the root cause to why my HA is stopping. I'm on the latest version of everything :-)

```
2024-08-28 13:40:23.107 ERROR (MainThread) [homeassistant] Error doing job: Task exception was never retrieved (None)
Traceback (most recent call last):
  File "/usr/src/homeassistant/homeassistant/helpers/update_coordinator.py", line 258, in _handle_refresh_interval
    await self._async_refresh(log_failures=True, scheduled=True)
  File "/usr/src/homeassistant/homeassistant/helpers/update_coordinator.py", line 453, in _async_refresh
    self.async_update_listeners()
  File "/usr/src/homeassistant/homeassistant/helpers/update_coordinator.py", line 168, in async_update_listeners
    update_callback()
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1005, in async_write_ha_state
    self._async_write_ha_state()
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1130, in _async_write_ha_state
    self.__async_calculate_state()
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1066, in __async_calculate_state
    available = self.available  # only call self.available once per update cycle
                ^^^^^^^^^^^^^^
  File "/config/custom_components/salus/binary_sensor.py", line 90, in available
    return self._coordinator.data.get(self._idx).available
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'available'

```

### Conversation

#### @angustyler commented at 2025-06-09T16:28:58Z

I get the same error every 30 seconds. Am happy to do any tests to help diagnose...


2025-06-09 17:22:59.722 ERROR (MainThread) [homeassistant] Error doing job: Task exception was never retrieved (None)
Traceback (most recent call last):
  File "/usr/src/homeassistant/homeassistant/helpers/update_coordinator.py", line 268, in _handle_refresh_interval
    await self._async_refresh(log_failures=True, scheduled=True)
  File "/usr/src/homeassistant/homeassistant/helpers/update_coordinator.py", line 479, in _async_refresh
    self.async_update_listeners()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/update_coordinator.py", line 178, in async_update_listeners
    update_callback()
    ~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1019, in async_write_ha_state
    self._async_write_ha_state()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1141, in _async_write_ha_state
    self.__async_calculate_state()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1080, in __async_calculate_state
    available = self.available  # only call self.available once per update cycle
                ^^^^^^^^^^^^^^
  File "/config/custom_components/salus/binary_sensor.py", line 90, in available
    return self._coordinator.data.get(self._idx).available
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'available'


---

## #60: HA stops working

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/60
- State: open
- Author: @ThomasGNielsen
- Created: 2024-07-16T11:50:26Z
- Updated: 2024-08-07T19:41:05Z
- Labels: none

### Issue body

I have a fairly straightforward Home Assistant system. However, when I add the SALUS integration, my system breaks down frequently. 
Everything works as expected until the breakdown. Nothing can be seen in the log. When I remove the integration, my system is stable again.
Anyone experiencing the same and/or have found a solution? The integration is not updated that regularly so I expect the problem will continue. 

### Conversation

#### @leonardpitzu commented at 2024-08-07T07:10:21Z

enable debug logging for the integration and paste the logs in here

#### @ThomasGNielsen commented at 2024-08-07T19:41:04Z

I have removed the integration to gain stability. Since removal HA have not had any issues.RegardsThomasDen 7. aug. 2024 kl. 09.10 skrev leonardpitzu ***@***.***>:﻿
enable debug logging for the integration and paste the logs in here

—Reply to this email directly, view it on GitHub, or unsubscribe.You are receiving this because you authored the thread.Message ID: ***@***.***>

---

## #59: Integration failing since new Salus APP was introduced.

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/59
- State: open
- Author: @vaibhavratnaparkhi
- Created: 2024-06-11T08:17:28Z
- Updated: 2024-12-16T07:13:01Z
- Labels: none

### Issue body

Integration failing since new Salus APP was introduced.
<img width="387" alt="salus error" src="https://github.com/epoplavskis/homeassistant_salus/assets/149868727/4c72040d-bd7e-44f8-a8cf-5e7ca15b00c5">


### Conversation

#### @vaibhavratnaparkhi commented at 2024-06-11T08:20:04Z

Error in log;

This error originated from a custom integration.

Logger: custom_components.salus
Source: custom_components/salus/__init__.py:58
integration: Salus iT600 (documentation, issues)
First occurred: 10:14:23 AM (2 occurrences)
Last logged: 10:18:50 AM

Connection error: check if you have specified gateway's HOST correctly.

Have Previously configured using the '16 zeroes' since it never accepts the 'actual EUID'

#### @vaibhavratnaparkhi commented at 2024-06-11T08:29:21Z

Have removed the integration also from hacs and reinstalled. Working fine now. Can close the issue :)

#### @sdrake001 commented at 2024-12-13T00:52:30Z

I have the same issue for two days now, I have removed the integration and reinstalled via hacs and it won’t connect. I know the ip address is correct and I have tried the actual EUID and 16 0’s and still no success. I have rebooted ha and restarted salus but still no luck.

#### @sdrake001 commented at 2024-12-16T07:12:59Z

After installing home assistant core last night v2024.12.3 the integration now works. 

---

## #58: HA not adjusting Salus Temperature

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/58
- State: open
- Author: @discodancerstu
- Created: 2024-05-24T13:20:51Z
- Updated: 2024-05-24T13:20:51Z
- Labels: none

### Issue body

HA is now not able to adjust/control my Salus thermostat temperatures, I can't figure out why.

I can see the entities and attributes, no problem, but adjusting the temperature of a thermostat in HA does not seem to get through to the thermostat.

However, HA can control the thermostat mode, ie from permanent hold to schedule etc.

If I manually adjust the temperature on the thermostat in the room, HA sees the adjustment.

So it my diagnosis is that HA isn't sending temperature adjustments through to the gateway, but the gateway sends information to HA. Any ideas please?

### Conversation

_No comments._

---

## #57: Migration to new SALUS Premium lite app - any impacts?

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/57
- State: closed
- Author: @snigehere
- Created: 2024-02-25T17:47:40Z
- Updated: 2024-03-04T10:38:46Z
- Labels: none

### Issue body

I am being prompted to migrate from the salus smart home app to the new SALUS Premium lite app .  The information about the app suggests the data is moved to a new service running on an AWS server .. is there some implication to the integration when this is done?
Anyone moved so far and can comment?

### Conversation

#### @snigehere commented at 2024-03-04T10:38:45Z

no response so closing - I will move and see if it has any impacts - I am assuming not as its local control vs cloud

---

## #56: HA 2024.01

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/56
- State: open
- Author: @slusaro2
- Created: 2024-01-07T19:41:21Z
- Updated: 2024-05-08T21:38:09Z
- Labels: none

### Issue body

I've checked logs after last update and there is something like this:

`Entity None (<class 'custom_components.salus.climate.SalusThermostat'>) is using deprecated supported features values which will be removed in HA Core 2025.1. Instead it should use <ClimateEntityFeature.TARGET_TEMPERATURE|PRESET_MODE: 17>, please create a bug report at https://github.com/jvitkauskas/homeassistant_salus/issues and reference https://developers.home-assistant.io/blog/2023/12/28/support-feature-magic-numbers-deprecation`

So here I am :)

### Conversation

#### @StaticSounds90 commented at 2024-05-08T21:29:33Z

From 2024.5.2
```
2024-05-08 22:05:18.678 WARNING (ImportExecutor_0) [homeassistant.components.climate.const] HVAC_MODE_HEAT was used from salus, this is a deprecated constant which will be removed in HA Core 2025.1. Use HVACMode.HEAT instead, please report it to the author of the 'salus' custom integration
2024-05-08 22:05:18.685 WARNING (ImportExecutor_0) [homeassistant.components.climate.const] HVAC_MODE_COOL was used from salus, this is a deprecated constant which will be removed in HA Core 2025.1. Use HVACMode.COOL instead, please report it to the author of the 'salus' custom integration
2024-05-08 22:05:18.693 WARNING (ImportExecutor_0) [homeassistant.components.climate.const] HVAC_MODE_OFF was used from salus, this is a deprecated constant which will be removed in HA Core 2025.1. Use HVACMode.OFF instead, please report it to the author of the 'salus' custom integration` just to add some
```

---

## #55: Devices containing space, Æ, Ø or Å are not discovered

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/55
- State: open
- Author: @StaticSounds90
- Created: 2023-12-28T21:57:34Z
- Updated: 2023-12-28T21:57:34Z
- Labels: none

### Issue body

Salus iT600 smart home devices containing either space, Æ, Ø or Å in their device name are not discovered.

Renaming the devices in the Salus smart home to not contain the above fixed it.

### Conversation

_No comments._

---

## #54: HA 2024.01 breaking changes

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/54
- State: open
- Author: @leonardpitzu
- Created: 2023-12-28T07:59:24Z
- Updated: 2024-10-09T10:29:07Z
- Labels: none

### Issue body

HA Core 2024.01 brings some changes which make this integration incompatible

`Traceback (most recent call last):
  File "/usr/src/homeassistant/homeassistant/helpers/entity_platform.py", line 507, in async_add_entities
    await asyncio.gather(*tasks)
  File "/usr/src/homeassistant/homeassistant/helpers/entity_platform.py", line 662, in _async_add_entity
    capabilities=entity.capability_attributes,
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/climate/__init__.py", line 333, in capability_attributes
    if ClimateEntityFeature.TARGET_HUMIDITY in supported_features:
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: argument of type 'int' is not iterable`

### Conversation

#### @Dozzki commented at 2024-01-02T16:38:14Z

@epoplavskis @jvitkauskas having same issue here. Is this even maintained still?

#### @ChristophCaina commented at 2024-01-04T08:06:21Z

might be related blog post from HA:
https://developers.home-assistant.io/docs/core/entity/climate#supported-features
https://developers.home-assistant.io/docs/core/entity/fan#supported-features

I've had a look into the source of the climate.py

```
from homeassistant.components.climate.const import (
    HVAC_MODE_HEAT,
    HVAC_MODE_COOL,
    HVAC_MODE_OFF,
    FAN_OFF,
    FAN_AUTO,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH
)
```

I am unsure, if this is related to the `FAN_***` modes - usually, it would be:
FAN_MODE.OFF, FAN_MODE.MEDIUM etc.
which is now depricated... 

ClimateEntityFeature / FanEntityFeature


The above would also explain this case:
#46 which is open since June... I wonder if this integration is still "alive" and maintained...

#### @Dozzki commented at 2024-01-04T09:17:10Z

It is actually fixed by HA team in new beta release 2024.1.0b5. With last release they changed some things and didnt leave backwards compatibility. With this one they added backwards compatibility to climate entity and it started working again. 
Now, regarding maintenance of this project, i believe it was handed over to different person like 3 months ago as original author mentioned he was not maintaining it anymore. But the new maintainer don't have any git history for the past 3 years so iam not sure why it was handed over to person who is not active in the community 🤷 sad

#### @mjrybarski commented at 2024-10-08T22:14:48Z

any news I just got the integration and fan still says 'Failed to perform the action climate/set_hvac_mode. Unknown error occurred while communicating with iT600 gateway'

#### @leonardpitzu commented at 2024-10-09T10:29:06Z

I have no device with a fan so I cannot debug it...

---

## #53: Getting "Unknown Error Occurred" when trying to connect

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/53
- State: open
- Author: @lavendaniel
- Created: 2023-11-20T15:22:26Z
- Updated: 2023-12-13T09:11:01Z
- Labels: none

### Issue body

Have the IP address correct, manually assigned to the Salus Gateway. Typed the EUID correctly. Home Assistant just throws "Unknown Error Occurred" and doesn't add the device.

### Conversation

#### @mkmk89 commented at 2023-11-25T22:25:50Z

I'm having exactly the same issue

#### @vaibhavratnaparkhi commented at 2023-12-02T00:51:45Z

Did you try using the 0000000000000000 as EUID

I was getting a similar error when connecting using the actual EUID from the hub, used the 0000000000000000 and works fine.

#### @mkmk89 commented at 2023-12-13T08:41:01Z

yes, that worked, thanks!

#### @vaibhavratnaparkhi commented at 2023-12-13T09:11:00Z

> yes, that worked, thanks!

That's great. Welcome !!!

---

## #52: How to add this to Home Assistant Green?

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/52
- State: closed
- Author: @lavendaniel
- Created: 2023-11-20T14:38:28Z
- Updated: 2023-11-20T15:21:16Z
- Labels: none

### Issue body

If I'd done my own Pi install or docker install I'd know where to look, but I got the off the shelf HA Green device and have no clue even where to start.

Really need to get the Salus smart button working with this. Then hopefully the Kiasa/Tuya heaters.

Any help much appreciated!

### Conversation

_No comments._

---

## #51: Not all Thermostats are visible

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/51
- State: closed
- Author: @5ssj
- Created: 2023-11-11T12:53:40Z
- Updated: 2023-11-11T17:20:38Z
- Labels: none

### Issue body

Hello!

I just configured my Salus system on Home Assistant and my issue is that only 4 of 6 thermostats are visible as entity/device.

![image](https://github.com/epoplavskis/homeassistant_salus/assets/150474006/1002b410-39fb-43fe-8b07-7a2833483785)

Has anybody run into the same problem?


Thanks
Johann

### Conversation

_No comments._

---

## #50: Config flow could not be loaded: undefined

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/50
- State: open
- Author: @212850a
- Created: 2023-11-02T08:08:48Z
- Updated: 2023-12-15T13:08:09Z
- Labels: none

### Issue body

Hi, when I try to add Salus iT600 integration to HA I get and error "Config flow could not be loaded: undefined".

In the logs I see the following:
```
Logger: homeassistant.util.package
Source: util/package.py:99 
First occurred: 10:01:37 (3 occurrences) 
Last logged: 10:01:50

Unable to install package pyit600==0.5.1: ERROR: Cannot install pyit600==0.5.1 because these package versions have conflicting dependencies. ERROR: ResolutionImpossible: for help visit https://pip.pypa.io/en/latest/topics/dependency-resolution/#dealing-with-dependency-conflicts WARNING: You are using pip version 22.0.3; however, version 23.3.1 is available. You should consider upgrading via the '/usr/local/bin/python3 -m pip install --upgrade pip' command.


Logger: aiohttp.server
Source: requirements.py:194 
First occurred: 10:01:50 (1 occurrences) 
Last logged: 10:01:50

Error handling request
Traceback (most recent call last):
  File "/usr/local/lib/python3.9/site-packages/aiohttp/web_protocol.py", line 435, in _handle_request
    resp = await request_handler(request)
  File "/usr/local/lib/python3.9/site-packages/aiohttp/web_app.py", line 504, in _handle
    resp = await handler(request)
  File "/usr/local/lib/python3.9/site-packages/aiohttp/web_middlewares.py", line 117, in impl
    return await handler(request)
  File "/usr/src/homeassistant/homeassistant/components/http/security_filter.py", line 60, in security_filter_middleware
    return await handler(request)
  File "/usr/src/homeassistant/homeassistant/components/http/forwarded.py", line 100, in forwarded_middleware
    return await handler(request)
  File "/usr/src/homeassistant/homeassistant/components/http/request_context.py", line 28, in request_context_middleware
    return await handler(request)
  File "/usr/src/homeassistant/homeassistant/components/http/ban.py", line 79, in ban_middleware
    return await handler(request)
  File "/usr/src/homeassistant/homeassistant/components/http/auth.py", line 219, in auth_middleware
    return await handler(request)
  File "/usr/src/homeassistant/homeassistant/components/http/view.py", line 137, in handle
    result = await result
  File "/usr/src/homeassistant/homeassistant/components/config/config_entries.py", line 173, in post
    return await super().post(request)
  File "/usr/src/homeassistant/homeassistant/components/http/data_validator.py", line 62, in wrapper
    result = await method(view, request, *args, **kwargs)
  File "/usr/src/homeassistant/homeassistant/helpers/data_entry_flow.py", line 70, in post
    result = await self._flow_mgr.async_init(
  File "/usr/src/homeassistant/homeassistant/data_entry_flow.py", line 205, in async_init
    flow, result = await task
  File "/usr/src/homeassistant/homeassistant/data_entry_flow.py", line 223, in _async_init
    flow = await self.async_create_flow(handler, context=context, data=data)
  File "/usr/src/homeassistant/homeassistant/config_entries.py", line 740, in async_create_flow
    await async_process_deps_reqs(self.hass, self._hass_config, integration)
  File "/usr/src/homeassistant/homeassistant/setup.py", line 360, in async_process_deps_reqs
    await requirements.async_get_integration_with_requirements(
  File "/usr/src/homeassistant/homeassistant/requirements.py", line 83, in async_get_integration_with_requirements
    await _async_process_integration(hass, integration, done)
  File "/usr/src/homeassistant/homeassistant/requirements.py", line 99, in _async_process_integration
    await async_process_requirements(
  File "/usr/src/homeassistant/homeassistant/requirements.py", line 162, in async_process_requirements
    await _async_process_requirements(
  File "/usr/src/homeassistant/homeassistant/requirements.py", line 194, in _async_process_requirements
    raise RequirementsNotFound(name, [req])
homeassistant.requirements.RequirementsNotFound: Requirements for salus not found: ['pyit600==0.5.1'].
```

I use container version of Home Assistant Core 2022.5.4, Homeassistant_salus 0.5.1 release code is cloned to custom_components folder where I have other third party working components.

### Conversation

#### @212850a commented at 2023-12-15T13:08:09Z

OK, upgrade of Home Assistant has sorted this problem. 

---

## #49: Notice of transfer of ownership

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/49
- State: open
- Author: @jvitkauskas
- Created: 2023-10-30T19:22:55Z
- Updated: 2023-11-24T05:23:04Z
- Labels: none

### Issue body

I have transferred ownership of this repo, pyit600 repo and pypi package to @epoplavskis. Edgaras has volunteered to continue the development of this project.

### Conversation

#### @Algernon3000 commented at 2023-11-24T05:23:03Z

Thanks so much @epoplavskis - this integration is so important to my HA setup!

---

## #48: Deprecated Code Causing Failure

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/48
- State: open
- Author: @Algernon3000
- Created: 2023-10-15T18:28:50Z
- Updated: 2023-10-15T18:28:50Z
- Labels: none

### Issue body

There appears to be an issue with the integration which I think is due to some deprecated code since Home Assistant V2023.5.0

Googling the error in the log led me to this page: https://community.home-assistant.io/t/error-async-get-registry-after-core-2023-5-0/567951/6
Someone there says: "I fixed this issue and submitted a pull request. The fix is trivial - in the init.py change line 21 from: async_get_registry as async_get_entity_registry, to: async_get as async_get_entity_registry, effectively async_get_registry was marked as deprecated and was removed in 2023.5.0 and async_get is the replacement."

I've tried a basic modification (basically just find and replacing) which was clearly rather optimistic, and didn't work. Could anyone advise how big a job it might be to update the init file to use the latest code (async_get) pls?



### Conversation

_No comments._

---

## #47: Selling my Salus devices on eBay

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/47
- State: closed
- Author: @jvitkauskas
- Created: 2023-10-11T21:31:30Z
- Updated: 2023-10-19T19:00:31Z
- Labels: none

### Issue body

Hi, I am selling another batch of my Salus devices on eBay. You may want to bid:

https://www.ebay.de/itm/186112299685
https://www.ebay.de/itm/186112301948
https://www.ebay.de/itm/186112305165
https://www.ebay.de/itm/186112315420
https://www.ebay.de/itm/186112319081
https://www.ebay.de/itm/186112320967
https://www.ebay.de/itm/186112325208
https://www.ebay.de/itm/186112327735
https://www.ebay.de/itm/186112328927
https://www.ebay.de/itm/186112331150
https://www.ebay.de/itm/186112339334
https://www.ebay.de/itm/186112339986
https://www.ebay.de/itm/186112340443
https://www.ebay.de/itm/186112341582

### Conversation

_No comments._

---

## #46: Change Fan mode not working

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/46
- State: open
- Author: @RR06
- Created: 2023-06-24T11:32:49Z
- Updated: 2025-03-14T11:26:21Z
- Labels: none

### Issue body

changing Salus thermostate “fan mode” gives error: 

Failed to call service climate/set_fan_mode. Unknown error occurred while communicatino with iT600 gateway

Can anyone offer a solution?


### Conversation

#### @efenex commented at 2023-08-15T09:07:30Z

same for me, came here looking for an update/fix so I have no solution either

#### @mharizanov commented at 2023-12-29T10:44:14Z

Same here

#### @mjrybarski commented at 2024-10-08T21:58:14Z

any update here? :)

#### @kyurkchyan commented at 2025-03-14T11:26:20Z

I have the same issue. Can't change the fan mode

---

## #45: sq610rf thermostats not found

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/45
- State: closed
- Author: @querkyzuerky
- Created: 2023-03-04T11:45:20Z
- Updated: 2023-03-04T16:41:56Z
- Labels: none

### Issue body

Hope you can help with this.  My set up has a UGE600 gateway, 3no SR600 smart relays, 5 no SQ610Rf thermostats and a KL08RF underfloor heating controller.  The integration identifies the smart relays but only sees one of the thermostats.  is there something that needs to be set to be able to see multiple thermostats?

### Conversation

#### @querkyzuerky commented at 2023-03-04T16:41:56Z

This may have sorted itself.  I originally had the gateway in the same room as one of the sensors and only that sensor was displayed.  I changed the room that the gateway was in and the remaining sensors are now displayed.

---

## #44: Maintainer wanted

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/44
- State: closed
- Author: @jvitkauskas
- Created: 2023-01-20T22:38:42Z
- Updated: 2023-10-30T19:26:32Z
- Labels: help wanted

### Issue body

I am no longer developing this integration and therefore I am seeking someone who is willing to maintain it. Please contact me if you are interested.

### Conversation

#### @YashoEsparta commented at 2023-09-10T18:34:25Z

Hi, i am interested in realize one change in SQ610 device for support HVAC_MODE_COOL mode, is possible?

#### @jvitkauskas commented at 2023-10-30T19:25:29Z

I have transferred ownership of this repo, pyit600 repo and pypi package to @epoplavskis. Edgaras has volunteered to continue the development of this project.

---

## #43: Cannot connect to UGE600 

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/43
- State: open
- Author: @imihailovs
- Created: 2023-01-14T11:03:24Z
- Updated: 2025-01-26T14:45:54Z
- Labels: none

### Issue body

I am trying to add UGE600 gateway via HACS installed component and I can't seem to connect to the gateway - tried both real and all-zero EUIDs. 

I've made sure to maintain Local WIFI setting and I've also tried connecting via Ethernet and WIFI connections one after another - no success - I'm getting "Invalid IP address. Try again." error message. 

Is there a log file somewhere that I can use to analyze the response from the GW?

### Conversation

#### @alex-ricobon commented at 2023-09-11T15:37:37Z

same issue here, did you manage to fix it?

#### @stvogel commented at 2023-10-25T10:04:49Z

I have the same problem for the UGE600, but I got the error-message: "Unknown error occurred"
In the log I find:
```
2023-10-25 09:48:07.134 ERROR (MainThread) [aiohttp.server] Error handling request
Traceback (most recent call last):
  File "/usr/local/lib/python3.11/site-packages/pyit600/gateway.py", line 929, in _make_encrypted_request
    response_json_string = self._encryptor.decrypt(response_bytes)
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/pyit600/encryptor.py", line 27, in decrypt
    plain: bytes = unpadder.update(padded_data) + unpadder.finalize()
                                                  ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/cryptography/hazmat/primitives/padding.py", line 160, in finalize
    result = _byte_unpadding_check(
             ^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/cryptography/hazmat/primitives/padding.py", line 102, in _byte_unpadding_check
    raise ValueError("Invalid padding bytes.")
ValueError: Invalid padding bytes.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/usr/local/lib/python3.11/site-packages/aiohttp/web_protocol.py", line 433, in _handle_request
    resp = await request_handler(request)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/aiohttp/web_app.py", line 504, in _handle
    resp = await handler(request)
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/aiohttp/web_middlewares.py", line 117, in impl
    return await handler(request)
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/http/security_filter.py", line 85, in security_filter_middleware
    return await handler(request)
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/http/forwarded.py", line 100, in forwarded_middleware
    return await handler(request)
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/http/request_context.py", line 28, in request_context_middleware
    return await handler(request)
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/http/ban.py", line 80, in ban_middleware
    return await handler(request)
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/http/auth.py", line 236, in auth_middleware
    return await handler(request)
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/http/headers.py", line 31, in headers_middleware
    response = await handler(request)
               ^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/http/view.py", line 148, in handle
    result = await handler(request, **request.match_info)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/http/decorators.py", line 63, in with_admin
    return await func(self, request, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/config/config_entries.py", line 177, in post
    return await super().post(request, flow_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/http/data_validator.py", line 72, in wrapper
    result = await method(view, request, data, *args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/helpers/data_entry_flow.py", line 110, in post
    result = await self._flow_mgr.async_configure(flow_id, data)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/data_entry_flow.py", line 293, in async_configure
    result = await self._async_handle_step(
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/data_entry_flow.py", line 394, in _async_handle_step
    result: FlowResult = await getattr(flow, method)(user_input)
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/config/custom_components/salus/config_flow.py", line 44, in async_step_user
    unique_id = await gateway.connect()
                ^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/pyit600/gateway.py", line 101, in connect
    all_devices = await self._make_encrypted_request(
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/pyit600/gateway.py", line 957, in _make_encrypted_request
    raise IT600CommandError(
pyit600.exceptions.IT600CommandError: Unknown error occurred while communicating with iT600 gateway
```
Seems to me as if this is a problem of the underlying pyit600 -library, https://github.com/jvitkauskas/pyit600

Edit:
I tried with the underlying pyit600-library. With command:
`python main.py --host 192.168.xxx.xxx --euid 001E5E0909xxxxxx`
I got the same error.

But
`python main.py --host 192.168.xxx.xxx --euid 0000000000000000`
works fine!

#### @andvarga79 commented at 2023-11-16T10:32:44Z

Hi All,
I just purchased a Salus IT600 underfloor heating automatization, hoping to integrate it in Home Assistant, and I am at the point that I will send it back if not doable.
I have downloaded latest of the integration from HACS and when I try to add IP and EUID the error of Failed to connect, please check IP address coms back. I have tried the troubleshooting from the readme, all looks good, but error persists.
I am not an IT person, and not really understanding the above solution.
Do you mind creating a tutorial as for a person without required IT knowledge? Thank you!

#### @nicu-cbn commented at 2023-11-18T23:03:21Z

Hello. I have the same error.
Also found in the HA logs the following:

Logger: pyit600
Source: custom_components/salus/config_flow.py:44
Integration: Salus iT600 ([documentation](https://github.com/jvitkauskas/homeassistant_salus), [issues](https://github.com/jvitkauskas/homeassistant_salus/issues))
First occurred: 00:47:29 (1 occurrences)
Last logged: 00:47:29

Timeout while connecting to gateway:


#### @palladin8282 commented at 2023-11-24T15:05:42Z

Hi, 
I have simmilar issue, 

But what I found also is that:

Also check if you have "Local Wifi Mode" enabled:

Open Smart Home app on your phone
Sign in
Double tap your Gateway to open info screen
Press gear icon to enter configuration
Scroll down a bit and check if "Disable Local WiFi Mode" is set to "No"
Scroll all the way down and save settings
Restart Gateway by unplugging/plugging USB power

In my gateway this mode was disabled

Trying this righ now - I will inform about results. 

#### @palladin8282 commented at 2023-11-24T15:31:14Z

Hi All, 
After enabling the Local Wifi Mode to on and restarting the gateway I was able to establish connection :) 
Maybe this will help you too. 

#### @nicu-cbn commented at 2023-11-27T08:28:10Z

On my side my router has an option to isolate IoT devices and Salus Gateway was one of those isolated devices (and the and the HA server not), that's why Home Assistant was unable to connect. 
Solving this was fixed my issue

#### @imihailovs commented at 2024-04-20T06:41:49Z

Came back to integrating the Gateway, but still facing the same issue. Both HA and Gateway are on the same subnet, firewall doesn't block anything. Local mode is enabled on the gateway.
What I have noticed is that I can't ping the IP address of a gateway. Could be normal, don't know.
Anyhow, the error I am getting from the logs is as follows:

`This error originated from a custom integration.

Logger: pyit600
Source: custom_components/salus/config_flow.py:44
integration: Salus iT600 (documentation, issues)
First occurred: 9:21:30 AM (7 occurrences)
Last logged: 9:29:17 AM

Timeout while connecting to gateway:`

#### @rexopl commented at 2024-09-25T09:37:08Z

Wow thanks @stvogel using `0000000000000000` works! o.O 

#### @bjorn-lebel commented at 2024-10-15T18:24:16Z

Hi, i have the same issue as @imihailovs,
The UG600 are connected and it works in the app, with equipment connected all through, that i can control through the app.

However I cant register the gateway with HA...

It looks like i am stuck in between, 
if I reset the gateway completely and connect to it in the offline mode I can access a webserver on the wifi side of the gateway (even if that webserver says 404...), so far it looks promising...

However if i instead connect the LAN, and it is registered to the internet, 
it goes into "darkmode" and dont respond to anything, 
either on the LAN side or on the wifi side with a configured SSID.
I can see the IPs and MAC addresses on my firewall but the UG600 doesnt respond to anything!

I am leaning to that a firmware update closed the access when connected to the internet.

I have factory reset it like 20 times by now and whatever I do I come back to the same state, where Local WiFi Access are enabled but doesnt respond (in either working mode).

TBH and warn others, I will return it and buy another system!

#### @DanielKarwacki commented at 2025-01-26T14:45:38Z

With my integration I had the `Invalid padding bytes.` error as well. The solution was to use `0000000000000000` as EUID instead the one taken from the sticker on UGE600 device.

@epoplavskis I believe that information (try with `0000000000000000`) in plugin README.md could save people lifes :) What do you think?

---

## #42: RX10RF not updating

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/42
- State: open
- Author: @willhaggan
- Created: 2023-01-04T23:53:12Z
- Updated: 2023-01-04T23:53:12Z
- Labels: none

### Issue body

I have lost automatic updates from the salus boiler switch RX10RF. This has been working for a over a year with no issues on home assistant.

It will strangely update if I go onto the salus android app and open the boiler switch overview page  in equipment but I am not doing anything apart from this.

 It is functioning correctly as in it is physically switching and updating on the salus smart home app just not on home assistant.

The salus thermostats  are still updating and reading correctly it is just the boiler switch.

I have tried uninstalling the salus component from home assistant but this did not fix the issue.

### Conversation

_No comments._

---

## #41: Support for ECM600 - Electric Monitor

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/41
- State: open
- Author: @Blue-beef
- Created: 2022-12-09T12:38:36Z
- Updated: 2022-12-09T12:38:36Z
- Labels: none

### Issue body

These electric meters are being used to measure the power usage of heat pumps, which is a requirement for UK installs. Integration with HA would be very helpful.

### Conversation

_No comments._

---

## #40: Selling my Salus devices on eBay

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/40
- State: closed
- Author: @jvitkauskas
- Created: 2022-12-04T22:11:21Z
- Updated: 2023-01-20T22:35:55Z
- Labels: none

### Issue body

Hi, I am selling my Salus devices on eBay. You may want to bid:

https://www.ebay.de/itm/185684523634
https://www.ebay.de/itm/185684530276
https://www.ebay.de/itm/185684533779
https://www.ebay.de/itm/185684535419
https://www.ebay.de/itm/185684537226
https://www.ebay.de/itm/185684538688
https://www.ebay.de/itm/185684540335


### Conversation

_No comments._

---

## #39: Temperature automations 

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/39
- State: open
- Author: @adrmnt
- Created: 2022-12-02T15:21:57Z
- Updated: 2022-12-02T15:21:57Z
- Labels: none

### Issue body

Hi,

I’m trying to automate the thermostats but are not working as expected. Unfortunately I’m not able to set the temperature at specific hour. Only 2 options are available, change HVAC or PRESET. If I’m manually editing the Yaml, I cannot add temperature attribute. 

Can you guide me please?
![3223525A-3A2F-4F3C-AA89-4F023012CCE3](https://user-images.githubusercontent.com/7668538/205326381-d9ad0735-358d-470a-b5c0-f16d406e7402.png)
![BB1619B8-23C4-46FC-A63B-0701C4D68BB8](https://user-images.githubusercontent.com/7668538/205326387-cbcd5ca9-2087-4434-bcb0-9ac448ea04c9.jpeg)
![14136027-4FE7-4AF2-B219-A8235E2B139C](https://user-images.githubusercontent.com/7668538/205326390-f29751f2-b3a2-4933-9bd3-c325d3920bd9.jpeg)


### Conversation

_No comments._

---

## #38: Troubleshooting UUID 15 chars not 16

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/38
- State: open
- Author: @parfienczyk
- Created: 2022-11-17T19:25:21Z
- Updated: 2023-12-28T21:53:26Z
- Labels: none

### Issue body

@jvitkauskas - what about Gateway's UUID which has 15 chars not 16 - I can't add my Gateway because I have an error with too short UUID

![Screenshot 2022-11-17 at 22 02 54](https://user-images.githubusercontent.com/1235773/202559625-2de75d42-80aa-4808-908b-89b960e56578.png)



### Conversation

#### @RazvanDespa commented at 2022-11-28T19:52:34Z

Hi,

I have the same problem. Also tried with 16's zeroes but no luck :(.

Any idea?

Thanks,
Razvan

#### @imihailovs commented at 2023-01-14T10:46:18Z

@parfienczyk - is it really an EUID? In my Salus Home app this patter shows up as Serian #, which is also 15 chars long. Don't think you should be using this one - take the number from the back of the device instead?

#### @StaticSounds90 commented at 2023-12-28T21:53:25Z

FIY. At the back of the gateway I found 4 stickers. The 16 character EUID was located on sticker B as indicated in the attached photo. You can't read it with the power attached. Mine accepted the 16 zeroes instead of the actual EUID.
I found it was easier to locate the EUID by browsing the gateway via https://eu.salusconnect.io/ if possible.
Both the DBN and the serial number was 15 characters. 
![image](https://github.com/epoplavskis/homeassistant_salus/assets/154476033/06797e38-f130-4805-994d-b3cc7d4b585d)


---

## #36: Can I run more than one gateway?

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/36
- State: closed
- Author: @snigehere
- Created: 2022-10-29T21:27:38Z
- Updated: 2024-01-13T23:00:07Z
- Labels: none

### Issue body

Can I run more that one gateway or am I limited to just one?  I have two boilers for two different spaces with separate gateways, boiler controllers and thermostats and would like to be able to control both via HA.  Can I run multiple instances of the integration?  Any pointers on how to do this would be appreciated

### Conversation

#### @snigehere commented at 2024-01-13T23:00:06Z

yes

---

## #35: SD600

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/35
- State: open
- Author: @DanCarstea
- Created: 2022-07-30T18:41:45Z
- Updated: 2022-07-30T18:41:45Z
- Labels: none

### Issue body

Hi,

Thankyou for your good job. I just installed HA and i have several problems with Xioami, smarthings and other but your Salus iT600 worked so easy...thank you again

One question. By any chance can you integrate also the smoke detectors SD600?

Thanks,

### Conversation

_No comments._

---

## #33: Not working

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/33
- State: closed
- Author: @ihyildiz
- Created: 2022-07-08T13:58:02Z
- Updated: 2022-07-09T07:05:42Z
- Labels: none

### Issue body

Hi there,

I have just installed Salus IT600 via Hacs. 

In Configuration.yaml I have added the right "toke".

After the restart I had in the "Dashboard" an entry in the sensors map. But I do not get the data from thermostat Salus SQ610. 

Gateway Salut iT6000 model UG600 / UGE600 runs fine on the mobile app. 

I have also worked the troubleshooting steps you recommended.

Any Idea?


![Bildschirmfoto 2022-07-08 um 15 49 34](https://user-images.githubusercontent.com/10075041/178006053-ca6930d1-7d81-404b-aecb-5b56eeabdb7f.png)
![Bildschirmfoto 2022-07-08 um 15 49 49](https://user-images.githubusercontent.com/10075041/178006058-8e5f889b-771c-4c29-9e86-cd94d7a8fbab.png)
![Bildschirmfoto 2022-07-08 um 15 57 34](https://user-images.githubusercontent.com/10075041/178006369-bbb3ba57-0be5-473a-bd45-ec84eabec990.png)

![Bildschirmfoto 2022-07-08 um 15 51 39](https://user-images.githubusercontent.com/10075041/178006060-9749358f-0b7a-4d61-9f35-10439469684c.png)



### Conversation

#### @ihyildiz commented at 2022-07-09T07:05:42Z

Hacs Repo wasn't correctly installed.

After cold start (power supply unplugged) hacs was there, and I could install these well working integration.

Thx.

---

## #32: Data not updating after system update

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/32
- State: open
- Author: @rs0rs
- Created: 2022-06-08T07:36:27Z
- Updated: 2022-06-08T08:47:37Z
- Labels: none

### Issue body

My entities does not update after having updated to "Home Assistant Core 2022.6.1", "Home Assistant Supervisor 2022.05.3" and "Home Assistant OS 8.1". Looking at the integrations page (/config/integrations) it shows, that the integration is not loaded (it is written in Danish, so bare with my Danglish :) ). This causes my picture-elements card to show all the entities with warning triangles. Before the updates, all entities did show correct values.
What can I do to get this working once again?
Thank you.

### Conversation

#### @rs0rs commented at 2022-06-08T08:47:37Z

Her are the log:
2022-06-08 10:41:15 WARNING (SyncWorker_0) [homeassistant.loader] We found a custom integration salus which has not been tested by Home Assistant. This component might cause stability problems, be sure to disable it if you experience issues with Home Assistant
2022-06-08 10:41:55 ERROR (MainThread) [homeassistant.setup] Setup failed for custom integration salus: Requirements for salus not found: ['pyit600==0.2.6'].

---

## #31: feature request - support cooling mode

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/31
- State: open
- Author: @zylxpl
- Created: 2022-05-26T10:00:51Z
- Updated: 2026-04-15T21:06:38Z
- Labels: none

### Issue body

Salus thermostats supports cooling mode. Would be nice if was supported by HA integration.  

### Conversation

#### @discodancerstu commented at 2024-06-02T14:47:58Z

+1 on this

#### @scsatta commented at 2024-09-15T10:28:26Z

+1

#### @Jordi-14 commented at 2026-04-15T21:06:38Z

I've made a fork with cooling. https://github.com/Jordi-14/homeassistant_salus .



---

## #30: SQ610RF - Humidity extraction

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/30
- State: open
- Author: @robump
- Created: 2022-05-07T13:57:50Z
- Updated: 2025-01-02T19:52:33Z
- Labels: none

### Issue body

Hi

Firstly, thank you for pulling together this HA integration, it has massively improved the usage of the setup.

I have temperature extracting well from my SQ610RF but cant seem to find humidity - see extract from my HA states below:

![image](https://user-images.githubusercontent.com/4338600/167257437-8cdd98f7-42d7-487d-afc9-c3deb8f670b9.png)

I have pulled down the code and installed the integration manually today and wondered what i was doing wrong as i have seen others are able to extract it?

Thank you in advance.

### Conversation

#### @mdelalan commented at 2022-05-21T23:55:48Z

Hi,
I had the same issue to get humidity from my SQ610 with Home assistant (docker image)
It turns out that the model name returned by the gateway is SQ610(WB) instead of SQ610 (or SQ610RF).
In order to get the humidity, I had to change the line 504 of the file pyit600/gateway.py from that :

           if model == "SQ610" or model == "SQ610RF":

to that :

           if model is not None and "SQ610" in model:

Hope it will help
Michael

#### @yah996 commented at 2022-10-08T13:37:30Z

Hi Michael, 

i am using a SQ610RF Model on Homeassistant. Can you please let me know, where is the pyit600/gateway.py file located in HA? I am using a VM edition... 

Many Thanks.... 

#### @mdelalan commented at 2022-10-09T17:03:15Z

Hi @yah996 

I'm using home assistant in Docker so I don't know if the following information will be applicable for a VM edition !

The file gateway.py is located here :
/usr/local/lib/python3.9/site-packages/pyit600/gateway.py

#### @yah996 commented at 2022-10-24T15:43:20Z

thanks, I found it. 

#### @DragosFlorea commented at 2022-11-07T07:01:16Z

Hi @jvitkauskas 
Do you have time to include in the next release the solution proposed by @mdelalan ?
Thanks

#### @nicolaeurs commented at 2022-11-07T17:59:53Z

> thanks, I found it.

Can you tell me how did you find it? I am in the same situation as you and do not seem to be able to find the file. Thanks.

#### @yah996 commented at 2022-11-07T19:40:26Z

are you using the terminal add on in HA? 

#### @nicolaeurs commented at 2022-11-08T05:13:07Z

Yes, I have it installed. 

#### @yah996 commented at 2022-11-08T07:40:08Z

ok, try this in the terminal add-on

shell to the homeassistant server, name='yourhostname'.
Use this commands:

docker exec -it $(docker ps -f name=homeassistant -q) bash
bash-5.1# find / -name gateway.py

/usr/local/lib/python3.10/site-packages/pyit600/gateway.py

Use vi or so to modify the gateway.py, this should be work. 

#### @mdelalan commented at 2022-11-08T23:34:35Z

> Hi @jvitkauskas Do you have time to include in the next release the solution proposed by @mdelalan ? Thanks

Hello,
I've noticed that the temperature returned by the gateway is not always the same as the one displayed on the SQ610 :
It seems that the value is not updated in realtime !
I played a little bit with the Android app Smart Home in Wifi local mode and I found the command that force the gateway to update the temperature/humidity with the one displayed on the SQ610 :

`await self._make_encrypted_request(                                                                       
            "write",                                                                                                                        
             {                                                                                                                                                                                   
                "requestAttr": "write",                                                                                    
                "id": [{"data": device["data"],"sIT600I":{"SetCommand_d":"42 37 34 00 00 00 00"}} for device in devices]                                  
             }                                                                                                                        
            )`

Maybe this can also be added in the next release ??

#### @nicolaeurs commented at 2022-11-10T19:14:03Z

Thank you yah966, but my HA is installed in a VM on a Synology NAS. And I am not an IT guy, I did it following some YouTube tutorials. 

#### @DragosFlorea commented at 2022-11-17T07:40:14Z

Hi @jvitkauskas 
I've updated my salus integration with 0.51 but from what I see there still no humidity. There are no entities for that ...
![image](https://user-images.githubusercontent.com/19181854/202385317-d3a385c7-dde4-48c8-8a3e-281198a1a446.png)

Thanks


#### @nicolaeurs commented at 2022-11-19T17:32:56Z

Thank you for the update, humidity appeared in states (developer tools - states - attributes). 

@DragosFlorea From there you can add it as an attribute in any of your cards in YAML. 

#### @diccosmin commented at 2023-04-25T17:52:47Z

Hello,
I use HASO in VM and I am not able to see the SQ610RF device. I see all other devices I have in the IT600 system but not the SQ610RF Thermostat. 
Also I don't have this file   /usr/local/lib/python3.9/site-packages/pyit600/gateway.py
Any suggestion from you please? Thank you !

later edit: I removed the integration and I added it again. Now I can see the SQ610RF but it shows nothing  also this time the TS600 Thermostat shows nothing.

#### @vaibhavratnaparkhi commented at 2023-12-02T00:54:52Z

Hi,

The humidity seems to be available, but cannot be tracked. Like we can see the temperature over a certain period of time, can we also have the humidity being tracked?

#### @voborl00 commented at 2024-12-22T19:27:15Z

hello, would like to track humidity as was mentioned in last comment - is there some way to it? thanks

#### @nicolaeurs commented at 2025-01-02T19:52:32Z

@voborl00 If the data appears in Developer tools - States - Attributes (for me, each thermostat has a ”current_humidity” attribute), then you can take it from there and insert it in any HA card using YAML. 

---

## #29: Home Assistant 2022.3.0 breaking change

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/29
- State: closed
- Author: @mindvisionro
- Created: 2022-03-02T22:06:15Z
- Updated: 2022-03-05T13:09:09Z
- Labels: none

### Issue body

After the update, the integration does not start.

https://pip.pypa.io/en/latest/topics/dependency-resolution/#dealing-with-dependency-conflicts

### Conversation

#### @willhaggan commented at 2022-03-03T07:47:19Z

Hi same issue here.

Logger: homeassistant.util.package
Source: util/package.py:99
First occurred: 07:41:43 (3 occurrences)
Last logged: 07:41:59

Unable to install package pyit600==0.3.2: ERROR: Cannot install pyit600==0.3.2 because these package versions have conflicting dependencies. ERROR: ResolutionImpossible: for help visit https://pip.pypa.io/en/latest/topics/dependency-resolution/#dealing-with-dependency-conflicts

#### @Diomet commented at 2022-03-03T10:12:40Z

Same here:

Logger: homeassistant.setup
Source: setup.py:155
First occurred: 12:10:24 (1 occurrences)
Last logged: 12:10:24

Setup failed for salus: Requirements for salus not found: ['pyit600==0.3.2'].

#### @mobopx commented at 2022-03-04T06:53:54Z

on 2022.3.1 it doesn't work either

#### @mobopx commented at 2022-03-04T11:48:08Z

i found such a tip, but i didn/t test it

https://community.home-assistant.io/t/2022-3-select-and-play-media/398201/192?u=mobopx

#### @Eugen66-cmd commented at 2022-03-04T12:04:21Z

Hi same issue here.

#### @SemyonSV commented at 2022-03-04T17:27:00Z

On 2022.3.1 it doesn't work

#### @jvitkauskas commented at 2022-03-04T21:47:42Z

Can you try 0.4.0?

#### @Eugen66-cmd commented at 2022-03-04T21:57:53Z

I reverted to 2022.2.7 because I can't use it at all. Not even delete it
from integrations, but if you think you have fixed it I'll try again ...

În vin., 4 mar. 2022 la 23:47, Julius Vitkauskas ***@***.***>
a scris:

> Can you try 0.4.0?
>
> —
> Reply to this email directly, view it on GitHub
> <https://github.com/jvitkauskas/homeassistant_salus/issues/29#issuecomment-1059555753>,
> or unsubscribe
> <https://github.com/notifications/unsubscribe-auth/ASMB5YXD2HWBTBCX4AAC3J3U6KAI3ANCNFSM5PYXGABA>
> .
> Triage notifications on the go with GitHub Mobile for iOS
> <https://apps.apple.com/app/apple-store/id1477376905?ct=notification-email&mt=8&pt=524675>
> or Android
> <https://play.google.com/store/apps/details?id=com.github.android&referrer=utm_campaign%3Dnotification-email%26utm_medium%3Demail%26utm_source%3Dgithub>.
>
> You are receiving this because you commented.Message ID:
> ***@***.***>
>


#### @Eugen66-cmd commented at 2022-03-04T22:01:40Z

Should I uninstall it first?

În vin., 4 mar. 2022 la 23:57, Eugen Ginta ***@***.***> a scris:

> I reverted to 2022.2.7 because I can't use it at all. Not even delete it
> from integrations, but if you think you have fixed it I'll try again ...
>
> În vin., 4 mar. 2022 la 23:47, Julius Vitkauskas ***@***.***>
> a scris:
>
>> Can you try 0.4.0?
>>
>> —
>> Reply to this email directly, view it on GitHub
>> <https://github.com/jvitkauskas/homeassistant_salus/issues/29#issuecomment-1059555753>,
>> or unsubscribe
>> <https://github.com/notifications/unsubscribe-auth/ASMB5YXD2HWBTBCX4AAC3J3U6KAI3ANCNFSM5PYXGABA>
>> .
>> Triage notifications on the go with GitHub Mobile for iOS
>> <https://apps.apple.com/app/apple-store/id1477376905?ct=notification-email&mt=8&pt=524675>
>> or Android
>> <https://play.google.com/store/apps/details?id=com.github.android&referrer=utm_campaign%3Dnotification-email%26utm_medium%3Demail%26utm_source%3Dgithub>.
>>
>> You are receiving this because you commented.Message ID:
>> ***@***.***>
>>
>


#### @Eugen66-cmd commented at 2022-03-04T22:20:56Z

OK, done. Just copied new files ad restart.
Works for me, no more errors.

În sâm., 5 mar. 2022 la 00:01, Eugen Ginta ***@***.***> a scris:

> Should I uninstall it first?
>
> În vin., 4 mar. 2022 la 23:57, Eugen Ginta ***@***.***> a scris:
>
>> I reverted to 2022.2.7 because I can't use it at all. Not even delete it
>> from integrations, but if you think you have fixed it I'll try again ...
>>
>> În vin., 4 mar. 2022 la 23:47, Julius Vitkauskas <
>> ***@***.***> a scris:
>>
>>> Can you try 0.4.0?
>>>
>>> —
>>> Reply to this email directly, view it on GitHub
>>> <https://github.com/jvitkauskas/homeassistant_salus/issues/29#issuecomment-1059555753>,
>>> or unsubscribe
>>> <https://github.com/notifications/unsubscribe-auth/ASMB5YXD2HWBTBCX4AAC3J3U6KAI3ANCNFSM5PYXGABA>
>>> .
>>> Triage notifications on the go with GitHub Mobile for iOS
>>> <https://apps.apple.com/app/apple-store/id1477376905?ct=notification-email&mt=8&pt=524675>
>>> or Android
>>> <https://play.google.com/store/apps/details?id=com.github.android&referrer=utm_campaign%3Dnotification-email%26utm_medium%3Demail%26utm_source%3Dgithub>.
>>>
>>> You are receiving this because you commented.Message ID:
>>> ***@***.***>
>>>
>>


#### @willhaggan commented at 2022-03-04T22:28:37Z

Hi there yes the latest update fixes the issue.
Thanks for the quick response.

#### @mindvisionro commented at 2022-03-05T13:09:09Z

Works with the latest update. Thanks for the quick fix.

---

## #28: Blocking call

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/28
- State: closed
- Author: @dennisgranasen
- Created: 2022-02-04T08:18:31Z
- Updated: 2022-02-10T17:25:45Z
- Labels: none

### Issue body

As the logs suggest:
```
Logger: homeassistant.util.async_
Source: util/async_.py:144
First occurred: 06:30:48 (1 occurrences)
Last logged: 06:30:48

Detected blocking call inside the event loop. This is causing stability issues. Please report issue to the custom component author for salus doing blocking calls at custom_components/salus/__init__.py, line 55: time.sleep(3)
```

### Conversation

#### @dennisgranasen commented at 2022-02-04T08:19:54Z

Log entry from the underlying lib:
```
Logger: pyit600
Source: /usr/local/lib/python3.9/site-packages/pyit600/gateway.py:939
First occurred: 06:30:41 (1 occurrences)
Last logged: 06:30:41

Timeout while connecting to gateway:
```

#### @jvitkauskas commented at 2022-02-08T11:02:28Z

Should be fixed in 0.3.3

---

## #27: Error on HA 2021.12.10 docker container

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/27
- State: closed
- Author: @brosu
- Created: 2022-01-28T07:49:13Z
- Updated: 2022-03-06T12:37:13Z
- Labels: none

### Issue body

Hello,

The following error error is displayed while adding the integration:
2022-01-28 09:23:17 ERROR (SyncWorker_2) [homeassistant.util.package] Unable to install package pyit600==0.3.1: ERROR: Cannot install pyit600==0.3.1 because these package versions have conflicting dependencies.
...
homeassistant.requirements.RequirementsNotFound: Requirements for salus not found: ['pyit600==0.3.1'].
Home Assistant 2021.12.10 running on Docker; no other HACS custom_component.

### Conversation

#### @jvitkauskas commented at 2022-03-06T12:37:13Z

Should be fixed in version 0.4.0

---

## #26: Always „Follow Schedule“ mode

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/26
- State: open
- Author: @xyz4tech
- Created: 2021-12-24T08:51:18Z
- Updated: 2023-04-05T10:03:38Z
- Labels: none

### Issue body

When I use the Salus integration to manually change the values of my Salus SQ610RF with the Lovelace Dashboard or the HomeKit Integration the mode „Follow Schedule“ alway comes up. It doesn‘t matter what values I changed. If I use the drop-down menus or the automation in Home Assistance the values are changed as desired after a short waiting period.

Do you have any idea what is going wrong with my configuration?

### Conversation

#### @Filip722 commented at 2022-05-02T23:16:53Z

Same here, installed it today, so no idea if older versions are OK. 
Found out that the proper way to change the mode (Auto-Hold-Off) is to set via "Preset" and not "Operation".

Unfortunately the standard card uses Preset for modes, so its always "Follow Schedule" mode, no matter what button do i click.

Seems like an easy fix - just change how the HA UI is talking with the integration - swap Operation to Preset.

For reference, talking about this card:
![image](https://user-images.githubusercontent.com/37023444/166341099-12b00e8f-655e-4375-ad36-0151d2031366.png)



#### @lukasha12 commented at 2022-05-08T16:54:08Z

I have the same problem too.

#### @alexcalcan commented at 2022-06-06T20:22:34Z

Same here. Any news or fixes?

#### @qweluke commented at 2022-10-30T19:33:13Z

Same here!

#### @qweluke commented at 2022-10-30T19:33:27Z

@jvitkauskas any chance for update?

#### @Diomet commented at 2023-02-13T12:12:38Z

Same here. Hoping for an update.

#### @bono122b commented at 2023-04-05T09:24:23Z

Hi. Had the same issue but after I turned off and turned on the integration it started to work fine for me at least for now. Although it seems like using salus mobile app is making the issue to come back and it is showing me different values on HA vs thermostat vs app. I guess I wont use app...

---

## #25: Unable to change hvac modes or presets - SQ610RF

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/25
- State: closed
- Author: @albei
- Created: 2021-12-06T07:17:12Z
- Updated: 2021-12-06T11:39:39Z
- Labels: none

### Issue body

Hello, I notice since the cold weather started that I am unable to change the hvac modes or presets.
I getting readings on temperature and current mode but there is no way I change it. The only thing that works is the temperature and even that reverse after couple of seconds. This is a inconvenient for me as I can't make automations switch presets from fallow schedule to off or hvac mode from Auto to off. That saddest thing is that I cannot trace the error. My guess is that the Fallow Schedule preset override every change you made in home assistant.
Thermo SQ610RF

### Conversation

#### @albei commented at 2021-12-06T11:39:31Z

Gonna Close it. I found The culprit, latest hassio update messed something. Reconfigured now looks like it works again. I can change the presets from automation.

---

## #24: Underfloor heating automation

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/24
- State: open
- Author: @cipriancaba
- Created: 2021-11-07T13:21:15Z
- Updated: 2021-11-10T18:54:39Z
- Labels: none

### Issue body

I have 2 distributors, 6 zones and 9 circuits each. I plan on buying the salus gateway, 18 actuators and 2 KL08RF command centres. Will I be able to control the KL08RF from HA with this gateway integration?

### Conversation

#### @yuandrk commented at 2021-11-10T18:54:39Z

@cipriancaba In this case, you need some thermostats (like TS600, HTRS-RF, etc.) for the controls to KL08RF command center, in HA you see only thermostats. 

---

## #23: KL08RF control any chance?

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/23
- State: open
- Author: @Gepar
- Created: 2021-11-06T09:56:14Z
- Updated: 2022-12-25T16:17:58Z
- Labels: none

### Issue body

Maybe i'll be little naive but can we control KL08RF to enable/disable heat like the thermostats this do?

### Conversation

#### @qweluke commented at 2022-10-30T19:32:33Z

AFAIK KL08RF does not support any kind of actions, event through official app.

#### @ajheyworth commented at 2022-11-19T08:26:18Z

I'm interested in this also - To command KL08RF groups on/off would be of particular benefit, so that heating can be controlled by HA with other sensors/intelligence and not just thermostats.

#### @microlomaniac commented at 2022-12-14T12:31:36Z

+1, I recently just found out that the Salus KL08RF uses Zigbee and even has a USB coordinator plugged into it (which I find quite funny). So I have two Zigbee networks in my home which don't talk to each other. I wonder if there is a way to combine the two.

In a perfect world, the room thermostats (VS10WRF/VS20WRF) would talk to both Zigbee networks. So they would be controllable through HASS but still send their data to KL08RF. But I don't see a way this is possible..

#### @ajheyworth commented at 2022-12-14T20:43:05Z

The Salus integration with HASS is working for me, but this is integrating the thermostats which in turn command the wiring centre.  Ideally Id like to get rid of the Salus thermotats (using KNX devices instead) and so then have HASS act as a bridge and emulate the thermostat commands to send to the wiring centre.

I also have a Shelly i4 wired up on the pump and boiler outputs of the wiring centre to understand these trends.

#### @microlomaniac commented at 2022-12-15T10:48:31Z

How have you integrated the thermostats into HASS while still having them commanding the wiring centre (by which I understand you mean the KL08RF)?

#### @ajheyworth commented at 2022-12-15T20:13:40Z

> How have you integrated the thermostats into HASS while still having them commanding the wiring centre (by which I understand you mean the KL08RF)?

If you use the Salus integration and then add Thermostat objects, you essentially have 'dual' control of each thermosatic zone; control from the thermostat itself and from HASS dashboards.  The functionality is limited - ie you cant override Salus/Omnie schedules and cannot by default read humidity, but you can control the mode and temperature setpoint. Of course you can also read the thermostat's temperature.
 

#### @microlomaniac commented at 2022-12-25T12:28:58Z

Please excuse my asking seemingly dumb questions, but I just want to make sure it works before changing anything.

My current situation: My VS20WRF thermostats are only paired to the KL08RF, which has its own Zigbee coordinator.
- If I put the VS20WRF thermostat(s) into pairing mode and add it to HASS, will it then still talk to KL08RF?
Thank you so much for your answers so far :)

#### @ajheyworth commented at 2022-12-25T16:17:58Z

Hi. No problem at all.

Theres no need to change your existing configuration.  Keep your
thermostats paired with the wiring centre, then add the Salus integration
and set it up to work with your gateway.  The integration doesnt require
the thermostats or wiring centre to talk with HASS via Zigbee - it allows
HASS to communicate with the Salus hub via IP.

The only trouble I had, was that my Salus Zigbee Hub has to be on the same
IP network as HASS to work properly, however when I do this, I then get
warnings in the Omnie/Salus app about unstable connectivity - its because
my firewall configuration is seeminglu much tighter than Salus wants to
talk with AWS/Salus servers.  You probably wont have the same issue.


On Sun, 25 Dec 2022, 12:29 microlomaniac, ***@***.***> wrote:

> Please excuse my asking seemingly dumb questions, but I just want to make
> sure it works before changing anything.
>
> My current situation: My VS20WRF thermostats are only paired to the
> KL08RF, which has its own Zigbee coordinator.
>
>    - If I put the VS20WRF thermostat(s) into pairing mode and add it to
>    HASS, will it then still talk to KL08RF?
>    Thank you so much for your answers so far :)
>
> —
> Reply to this email directly, view it on GitHub
> <https://github.com/jvitkauskas/homeassistant_salus/issues/23#issuecomment-1364674481>,
> or unsubscribe
> <https://github.com/notifications/unsubscribe-auth/ABECNKD5PAZKCOYTKRUPZ6TWPA4ZJANCNFSM5HPNXVJQ>
> .
> You are receiving this because you commented.Message ID:
> ***@***.***>
>


---

## #22: Floor temperature - new feature request

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/22
- State: open
- Author: @zylxpl
- Created: 2021-10-22T18:39:17Z
- Updated: 2021-11-06T09:58:26Z
- Labels: none

### Issue body

Most of Salus thermostats have S1, S2 terminals witch allow to connect floor temperature sensor. When connected, floor temperature  is reported in app. Any chance to add this to default to HA?
![termostat1](https://user-images.githubusercontent.com/13242378/138506377-89b8cbba-34a7-4056-b9ac-e2e992a58696.jpg)
![termostat2](https://user-images.githubusercontent.com/13242378/138506382-c56995f7-5e20-42c4-adde-c03489ced702.jpg)



### Conversation

#### @Gepar commented at 2021-11-06T09:58:26Z

Hello, i also have S1 terminal with floor temperature sensor but my VS20WRF show it in app only if i set in settings "use as main termperature sensor". 
When i set "use as additional sensor to limit floor temperature" i can only set limit to 27 for my laminate but app show then air temperature only.
I suspect that VS20WRF has both temperature to do this logic but can we get it?
Also right now output from library doesn't show it is control over floor (S1) or over air, it will be useful to get this info.

---

## #21: NA family of Devices just released

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/21
- State: open
- Author: @michaelklatsky
- Created: 2021-10-22T12:32:51Z
- Updated: 2021-10-22T12:32:51Z
- Labels: none

### Issue body

I have been testing this with the Salus UG888 gateway (for North America) and it can communicate with the gateway but is not pulling in any additional devices - TRV’s and Thermostats.  Do you think that the code needs to have the new models/devices added?

SG888ZB Gateway 
AC10RF Coordinator
AS20WRF/BRF Digital Thermostat
AWRT10RF Wireless Radiant Thermostat
AKL01PRF Zone Pump Wiring Center
AKL08RF Zone Valve Wiring Center I
ARV10RFM Radiator Valve Actuator

### Conversation

_No comments._

---

## #20: unable to connect - EUID error 

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/20
- State: open
- Author: @loopez76
- Created: 2021-10-18T20:14:15Z
- Updated: 2024-04-02T12:49:38Z
- Labels: none

### Issue body

Same error - "Failed to connect, please check EUID"

IP is pingable from HA (same segment), troubleshooting done, done several reboots. In HA timeout - any ideas ? Same error on 0.3.0 0.3.1

In log of HA:
2021-10-20 17:55:00 ERROR (MainThread) [pyit600] Timeout while connecting to gateway:

SW vewrsion: 020143210405 coordinator 20210317

@jvitkauskas any chance for help ? Multiple resets of gateway did nothing. with GH working fine but GH is connecting over cloud not directly



### Conversation

#### @Raoulex commented at 2021-10-21T17:21:00Z

Same issue here also.

#### @zylxpl commented at 2021-10-22T18:27:11Z

had same issue. After factory reset  (more than one) it started to work. Use only lower case characters in euid.

#### @thatvalis commented at 2021-11-14T09:34:46Z

Same issue here. Have done a lot of factory resets and/or reconnecting power.
Same error: "Failed to connect, please check EUID"

#### @loopez76 commented at 2021-11-22T21:46:57Z

Still no win. Checked on another gateway with same results. Looks like since some firmware is not working. Integration with GH works fine with no issues


#### @ncwp commented at 2022-01-03T16:26:24Z

I am getting the same error too, with the timeout error in the log.
Same software and coordinator versions as @loopez76.

#### @Wersal-kp commented at 2022-01-07T21:43:07Z

I also have the same error :/ "Failed to connect, please check EUID" and timeout error in the log. The same software id and coordinator. What is this euid? Is this a salus gateway zigbee key or what? What ports should be open on gateway?

#### @Wersal-kp commented at 2022-01-07T21:52:58Z

I just used '0000000000000000' as e EUID and it works.

#### @loopez76 commented at 2022-01-07T22:30:23Z

> 

Just retried with 0000000000000000 as EUID - and confirm. It works.

#### @jvitkauskas commented at 2022-01-14T20:22:06Z

Thanks, added this suggestion to troubleshooting section of the README

#### @ncwp commented at 2022-01-17T10:31:21Z

FYI the 0000000000000000 EUID did not work for me.
It looks like my gateway is actually timing out, never responds with any data. If I browse to the gateway in the regular browser I see a lot of requests to `deviceid/read` and they all time out there too. So I guess that maybe this is a problem that cannot be fixed in Python. main.py from pyit600 also times out.

#### @pekarsky commented at 2022-01-24T19:59:54Z

> FYI the 0000000000000000 EUID did not work for me. It looks like my gateway is actually timing out, never responds with any data. If I browse to the gateway in the regular browser I see a lot of requests to `deviceid/read` and they all time out there too. So I guess that maybe this is a problem that cannot be fixed in Python. main.py from pyit600 also times out.

Oh, I was able to query GW with main.py from py600it, using this EUID
Working on adding integration

Wow! it is working, not sure, for how long

#### @BrodaBob commented at 2022-02-27T16:51:12Z

I don't see any EUID on my gateway. I only see a 15-digit serial #. And that's the same as I can see displayed in the Information menu in the app.
I've tried the 16-zero euid to no avail.
I'm in Europe, btw.
Any advice? :-)

#### @RazvanDespa commented at 2022-11-28T19:29:39Z

Hi,

I have the same problem, the EUID i see in the app or on the UGE600 gateway has only 15 characters. I have tried also with 16 zeroes but still no luck.

Any idea?

Thanks,
Razvan

#### @BrodaBob commented at 2022-11-28T20:35:36Z

> Hi,
> 
> I have the same problem, the EUID i see in the app or on the UGE600 gateway has only 15 characters. I have tried also with 16 zeroes but still no luck.
> 
> Any idea?
> 
> Thanks, Razvan

Yeah I figured it out. You're looking at the wrong string. Remove the cables and then you see the correct 16-digit string on the left side :-)

#### @RazvanDespa commented at 2022-11-28T21:01:02Z

> 

@BrodaBob you are the master ... yes, next there were more codes but due to the position i haven't seen them. All is good now.

#### @ConstantinOWORX commented at 2023-08-30T13:21:13Z

Make sure to enable the wi-fi local mode, that fixed it for me.

#### @alex-ricobon commented at 2023-09-11T15:41:25Z

> Make sure to enable the wi-fi local mode, that fixed it for me.

Do I need to connect the gateway to WiFi, or just enable local WiFi mode?

#### @trullock commented at 2024-04-02T10:24:33Z

I have the JG Aura branded version of the it600,

Where do I enable Local Wifi mode? It doesn't appear as an option anywhere

~And where do i find the EUID?~ OK so I have to unplug the usb adaptor and its on the underside.

I've found I can telnet to the box with admin/admin and get root access, I've had a poke around but I can't see any clue as to how to activate the local control, which currently appears to be disabled for me. I'm connected via ethernet, do I have to connect via WiFi to see the option?

Thanks

#### @trullock commented at 2024-04-02T12:49:36Z

OK, so telneted to the box 
and exec
`/mnt/sal6dg1/run_sal6dg1.sh`
Use the app to change various thermostat settings and you can see a heap of debug information flying by

---

## #19: After update to 0.3.0, any thermostat doesn't work in HA  

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/19
- State: closed
- Author: @yuandrk
- Created: 2021-09-27T11:55:29Z
- Updated: 2021-10-02T08:24:15Z
- Labels: none

### Issue body

Dear @jvitkauskas  
Today I updated pyit600 to 0.3.0, but after the restart, all thermostats are not available. 

This message show in logs : 

Logger: pyit600
Source: /usr/local/lib/python3.9/site-packages/pyit600/gateway.py:544
First occurred: 14:36:08 (1298 occurrences)
Last logged: 14:54:25

Failed to poll device 001e5e09026820c2
Failed to poll device 001e5e0902681f37
Failed to poll device 001e5e09026821a6
Failed to poll device 001e5e090208ed91
Failed to poll device 001e5e0902518e08
Traceback (most recent call last):
  File "/usr/local/lib/python3.9/site-packages/pyit600/gateway.py", line 500, in _refresh_climate_devices
    device = ClimateDevice(
TypeError: <lambda>() missing 3 required positional arguments: 'fan_mode', 'fan_modes', and 'locked'


### Conversation

#### @maymaymay commented at 2021-09-28T06:22:51Z

Same here:
```
2021-09-28 06:13:16 ERROR (MainThread) [pyit600] Failed to poll device 001e5e090208eeca
Traceback (most recent call last):
File "/usr/local/lib/python3.9/site-packages/pyit600/gateway.py", line 500, in _refresh_climate_devices
device = ClimateDevice(
TypeError: <lambda>() missing 3 required positional arguments: 'fan_mode', 'fan_modes', and 'locked'
2021-09-28 06:13:16 ERROR (MainThread) [pyit600] Failed to poll device 001e5e090208f361
Traceback (most recent call last):
File "/usr/local/lib/python3.9/site-packages/pyit600/gateway.py", line 500, in _refresh_climate_devices
device = ClimateDevice(
TypeError: <lambda>() missing 3 required positional arguments: 'fan_mode', 'fan_modes', and 'locked'
2021-09-28 06:13:16 ERROR (MainThread) [pyit600] Failed to poll device 001e5e090208ed34
Traceback (most recent call last):
File "/usr/local/lib/python3.9/site-packages/pyit600/gateway.py", line 500, in _refresh_climate_devices
device = ClimateDevice(
TypeError: <lambda>() missing 3 required positional arguments: 'fan_mode', 'fan_modes', and 'locked'
2021-09-28 06:13:16 ERROR (MainThread) [pyit600] Failed to poll device 001e5e090208f497
Traceback (most recent call last):
File "/usr/local/lib/python3.9/site-packages/pyit600/gateway.py", line 500, in _refresh_climate_devices
device = ClimateDevice(
TypeError: <lambda>() missing 3 required positional arguments: 'fan_mode', 'fan_modes', and 'locked'
2021-09-28 06:13:16 ERROR (MainThread) [pyit600] Failed to poll device 001e5e090208f610
Traceback (most recent call last):
File "/usr/local/lib/python3.9/site-packages/pyit600/gateway.py", line 500, in _refresh_climate_devices
device = ClimateDevice(
TypeError: <lambda>() missing 3 required positional arguments: 'fan_mode', 'fan_modes', and 'locked'
2021-09-28 06:13:16 ERROR (MainThread) [pyit600] Failed to poll device 001e5e090208f186
Traceback (most recent call last):
File "/usr/local/lib/python3.9/site-packages/pyit600/gateway.py", line 500, in _refresh_climate_devices
device = ClimateDevice(
TypeError: <lambda>() missing 3 required positional arguments: 'fan_mode', 'fan_modes', and 'locked'
```

#### @jvitkauskas commented at 2021-10-01T19:05:32Z

Sorry that I didn't test it when merging changes. Can you please try version 0.3.1?

#### @maymaymay commented at 2021-10-02T06:10:56Z

Hi  @jvitkauskas now with 0.3.1 its working again.
Thank YOU!

#### @jvitkauskas commented at 2021-10-02T08:24:03Z

Thanks. Closing.

---

## #18: Integration not showing up when trying to install

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/18
- State: open
- Author: @kaninfod
- Created: 2021-09-04T13:01:52Z
- Updated: 2021-09-04T17:34:29Z
- Labels: none

### Issue body

Hi 
I have had the salus integration working for months, but then one day it was not working anymore. I have tried to install it as described - both manually and through HACS. In HACS the repository is added fine, but when i go to configuration > integrations > add integration the salus integration dows not show up. Same for manual installation.
The files are added to `config/custom_components/salus`

Do you have any suggestions? has this behaviour been reported before?

### Conversation

#### @yuandrk commented at 2021-09-04T17:34:29Z

Hi @kaninfod 
I have early the same issue 
Helps me reboot the whole system.

---

## #17: Salus does not apper in integrations

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/17
- State: closed
- Author: @eemenda
- Created: 2021-08-15T11:57:25Z
- Updated: 2021-08-15T15:19:08Z
- Labels: none

### Issue body

After installing salus in hacs, salus does'nt apper in integrations. Also triying with coping folder in custom components.

### Conversation

#### @eemenda commented at 2021-08-15T15:19:08Z

Solved: clean browser cache!

---

## #15: Salus SR600 - delayed state change in home assistant UI

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/15
- State: open
- Author: @besthost86
- Created: 2021-06-19T19:15:12Z
- Updated: 2022-01-08T11:21:33Z
- Labels: none

### Issue body

When I click one of those two buttons (SR600 switches set to toggle on/off), I need to wait several seconds for them to change color which indicates a change of state. The switch itself responds instantaneously though. Then I have to wait 9+ seconds for it to show a change of state. I'm using Salus Gateway. Could this be a gateway problem?

![dashboardHA](https://user-images.githubusercontent.com/38145263/122653048-5e980580-d142-11eb-9702-29a893b87ef8.JPG)


### Conversation

#### @niklas007 commented at 2022-01-08T11:21:33Z

Got ther same issue here / i think its the integration between HA and the uge600 gateway that doesnt speek to each other quickly enught. 
I would get ride of the gateway if someone could integrate the salus trv:s to work with z2m

---

## #13: SR600 New features for button S1-S2

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/13
- State: open
- Author: @George-andrew
- Created: 2021-04-06T09:34:34Z
- Updated: 2021-04-06T09:34:34Z
- Labels: none

### Issue body

Dear @jvitkauskas, 

Could you please add new features for SR600, 
Below a description of how it works SR600  

I hope it helps you. 

```
"sButtonS": 
{
"Mode": 3,
"Mode_a": 3,
"PowerOnState": 0,
"ButtonStatus": 1,
"LostConnectionState": 0
 },



When "ButtonStatus" = 1 - terminals S1-S2 is close;
When "ButtonStatus" = 0 - terminals S1-S2 is open;

Description of Mode S1-S2 : 
When "Mode": 0 - S1-S2 no function, not showed S1-S2 on the app;
When "Mode": 1 - S1-S2 Switch on and off output; 
When "Mode": 2 - Reverse output for suitable for lighting; 
When "Mode": 3 - No output control, only show in app; 
When "Mode": 4 - S1-S2 Switch toggle relay;

Description of Power On State after turn on supply: 
When "PowerOnState": 0 - SR600 Keep last state after power cycle;
When "PowerOnState": 1 - SR600 Turn OFF relay after power cycle; 
When "PowerOnState": 2 - SR600 Turn ON relay after power cycle; 

Description of Lost Connection State after lost link ZigBee: 
When "LostConnectionState": 0 - not configured;
When "LostConnectionState": 1 - Output Off; Input enabled;
When "LostConnectionState": 3 - Output ON; Input enabled;
When "LostConnectionState": 5 - Maintain current state, input enabled ;

```

### Conversation

_No comments._

---

## #12: Bug with PS600 

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/12
- State: closed
- Author: @George-andrew
- Created: 2021-02-16T14:40:50Z
- Updated: 2021-02-22T10:41:26Z
- Labels: none

### Issue body

Dear Julius, 

I found a bug with my PS600,
in HA shows two devices like the temperature sensor and binary sensor with the same name  

Below in attachment my screenshot :  
![image](https://user-images.githubusercontent.com/67461821/108077744-28038e80-706d-11eb-89de-be8c6ebfb7c8.png)
![image](https://user-images.githubusercontent.com/67461821/108077822-41a4d600-706d-11eb-98a3-7aebdd37b3c5.png)


``

### Conversation

#### @jvitkauskas commented at 2021-02-19T15:54:45Z

Can you check if binary sensor gets activated if you remove back cover (not the front one which contains battery)? There is also a button on the side. I wonder what does it do.

Edit: tried it myself and it does not seem to do anything. If that bothers you, you can just disable that entity in homeassistant UI. So far, I am a bit reluctant to do a device-specific hacks in the integration.

#### @George-andrew commented at 2021-02-22T10:41:26Z

@jvitkauskas OK, many thanks for your answer 
But if you have will anytime, please hide this  entity in homeassistant UI  

---

## #11: Unavailable entries after reboot. 

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/11
- State: closed
- Author: @bse4792
- Created: 2021-02-11T06:44:38Z
- Updated: 2021-04-05T13:16:00Z
- Labels: none

### Issue body

Hi I'm facing a weird problem.

All is working well and fine when I install via hacs.
I add the integration give key and ip, all entries comes and changeable. 

But when I restart HA, then all entries becomes unavailable. 
Then I can remove and add integration and then it's working fine. 

I have tried reinstall via hacs, but nothing seems to work. 

Kindly Daniel 

### Conversation

#### @jvitkauskas commented at 2021-02-19T15:57:45Z

Can you see any errors in the logs? Also, are you sure IP of the gateway remains the same?

How are you restarting HA? Supervisor -> System -> Reboot host?

#### @bse4792 commented at 2021-02-19T17:04:04Z

Hi I just removed integration now and reintegrated it to be sure it was OK and working. 

Was working perfectly before reboot but after not. 

![Screenshot_20210219-175934](https://user-images.githubusercontent.com/29598723/108536224-79658500-72dc-11eb-9d2e-4af26c24bca3.jpg)
Here is the log after normal reboot as you described never do it in other ways. 



#### @bse4792 commented at 2021-02-19T17:08:12Z

It also come with this error

![Screenshot_20210219-180631](https://user-images.githubusercontent.com/29598723/108537030-6acb9d80-72dd-11eb-9b82-757b09ecb9b8.jpg)


#### @bse4792 commented at 2021-02-19T19:53:01Z

Here is proof it's working prereboot

![Screenshot_20210219-205003](https://user-images.githubusercontent.com/29598723/108554433-5e067400-72f4-11eb-831b-511f7137ef4b.jpg)
![Screenshot_20210219-205018](https://user-images.githubusercontent.com/29598723/108554445-62cb2800-72f4-11eb-96ba-c8f6a7605404.jpg)
![Screenshot_20210219-205046](https://user-images.githubusercontent.com/29598723/108554458-66f74580-72f4-11eb-8760-80a064e31407.jpg)


#### @jvitkauskas commented at 2021-02-19T21:01:10Z

Some questions you can answer to help me reproduce this:
* Are you running homeassistant on a raspberry pi (which version?) or on a PC or in a VM? Also what is the connection wifi/wired ethernet?
* Is your Salus gateway connected over wired ethernet or wifi?
* How are you rebooting homeassistant?

#### @bse4792 commented at 2021-02-19T21:14:35Z

VM on esxi 6.0 with image from home assistant. So obviously wired ethernet. 

wired ethernet on uge600 but WiFi credentials are added

Configuration -> server control -> reboot

#### @bse4792 commented at 2021-02-19T21:15:20Z

![Screenshot_20210219-221506](https://user-images.githubusercontent.com/29598723/108562305-f22a0880-72ff-11eb-8555-347861cf3507.jpg)


#### @marithpl commented at 2021-02-24T10:22:16Z

I've got the same problem. Usually after fresh start of Home Assistant the Salus Thermostats are unavailable.

`2021-02-24 11:15:32 ERROR (MainThread) [custom_components.salus] Authentication error: check if you have specified gateway's EUID correctly.
`

Usually restart HA from UI helps, but not always.

My config is:
Home Assistant installed via Docker on Synology NAS
Salus Gateway conntected via Wi-Fi with strong signal

#### @jvitkauskas commented at 2021-02-27T12:30:01Z

Unfortunately I can't reproduce this, think I'll do a 3 time connection retry. Maybe it would help.

#### @jvitkauskas commented at 2021-03-10T22:00:21Z

I've added a simple 3 time retry with 3 second delay between retries.

#### @jvitkauskas commented at 2021-03-15T19:32:51Z

@bse4792 @marithpl have you tried new version? Did it solve your problems?

#### @bse4792 commented at 2021-03-15T20:44:07Z

Hi @jvitkauskas yes i have tried, but it did not resolve the problem.

i'm considering trying a new HA install just to test, if that is my problem

#### @jvitkauskas commented at 2021-03-15T20:48:21Z

It sucks that I cannot reproduce this myself. Maybe one of you have access to a smart(er) switch with port mirroring and could set up wireshark to see how many connection attempts/requests are being sent to gateway and of they timeout or whatnot. Or just dump tcp traffic destined to salus gateway on the home assistant machine.

#### @bse4792 commented at 2021-03-15T21:27:40Z

i'm getting a dream mashine some time this week and will resetup my wifi/network completely

if you could help me with tcp trafic dump then it would be helpful.

as of now i'm using pfsense in VM and i'm expecting that to cause some problems.
can you send private massage then we can take this a bit more secure

#### @marithpl commented at 2021-03-15T22:35:52Z

Recently I didn't observe this problem.

#### @bse4792 commented at 2021-04-05T13:16:00Z

seams to be working now

---

## #10: Salus is'ent showing up in integrations

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/10
- State: closed
- Author: @jansejer
- Created: 2021-01-31T00:28:58Z
- Updated: 2021-02-01T22:55:48Z
- Labels: none

### Issue body

Hi, Any idea why Salus dosent show up under configurations->integrations after making the install in HACS?

### Conversation

#### @jvitkauskas commented at 2021-01-31T10:39:24Z

The readme was a bit outdated. You basically have to copy `custom_components` folder from this repository to `/config`

#### @jvitkauskas commented at 2021-02-01T21:10:22Z

@jansejer did that solve your issue?

#### @jansejer commented at 2021-02-01T21:22:44Z

yes it works absolutely perfect now. thanks

#### @jvitkauskas commented at 2021-02-01T22:55:48Z

Thanks. Closing this.

---

## #9: New features

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/9
- State: open
- Author: @marithpl
- Created: 2021-01-30T23:05:09Z
- Updated: 2023-11-28T15:26:26Z
- Labels: none

### Issue body

I really appreciate your good job.
I've got a question if is possible to extract to HA two things:
1) Humidity form thermostats
2) Some thermostats eg. SQ610 have function "Comfort floor" available in installer menu.
Comfort mode is turn on heating for X minutes every hour to maintain comfortable warm floor.
I really excited of this feature but it's not economic for heating for ex. at night. I wish to have this attribute to make automation when comfort floor should be turned on or off.


### Conversation

#### @jvitkauskas commented at 2021-01-31T10:37:29Z

1. Humidity for SQ610 was added by @albei I don't have that model, so I can't test. Are you talking about SQ610?
2. Do you have this function available in the official app?

#### @albei commented at 2021-01-31T10:40:54Z

The function exists in the app as a settings that you can access in advance mode. Gonna try search for it in Salus ha

#### @marithpl commented at 2021-01-31T10:45:55Z

1.I use SQ610RF, and I have humidity in in Salus App but not in HA.
2. On third screenshot I mark an Comfort Floor function


<img width="280" alt="image" src="https://user-images.githubusercontent.com/25366097/106381509-8a943380-63b9-11eb-8aad-f7f6b38d62d9.png">

<img width="280" alt="image" src="https://user-images.githubusercontent.com/25366097/106381531-bca59580-63b9-11eb-8eee-52f54af3efc1.png">

<img width="280" alt="image" src="https://user-images.githubusercontent.com/25366097/106381604-48b7bd00-63ba-11eb-86cf-7427f03c216a.png">



#### @albei commented at 2021-01-31T10:53:05Z

You can look humidity up in developer tools in States section. Look it up by name. 

If you wanna us it you have to make a custom sensor in your configuration.yaml with the humidity parameter like this.
```yaml
climate_YOUR_THERMO_NAME_humidity:
    friendly_name: "You can chose your friendly name"
    unit_of_measurement: '%'
    value_template: "{{state_attr ('thermostat_entity_name', 'current_humidity')}} "
```

#### @marithpl commented at 2021-01-31T11:02:23Z

I can't see humidity. Maybe I need to update a module?
edited: I copied files and it works
<img width="427" alt="image" src="https://user-images.githubusercontent.com/25366097/106381889-2626a380-63bc-11eb-8435-c21e97c4511b.png">


#### @albei commented at 2021-01-31T11:43:08Z

What version do you have installed?
Looks like you have previous version of pyit600 since you dont have the complete hvac_modes.
it should look like this
```yaml
hvac_modes:
  - 'off'
  - heat
  - auto
min_temp: 5
max_temp: 35
preset_modes:
  - Follow Schedule
  - Permanent Hold
  - 'Off'
current_temperature: 24.1
temperature: 5
current_humidity: 54
hvac_action: 'off'
preset_mode: 'Off'
friendly_name: Thermo
supported_features: 17
```


#### @marithpl commented at 2021-01-31T11:49:18Z

I edited previous comment, that I updated.
Is it possible to have this extension in HACS? To get notification about new version?

I hope "comfort floor" feature is possible to get in HA.

#### @albei commented at 2021-01-31T11:51:39Z

@jvitkauskas i dont know how can the settings section of the thermostat can be added to homeassistant.
The thermostat Card only has Preset and Operation options in the settings.
The Comfort Warm Floor property is in the: 'customPropertiesForQuantumThermostat'
 
 ```json       
                    propName: "ComforWarmFloor_Custom",
                    propTitleKey: "equipment.property.names.quantumThermostat.ComfortWarmFloor"                  
 ```
 The way it is constructed:
 ```json
 else if ("ComforWarmFloor_Custom" === d) c = [{
                        key: "equipment.property.values.disabled",
                        value: "00"
                    }, {
                        text: t.translate("equipment.property.values.levelNumber", {
                            number: 1
                        }),
                        value: "01"
                    }, {
                        text: t.translate("equipment.property.values.levelNumber", {
                            number: 2
                        }),
                        value: "02"
                    }, {
                        text: t.translate("equipment.property.values.levelNumber", {
                            number: 3
                        }),
                        value: "03"
                    }], a = {
                        type: "dropdown",
                        collection: c
```


#### @albei commented at 2021-01-31T11:53:18Z

> I edited previous comment, that I updated.
> Is it possible to have this extension in HACS? To get notification about new version?
> 
> I hope "comfort floor" feature is possible to get in HA.

It is in hacs, it has what it needs to be installed. I added the repository and it works flawless :)

#### @jvitkauskas commented at 2021-01-31T13:42:09Z

@albei do you know how can I submit this to HACS default repositories?

#### @albei commented at 2021-01-31T13:46:56Z

> @albei do you know how can I submit this to HACS default repositories?

This is process: 
https://hacs.xyz/docs/publish/include
https://github.com/hacs/default

#### @jvitkauskas commented at 2021-01-31T18:03:02Z

Ok, I have these PRs pending
* https://github.com/home-assistant/wheels-custom-integrations/pull/261
* https://github.com/hacs/default/pull/802

Also, I have bought SQ610RF, but I probably will have to wait a few weeks till it gets to me.

#### @marithpl commented at 2021-02-01T15:27:54Z

As I understand it's possible to have comfort floor in HA?

PS. I am not able to found this extension in HACS (https://hacs-repositories.web.app)

#### @jvitkauskas commented at 2021-02-01T21:08:33Z

@marithpl I'll see what I can do once I get the device. Regarding HACS, I've written in the past comment that I have submitted it, but PRs are pending review. Hopefully somebody will take a look at them soon.

#### @martinez1000 commented at 2021-02-11T15:16:41Z

I am impressed with this repo, unfortunately I have an IT500 based system installed. Have you prepared similar or are you planning for the IT500? Unfortunately, I found only working elements for the IT500 for Node-red, but I would prefer, as probably most, the integration with HA and access to Lovelace UI.

#### @jvitkauskas commented at 2021-02-12T13:48:13Z

> IT500

Took a quick look at iT500 app. It seems to be an entirely different system and also cloud-only. So no code could be reused from iT600 integration. Unfortunately, I have no plans for iT500 support.

#### @marithpl commented at 2021-02-22T07:42:07Z

@jvitkauskas Any update with comfort floor feature?

#### @jvitkauskas commented at 2021-02-22T08:18:55Z

I'll have SQ610 coming to me this week. Probably will take a look at this this weekend.

#### @torsteinhs commented at 2021-02-25T07:46:06Z

I really appreciate the work you are doing here. I am currently testing out several sensors, as I am working in a company that sell these products. 
For now, I am testing with the following products, and can provide some feedback on how these are working:
-SQ610: I have set up two of these, they work perfectly
-WLS600: One of these, it also works perfectly. Really nice that you can extract the temperature (which you can't in the Salus app)
-OS600: Same as WLS600, works perfectly and even lets you see the temperature
-SD600: I have two of these, but only one is discovered. I have tried to completely remove and reinstall the integration. The one that is discovered works like a charm. Maybe it also has some temperature sensor that could be used?
-SPE600: I have one of these, works perfectly
-SR600: I have 6 of these, but none of them are discovered. I will try again to see if it is a PICNINC issue (Problem In Chair, Not In Computer), but as stated above, I have tried removing and reinstalling the integration without any improvement.

I do not have any particular skills when it comes to programming, but if there  is any information that I can assist you with, please let me know!

#### @jvitkauskas commented at 2021-02-26T19:53:42Z

@marithpl I've checked that comfort floor feature and setting it seems to be unnecessarily complicated. The issue is that all settings needs to be set at once and there's no easy way to get current settings. The app basically has everything hardcoded and reconstructs full settings and sends it back each time you change anything (I think it even sets current time). I've checked the manual and it seems like it just enables heating for a certain period time. Is there any reason you could not automate it using other home assistant automation features? You could probably set temperature to 35 degrees to enable heating and then set it back periodically.

#### @torsteinhs commented at 2021-03-01T08:29:56Z

@jvitkauskas I have sent you an e-mail with some information. I am currently running HA on a raspberr pi.

#### @jvitkauskas commented at 2021-04-04T16:40:21Z

@torsteinhs can you update to 0.2.7 and see if SR600 devices are available?

Regarding SD600, I have bought it and it works fine for me. Not sure why the gateway doesn't report information for you.

#### @torsteinhs commented at 2021-04-05T08:30:59Z

@jvitkauskas All my SR600 units are showing after the update. Regarding the SD600, I have from time to time been able to discover one of my two units, but never both at the same time. It also seems to disappear after a while.

#### @Ashden commented at 2022-01-26T15:08:15Z

> You can look humidity up in developer tools in States section. Look it up by name.
> 
> If you wanna us it you have to make a custom sensor in your configuration.yaml with the humidity parameter like this.
> 
> ```yaml
> climate_YOUR_THERMO_NAME_humidity:
>     friendly_name: "You can chose your friendly name"
>     unit_of_measurement: '%'
>     value_template: "{{state_attr ('thermostat_entity_name', 'current_humidity')}} "
> ```

While this works as a custom sensor, the Salus integration in Homebridge exposes the humidity sensor automagically and it's linked to the thermostat (adding the integration to HA causes HA to have both temp and humidity entities for the thermostat). This also leads to being able to ask Siri for the humidity and getting the data, in the case of Apple Home integration.

Is this possible to be implemented in this integration? 

#### @sarbuandreidaniel commented at 2022-12-19T15:29:09Z

> @marithpl I've checked that comfort floor feature and setting it seems to be unnecessarily complicated. The issue is that all settings needs to be set at once and there's no easy way to get current settings. The app basically has everything hardcoded and reconstructs full settings and sends it back each time you change anything (I think it even sets current time). I've checked the manual and it seems like it just enables heating for a certain period time. Is there any reason you could not automate it using other home assistant automation features? You could probably set temperature to 35 degrees to enable heating and then set it back periodically.

@jvitkauskas Any updates here ? I'm interested too into the comfort floor setting, or any other advanced settings.

#### @george-apostu8 commented at 2023-11-28T15:26:25Z

Any updates on `"comfort floor feature"`?

---

## #6: Missing follow schedule button from thermostat card.

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/6
- State: closed
- Author: @albei
- Created: 2020-12-31T10:29:31Z
- Updated: 2021-01-10T14:27:06Z
- Labels: none

### Issue body

Something is not quite complete. I tested both homeassistant_salus gits, yours and konradb3's. In Konradsb3's the follow schedule button exists in your doesnt. I only see the heat and the off button. It a little beyond me, cant manage to find the cause. Gonna still look for it comparing the code.

### Conversation

#### @albei commented at 2020-12-31T10:45:14Z

I found what is missing, gonna do a patch later today together with another small change I made for temp display.

#### @jvitkauskas commented at 2021-01-10T14:27:05Z

Fixed in pyit600. Thanks.

---

## #3: athom homey integration with Salus thermostates

- URL: https://github.com/epoplavskis/homeassistant_salus/issues/3
- State: closed
- Author: @SemyonSV
- Created: 2020-10-06T04:23:43Z
- Updated: 2020-10-10T20:08:31Z
- Labels: none

### Issue body

Hi!
is it possible to integrate Salus thermostats with athom homey?

### Conversation

#### @jvitkauskas commented at 2020-10-06T17:59:53Z

Yes, it should be doable in case somebody wants to rewrite code in JavaScript.
