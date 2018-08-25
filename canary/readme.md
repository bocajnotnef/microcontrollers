# What

We have a faulty GFI in our garage that keeps knocking our beer fridge / deep freeze offline. This happens semi-randomly and we haven't been able to pin down a pattern, so I wrote a script to listen for a heartbeat from a microcontroller that I've put on the same circuit. If the script doesn't hear from the microcontroller for a timeout, it sends me an email.

Eventually the 'email' will be adapted to trigger a webhook on a telegram bot that will notify our housing group chat, and I'll abstract the 'canary' system to handle multiple canaries and to specify actions for them based on their MACs in a config file.

# How

I've been [fiddling with microcontrollers](https://highnoiseratio.org/esp8266-intro.html) for a little bit now. Originally I had some I was planning to eventually use to automatically monitor greenhouse conditions--it would periodically sample environmental readings and then transmit them to a script I ran on a raspi, which would write them to a database.

It was fairly easy to modify the program for the microcontroller, I just removed the lines that dealt with sensors and simplified its message sent to the raspi. I spun up a spare email account on a domain I have and followed [a tutorial](https://medium.freecodecamp.org/send-emails-using-code-4fcea9df63f) on using email with python to get it to email me when I wanted. The rest was some simple logic!


config file format follows:

```
[DEFAULT]
EmailDomain = mail.server.domain
EmailUser = person@address.tld
EmailPassword = seeecccrreeettt
EmailSTARTTLSPort = 555
EmailTarget = otherperson@otheraddress.tld
EmailSubject = words
```