<!-- README.md -->
<!-- Qompass AI - [Add description here] -->
<!-- Copyright (C) 2025 Qompass AI, All rights reserved -->
<!-- ---------------------------------------- -->
#!/bin/sh
#
#	Version 3.7
#	OneRNG configuration file
#
#	Disable rngd startup by setting ONERNG_START_RNGD to "0"
#	
#	set ONERNG_MODE_COMMAND to choose system mode:
#
#	cmd0	- Avalanche noise with whitener (default)
#	cmd1	- Raw avalanche noise
#	cmd2	- Avalanche noise and RF noise with whitener
#	cmd3	- Raw avalanche noise and RF noise
#	cmd4	- No noise
#	cmd5	- No noise
#	cmd6	- RF noise with whitener
#	cmd7	- Raw RF noise
#
#	set ONERNG_VERIFY_FIRMWARE to "0" to disable firmware verification
#
#	set ONERNG_AES_WHITEN to "0" to disable additional whitening of OneRNG's data prior to passing
#		it to rngd
#
#	set ONERNG_URANDOM_RESEED to the rate at which /dev/urandom is has entropy added to it from the
#		system entropy pool - measured in seconds - "0" means continually top it up
#
#	set ONERNG_ENTROPY to a floating point value >0 and <1 that represents the amount of entropy
#		per bit provided by OneRNG. If you are feeling a little extra paranoid and want to
#		feed more entropy into the kernel you can make this value smaller.
#
#	set ONERNG_FEED_KERNEL if you have a newer kernel without a functioning RNGD - you can test for this
#		if "cat /dev/random >/dev/null" doesn't cause the OneRNG's LED to dim. If ONERNG_FEED_KERNEL
#		is set to "1" then instead of starting rngd insertion of a OneRNG will start a daemon that
#		will periodically copy data from the OneRNG to /dev/random
#
#	set ONERNG_FEED_RATE to the number of seconds between every feed of /dev/random if ONERNG_FEED_KERNEL 
#		is set. If you set it to "0" /dev/random will continually be fed (check out your system, make sure
#		this doesn't soak the CPU)
#
ONERNG_START_RNGD="1"
ONERNG_MODE_COMMAND="cmd0"
ONERNG_VERIFY_FIRMWARE="1"
ONERNG_AES_WHITEN="1"
ONERNG_URANDOM_RESEED="0"
ONERNG_ENTROPY=".93750"

