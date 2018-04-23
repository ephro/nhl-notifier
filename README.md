# nhl-notifier

This repository is an easy way to connect the NHL stats to webhooks in IFTTT.

Currently two triggers are supported, score, and power play.

After you setup your webhooks on IFTTT you need to make a file called private_key with the key for your webhooks.
The script will read the first line of that file to get your key.

Once the script is running, any time there is a new score or power play it will send an trigger to your IFTTT account
in the format of [team_abbr]_score or [team_abbr]_power_play. The [team_abbr] is a lowercase team abbreviation, such as
vgk for the Vegas Golden Knights.

To setup Webhooks in IFTTT, go to this page:

https://ifttt.com/maker_webhooks

Connect to webhooks and go to settings. You should see a URL that looks like this:

https://maker.ifttt.com/use/<REDACTED>

The part that is redacted is what you want to copy and add to a file called private_key in the same file as the notifier.py.

After that you want to go to your normal IFTTT account page. Make a new Applet and set the trigger to be 'Webhooks'

For the event name put in the event name as described above. Then connect the action to whatever action you want to have happen.
