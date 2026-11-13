<div align="center">

<h1>ClipForge</h1>

<p><strong>Paste a link. Pick your favourites. Get Shorts that look edited.</strong></p>

<p>
  ClipForge is a skill for Claude. You give it a YouTube link or a video file.<br />
  It finds the best moments, shows you a scored shortlist, and turns the ones<br />
  you choose into finished vertical clips for YouTube Shorts, Instagram Reels<br />
  and TikTok.
</p>

<p>
  The clips come out edited, not just cut: the picture fills the screen, the<br />
  colour is graded, the camera punches in on the big moments, and the headline<br />
  and captions are animated.
</p>

<p>Created by <a href="https://www.instagram.com/samknows.ai">samknows.ai</a></p>

<p>
  <a href="https://www.instagram.com/samknows.ai/">
    <img src="https://raw.githubusercontent.com/lowdevco/Video-editing-effects/main/assets/samknowsai.jpeg" width="380" alt="samknows.ai" />
  </a>
</p>

<hr />

<h2>What you type</h2>

<table align="center">
  <thead>
    <tr>
      <th align="center">Command</th>
      <th align="center">Best for</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="center"><code>/clip-gameplay</code></td>
      <td align="center">Game recordings and streams</td>
    </tr>
    <tr>
      <td align="center"><code>/clip-podcast</code></td>
      <td align="center">Podcasts, interviews, talking to camera</td>
    </tr>
    <tr>
      <td align="center"><code>/clip-sports</code></td>
      <td align="center">Matches and broadcasts</td>
    </tr>
    <tr>
      <td align="center"><code>/clip-tutorial</code></td>
      <td align="center">How-to videos, lessons, screen recordings</td>
    </tr>
    <tr>
      <td align="center"><code>/clip-video</code></td>
      <td align="center">Everything else: vlogs, reviews, events</td>
    </tr>
    <tr>
      <td align="center"><code>/clip-edit</code></td>
      <td align="center">A clip you have already cut</td>
    </tr>
  </tbody>
</table>

<p>Add what you want after the command:</p>

<pre><code>/clip-gameplay &lt;link&gt; top 3, neon captions, watermark @myname</code></pre>

<p><em>No command? Just ask for shorts. ClipForge works out what kind of video it is.</em></p>

<hr />

<h2>What happens next</h2>

<table align="center">
  <thead>
    <tr>
      <th align="center">Step</th>
      <th align="center">What ClipForge does</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="center"><strong>1</strong></td>
      <td align="center">Gets the video</td>
    </tr>
    <tr>
      <td align="center"><strong>2</strong></td>
      <td align="center">Finds 8 to 12 moments and scores each one out of 100</td>
    </tr>
    <tr>
      <td align="center"><strong>3</strong></td>
      <td align="center">Shows you the list and waits. Nothing is rendered until you choose</td>
    </tr>
    <tr>
      <td align="center"><strong>4</strong></td>
      <td align="center">Edits and renders your picks</td>
    </tr>
    <tr>
      <td align="center"><strong>5</strong></td>
      <td align="center">Writes a title, caption and hashtags for each clip</td>
    </tr>
  </tbody>
</table>

<hr />

<h2>Install</h2>

<h3>Claude Code</h3>

<p>Paste this as a message in Claude Code:</p>

<pre><code>Install the ClipForge skill from https://github.com/lowdevco/Clip-Forge</code></pre>

<p>
  Claude downloads the repository and runs the installer, asking before it<br />
  runs commands. Then start a new session.
</p>

<details>
  <summary>Or do it by hand</summary>
  <br />
  <pre><code>git clone https://github.com/lowdevco/Clip-Forge</code></pre>
  <pre><code>python Clip-Forge/tools/build.py --install</code></pre>
</details>

<h3>Claude chat (claude.ai and the desktop app)</h3>

<table align="center">
  <thead>
    <tr>
      <th align="center">Step</th>
      <th align="center">What to do</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="center"><strong>1</strong></td>
      <td align="center">Download <code>clip-forge.zip</code> from the <a href="https://github.com/lowdevco/Clip-Forge/releases/latest">latest release</a></td>
    </tr>
    <tr>
      <td align="center"><strong>2</strong></td>
      <td align="center">In Claude, open <strong>Settings</strong>, find <strong>Skills</strong>, and upload the zip</td>
    </tr>
    <tr>
      <td align="center"><strong>3</strong></td>
      <td align="center">On the same page, make sure code execution and file creation is switched on</td>
    </tr>
  </tbody>
