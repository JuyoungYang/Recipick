from django.db import models

class Recipe(models.Model):
    # CSV 컬럼명과 매핑된 DB 필드
    CKG_NM = models.CharField(max_length=255, verbose_name="요리 이름", null=True)
    CKG_MTRL_CN = models.TextField(verbose_name="재료", null=True)
    CKG_INBUN_NM = models.CharField(max_length=50, verbose_name="인분", null=True)
    CKG_TIME_NM = models.CharField(max_length=50, verbose_name="조리 시간", null=True)
    RCP_IMG_URL = models.TextField(verbose_name="이미지 URL", null=True)
    CKG_METHOD_CN = models.TextField(verbose_name="조리 방법 (AI 생성)", null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성 날짜")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정 날짜")

    class Meta:
        db_table = "recipes"
        verbose_name = "레시피"
        verbose_name_plural = "레시피"

    def __str__(self):
        return self.CKG_NM if self.CKG_NM else "레시피 이름 없음"

    # API 응답이나 Serializer에서 사용하기 위한 프로퍼티
    @property
    def name(self):
        return self.CKG_NM

    @property
    def ingredients(self):
        return self.CKG_MTRL_CN

    @property
    def servings(self):
        return self.CKG_INBUN_NM

    @property
    def cook_time(self):
        return self.CKG_TIME_NM

    @property
    def image(self):
        return self.RCP_IMG_URL

    @property
    def instructions(self):
        return self.CKG_METHOD_CN
