from django.core.management.base import BaseCommand
from recipe.utils import load_recipes_from_csv


class Command(BaseCommand):
    help = 'Import recipes from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='CSV 파일 경로')

    def handle(self, *args, **options):
        file_path = options['csv_file']
        load_recipes_from_csv(file_path)
        self.stdout.write(self.style.SUCCESS('CSV 파일에서 레시피를 성공적으로 불러왔습니다.'))
