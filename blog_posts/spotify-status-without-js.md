Title: Fully automatic updating Spotify status... without JavaScript?
Summary: How I managed to keep my website JavaScript-free while still showing my current Spotify status in real-time.
Date: 2024-12-08
Image: /assets/blog/spotify-status.png
Hash: spotify
---------
## The challenge: A real-time status using CSS only

Typically, when you want real-time updates on a website, like displaying the song you're currently listening to on
Spotify, you use JavaScript. It's just what you use for fetching data and manipulating the page dynamically. 
You would never do some cursed CSS-only solution, right? How would you even fetch data without JavaScript?

Well, my website was built to be completely JavaScript-free, and I didn't want to "throw that away" for a single
feature. 
So my goal was: Building a **fully automatic and dynamically updating** Spotify status without 
writing a single line of client-side JavaScript?  
It turns out this _is_ possible. 
The trick involves server-side streaming and a rather silly, but effective, use of CSS.

## The solution: Streaming CSS updates

The core idea is surprisingly simple: instead of fetching a complete HTML file and closing the connection, the server
just never closed the connection; it keeps the connection to the browser open. 
This allows the server to continuously "append" new data to the page, after the browser already loaded it.

Instead of changing the page content with JavaScript, I just send new `<style>` tags. 
Every time my Spotify status changes, the server injects a new block of CSS that overwrites the previous styles. 
All the dynamic elements you see (the song title, artist, album art, and the progress bar) 
are controlled entirely by these streamed CSS rules.

My friend yui ([https://yui.dev/](https://yui.dev/)), whose website is genuinely amazing, was the one who suggested this
clever approach to me. Please check out their work!

Here’s a simplified example of what the server sends when a new song starts playing:
```html

<style>
    .song-title::before {
        content: "New Song Title";
    }
</style>
```

This new rule is added to the bottom of the document. Thanks to the "cascading" part of Cascading Style Sheets (CSS),
the last rule defined for an element wins. The new content simply overwrites the old one, and the song title on the page
changes instantly.

## The backend

So, how does the server know when to send an update? I use a simple Python with Flask. 
The server permanently checks the Spotify API for my latest status (song title, artist, playback position).

When it detects a change, it generates the new CSS and sends it down all open connections. 
In Flask, this is easy to do with a python generator that `yield`s the CSS updates as events happen.

A grossly oversimplified version of the code looks like this:

```python
while True:
    # This line waits for a new event (e.g., song change) to come in
    event = event_queue.get()
    if event is None:
        break
    # This sends the new CSS to the browser
    yield event
```

I can add any update I want to the `event_queue`, and it gets streamed to the browser in real-time.

## Keeping everything perfectly in sync

Now, a small problem with relying on CSS is that animations, like a progress bar, aren't always perfectly synced with
the actual status.
To solve this, my system updates the CSS in two ways:

1. **Immediate Updates:** If I pause, skip, or jump to a different timestamp in a song, the server detects this and
   sends a full CSS update **immediately**.
2. **Periodic Resync:** To correct any potential de-sync, the server also sends a complete, fresh set of CSS rules every
   five seconds, ensuring the progress bar and other details are always accurate.

Here's a look at it in action:

<video controls>
    <source src="/assets/blog/spotify-playing.webm" type="video/webm">
    <source src="/assets/blog/spotify-playing.mp4" type="video/mp4">
</video>

## Problems... (and solutions)
This approach isn't without its issues. The most obvious issue is that with a constantly open connection, the
browser's tab will show a "loading" spinner. 

I solved this with a little trickery. 
I load the widget in an iframe, the initial HTML page loads completely and then uses a `Refresh` header to redirect to
a second page after 5 seconds. This second page is the one that uses the "open" connection. Because the initial page
finished loading, the browser considers the site "loaded", even while the Spotify element continues to receive
background updates.

Another issue was adding a button to open the current song in Spotify. The solution: Overlay a new `<a>` element, every
time the song changes, with the correct link to open the song in Spotify. This *does* mean that if you 
have my website open for hours, you will end up with hundreds of `<a>` elements stacked on top of each other.

Also, if you keep the page open for a very long time, the CSS will grow indefinitely. 
This is less of a problem than expected, as the CSS is "just text" and rather small, and browsers are quite good at 
optimizing it. Unless you plan on keeping the connection open for weeks, this shouldn't be an issue.

## Update: Perfectly synced live lyrics!

I've since pushed this concept even further by adding live lyrics. By *totally* not breaking Spotify's ToS to fetch the
lyric data, I can get the timestamps for every line.

The server sends all the lyrics and their timings to the browser as a single, keyframed CSS animation when the song
first loads. This means the entire synchronization happens client-side within CSS, and the server only needs to send one
update per song change. The result is lyrics that are almost perfectly synced to what I'm hearing.

## Conclusion

This was an incredibly fun experiment, and I spent way too many hours on it. 
Anyone sane enough should absolutely just use JavaScript for something like this; it would have been infinitely easier.

But nevertheless, working on this was super fun, having to figure out 

If you're curious to see the beautiful mess of code that makes this all work, you can find it on my GitHub:
[https://github.com/lina-x64/lina.sh](https://github.com/lina-x64/lina.sh)



<div class="listening-wrapper" id="status">
    <iframe loading="lazy" class="listening-to" src="/listening_to?refresh=1" allowtransparency="true"></iframe>
</div>

<style>
.listening-to {
    border: none;
    background: none;
    width: 350px;
    height: 140px;
}
.listening-wrapper {
    margin-top: 20px;
    vertical-align: middle;
    display: flex;
    justify-content: center;
}
</style>