</table>

<hr />

<h2>How to use it</h2>

<h3>In Claude Code</h3>

<p>Claude Code downloads the video for you, so the link is all it needs.</p>

<table align="center">
  <thead>
    <tr>
      <th align="center">Step</th>
      <th align="center">What to do</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="center"><strong>1</strong></td>
      <td align="center">Type a command with your YouTube link, for example <code>/clip-podcast https://youtu.be/...</code></td>
    </tr>
    <tr>
      <td align="center"><strong>2</strong></td>
      <td align="center">Wait for the scored list, then answer with your picks, for example <code>top 3</code></td>
    </tr>
    <tr>
      <td align="center"><strong>3</strong></td>
      <td align="center">Find the finished clips in the <code>shorts</code> folder Claude tells you about</td>
    </tr>
  </tbody>
</table>

<h3>In Claude chat</h3>

<p>Claude chat cannot download from YouTube, so you give it the video file.</p>

<table align="center">
  <thead>
    <tr>
      <th align="center">Step</th>
      <th align="center">What to do</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="center"><strong>1</strong></td>
      <td align="center">Open <a href="https://vidssave.com">vidssave.com</a>, paste the YouTube link, and download the video as MP4. 720p is enough</td>
    </tr>
    <tr>
      <td align="center"><strong>2</strong></td>
      <td align="center">Attach the file to a new chat (up to 500 MB) and type a command, for example <code>/clip-podcast</code></td>
    </tr>
    <tr>
      <td align="center"><strong>3</strong></td>
      <td align="center">Wait for the scored list, then answer with your picks, for example <code>top 3</code></td>
    </tr>
    <tr>
      <td align="center"><strong>4</strong></td>
      <td align="center">Download the finished clips Claude sends back</td>
    </tr>
  </tbody>
</table>

<hr />

<h2>Edit styles</h2>

<p>Say the name of a style to use it. Each command has a sensible default.</p>

<table align="center">
  <thead>
    <tr>
      <th align="center">Style</th>
      <th align="center">Good for</th>
      <th align="center">The look</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="center"><code>hype</code></td>
      <td align="center">Gameplay, sports</td>
      <td align="center">Vivid colour, zoom hits with shake and flash, a bass thump on big moments, bold all-caps headline, progress bar</td>
    </tr>
    <tr>
      <td align="center"><code>premium</code></td>
      <td align="center">Most videos (the default)</td>
      <td align="center">Punchy colour, a slow push-in, zoom hits with a soft thump</td>
    </tr>
    <tr>
      <td align="center"><code>story</code></td>
      <td align="center">Podcasts, talking to camera</td>
      <td align="center">Soft colour, zoom cuts between sentences, animated captions</td>
    </tr>
    <tr>
      <td align="center"><code>clean</code></td>
      <td align="center">Business, tutorials</td>
      <td align="center">Soft colour and animated text, nothing else</td>
    </tr>
    <tr>
      <td align="center"><code>raw</code></td>
      <td align="center">When you want it untouched</td>
      <td align="center">A plain cut with a simple headline</td>
    </tr>
  </tbody>
</table>

<hr />

<h2>What the editor can do</h2>

