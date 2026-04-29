Title: I accidentally made law enforcement shut down their fake honeypot
Summary: How I stumbled across a fake booter site run by international police, and how they panicked when I started digging
Date: 2026-04-29
Image: /assets/blog/cyberzap-pricing.png
Hash: ddos
---------

## What is Operation PowerOFF?

Before we get into the funny part, you need a quick summary. Operation PowerOFF is a massive international effort to
stop DDoS for hire services. While it includes agencies like the FBI, the UK National Crime Agency, and Europol, the
whole thing seems to be heavily coordinated by the Dutch Politie.[^operation-poweroff]

The Dutch police appear to run the actual infrastructure for these operations. They have been active for quite some time
now, and over the years, they have managed to seize a maybe around one hundred domains[^seized-fyi] and make a few arrests here and there[^europol-arrests].

## Digging into "Cyberzap"

I have been looking around Operation PowerOFF for a bit, and whilst digging around, I stumbled across a website called ``https://cyberzap.fun/``.

It did not look flawlessly professional, but it definitely looked legit enough. It perfectly mirrored the thousands of
skidded booter sites floating around the internet. It was not perfect, but there was absolutely a solid effort put into
it. They even set up robots.txt files, sitemaps, SEO friendly meta tags, and everything else a real website needs to rank on search engines.
<img 
  src="/assets/blog/cyberzap.png" 
  alt="Cyberzap Site" 
  style="width: 100%; height: 310px; object-fit: cover; object-position: top;" 
/>
<div class="subtext">There's more to this image! You can view the whole website by clicking on the image to open it in a new tab</div>

However, there was a massive giveaway if you even slightly started looking. The Dutch police absolutely love using bit.nl as their server host. And when
you check the MX DNS records, Cyberzap used bit.nl for their mail servers.

