import openai
from django.conf import settings


def save_recipe_with_ai_instructions(recipe):
    """
    AI를 사용하여 레시피 조리 방법을 생성하고 저장하는 유틸리티 함수
    """
    try:
        # GPT API 호출을 위한 프롬프트 생성
        prompt = f"""
        레시피 이름: {recipe.name}
        필요한 재료: {recipe.ingredients}
        조리 시간: {recipe.cook_time}분
        인분: {recipe.servings}인분
        
        위 레시피의 상세한 조리 방법을 단계별로 설명해주세요.
        """

        # GPT API 호출
        response = openai.ChatCompletion.create(
            model=settings.GPT_MODEL_NAME,
            messages=[
                {"role": "system", "content": settings.SYSTEM_RECIPE_EXPERT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1000,
        )

        # 생성된 조리 방법 저장
        instructions = response.choices[0].message.content.strip()
        recipe.cooking_instructions = instructions
        recipe.save()

        return instructions

    except Exception as e:
        raise Exception(f"레시피 생성 중 오류 발생: {str(e)}")
