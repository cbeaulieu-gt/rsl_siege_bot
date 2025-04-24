import sys
import time


class DiscordMemberFetcher:
    def __init__(self, api_client, guild_id):
        self.api_client = api_client
        self.guild_id = guild_id

    def fetch_all_members(self):
        """
        Fetches all members from the guild using pagination.

        :return: List of all members.
        """
        members = []
        after = None
        limit = 1000
        progress_chars = ['|', '/', '-', '\\']
        progress_index = 0
        start_time = time.time()

        while True:
            # Update the progress bar
            elapsed_time = time.time() - start_time
            progress_index = int((elapsed_time % 5) / (5 / len(progress_chars)))
            sys.stdout.write(f"\rFetching data from server... {progress_chars[progress_index]}")
            sys.stdout.flush()

            # Fetch members
            data = self.api_client.get_guild_members(self.guild_id, limit, after)
            if not data:
                break

            members.extend(data)
            after = data[-1]["user"]["id"]

            # Rate limit buffer (optional, Discord may send a Retry-After header)
            time.sleep(1)

        # Clear the progress bar and print the final result
        sys.stdout.write("\rFetching data from server... Done!\n")
        sys.stdout.flush()

        return members


class Member:
    def __init__(self, username, nickname, roles):
        self.Username = username
        self.Nickname = nickname
        self.Roles = roles

    @staticmethod
    def from_api(api_member):
        """
        Extracts member information from the API response and returns a new Member object.

        :param api_member: Dictionary containing member data from the API.
        :return: A new Member object.
        """
        username = f"{api_member['user']['username']}#{api_member['user']['discriminator']}"
        nickname = api_member.get("nick", "No nickname")
        roles = api_member.get("roles", [])
        return Member(username, nickname, roles)


