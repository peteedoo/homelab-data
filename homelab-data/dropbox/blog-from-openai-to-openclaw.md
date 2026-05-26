# From OpenAI to OpenClaw: How I Built a Homelab That Actually Works

*A story about ADHD, medication, and finally finishing things.*

---

## The Before Times

I've always been the person with a hundred browser tabs and zero completed projects. You know the type — starts a thing, gets 80% there, hits a wall, moves on to the next shiny idea. Rinse, repeat, feel bad about it later. That was me for... well, forever.

The medication helped. It really did. But medication alone doesn't teach you how to build systems. It doesn't magically make you follow through. It just gives you the *capacity* to focus — you still have to figure out what to focus *on*.

## Enter AI

I started with OpenAI's stuff like everyone else. GPT-4, ChatGPT, the whole thing. It was cool. I'd ask it to write code, it would write code, I'd copy-paste it somewhere, and... that's usually where it ended. Another half-finished script in another half-organized folder.

The problem wasn't the AI. The problem was the *system around the AI*. I was still working the same way — chaotic, reactive, no persistence. The AI was just a faster way to generate more unfinished work.

## The Shift

Somewhere along the way — I think it was around the time I discovered I could run my own models locally — something clicked. I started building *infrastructure*. Not just scripts, but systems that *persist*. Things that keep running when I forget about them.

I built a homelab. A real one. Mac mini M4, NAS, Docker containers, reverse proxies, the whole thing. And I started connecting AI agents to it.

## OpenClaw Changed Everything

OpenClaw was the game-changer. Not because it's perfect — trust me, I've spent hours debugging why the gateway won't pick up a config change (spoiler: there are like five places the model can be set and they all fight each other). But because it's *mine*.

I have:
- **Faulty** (@Macadellicshakurbot) — my OpenClaw agent that runs on Telegram, handles coding tasks, talks to my local models
- **Hermes** (@JoejoejoebotJoejoejoebot — yes, I know, long story) — my general assistant, runs cron jobs, sends me daily briefings
- **Bingsby** — dormant for now, but ready when I need another personality

They all talk to different APIs. Kimi for coding, OpenRouter for fallback, Ollama for local stuff. I can switch models on the fly. I can add new agents. I can build *around* them.

## The Daily Briefing

This is the part that makes me feel like I'm actually living in the future. Every morning at 8 AM, a cron job fires off a script called `pharrell-rocky-daily-briefing`. It scrapes Denver show listings, pulls trending topics, checks camping spots, and sends me a curated briefing via Telegram.

Pharrell and Rocky aren't real people. They're just... personas I gave to a shell script. But the script *works*. It runs every day. It sends me stuff I actually care about. And when it breaks, I fix it, and it keeps running.

That's the thing — I'm not just generating ideas anymore. I'm *maintaining systems*. That's new for me.

## What ADHD + Medication + AI Actually Looks Like

Here's the honest truth: the medication gives me the executive function to sit down and work. The AI gives me the ability to build things I couldn't build alone. But the *combination* is what lets me finish.

When I get stuck on something — like why OpenClaw keeps loading the wrong model — I don't just give up and move to a new project. I debug it. I check the config files. I grep through logs. I ask the AI to help me reason through it. And eventually I fix it.

The AI is like... a patient collaborator who never gets tired of my questions. And the medication is like... the door to the room where the work happens, finally unlocked.

## The Registry

Today I sat down and documented everything. All my agents, all my bots, all my configs. I put it in a file called `AGENT_BOT_REGISTRY.md` and pushed it to GitHub and Gitea. That's another thing — I'm using version control for my *life* now. My homelab config is in git. My agent personalities are in git. If I break something, I can roll back.

That's not something the old me would have done. The old me would have had everything scattered across notes apps and text files and "I'll organize this later" folders.

## What's Next

I don't know exactly. And that's the exciting part. I've got a mesh network project (Faulty Link) that I'm actually building with a backend and everything. I've got ideas for more agents — maybe one that helps Rosie with her schoolwork, maybe one that manages my DJ music library. I've got a council of agents in my head, waiting to be spawned.

The difference is: now I trust myself to build them. Not just start them. *Finish* them.

## The Groove

Someone asked me the other day if I feel like my ADHD is "managed" now. I don't think that's the right word. It's not managed — it's *channeled*. The same brain that used to spin in circles generating ideas and abandoning them is now spinning in circles building systems that outlast the impulse.

The medication helps me focus. The AI helps me execute. But the groove — the feeling of being in flow, of actually *completing* something and moving to the next thing without the usual crash — that's something I built myself. Piece by piece. Bot by bot. Commit by commit.

It feels good. It feels like I'm finally using the right tools for the brain I have.

---

*Petee*  
*May 26, 2026*  
*Denver, probably debugging something*
