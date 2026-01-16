from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="DROP INDEX IF EXISTS api_hnstorysummary_story_id_bio_hash_cb85b518_uniq;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RemoveField(
            model_name="hnstorysummary",
            name="bio_hash",
        ),
        migrations.AlterField(
            model_name="hnoverviewarticle",
            name="batch",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="overviews", to="api.hnbatch"),
        ),
        migrations.AlterUniqueTogether(
            name="hnoverviewarticle",
            unique_together={("batch", "bio_hash")},
        ),
    ]
