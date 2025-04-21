from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tripdetails',
            name='facility',
        ),
        migrations.AddField(
            model_name='tripdetails',
            name='facility',
            field=models.ManyToManyField(blank=True, to='home.facility'),
        ),
    ]
