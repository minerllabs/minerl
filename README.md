# Minecraft Play-and-Record

This branch of minerl allows you to play, record, and upload recordings.
Once the repo is cloned, run from the root:

```bash
./play.sh
```

Or, alternatively, this command should get you started rightaway!

```bash
git clone git@github.com:openai/minerl -b peterz/human_recorder --depth 1 && cd minerl && ./play.sh
```

The only python package this depends on is [boostedblob](https://github.com/hauntsaninja/boostedblob) for file upload, so it
will not mess up your environment.

Once in-game, start or continue a new survival game - your gameplay is recorded when you are in-game, and paused in menus.