I decided to sign up to see how deep this went. I just wanted to let them know that I'm just researching, and not an
active cyberterrorist™. So I registered with the email ``conducting-research-hello-operation-poweroff@lina.sh``.
<div class="subtext">(I sadly didn't take any screenshots of the registration page, but it had a turnstile captcha and everything)</div>

Surprisingly, they even sent a real activation email! With an activation link that had a token embedded, and manual code you could enter.
<img 
  src="/assets/blog/signup-email.png"
    alt="Signup Email"
/>

The dashboard looked maybe a little empty, *but* still believable. It had fake network speed graphs that updated on the current time,
and a fake counter of connected bots.
<img
    src="/assets/blog/cyberzap-dashboard.png"
    alt="Cyberzap Dashboard"
/> 
<div class="subtext">Screenshot was taken a bit later, after I was already playing around with the website</div>

I wanted to see what happened if I "ordered an attack". 
Again, I didn't want them to think I am an evil hacker, so I entered a silly domain.

<img
    src="/assets/blog/ordering-an-attack.png"
    alt="Benjamin Netanyahu, please smite this website!!!"
/>

You could choose Bitcoin, Monero, PayPal, or Credit Card.

<img 
    src="/assets/blog/payment-methods.png"
    alt="I'm paying with Monero, Opsec status: ON ✅"
/>

But no matter what you picked, it would just load around for a few seconds, and then present you with the message
``Payment Error - There was an error processing your payment. Please try again or contact support.``

You can view your past "attacks" in a history tab, where it will just show that the payment failed.
They really just let you prove your criminal intent, grab your IP address and email,
and they probably plan to use that as "evidence" if it ever comes to it.

## Scare tactics: Netcrashers

Cyberzap is meant to be a "secret" trap. But they also run another type of site. I found ``https://netcrashers.net/`` around
the same time.

<img src="/assets/blog/netcrashers.png" alt="Netcrashers Site" />

This site looks a lot faker, it gives us the promise to "crash all nets". But the moment you click any
button on the website, you immediately get redirected to a "scary" police warning  page. 
That page literally says the domain is created and owned by the Dutch Police.

<img src="/assets/blog/powered-by-dutchies.png" alt="Scary Police Warning" />
<div class="subtext">
"The Dutch Police has strong indications that you were looking for a DDoS-for-hire service. 
DDoS attacks are illegal and have serious consequences. 
You always leave traces online when committing cybercrime."
😈
</div>

This is clearly designed for kids. A teenager looks up a DDoS site, clicks a button, and gets a huge
jump scare with police badges. They get scared and close the tab.

## Oops, they shut the whole thing down because of me >w<

While I was digging around Cyberzap, testing shit, and taking screenshots, something quite funny happened:
The feds literally pulled the plug on the site.

I tried to load the page again, and I got hit with a 401 Unauthorized prompt. The website was locked down.

<img src="/assets/blog/cyberzap-locked.png" alt="Cyberzap Login Prompt" />
<div class="subtext">Yeah I'm not changing my browser language to English for this screenshot...</div>

I guess they saw my email address that greeted them. They probably received logs of someone "falling for it",
and saw someone was poking around their secret website, and knew who was behind it.
They completely panicked. They even shut down a completely unused domain called ``bytecannon.net`` with the exact same authorization message.

It's important to mention that the scary ``netcrashers.net`` site stayed online. But that one was _meant_ to be associated with them.

I did manage to archive the main-homepage of `cyberzap.fun` in time though: [https://archive.ph/IS0k6](https://archive.ph/IS0k6).
This blog post is quite "image heavy", so I am quite sorry about the bad resolution of some images, but it's just screenshots I took to send to friends.
I sadly wasn't able to archive high-quality stuff of everything.

## What is the actual goal here?

This brings up a really good question. What is the point of all this?

The banner on ``netcrashers.net`` mentions "Law enforcement combats cybercrime both overtly and covertly". We
essentially found both of those methods. Netcrashers is the overt one, and Cyberzap is the covert one.

When I looked at my attack order on Cyberzap, I noticed an ID in the URL that was given to me. My request was number 15.
That means there were only 14 other "attacks" ever ordered on that site. And honestly, **most of those were probably the
feds testing their own code**. Because honestly, who the fuck would still fall for this website? Despite all the "work"
they put in, how much money was blown on building this fake dashboard?

Catching people probably isn't the only goal. By running these honeypots, the police create suspicion and paranoia in the
community. If you want to buy a DDoS attack, you now have to wonder if the website is real or just a police honeypot
logging your IP. They want people to stop trusting these services entirely.

So yeah, those honeypots are real and out there, so the message clearly is: "you can't trust DDoS services".
It should obviously go without saying: you just shouldn't use booter services in the first place.

"Operation PowerOFF" also recently uploaded an AI-slop "propaganda" video[^ai-slop]:
<video width="640" height="360" controls muted>
    <source src="/assets/blog/sloppy-slop.mp4" type="video/mp4">
    Your browser does not support the video tag.
</video>
<div class="subtext">Highest grade slop provided directly by law enforcement.</div>

It showed them knocking on the door of a 16 year old kid who hit Minecraft servers offline. They made this kid look like
a final boss, and showed themselves as how incredibly tuff they are for raiding a teenager.  
Is it a real story? Probably not. I suppose it is meant to scare children, like ``netcrashers.net``. But it really just
feels more like feds jerking themselves off on how cool they are. 
[In a Reddit AMA](https://www.reddit.com/r/AMA/comments/1sso4dh/guess_whos_back_the_dutch_police_involved_in/) that 
they did just a week ago, they described this monstrosity as a "cool video" on their "branding page".

Does this video and the honeypot have any real impact? Let's be honest: probably not. It feels like they are just
redistributing wealth from the average taxpayer to AI video slop corporations.

We do know that Operation PowerOFF did this exact same thing in the past. The NCA
actually wrote an article[^nca-article] in March 2023 about how they infiltrated the cyber crime market
with disguised DDoS sites. 

We likely just stumbled across their new project. Checking the domain registration, you can see that it was created on
April 3, 2025. I also checked the internet archive. The site was captured in July 2025, and it was still empty back
then[^empty], so it is questionable when they actually launched it.

It is honestly just funny. They spend all this money on propaganda to scare children and complex honeypots that are
still super easy to detect. And the moment someone starts digging, they panic and shut the whole thing down.

Sorry glowies, you'll have to try again.

[^operation-poweroff]: [https://en.wikipedia.org/wiki/Operation_PowerOFF](https://en.wikipedia.org/wiki/Operation_PowerOFF) yes i am using wikipedia as a source, it's a better summary than news articles, do your own research if you want
[^seized-fyi]: [https://seized.fyi/operation-poweroff](https://seized.fyi/operation-poweroff) [https://seized.fyi/operation-poweroff-2](https://seized.fyi/operation-poweroff-2) [https://seized.fyi/operation-poweroff-3](https://seized.fyi/operation-poweroff-3) and more individual banners that can be found on this website
[^europol-arrests]: [https://www.europol.europa.eu/media-press/newsroom/news/europol-supported-global-operation-targets-over-75-000-users-engaged-in-ddos-attacks](https://www.europol.europa.eu/media-press/newsroom/news/europol-supported-global-operation-targets-over-75-000-users-engaged-in-ddos-attacks)
[^nca-article]: [https://archive.ph/x68v0](https://archive.ph/x68v0) Interestingly enough, this article is now a 404, which is why you get an archived link.
[^empty]: [https://web.archive.org/web/20250714195639/http://cyberzap.fun/](https://web.archive.org/web/20250714195639/http://cyberzap.fun/)
[^ai-slop]: [https://operation-poweroff.com/assets/video.mp4](https://operation-poweroff.com/assets/video.mp4)