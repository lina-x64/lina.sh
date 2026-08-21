Title: I accidentally logged hundreds of thousands of phone calls to military bases
Summary: How an expired nameserver let me take over e164.arpa zones for multiple territories, and why I probably should have checked my logs sooner.
Date: 2026-07-30
Image: /assets/blog/e164/cover.png
Hash: e164
VGWort: 2a0774cfd693439a98cb0dc98424be9b
---------

DNS hijacking is silly. I already took over different `.gov` and `.edu` domains in the past, but I just immediately
reported that and moved on.  
This one is a little different though, it's about how I took over phone-network infrastructure domains (`e164.arpa`) of
entire territories, and accidentally logged hundreds of thousands of phone calls to military bases. But let's start at
the beginning.

## What is e164.arpa anyway?

ENUM (`e164.arpa`) was an idea from the early 2000s[^rfc]: take a phone number, reverse the digits, put dots between
them, and add `.e164.arpa` at the end, so `+49 30 123456` becomes something like `6.5.4.3.2.1.0.3.9.4.e164.arpa`. You
can see that every German number will end up under `.9.4.e164.arpa`, which is the zone for all +49 numbers, and that
zone is controlled by DENIC (the same organization that runs `.de`). This means the DENIC decides which carrier or person
gets which number ranges under that zone, just like they hand out `.de` domains (which makes it decentralized, making every
country decide on delegation themselves).

The idea was that carriers could then look these domains up and get back a record saying "hey, this number can be
reached over SIP/VoIP under this address", skipping the expensive phone network and re-routing calls over the cheap 
internet instead.

It never really took off though, and even back in its early days it saw barely any use. Over the years it just
deteriorated further, and today it's basically completely dead. I do actually own
[5.8.7.1.7.1.3.2.6.1.9.4.e164.arpa](https://5.8.7.1.7.1.3.2.6.1.9.4.e164.arpa) and
point it at this website, although technically I'm not supposed to do that (you can figure out my secondary number from
that!). Germany is actually one of the last countries that still technically allows registering an `e164.arpa` domain,
although I was the first person since 2019 to register one[^denic-jahresbericht].

The RFC says you should only set NAPTR records on these domains, which are the records that tell carriers where to route a call.
It states that you *absolutely shouldn't* be using .arpa domains as normal "domains" and host stuff like websites on them,
they are meant to be "infrastructure" domains (you might know `in-addr.arpa` for reverse DNS lookups for example).
But there's nobody who can actually stop you from doing it, it's still just DNS at the end of the day, 
and nothing prevents you from slapping an A record on there and hosting a website. Some people actually really dislike that,
and try to get Certificate Authorities to no longer issue certificates for `.arpa` domains[^no-fun].


## Hijacking a territory's phone network

I was scanning `e164.arpa` to see if any of the delegated zones were hijackable, mostly out of curiosity about how
neglected this whole system really was.

I found three country-code zones, `0.9.2.e164.arpa`, `6.4.2.e164.arpa`, and `7.4.2.e164.arpa`, all delegated to the same
two nameservers: `ns6.icb.co.uk` and `ns.enum.org.uk`.

![](/assets/blog/e164/dig-three-zones.png)

Quick explainer for anyone who isn't a DNS person: when a domain is delegated to a nameserver, it basically means "for
any question about this domain, go ask this server, it has the answers", and if I control the nameserver a domain points
to, I control every DNS response for that domain.

`icb.co.uk` still exists as a domain, but the specific `ns6.icb.co.uk` subdomain no longer resolves to anything, meaning
any request falls back to the second listed nameserver instead: `ns.enum.org.uk`.

And that domain had expired, so I bought it for just 5€, and just like that I controlled the DNS for `0.9.2.e164.arpa`,
`6.4.2.e164.arpa`, and `7.4.2.e164.arpa`. Reversed, those are phone codes +290, +246, and +247: Saint Helena, the
British Indian Ocean Territory (Diego Garcia), and Ascension Island respectively (funnily enough, those
territories also have the popular ccTLDs `.sh`, `.io`, and `.ac`).

To be clear about what this meant: when a carrier does an ENUM lookup for one of these numbers, they're essentially
asking "where do I route this call?", and I could answer with whatever I wanted. I could point it at my own SIP server,
accept the incoming call, and then place an outgoing call to the real destination with a spoofed number.
The person being called would see the original number ringing, and after picking up would speak to the person on the
other end as if everything was normal, but I'd be sitting silently in the middle of the entire conversation.
I would theoretically be able to do this for every single request that I got if I could re-route a number, *if*
anyone was still actually using this system.

I reported it right away to everyone I could think of, through multiple channels into the British government, and got
nothing back. My best guess is that someone at the Internet Computer Bureau (who seemingly managed them in the past)
set these nameservers up over a decade ago. Then `e164.arpa` slowly died out, and whoever set it up either moved on or
just forgot about it, leaving nobody to renew a domain nobody remembered they depended on.

## Checking if anyone actually uses this

