# makefun-gta6-forecast-01

[![make.fun · gta6-twitch-ccu-forecast-01](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/shibadogcap-ops/makefun-gta6-forecast-01/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/shibadogcap-ops/makefun-gta6-forecast-01/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)

A deterministic forecaster for Grand Theft Auto VI's launch-day Twitch viewership. Given the category's viewer count at the end of release day's first hour (UTC), it projects hours 2–24 as five quantiles per hour: it anchors on the first-hour count and applies the median launch-day shape of past comparable game launches — each comparable's hourly counts taken as log-ratios to its own first hour — with a spread from the cross-launch dispersion, excluding non-launch data, early-access-contaminated launches, weak analogues and launches whose unlock clearly fell mid-day UTC.

## Run it

```sh
mkdir -p out && MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

`main.py` reads every `*.in` case file in the input directory and writes one `<id>.out` forecast per case to the output directory. Python 3.13, standard library only, no network.
