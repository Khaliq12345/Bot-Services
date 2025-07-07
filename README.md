Bot logic

Services
- Schedule System
- Comment and Login Bot
- Splitting Services
- AI message service

Steps - 
1. Schedule Bot starts the flow (7am utc starts the bot with creator1 account)
2. user1 account will go through 100 users
3. For each user the bot will use the account of creator1 to leave comment on the latest post of the user
4. Blacklist that user for creator1 for life and other creators just 1 month. Make sure to update assigned to None, last_interation_date and past_creators
5. Wait for like a random minute between 5 to 10 minutes before proceeding with the next user
