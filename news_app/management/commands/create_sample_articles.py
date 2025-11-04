"""Create realistic sample articles with proper images."""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify

from news_app.models import Article, Publisher  # pylint: disable=import-error


class Command(BaseCommand):
    """Django management command to create sample articles with images."""

    help = 'Create realistic sample articles with proper images'

    def handle(self, *args, **options):
        """Handle command execution."""
        user_model = get_user_model()

        # Get or create journalist user
        journalist, created = user_model.objects.get_or_create(
            username='journalist',
            defaults={
                'email': 'journalist@himalayantimes.com',
                'first_name': 'News',
                'last_name': 'Reporter',
                'role': 'journalist'
            }
        )

        if created:
            journalist.set_password('journalist123')
            journalist.save()

        # Get or create publisher
        publisher, created = Publisher.objects.get_or_create(
            name='The Himalayan Times',
            defaults={
                'description': 'Leading news organization in Nepal',
                'website': 'https://thehimalayantimes.com'
            }
        )

        articles = self.get_sample_articles()
        created_count = 0

        for article_data in articles:
            # Create unique slug
            base_slug = slugify(article_data['title'])
            slug = base_slug
            counter = 1
            while Article.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            # Check if article exists
            title = article_data['title']
            if not Article.objects.filter(title=title).exists():
                article = Article.objects.create(
                    title=title,
                    slug=slug,
                    author=journalist,
                    publisher=publisher,
                    summary=article_data['summary'],
                    content=article_data['content'],
                    source_image_url=article_data['image'],
                    is_approved=True,
                    status='published'
                )
                created_count += 1
                self.stdout.write(f"Created: {article.title}")

        msg = f'Created {created_count} sample articles with images.'
        self.stdout.write(msg)

    def get_sample_articles(self):
        """Return list of sample article data with source images."""
        # Mix of newspaper source URLs and fallback Unsplash images
        unsplash_base = 'https://images.unsplash.com/'
        return [
            {
                'title': 'Himalayan Times: Tourism Recovery Shows Growth',
                'summary': 'Tourist arrivals increased significantly.',
                'content': 'Nepal tourism shows strong recovery.',
                'image': ('https://thehimalayantimes.com/uploads/'
                          'images/2024/tourism-nepal.jpg')
            },
            {
                'title': 'Kathmandu Post: Hydroelectric Project Complete',
                'summary': 'Energy project achieves full capacity.',
                'content': 'Major hydroelectric project operational.',
                'image': ('https://kathmandupost.com/assets/'
                          'news-images/hydro-power.jpg')
            },
            {
                'title': 'Digital Banking Transforms Rural Areas',
                'summary': 'Mobile banking reaches remote villages.',
                'content': 'Banking services now available everywhere.',
                'image': unsplash_base + 'photo-1563013544-824ae1b704d3?w=800'
            },
            {
                'title': 'Climate Adaptation in Mountains',
                'summary': 'Communities develop new solutions.',
                'content': 'Local adaptation strategies effective.',
                'image': (unsplash_base +
                          'photo-1506905925346-21bda4d32df4?w=800')
            },
            {
                'title': 'Cultural Heritage Preservation',
                'summary': 'UNESCO launches restoration program.',
                'content': 'Heritage sites receive conservation support.',
                'image': unsplash_base + 'photo-1544735716-392fe2489ffa?w=800'
            }
        ]
