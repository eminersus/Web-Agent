# Default Login Credentials

To make development easier, the Web Agent automatically creates a default user account when you first start the services.

## Credentials

- **Email:** `user@localhost`
- **Password:** `password`

## How It Works

When you run `docker-compose up`, an initialization script automatically:
1. Waits for MongoDB to be ready
2. Checks if the default user exists
3. Creates the user if it doesn't exist
4. Shows you the login credentials in the logs

## Access LibreChat

Simply open http://localhost:3080 in your browser and log in with the credentials above!

## Security Note

⚠️ **These are development credentials only!**

For production use:
1. Change the default password
2. Create proper user accounts
3. Enable email verification
4. Configure proper authentication

## Custom Users

You can still create additional users by:
1. Logging in with the default account
2. Using the LibreChat interface to manage users
3. Or manually adding users to MongoDB

## Session Duration

The session is configured to last a very long time (configurable in `docker-compose.yaml`) so you won't need to log in frequently during development.

