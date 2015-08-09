# AskScience-Flair
script for handling flair on reddit


#Features

grabs submissions from the modqueue of restricted subreddits and adds them to a SQL database.

After 5 minutes comments on posts that do not have link flair.

If a user replies to the comment with a valid flair choice that flair is added to the post.

After one hour removes posts that are not flaired.

After one day removes posts that have not been cleared.

Does not act on posts that have either been approved or removed by another moderator.