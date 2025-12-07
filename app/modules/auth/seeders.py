from app.modules.auth.models import User
from app.modules.profile.models import UserProfile
from core.seeders.BaseSeeder import BaseSeeder


class AuthSeeder(BaseSeeder):

    priority = 1  # Higher priority

    def run(self):

        # Seeding users
        users = [
            User(
                email="user1@example.com",
                password="1234",
                is_email_verified=True,
                email_verification_token=None,
            ),
            User(
                email="user2@example.com",
                password="1234",
                is_email_verified=True,
                email_verification_token=None,
            ),
            User(
                email="user3@example.com",
                password="1234",
                is_email_verified=True,
                email_verification_token=None,
                twofa_key=(
                    "gAAAAABpMdv6Anu0b37433nNL_HofqZwdzCJsik1c-fX4RT-490kZUphRzWk_"
                    "f_0lt2GMwyMKkUQvaCeexE1PoRRxxhvvlIePamRsmv1TgjZACEd_0FBe0sG_6-Ka91AeHnJhWSXheV7"
                ),
            ),
        ]

        # Inserted users with their assigned IDs are returned by `self.seed`.
        seeded_users = self.seed(users)

        # Create profiles for each user inserted.
        user_profiles = []
        names = [("John", "Doe"), ("Jane", "Doe")]

        for user, name in zip(seeded_users, names):
            profile_data = {
                "user_id": user.id,
                "orcid": "",
                "affiliation": "Some University",
                "name": name[0],
                "surname": name[1],
            }
            user_profile = UserProfile(**profile_data)
            user_profiles.append(user_profile)

        # Seeding user profiles
        self.seed(user_profiles)