[Q Misell](https://magicalcodewit.ch/) (a researcher of the Max-Planck-Institute for Informatics) had heard about this and reported it to RIPE (who manages `e164.arpa`) on my behalf, but RIPE also declined to do anything, because
`e164.arpa` delegations are governed by an ITU-T committee at the UN level. And RIPE wasn't willing to go against a 
decision made by a UN committee, which would probably be a bureaucratic nightmare.

Q also asked if I had any data on how much traffic these zones actually got, which I didn't know.
And because I was very curious about that myself, I set up logging on `0.9.2.e164.arpa` (Saint Helena) to find out, and waited a full day.

Not a single query came in. So after trying my best to get anyone to care and getting nowhere, I just kept the domains,
since nobody seemed to be relying on them anyway.

I hosted my [personal site](https://web.archive.org/web/20250925203323/https://6.4.2.e164.arpa/) on it,
spun up [a Fediverse instance](https://archive.ph/o2dbx), a Matrix
homeserver, and handed out subdomains to friends, because why not, it's a dead system. It's not like it's gonna
hurt anyone, and no one cares. So it's time to be whimsical and have fun with it.

![](/assets/blog/e164/fedi-instance.png)

## Six months later...

Just out of curiosity, I checked the logs again on all three zones,
since I enabled logging running on the other two as well when I set everything up.

Hundreds of thousands of ENUM queries, all logged[^query-breakdown]. Since the domain name is literally just the phone number reversed,
you can simply flip it back around to get the real number, so I had full phone numbers, timestamps, and the source IP
addresses of the DNS resolvers making the requests.

![](/assets/blog/e164/log_screenshot.png)
<div class="subtext">Hundreds of thousands of lines in logs looking just like this (phone numbers are randomized)</div>

Almost none of it was for Saint Helena (`0.9.2.e164.arpa`), it was basically almost entirely `6.4.2.e164.arpa` and
`7.4.2.e164.arpa`: Diego Garcia and Ascension Island. The source IPs were mostly American. That would at least explain
why I originally didn't see any traffic, as I was only logging Saint Helena.

So I had accidentally logged hundreds of thousands of phone numbers and timestamps for calls going to military bases.
And as described earlier, a malicious actor could have simply MITM'd every single one of them. I mean I am no expert,
but I would assume that in hundreds of thousands of calls between soldiers and their families, sensitive information
would always slip here and there eventually. A nation state with an interest in what's happening on those bases would
have absolutely
loved sitting on this for months without anyone noticing.
It's not hard to imagine who might want that kind of intel on Diego Garcia specifically, but I'll get to that later.

My DNS server replied with an `NXDOMAIN` for all queries, so they were just being routed over the normal phone network.
But after realizing this I shut the DNS server down and deleted all the log files.

## Suddenly, people care

I reported it for a second time to the UK's National Cyber Security Centre (NCSC), and this time, mentioning that
military
bases were involved, they actually cared a *lot*.

They couldn't figure out who had originally set up the abandoned delegation, and actually fixing it properly ran into
the same ITU-committee issues from earlier, so for a while nothing changed. Even a year later I still
owned the domain and could've in theory still intercept the traffic, though I had wiped the zone completely so
`ns.enum.org.uk` just returned NXDOMAIN for everything at that point.

Then on March 20th, 2026, Iran fired ballistic missiles at Diego Garcia[^strike].
It maybe would've been interesting to see if there was a spike in calls from worried family members that day, but by
then I was long done logging anything. But this shows that a state actor could have been interested in this information.

Shortly after, the NCSC let me transfer ownership of the domain directly to them, *right after* I had to renew it for
another 5€ (because otherwise, it would be up for grabs again, and anyone could do the aforementioned stuff).

So the NCSC now controls `ns.enum.org.uk`, but the nameservers for those three zones still point there.
So in the end, I was down 10€ in domain fees, there was sadly no bug bounty (I thankfully didn't get my door kicked in
at least).
And on top of that, it's a funny story :P

[^rfc]: [RFC 3761 - The E.164 to URI DDDS Application (ENUM)](https://www.rfc-editor.org/rfc/rfc3761)
[^denic-jahresbericht]: The DENIC publishes [annual reports](https://www.denic.de/produkte/enum-domains/) on their ENUM registrations, the last time anyone 
registered one was in [2019](https://www.denic.de/fileadmin/Downloads/ENUM/ENUM-Jahresbericht__2019.pdf), up until when I registered three in [2025](https://www.denic.de/fileadmin/Downloads/ENUM/ENUM-Jahresbericht-2025.pdf).
[^no-fun]: <img src="/assets/blog/e164/no-fun.png" style="display: inline-block; height: 6em; width: auto; vertical-align: top; margin: 0 0.25em;">
[^query-breakdown]: At this point, a friend of mine ([86dd](https://86dd.eu/)) had set up a secondary nameserver for the zones, without any logging.
I had logged 100,170 queries to `6.4.2.e164.arpa` and 99,902 queries to `7.4.2.e164.arpa`, and 9,133 queries to `0.9.2.e164.arpa`. 
This should be approximately half of the total queries that were sent to us; Meaning it were ~400.000 requests in total
[^strike]: [Wikipedia: 2026 Iranian strike on Diego Garcia](https://en.wikipedia.org/wiki/2026_Iranian_strike_on_Diego_Garcia)
