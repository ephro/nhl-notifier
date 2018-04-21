# nhl-notifier

This repository is an easy way to connect the NHL stats to webhooks in IFTTT.

Currently two triggers are supported, score, and power play.

After you setup your webhooks on IFTTT you need to make a file called private_key with the key for your webhooks.
The script will read the first line of that file to get your key.

Once the script is running, any time there is a new score or power play it will send an trigger to your IFTTT account
in the format of [team_abbr]_score or [team_abbr]_power_play. The [team_abbr] is a lowercase team abbreviation, such as
vgk for the Vegas Golden Knights.

