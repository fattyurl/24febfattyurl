from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    protocol = "https"
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        return [
            "home",
            "qr_generator",
            "bitly_alternative",
            "promise_page",
            "about_page",
            "privacy_page",
            "terms_page",
            "contact_page",
        ]

    def location(self, item):
        return reverse(item)
