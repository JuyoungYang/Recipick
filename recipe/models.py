from django.db import models


class Recipe(models.Model):
    # 요리명 필드 - 빈 값을 허용하지 않음
    name = models.CharField(
        max_length=200, verbose_name="요리명", null=False, blank=False
    )

    # 레시피 이미지 URL 필드 - 선택적 입력 가능
    image = models.URLField(
        verbose_name="레시피 이미지", null=True, blank=True, default=""
    )

    # 조리 시간 필드 - 선택적 입력 가능
    cook_time = models.CharField(
        max_length=50, verbose_name="조리 시간", null=True, blank=True, default=""
    )

    # 인분 수 필드 - 기본값 0
    servings = models.IntegerField(
        verbose_name="인분 수", null=True, blank=True, default=0
    )

    # 재료 목록 필드 - JSON 형식으로 저장
    ingredients = models.JSONField(
        verbose_name="재료 목록", null=True, blank=True, default=list
    )

    # 조리방법 필드 - 긴 텍스트 저장 가능
    instructions = models.TextField(
        verbose_name="조리방법", null=True, blank=True, default=""
    )

    def __str__(self):
        """
        모델의 문자열 표현을 반환합니다.
        Returns:
            str: 레시피 이름
        """
        return self.name

    class Meta:
        """
        Model metadata 정의
        """

        db_table = "recipes"  # 데이터베이스 테이블명
        verbose_name = "레시피"  # Admin 페이지에서 표시될 단수 이름
        verbose_name_plural = "레시피"  # Admin 페이지에서 표시될 복수 이름
