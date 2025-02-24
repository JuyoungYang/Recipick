from django.db import models


class Recipe(models.Model):
    CKG_NM = models.CharField(
        max_length=255,
        verbose_name="요리명",
        null=True,
    )
    CKG_MTRL_CN = models.TextField(
        verbose_name="재료 목록",
        null=True,
    )
    CKG_INBUN_NM = models.CharField(
        max_length=50,
        verbose_name="인분 수",
        null=True,
    )
    CKG_TIME_NM = models.CharField(
        max_length=50,
        verbose_name="조리 시간",
        null=True,
    )
    RCP_IMG_URL = models.TextField(
        verbose_name="레시피 이미지",
        null=True,
    )
    name = models.CharField(
        max_length=200,
        verbose_name="요리명",
        null=False,
    )
    instructions = models.TextField(
        verbose_name="조리방법",
        null=True,
    )

    class Meta:
        db_table = "recipes"
        verbose_name = "레시피"
        verbose_name_plural = "레시피"

    def __str__(self):
        return self.name

    # property 추가
    @property
    def image(self):
        return self.RCP_IMG_URL

    @property
    def cook_time(self):
        return self.CKG_TIME_NM

    @property
    def servings(self):
        return self.CKG_INBUN_NM

    @property
    def ingredients(self):
        return self.CKG_MTRL_CN
