from django.core.management.base import BaseCommand

from recipes.services.recipe_service import fetch_and_save_recipes


class Command(BaseCommand):
    help = "Fetch recipes from TheMealDB and save/update them in the local database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--q",
            default="chicken",
            help="Search query for TheMealDB (default: chicken).",
        )

    def handle(self, *args, **options):
        query = (options.get("q") or "chicken").strip() or "chicken"
        saved = fetch_and_save_recipes(query=query)
        self.stdout.write(
            self.style.SUCCESS(
                f'Synchronized recipes for query="{query}". Saved/updated: {saved}'
            )
        )