<table align="center">
  <thead>
    <tr>
      <th align="center">Feature</th>
      <th align="center">Details</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="center"><strong>Framing</strong></td>
      <td align="center">Full screen, follow the speaker, two speakers stacked, facecam on top, or blurred background</td>
    </tr>
    <tr>
      <td align="center"><strong>Speaker tracking</strong></td>
      <td align="center">Spots camera cuts, finds the faces in each shot, and keeps the person talking in frame</td>
    </tr>
    <tr>
      <td align="center"><strong>Big moments</strong></td>
      <td align="center">Zoom hit, shake, flash or slow motion, plus a pop-up word such as "GOAL" or "CLUTCH"</td>
    </tr>
    <tr>
      <td align="center"><strong>Headline</strong></td>
      <td align="center">Animated, with your key words in an accent colour</td>
    </tr>
    <tr>
      <td align="center"><strong>Captions</strong></td>
      <td align="center">Word by word, in four looks: <code>bold</code>, <code>clean</code>, <code>neon</code>, <code>fire</code>. English and Malayalam</td>
    </tr>
    <tr>
      <td align="center"><strong>Sound</strong></td>
      <td align="center">Volume evened out, with thump, whoosh and pop effects made by the skill itself</td>
    </tr>
    <tr>
      <td align="center"><strong>Finishing touches</strong></td>
      <td align="center">Outro tag, channel watermark, progress bar, silences trimmed</td>
    </tr>
    <tr>
      <td align="center"><strong>Safe area</strong></td>
      <td align="center">Text stays clear of the app buttons on Shorts, Reels and TikTok</td>
    </tr>
  </tbody>
</table>

<hr />

<h2>What Claude Code needs on your computer</h2>

<p>
  In Claude Code the tools run on your own machine. Claude chat runs them in<br />
  its own workspace, so this section does not apply there.
</p>

<table align="center">
  <thead>
    <tr>
      <th align="center">Needed</th>
      <th align="center">How to get it</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="center"><strong>Python 3.9 or newer</strong></td>
      <td align="center"><a href="https://www.python.org/downloads/">python.org</a></td>
    </tr>
    <tr>
      <td align="center"><strong>ffmpeg, full build</strong></td>
      <td align="center">Windows: <code>winget install Gyan.FFmpeg</code></td>
    </tr>
    <tr>
      <td align="center"><strong>Python packages</strong></td>
      <td align="center"><code>pip install opencv-python numpy yt-dlp faster-whisper</code></td>
    </tr>
    <tr>
      <td align="center"><strong>Visual C++ runtime (Windows only)</strong></td>
      <td align="center">Needed for turning speech into text</td>
    </tr>
  </tbody>
</table>

<p><em>Not sure what you have? Claude checks on first use and tells you what to install. You can also run <code>python scripts/check_setup.py</code> yourself.</em></p>

<hr />

<h2>What is in this repository</h2>

<table align="center">
  <thead>
    <tr>
      <th align="center">Path</th>
      <th align="center">What it is</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="center"><code>SKILL.md</code></td>
      <td align="center">The instructions Claude follows</td>
    </tr>
    <tr>
      <td align="center"><code>references/</code></td>
      <td align="center">A guide for each kind of video, plus a guide to editing</td>
    </tr>
    <tr>
      <td align="center"><code>commands/</code></td>
      <td align="center">The name and description of each command</td>
    </tr>
    <tr>
      <td align="center"><code>scripts/</code></td>
      <td align="center">The tools that download, transcribe, analyse, track and render</td>
    </tr>
    <tr>
      <td align="center"><code>assets/</code></td>
      <td align="center">Fonts, face-detection models and a Windows download helper</td>
    </tr>
    <tr>
      <td align="center"><code>tools/build.py</code></td>
      <td align="center">Builds the zip files and installs the skill</td>
    </tr>
    <tr>
      <td align="center"><code>tools/selftest.py</code></td>
      <td align="center">Checks the whole skill without rendering any video</td>
    </tr>
  </tbody>
</table>

<hr />

<h2>Good to know</h2>

<p>Speaker tracking is an estimate based on mouth movement. It can pick the wrong person, so look at the preview.</p>

<p>For kill feeds and scoreboards, ClipForge detects that something changed. Claude then reads the frame to see what.</p>

<p>The edits follow what editors usually do. They make a clip look finished. Nobody can promise views.</p>

<hr />

<h2>Credits and licence</h2>

<p>Created by <a href="https://www.instagram.com/samknows.ai">samknows.ai</a></p>

<p>Released under the <a href="LICENSE">MIT License</a>, copyright &copy; 2026 lowdevco.</p>

<p>
  <small>
    Some bundled files keep their own licences: the Poppins, Anton and Noto Sans<br />
    Malayalam fonts (SIL Open Font License, texts in <code>assets/fonts/</code>), the YuNet<br />
    face-detection models from OpenCV Zoo (MIT), and OpenCV's Haar cascade (its<br />
    licence is stated inside the file).
  </small>
</p>

</div>
