from locust import HttpUser, task, between
import random
import string


def random_url():
    slug = "".join(random.choices(string.ascii_lowercase, k=8))
    return f"https://example.com/{slug}"


class URLShortenerUser(HttpUser):
    # Real users don't hammer instantly — 0.1-0.3s think time
    # This gives realistic numbers without overwhelming local DB
    wait_time = between(0.1, 0.3)

    short_codes = []

    @task(1)
    def shorten(self):
        resp = self.client.post(
            "/shorten",
            json={"url": random_url()},
        )
        if resp.status_code == 200:
            code = resp.json().get("short_code")
            if code:
                URLShortenerUser.short_codes.append(code)

    @task(9)
    def redirect(self):
        """9x more reads than writes — realistic production ratio."""
        if not URLShortenerUser.short_codes:
            return
        code = random.choice(URLShortenerUser.short_codes)
        self.client.get(f"/{code}", allow_redirects=False)